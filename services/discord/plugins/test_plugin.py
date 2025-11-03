#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_plugin.py

Discord Bot テストコマンドプラグイン

機能:
- 接続確認
- チャンネル通知
- 管理者機能テスト
"""

import os
import logging
from datetime import datetime

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)

# プロジェクトルートをPYTHONPATHに追加
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase


class TestPlugin(PluginBase, commands.Cog):
    """テストコマンドプラグイン"""

    def __init__(self, bot: commands.Bot):
        """
        Args:
            bot: Discord Botインスタンス
        """
        self.bot = bot
        logger.info("✅ テストプラグイン読み込み完了")

    @commands.command(name='ping')
    async def ping(self, ctx: commands.Context):
        """
        Bot応答確認

        使用例:
            !ping
        """
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"レイテンシ: {latency}ms",
            color=discord.Color.green()
        )
        embed.add_field(name="サーバー", value=ctx.guild.name if ctx.guild else "DM", inline=True)
        embed.add_field(name="チャンネル", value=ctx.channel.name if hasattr(ctx.channel, 'name') else "DM", inline=True)
        embed.set_footer(text=f"リクエスト: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    @commands.command(name='hello')
    async def hello(self, ctx: commands.Context):
        """
        挨拶コマンド

        使用例:
            !hello
        """
        user_mention = ctx.author.mention
        admin_config = getattr(self.bot, 'config', {}).get('admin', {})
        is_admin = str(ctx.author.id) in admin_config.get('user_ids', [])

        greeting = f"こんにちは、{user_mention}さん！"
        if is_admin:
            greeting += "\n👑 管理者権限を確認しました。"

        embed = discord.Embed(
            title="👋 NeuroHub Bot",
            description=greeting,
            color=discord.Color.blue()
        )
        embed.add_field(name="あなたのID", value=ctx.author.id, inline=True)
        embed.add_field(name="ユーザー名", value=ctx.author.name, inline=True)
        embed.set_thumbnail(url=ctx.author.avatar.url if ctx.author.avatar else None)
        embed.set_footer(text=f"起動時刻: {self.bot.start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        await ctx.send(embed=embed)

    @commands.command(name='info')
    async def info(self, ctx: commands.Context):
        """
        Bot情報表示

        使用例:
            !info
        """
        stats = self.bot.get_stats() if hasattr(self.bot, 'get_stats') else {}

        embed = discord.Embed(
            title="ℹ️ NeuroHub Bot 情報",
            description="AI統合Discord Bot",
            color=discord.Color.blue()
        )

        # Bot基本情報
        embed.add_field(name="Bot名", value=self.bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="稼働時間", value=stats.get('uptime_formatted', '不明'), inline=True)

        # サーバー情報
        embed.add_field(name="接続サーバー", value=f"{len(self.bot.guilds)} サーバー", inline=True)
        embed.add_field(name="総ユーザー数", value=f"{stats.get('users', 0)} ユーザー", inline=True)
        embed.add_field(name="プラグイン数", value=f"{stats.get('plugins_loaded', 0)} 個", inline=True)

        # 統計情報
        embed.add_field(name="処理メッセージ", value=f"{stats.get('messages_processed', 0)} 件", inline=True)
        embed.add_field(name="実行コマンド", value=f"{stats.get('commands_executed', 0)} 回", inline=True)
        embed.add_field(name="LLMリクエスト", value=f"{stats.get('llm_requests', 0)} 回", inline=True)

        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text=f"リクエスト: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    @commands.command(name='status')
    async def status(self, ctx: commands.Context):
        """
        Bot状態表示

        使用例:
            !status
        """
        # 管理者のみ実行可能
        if not self.bot.is_admin(ctx.author.id):
            await ctx.send("❌ このコマンドは管理者専用です")
            return

        stats = self.bot.get_stats() if hasattr(self.bot, 'get_stats') else {}

        embed = discord.Embed(
            title="📊 Bot ステータス",
            description="詳細統計情報",
            color=discord.Color.gold()
        )

        # システム情報
        embed.add_field(name="稼働時間", value=stats.get('uptime_formatted', '不明'), inline=False)

        # 統計情報
        stats_text = "\n".join([
            f"メッセージ処理: {stats.get('messages_processed', 0)} 件",
            f"コマンド実行: {stats.get('commands_executed', 0)} 回",
            f"スパムブロック: {stats.get('spam_blocked', 0)} 件",
            f"LLMリクエスト: {stats.get('llm_requests', 0)} 回",
            f"音声セッション: {stats.get('voice_sessions', 0)} 回"
        ])
        embed.add_field(name="📈 統計", value=stats_text, inline=False)

        # サーバー情報
        guilds_text = "\n".join([
            f"{guild.name} ({guild.member_count} ユーザー)"
            for guild in self.bot.guilds[:5]
        ])
        if len(self.bot.guilds) > 5:
            guilds_text += f"\n... 他 {len(self.bot.guilds) - 5} サーバー"

        embed.add_field(name="🏰 接続サーバー", value=guilds_text, inline=False)

        embed.set_footer(text=f"管理者: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    @commands.command(name='notify')
    async def notify(self, ctx: commands.Context, *, message: str):
        """
        通知チャンネルにメッセージを送信（管理者専用）

        使用例:
            !notify テストメッセージ
        """
        # 管理者のみ実行可能
        if not self.bot.is_admin(ctx.author.id):
            await ctx.send("❌ このコマンドは管理者専用です")
            return

        admin_config = getattr(self.bot, 'config', {}).get('admin', {})
        notification_channel_id = admin_config.get('notification_channel_id')

        if not notification_channel_id:
            await ctx.send("❌ 通知チャンネルが設定されていません")
            return

        try:
            channel = self.bot.get_channel(int(notification_channel_id))
            if not channel:
                await ctx.send("❌ 通知チャンネルが見つかりません")
                return

            embed = discord.Embed(
                title="📢 管理者通知",
                description=message,
                color=discord.Color.orange()
            )
            embed.set_footer(text=f"送信者: {ctx.author.display_name}")
            embed.timestamp = datetime.now()

            await channel.send(embed=embed)
            await ctx.send(f"✅ 通知を送信しました: <#{notification_channel_id}>")

        except Exception as e:
            await ctx.send(f"❌ 通知送信エラー: {str(e)}")
            logger.error(f"通知送信エラー: {e}")


async def setup(bot: commands.Bot):
    """プラグインセットアップ（自動読み込み用）"""
    await bot.add_cog(TestPlugin(bot))
