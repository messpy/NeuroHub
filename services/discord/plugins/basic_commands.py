#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
basic_commands.py

基本コマンドプラグイン
- ping/pong
- サーバー情報
- ユーザー情報
- Bot統計
"""

import discord
from discord.ext import commands

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase


class BasicCommands(PluginBase, commands.Cog):
    """基本コマンド集"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.description = "基本的なBot管理コマンド"
        self.version = "1.0.0"

    @commands.command(name='ping')
    async def ping(self, ctx: commands.Context):
        """Botの応答速度を確認"""
        latency = round(self.bot.latency * 1000)
        await ctx.send(f'🏓 Pong! レイテンシ: {latency}ms')

    @commands.command(name='info')
    async def info(self, ctx: commands.Context):
        """Botの情報を表示"""
        stats = self.bot.get_stats()

        embed = discord.Embed(
            title="🤖 NeuroHub Bot 情報",
            color=discord.Color.blue()
        )
        embed.add_field(name="サーバー数", value=stats['guilds'], inline=True)
        embed.add_field(name="ユーザー数", value=stats['users'], inline=True)
        embed.add_field(name="稼働時間", value=stats['uptime_formatted'], inline=True)
        embed.add_field(name="処理メッセージ", value=stats['messages_processed'], inline=True)
        embed.add_field(name="コマンド実行数", value=stats['commands_executed'], inline=True)
        embed.add_field(name="LLMリクエスト", value=stats['llm_requests'], inline=True)
        embed.add_field(name="プラグイン数", value=stats['plugins_loaded'], inline=True)
        embed.add_field(name="スパムブロック", value=stats['spam_blocked'], inline=True)

        await ctx.send(embed=embed)

    @commands.command(name='server')
    async def server(self, ctx: commands.Context):
        """サーバー情報を表示"""
        guild = ctx.guild

        embed = discord.Embed(
            title=f"🏠 {guild.name}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="サーバーID", value=guild.id, inline=False)
        embed.add_field(name="オーナー", value=guild.owner.mention, inline=True)
        embed.add_field(name="メンバー数", value=guild.member_count, inline=True)
        embed.add_field(name="チャンネル数", value=len(guild.channels), inline=True)
        embed.add_field(name="ロール数", value=len(guild.roles), inline=True)
        embed.add_field(name="作成日", value=guild.created_at.strftime('%Y-%m-%d'), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name='user')
    async def user(self, ctx: commands.Context, member: discord.Member = None):
        """ユーザー情報を表示"""
        member = member or ctx.author

        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ユーザー名", value=f"{member.name}#{member.discriminator}", inline=False)
        embed.add_field(name="ユーザーID", value=member.id, inline=True)
        embed.add_field(name="サーバー参加日", value=member.joined_at.strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="アカウント作成日", value=member.created_at.strftime('%Y-%m-%d'), inline=True)
        embed.add_field(name="ロール数", value=len(member.roles) - 1, inline=True)  # @everyoneを除く

        await ctx.send(embed=embed)

    @commands.command(name='help_custom')
    async def help_custom(self, ctx: commands.Context):
        """カスタムヘルプメッセージ"""
        embed = discord.Embed(
            title="📖 NeuroHub Bot ヘルプ",
            description="利用可能なコマンド一覧",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="🔧 基本コマンド",
            value="""
            `!ping` - Bot応答速度確認
            `!info` - Bot情報表示
            `!server` - サーバー情報表示
            `!user [@user]` - ユーザー情報表示
            """,
            inline=False
        )

        embed.add_field(
            name="🤖 AI機能",
            value="""
            `@NeuroHub [質問]` - AIに質問
            `!llm [質問]` - LLMで応答生成
            `!knowledge [検索ワード]` - ナレッジベース検索
            """,
            inline=False
        )

        embed.add_field(
            name="🎵 音声機能",
            value="""
            `!join` - ボイスチャンネルに参加
            `!leave` - ボイスチャンネルから退出
            `!tts [テキスト]` - テキスト読み上げ
            """,
            inline=False
        )

        embed.add_field(
            name="🛡️ 管理コマンド",
            value="""
            `!plugin list` - プラグイン一覧
            `!plugin load [name]` - プラグイン読み込み
            `!plugin unload [name]` - プラグイン無効化
            `!whitelist add [@user]` - ホワイトリスト追加
            """,
            inline=False
        )

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """プラグインセットアップ"""
    await bot.add_cog(BasicCommands(bot))
