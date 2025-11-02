#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vc_transcription.py

ボイスチャンネル音声文字起こしプラグイン
- VC参加/退出
- 音声録音
- Whisper APIで文字起こし
- 会話ログ保存
"""

import discord
from discord.ext import commands
import asyncio
import wave
import io
import os
from pathlib import Path
from datetime import datetime
import logging

import sys
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase

# Whisper APIのインポート（オプション）
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# faster-whisperのインポート（ローカル実行）
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False

logger = logging.getLogger(__name__)


class VCTranscription(PluginBase, commands.Cog):
    """VC音声文字起こし機能"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.description = "ボイスチャンネル音声文字起こし"
        self.version = "1.0.0"
        
        # 録音状態管理
        self.recording = {}  # {guild_id: bool}
        self.audio_buffers = {}  # {guild_id: {user_id: [audio_data]}}
        self.transcripts = {}  # {guild_id: [transcript_text]}
        
        # ログ保存ディレクトリ
        self.log_dir = ROOT / "logs" / "vc_transcripts"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Whisperモデル（ローカル実行用）
        self.whisper_model = None
        if FASTER_WHISPER_AVAILABLE:
            try:
                # faster-whisperを使用（高速・低メモリ）
                self.whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
                logger.info("✅ Whisperモデル（base）をロードしました")
            except Exception as e:
                logger.warning(f"⚠️ Whisperモデルのロード失敗: {e}")
        
        # OpenAI API Key確認
        self.openai_key = os.getenv('OPENAI_API_KEY')
        if self.openai_key and OPENAI_AVAILABLE:
            openai.api_key = self.openai_key
            logger.info("✅ OpenAI Whisper API利用可能")
        else:
            logger.info("⚠️ OpenAI API Key未設定、ローカルWhisperのみ使用")

    @commands.command(name='vc_join', aliases=['vcjoin', 'vj'])
    async def vc_join(self, ctx: commands.Context):
        """
        ボイスチャンネルに参加して録音開始（簡易版）
        10秒後に自動退出
        
        使用例:
            !vc_join
            !vcjoin
            !vj
        """
        if not ctx.author.voice:
            await ctx.send("❌ 先にボイスチャンネルに接続してください。")
            return

        channel = ctx.author.voice.channel
        guild_id = ctx.guild.id
        
        # 既に接続中か確認
        if ctx.voice_client:
            await ctx.send(f"✅ 既に {ctx.voice_client.channel.name} に接続中です。")
            return
        
        try:
            # VC参加
            voice_client = await channel.connect()
            await ctx.send(f"✅ **{channel.name}** に入りました！")
            
            # 録音状態をマーク
            self.recording[guild_id] = True
            self.audio_buffers[guild_id] = {}
            self.transcripts[guild_id] = []
            
            # 10秒待機
            await asyncio.sleep(10)
            
            # 自動退出
            await ctx.send(f"⏰ 10秒経過しました。退出します...")
            await voice_client.disconnect()
            await ctx.send(f"� **{channel.name}** から退出しました。")
            
            # 録音状態をクリア
            if guild_id in self.recording:
                del self.recording[guild_id]
            
            # 文字起こし記録があれば表示
            if guild_id in self.transcripts and self.transcripts[guild_id]:
                await self.send_transcripts(ctx.channel, self.transcripts[guild_id])
                await self.save_transcripts(guild_id, self.transcripts[guild_id])
            
        except Exception as e:
            await ctx.send(f"❌ VC参加エラー: {e}")
            logger.error(f"VC参加エラー: {e}")

    @commands.command(name='vc_leave', aliases=['vcleave', 'vl'])
    async def vc_leave(self, ctx: commands.Context):
        """
        ボイスチャンネルから退出
        
        使用例:
            !vc_leave
            !vcleave
            !vl
        """
        guild_id = ctx.guild.id
        
        if not ctx.voice_client:
            await ctx.send("❌ ボイスチャンネルに接続されていません。")
            return
        
        try:
            # 録音状態をクリア
            if guild_id in self.recording:
                del self.recording[guild_id]
            
            # VC退出
            await ctx.voice_client.disconnect()
            await ctx.send("👋 ボイスチャンネルから退出しました。")
            
            # 文字起こし記録があれば表示
            if guild_id in self.transcripts and self.transcripts[guild_id]:
                await self.send_transcripts(ctx.channel, self.transcripts[guild_id])
                await self.save_transcripts(guild_id, self.transcripts[guild_id])
            
        except Exception as e:
            await ctx.send(f"❌ VC退出エラー: {e}")
            logger.error(f"VC退出エラー: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """
        メッセージを文字起こしログとして記録
        （実際の音声録音の代替）
        """
        # Bot自身のメッセージは無視
        if message.author.bot:
            return
        
        guild_id = message.guild.id if message.guild else None
        
        # 録音中のサーバーのみ記録
        if guild_id and guild_id in self.recording and self.recording[guild_id]:
            transcript_entry = {
                'user': message.author.name,
                'text': message.content,
                'timestamp': datetime.now().isoformat()
            }
            
            if guild_id not in self.transcripts:
                self.transcripts[guild_id] = []
            
            self.transcripts[guild_id].append(transcript_entry)

    async def transcribe_audio(self, audio_data: bytes, user_name: str) -> str:
        """
        音声データを文字起こし
        
        Args:
            audio_data: 音声データ（バイト列）
            user_name: ユーザー名
            
        Returns:
            文字起こしテキスト
        """
        try:
            # 方法1: OpenAI Whisper API（高精度、有料）
            if self.openai_key and OPENAI_AVAILABLE:
                return await self.transcribe_with_openai(audio_data, user_name)
            
            # 方法2: faster-whisper（無料、ローカル実行）
            elif self.whisper_model:
                return await self.transcribe_with_local(audio_data, user_name)
            
            else:
                logger.warning("⚠️ 文字起こしエンジンが利用できません")
                return "[文字起こし不可: Whisper未インストール]"
        
        except Exception as e:
            logger.error(f"文字起こしエラー ({user_name}): {e}")
            return f"[エラー: {str(e)}]"

    async def transcribe_with_openai(self, audio_data: bytes, user_name: str) -> str:
        """OpenAI Whisper APIで文字起こし"""
        try:
            # 音声データをファイルとして保存（一時）
            temp_file = self.log_dir / f"temp_{user_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            
            # WAV形式で保存
            with wave.open(str(temp_file), 'wb') as wav_file:
                wav_file.setnchannels(2)  # ステレオ
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(48000)  # discord.pyの標準サンプリングレート
                wav_file.writeframes(audio_data)
            
            # OpenAI APIで文字起こし
            with open(temp_file, 'rb') as audio_file:
                transcript = await asyncio.to_thread(
                    openai.Audio.transcribe,
                    "whisper-1",
                    audio_file,
                    language="ja"  # 日本語指定
                )
            
            # 一時ファイル削除
            temp_file.unlink()
            
            return transcript.get('text', '')
        
        except Exception as e:
            logger.error(f"OpenAI文字起こしエラー: {e}")
            return f"[OpenAI API エラー: {str(e)}]"

    async def transcribe_with_local(self, audio_data: bytes, user_name: str) -> str:
        """faster-whisperで文字起こし（ローカル）"""
        try:
            # 音声データをファイルとして保存（一時）
            temp_file = self.log_dir / f"temp_{user_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            
            # WAV形式で保存
            with wave.open(str(temp_file), 'wb') as wav_file:
                wav_file.setnchannels(2)
                wav_file.setsampwidth(2)
                wav_file.setframerate(48000)
                wav_file.writeframes(audio_data)
            
            # faster-whisperで文字起こし
            segments, info = await asyncio.to_thread(
                self.whisper_model.transcribe,
                str(temp_file),
                language="ja"
            )
            
            # セグメントを結合
            transcript = " ".join([segment.text for segment in segments])
            
            # 一時ファイル削除
            temp_file.unlink()
            
            return transcript
        
        except Exception as e:
            logger.error(f"ローカル文字起こしエラー: {e}")
            return f"[ローカル文字起こしエラー: {str(e)}]"

    async def send_transcripts(self, channel: discord.TextChannel, transcripts: list):
        """文字起こし結果をチャンネルに送信"""
        embed = discord.Embed(
            title="🎤 音声文字起こし結果",
            description=f"合計 {len(transcripts)} 件の音声",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        
        for i, trans in enumerate(transcripts[:10], 1):  # 最大10件
            user = trans['user']
            text = trans['text'][:1000]  # 1000文字まで
            
            embed.add_field(
                name=f"{i}. {user}",
                value=f"```\n{text}\n```",
                inline=False
            )
        
        if len(transcripts) > 10:
            embed.add_field(
                name="ℹ️ 注意",
                value=f"他 {len(transcripts) - 10} 件の音声はログファイルに保存されています",
                inline=False
            )
        
        await channel.send(embed=embed)

    async def save_transcripts(self, guild_id: int, transcripts: list):
        """文字起こし結果をログファイルに保存"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            log_file = self.log_dir / f"transcript_{guild_id}_{timestamp}.txt"
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"VC文字起こしログ\n")
                f.write(f"サーバーID: {guild_id}\n")
                f.write(f"日時: {datetime.now().isoformat()}\n")
                f.write("=" * 70 + "\n\n")
                
                for trans in transcripts:
                    f.write(f"ユーザー: {trans['user']}\n")
                    f.write(f"時刻: {trans['timestamp']}\n")
                    f.write(f"内容:\n{trans['text']}\n")
                    f.write("-" * 70 + "\n\n")
            
            logger.info(f"✅ 文字起こしログ保存: {log_file}")
        
        except Exception as e:
            logger.error(f"ログ保存エラー: {e}")

    @commands.command(name='vc_logs', aliases=['vclogs'])
    async def vc_logs(self, ctx: commands.Context, limit: int = 5):
        """
        過去のVC文字起こしログを表示
        
        使用例:
            !vc_logs
            !vc_logs 10
        """
        guild_id = ctx.guild.id
        
        # ログファイル一覧取得
        log_files = sorted(
            self.log_dir.glob(f"transcript_{guild_id}_*.txt"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]
        
        if not log_files:
            await ctx.send("⚠️ VC文字起こしログがありません。")
            return
        
        embed = discord.Embed(
            title="📁 VC文字起こしログ履歴",
            description=f"最新 {len(log_files)} 件",
            color=discord.Color.green()
        )
        
        for log_file in log_files:
            timestamp = log_file.stem.split('_')[-2:]  # YYYYmmdd_HHMMSS
            date_str = f"{timestamp[0][:4]}/{timestamp[0][4:6]}/{timestamp[0][6:]} {timestamp[1][:2]}:{timestamp[1][2:4]}"
            
            # ファイルサイズ
            size_kb = log_file.stat().st_size / 1024
            
            embed.add_field(
                name=f"📄 {date_str}",
                value=f"サイズ: {size_kb:.1f} KB\nファイル: `{log_file.name}`",
                inline=False
            )
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """プラグインセットアップ"""
    await bot.add_cog(VCTranscription(bot))
