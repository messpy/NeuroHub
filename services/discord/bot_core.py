#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bot_core.py

NeuroHub Discord Bot コアシステム
- プラグインベース拡張性
- LLM統合
- データベース連携
- 音声機能
- 荒らし対策
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv

# .envファイルの読み込み
load_dotenv()

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.db.database_manager import DatabaseManager
from services.db.knowledge_manager import KnowledgeManager
from services.discord.plugin_manager import PluginManager
from services.discord.anti_spam import AntiSpamManager
from services.discord.voice_manager import VoiceManager

logger = logging.getLogger(__name__)


class NeuroHubBot(commands.Bot):
    """
    NeuroHub Discord Bot

    機能:
    - プラグインベース拡張システム
    - LLM連携（Ollama等）
    - データベース統合
    - 音声認識・TTS
    - 荒らし対策（レート制限、スパム検出）
    - ナレッジベース活用
    """

    def __init__(self, command_prefix: str = "!", intents: discord.Intents = None):
        """
        Args:
            command_prefix: コマンドプレフィックス（デフォルト: !）
            intents: Discord intents（NoneならデフォルトIntents使用）
        """
        # Intentsの設定（全権限）
        if intents is None:
            intents = discord.Intents.default()
            intents.message_content = True
            intents.voice_states = True
            intents.members = True
            intents.presences = True

        super().__init__(command_prefix=command_prefix, intents=intents)

        # コアコンポーネント
        self.db = DatabaseManager()
        self.km = KnowledgeManager(self.db)
        self.plugin_manager = PluginManager(self)
        self.anti_spam = AntiSpamManager(self)
        self.voice_manager = VoiceManager(self)

        # Bot設定
        self.start_time = datetime.now()
        self.config = self._load_config()
        self.llm_config = self._load_llm_config()

        # 統計情報
        self.stats = {
            'messages_processed': 0,
            'commands_executed': 0,
            'spam_blocked': 0,
            'llm_requests': 0,
            'voice_sessions': 0
        }

        # イベントハンドラー登録
        self._register_event_handlers()

        logger.info("🤖 NeuroHub Discord Bot 初期化完了")

    def _load_config(self) -> Dict[str, Any]:
        """Discord Bot設定を読み込み"""
        config_path = ROOT / "config" / "discord_config.yaml"
        if config_path.exists():
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
        else:
            config = {}

        # 環境変数から管理者設定を読み込み
        admin_user_ids = os.getenv('DISCORD_ADMIN_USER_IDS', '').split(',')
        admin_usernames = os.getenv('DISCORD_ADMIN_USERNAMES', '').split(',')

        # デフォルト設定
        default_config = {
            'bot': {
                'prefix': '!',
                'description': 'NeuroHub AI Discord Bot',
                'status': 'NeuroHubで稼働中'
            },
            'features': {
                'llm_enabled': True,
                'voice_enabled': True,
                'anti_spam_enabled': True,
                'knowledge_base_enabled': True,
                'vision_enabled': True,
                'reaction_enabled': True
            },
            'anti_spam': {
                'max_messages_per_minute': 10,
                'max_duplicate_messages': 3,
                'timeout_duration': 60
            },
            'admin': {
                'user_ids': [uid.strip() for uid in admin_user_ids if uid.strip()],
                'usernames': [name.strip() for name in admin_usernames if name.strip()],
                'main_guild_id': os.getenv('DISCORD_MAIN_GUILD_ID'),
                'log_channel_id': os.getenv('DISCORD_LOG_CHANNEL_ID'),
                'notification_channel_id': os.getenv('DISCORD_NOTIFICATION_CHANNEL_ID')
            }
        }

        # デフォルト設定とマージ
        def merge_dict(default, custom):
            for key, value in custom.items():
                if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                    merge_dict(default[key], value)
                else:
                    default[key] = value
            return default

        return merge_dict(default_config, config)

    def _load_llm_config(self) -> Dict[str, Any]:
        """LLM設定を読み込み"""
        llm_config_path = ROOT / "config" / "llm_config.yaml"
        if llm_config_path.exists():
            import yaml
            with open(llm_config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        return {}

    def _register_event_handlers(self):
        """イベントハンドラーを登録"""
        @self.event
        async def on_ready():
            """Bot起動完了時"""
            logger.info(f"✅ {self.user.name} としてログイン成功！")
            logger.info(f"Bot ID: {self.user.id}")
            logger.info(f"接続サーバー数: {len(self.guilds)}")

            # 管理者ユーザーの確認
            admin_config = self.config.get('admin', {})
            admin_ids = admin_config.get('user_ids', [])
            if admin_ids:
                logger.info(f"👑 管理者ID: {admin_ids}")

            # ステータス設定
            status = self.config.get('bot', {}).get('status', 'NeuroHubで稼働中')
            await self.change_presence(
                activity=discord.Game(name=status)
            )

            # プラグイン読み込み
            await self.plugin_manager.load_all_plugins()

            # コマンドリスト表示（デバッグ用）
            logger.info(f"📋 登録コマンド数: {len(self.commands)}")
            for cmd in self.commands:
                logger.info(f"  - {cmd.name} ({cmd.cog_name if cmd.cog else 'No Cog'})")

            # ログチャンネルに起動通知
            await self._send_startup_notification()

            # データベースにBot起動記録
            self._log_bot_event('bot_start', {'guilds': len(self.guilds)})

        @self.event
        async def on_message(message: discord.Message):
            """メッセージ受信時"""
            # Botメッセージは無視
            if message.author.bot:
                return

            self.stats['messages_processed'] += 1

            # 荒らし対策チェック
            if self.config.get('features', {}).get('anti_spam_enabled', True):
                if await self.anti_spam.check_spam(message):
                    self.stats['spam_blocked'] += 1
                    return

            # LLMメンション応答
            if self.user in message.mentions and self.config.get('features', {}).get('llm_enabled', True):
                await self._handle_llm_mention(message)

            # コマンド処理
            await self.process_commands(message)

        @self.event
        async def on_command(ctx: commands.Context):
            """コマンド実行時"""
            self.stats['commands_executed'] += 1
            logger.info(f"コマンド実行: {ctx.command} by {ctx.author}")

        @self.event
        async def on_command_error(ctx: commands.Context, error: commands.CommandError):
            """コマンドエラー時"""
            logger.error(f"コマンドエラー: {error}")

            if isinstance(error, commands.CommandNotFound):
                await ctx.send(f"❌ コマンドが見つかりません。`{self.command_prefix}help`でコマンド一覧を確認してください。")
            elif isinstance(error, commands.MissingPermissions):
                await ctx.send("❌ このコマンドを実行する権限がありません。")
            elif isinstance(error, commands.MissingRequiredArgument):
                await ctx.send(f"❌ 必須引数が不足しています: `{error.param.name}`")
            else:
                await ctx.send(f"❌ エラーが発生しました: {str(error)}")

        @self.event
        async def on_voice_state_update(member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
            """ボイスチャンネル状態変更時"""
            if self.config.get('features', {}).get('voice_enabled', True):
                await self.voice_manager.handle_voice_state_update(member, before, after)

    async def _handle_llm_mention(self, message: discord.Message):
        """LLMメンション応答処理"""
        try:
            # メンションを除去してクエリ抽出
            query = message.content.replace(f'<@{self.user.id}>', '').strip()

            if not query:
                await message.reply("何か質問してください！")
                return

            # タイピング表示
            async with message.channel.typing():
                # LLM呼び出し
                response = await self._call_llm(query, message.author.id)
                self.stats['llm_requests'] += 1

                # ナレッジベース検索
                knowledge = self.km.search_knowledge(query, limit=3)

                # 応答送信
                embed = discord.Embed(
                    title="🤖 NeuroHub AI応答",
                    description=response,
                    color=discord.Color.blue()
                )

                if knowledge:
                    kb_text = "\n".join([f"• {k['title']}" for k in knowledge[:2]])
                    embed.add_field(name="📚 関連ナレッジ", value=kb_text, inline=False)

                embed.set_footer(text=f"リクエスト: {message.author.display_name}")
                await message.reply(embed=embed)

                # LLM履歴をDBに記録
                self._log_llm_interaction(query, response, message.author.id)

        except Exception as e:
            logger.error(f"LLM応答エラー: {e}")
            await message.reply(f"❌ LLM処理中にエラーが発生しました: {str(e)}")

    async def _call_llm(self, query: str, user_id: int) -> str:
        """LLMを呼び出し"""
        try:
            # agents/llm_agent.pyを使用
            from agents.agent_llm import LLMAgent

            agent = LLMAgent()
            response = await asyncio.to_thread(
                agent.query,
                query,
                provider='ollama'  # デフォルトはOllama
            )

            return response if response else "申し訳ございません、応答を生成できませんでした。"

        except Exception as e:
            logger.error(f"LLM呼び出しエラー: {e}")
            return f"LLMエラー: {str(e)}"

    def _log_bot_event(self, event_type: str, data: Dict[str, Any]):
        """Botイベントをデータベースに記録"""
        try:
            event_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'event_type': event_type,
                'data': str(data),
                'bot_id': str(self.user.id) if self.user else 'unknown'
            }
            # 専用テーブルがあれば記録（なければスキップ）
            # self.db.insert_data('bot_events', event_data)
        except Exception as e:
            logger.warning(f"イベント記録エラー: {e}")

    def _log_llm_interaction(self, query: str, response: str, user_id: int):
        """LLM対話をデータベースに記録"""
        try:
            llm_data = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'session_id': f'discord_{user_id}',
                'provider': 'ollama',
                'model': self.llm_config.get('llm', {}).get('providers', {}).get('ollama', {}).get('model', 'unknown'),
                'request_type': 'discord_mention',
                'prompt_text': query,
                'response_text': response,
                'status_code': 200,
                'success': True,
                'token_count_input': len(query.split()),
                'token_count_output': len(response.split()),
                'token_count_total': len(query.split()) + len(response.split()),
                'metadata': f'{{"user_id": {user_id}}}'
            }
            self.db.insert_data('llm_history', llm_data)
        except Exception as e:
            logger.warning(f"LLM履歴記録エラー: {e}")

    async def _send_startup_notification(self):
        """起動通知をログチャンネルに送信"""
        try:
            admin_config = self.config.get('admin', {})
            log_channel_id = admin_config.get('log_channel_id')

            logger.info(f"📢 起動通知送信開始 - チャンネルID: {log_channel_id}")

            if log_channel_id:
                channel = self.get_channel(int(log_channel_id))
                logger.info(f"📢 チャンネル取得: {channel}")

                if channel:
                    embed = discord.Embed(
                        title="🚀 NeuroHub Bot 起動",
                        description="Botが正常に起動しました",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="サーバー数", value=len(self.guilds), inline=True)
                    embed.add_field(name="プラグイン数", value=len(self.plugin_manager.plugins), inline=True)
                    embed.add_field(name="起動時刻", value=self.start_time.strftime('%Y-%m-%d %H:%M:%S'), inline=True)

                    await channel.send(embed=embed)
                    logger.info("✅ 起動通知送信成功")
                else:
                    logger.warning(f"⚠️ チャンネルが見つかりません: {log_channel_id}")
            else:
                logger.warning("⚠️ log_channel_idが設定されていません")
        except Exception as e:
            logger.error(f"❌ 起動通知送信エラー: {e}", exc_info=True)

    def is_admin(self, user_id: int) -> bool:
        """ユーザーが管理者かどうかチェック"""
        admin_config = self.config.get('admin', {})
        admin_ids = admin_config.get('user_ids', [])
        return str(user_id) in admin_ids

    def is_admin_username(self, username: str) -> bool:
        """ユーザー名が管理者かどうかチェック"""
        admin_config = self.config.get('admin', {})
        admin_usernames = admin_config.get('usernames', [])
        return username.lower() in [name.lower() for name in admin_usernames]

    async def send_log(self, message: str, level: str = "info"):
        """ログチャンネルにメッセージを送信"""
        try:
            admin_config = self.config.get('admin', {})
            log_channel_id = admin_config.get('log_channel_id')

            if log_channel_id:
                channel = self.get_channel(int(log_channel_id))
                if channel:
                    colors = {
                        'info': discord.Color.blue(),
                        'warning': discord.Color.orange(),
                        'error': discord.Color.red(),
                        'success': discord.Color.green()
                    }

                    embed = discord.Embed(
                        title=f"📋 {level.upper()}",
                        description=message,
                        color=colors.get(level, discord.Color.blue())
                    )
                    await channel.send(embed=embed)
        except Exception as e:
            logger.warning(f"ログ送信エラー: {e}")

    async def add_plugin(self, plugin_path: str):
        """プラグインを追加"""
        return await self.plugin_manager.load_plugin(plugin_path)

    async def remove_plugin(self, plugin_name: str):
        """プラグインを削除"""
        return await self.plugin_manager.unload_plugin(plugin_name)

    def get_stats(self) -> Dict[str, Any]:
        """統計情報を取得"""
        uptime = datetime.now() - self.start_time
        return {
            **self.stats,
            'uptime_seconds': uptime.total_seconds(),
            'uptime_formatted': str(uptime).split('.')[0],
            'guilds': len(self.guilds),
            'users': sum(g.member_count for g in self.guilds),
            'plugins_loaded': len(self.plugin_manager.plugins)
        }

    async def shutdown(self):
        """Botをシャットダウン"""
        logger.info("🛑 Bot シャットダウン中...")

        # 音声接続を全て切断
        for vc in self.voice_clients:
            await vc.disconnect()

        # プラグインをアンロード
        await self.plugin_manager.unload_all_plugins()

        # データベース記録
        self._log_bot_event('bot_shutdown', self.get_stats())

        await self.close()
        logger.info("✅ Bot シャットダウン完了")


def run_bot(token: str = None):
    """
    Botを起動

    Args:
        token: Discord Bot Token（Noneなら環境変数から取得）
    """
    if token is None:
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            raise ValueError("DISCORD_BOT_TOKEN が設定されていません")

    bot = NeuroHubBot()

    try:
        bot.run(token)
    except KeyboardInterrupt:
        logger.info("Ctrl+C 検出 - シャットダウン中...")
        asyncio.run(bot.shutdown())
    except Exception as e:
        logger.error(f"Bot実行エラー: {e}")
        raise


if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    run_bot()
