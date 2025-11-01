#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice_manager.py

Discord Bot 音声機能マネージャー
- ボイスチャンネル接続・切断
- 音声認識（Speech-to-Text）
- 音声合成（Text-to-Speech）
- 音楽再生
"""

import asyncio
import logging
from typing import Dict, Optional, List
from pathlib import Path

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class VoiceManager:
    """
    音声機能マネージャー

    機能:
    - ボイスチャンネル参加/退出
    - 音声認識（将来的にWhisper統合）
    - TTS（Text-to-Speech）
    - 音楽再生・キュー管理
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # アクティブな音声接続
        self.voice_clients: Dict[int, discord.VoiceClient] = {}

        # 音楽キュー（サーバーごと）
        self.music_queues: Dict[int, asyncio.Queue] = {}

        # 音声認識状態
        self.recognition_active: Dict[int, bool] = {}

        # 設定
        self.config = {
            'auto_disconnect_timeout': 300,  # 5分間使用がなければ自動切断
            'max_queue_size': 50,             # 音楽キューの最大サイズ
            'default_volume': 0.5             # デフォルト音量（0.0-1.0）
        }

        logger.info("🎵 VoiceManager 初期化完了")

    async def join_voice_channel(self, channel: discord.VoiceChannel) -> Optional[discord.VoiceClient]:
        """
        ボイスチャンネルに参加

        Args:
            channel: 参加するボイスチャンネル

        Returns:
            discord.VoiceClient: 接続成功時のVoiceClient
        """
        try:
            # すでに接続されている場合は移動
            guild_id = channel.guild.id
            if guild_id in self.voice_clients:
                voice_client = self.voice_clients[guild_id]
                await voice_client.move_to(channel)
                logger.info(f"🎵 ボイスチャンネル移動: {channel.name}")
                return voice_client

            # 新規接続
            voice_client = await channel.connect()
            self.voice_clients[guild_id] = voice_client

            # 音楽キュー初期化
            if guild_id not in self.music_queues:
                self.music_queues[guild_id] = asyncio.Queue(maxsize=self.config['max_queue_size'])

            logger.info(f"✅ ボイスチャンネル接続: {channel.name}")
            return voice_client

        except Exception as e:
            logger.error(f"❌ ボイスチャンネル接続エラー: {e}")
            return None

    async def leave_voice_channel(self, guild_id: int) -> bool:
        """
        ボイスチャンネルから退出

        Args:
            guild_id: サーバーID

        Returns:
            bool: 成功したらTrue
        """
        try:
            if guild_id not in self.voice_clients:
                return False

            voice_client = self.voice_clients[guild_id]
            await voice_client.disconnect()

            del self.voice_clients[guild_id]

            # 音楽キューをクリア
            if guild_id in self.music_queues:
                while not self.music_queues[guild_id].empty():
                    self.music_queues[guild_id].get_nowait()

            logger.info(f"👋 ボイスチャンネル退出: Guild {guild_id}")
            return True

        except Exception as e:
            logger.error(f"❌ ボイスチャンネル退出エラー: {e}")
            return False

    async def handle_voice_state_update(self, member: discord.Member,
                                       before: discord.VoiceState,
                                       after: discord.VoiceState):
        """
        ボイスチャンネル状態変更時のハンドラー

        Args:
            member: メンバー
            before: 変更前の状態
            after: 変更後の状態
        """
        guild_id = member.guild.id

        # Bot自身の状態変更は無視
        if member.id == self.bot.user.id:
            return

        # ボイスチャンネルに誰もいなくなったら退出
        if guild_id in self.voice_clients:
            voice_client = self.voice_clients[guild_id]
            if voice_client.channel:
                # Botを除くメンバー数をカウント
                human_members = [m for m in voice_client.channel.members if not m.bot]

                if len(human_members) == 0:
                    logger.info(f"🚪 ボイスチャンネルが空になったため退出します: {voice_client.channel.name}")
                    await asyncio.sleep(5)  # 5秒待ってから退出

                    # 再度確認（5秒以内に誰か入ったかもしれない）
                    human_members = [m for m in voice_client.channel.members if not m.bot]
                    if len(human_members) == 0:
                        await self.leave_voice_channel(guild_id)

    async def play_audio(self, guild_id: int, audio_source: discord.AudioSource) -> bool:
        """
        音声を再生

        Args:
            guild_id: サーバーID
            audio_source: 音声ソース

        Returns:
            bool: 成功したらTrue
        """
        try:
            if guild_id not in self.voice_clients:
                logger.warning("⚠️ ボイスチャンネルに接続されていません")
                return False

            voice_client = self.voice_clients[guild_id]

            # すでに再生中なら停止
            if voice_client.is_playing():
                voice_client.stop()

            voice_client.play(audio_source)
            logger.info(f"▶️ 音声再生開始: Guild {guild_id}")
            return True

        except Exception as e:
            logger.error(f"❌ 音声再生エラー: {e}")
            return False

    async def play_file(self, guild_id: int, file_path: str, volume: float = None) -> bool:
        """
        音声ファイルを再生

        Args:
            guild_id: サーバーID
            file_path: 音声ファイルパス
            volume: 音量（0.0-1.0、Noneならデフォルト）

        Returns:
            bool: 成功したらTrue
        """
        if volume is None:
            volume = self.config['default_volume']

        try:
            audio_source = discord.FFmpegPCMAudio(file_path)
            audio_source = discord.PCMVolumeTransformer(audio_source, volume=volume)

            return await self.play_audio(guild_id, audio_source)

        except Exception as e:
            logger.error(f"❌ ファイル再生エラー: {e}")
            return False

    async def text_to_speech(self, guild_id: int, text: str, language: str = 'ja') -> bool:
        """
        Text-to-Speech（テキストを音声で再生）

        Args:
            guild_id: サーバーID
            text: 読み上げテキスト
            language: 言語コード（デフォルト: ja）

        Returns:
            bool: 成功したらTrue
        """
        try:
            # gTTS（Google Text-to-Speech）を使用
            from gtts import gTTS
            import tempfile

            # 一時ファイルに音声保存
            tts = gTTS(text=text, lang=language)

            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as fp:
                temp_file = fp.name
                tts.save(temp_file)

            # 音声再生
            success = await self.play_file(guild_id, temp_file)

            # 再生終了後にファイル削除（非同期で待機）
            async def cleanup():
                await asyncio.sleep(10)  # 再生完了を待つ
                try:
                    Path(temp_file).unlink()
                except:
                    pass

            asyncio.create_task(cleanup())

            return success

        except ImportError:
            logger.error("❌ gTTSがインストールされていません: pip install gtts")
            return False
        except Exception as e:
            logger.error(f"❌ TTS エラー: {e}")
            return False

    async def start_speech_recognition(self, guild_id: int) -> bool:
        """
        音声認識を開始（将来的にWhisper統合）

        Args:
            guild_id: サーバーID

        Returns:
            bool: 成功したらTrue
        """
        if guild_id not in self.voice_clients:
            logger.warning("⚠️ ボイスチャンネルに接続されていません")
            return False

        # TODO: Whisper等の音声認識エンジン統合
        self.recognition_active[guild_id] = True
        logger.info(f"🎤 音声認識開始: Guild {guild_id}")
        return True

    async def stop_speech_recognition(self, guild_id: int) -> bool:
        """
        音声認識を停止

        Args:
            guild_id: サーバーID

        Returns:
            bool: 成功したらTrue
        """
        if guild_id in self.recognition_active:
            self.recognition_active[guild_id] = False
            logger.info(f"🛑 音声認識停止: Guild {guild_id}")
            return True
        return False

    def is_connected(self, guild_id: int) -> bool:
        """ボイスチャンネルに接続中か確認"""
        return guild_id in self.voice_clients

    def is_playing(self, guild_id: int) -> bool:
        """音声再生中か確認"""
        if guild_id not in self.voice_clients:
            return False
        return self.voice_clients[guild_id].is_playing()

    async def set_volume(self, guild_id: int, volume: float) -> bool:
        """
        音量を変更

        Args:
            guild_id: サーバーID
            volume: 音量（0.0-1.0）

        Returns:
            bool: 成功したらTrue
        """
        if guild_id not in self.voice_clients:
            return False

        voice_client = self.voice_clients[guild_id]
        if hasattr(voice_client.source, 'volume'):
            voice_client.source.volume = max(0.0, min(1.0, volume))
            logger.info(f"🔊 音量変更: {volume * 100}%")
            return True
        return False
