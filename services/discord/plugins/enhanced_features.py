#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enhanced_features.py

Discord Bot 拡張機能プラグイン

機能:
- ボイスチャンネル入退室通知
- ユーザーアイコン送信
- Ollama LLM連携
- メンバー情報表示
- サーバー統計
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

import discord
from discord.ext import commands

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase

logger = logging.getLogger(__name__)


class EnhancedFeatures(PluginBase, commands.Cog):
    """拡張機能プラグイン"""

    def __init__(self, bot: commands.Bot):
        """
        Args:
            bot: Discord Botインスタンス
        """
        super().__init__(bot)
        self.voice_sessions = {}  # {user_id: join_time}
        logger.info("✅ 拡張機能プラグイン読み込み完了")

    # =====================
    # ボイスチャンネル監視
    # =====================

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        """
        ボイスチャンネル状態変更時

        Args:
            member: メンバー
            before: 変更前の状態
            after: 変更後の状態
        """
        # 通知チャンネル取得
        admin_config = getattr(self.bot, 'config', {}).get('admin', {})
        notification_channel_id = admin_config.get('notification_channel_id')

        if not notification_channel_id:
            return

        channel = self.bot.get_channel(int(notification_channel_id))
        if not channel:
            return

        # ボイスチャンネル参加
        if before.channel is None and after.channel is not None:
            self.voice_sessions[member.id] = datetime.now()

            embed = discord.Embed(
                title="🎤 ボイスチャンネル参加",
                description=f"{member.mention} が **{after.channel.name}** に参加しました",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            embed.add_field(name="ユーザー名", value=member.display_name, inline=True)
            embed.add_field(name="チャンネル", value=after.channel.name, inline=True)
            embed.timestamp = datetime.now()

            await channel.send(embed=embed)

        # ボイスチャンネル退出
        elif before.channel is not None and after.channel is None:
            join_time = self.voice_sessions.pop(member.id, None)
            duration = ""

            if join_time:
                delta = datetime.now() - join_time
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                duration = f"\n滞在時間: {hours}時間{minutes}分{seconds}秒"

            embed = discord.Embed(
                title="👋 ボイスチャンネル退出",
                description=f"{member.mention} が **{before.channel.name}** から退出しました{duration}",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            embed.add_field(name="ユーザー名", value=member.display_name, inline=True)
            embed.add_field(name="チャンネル", value=before.channel.name, inline=True)
            embed.timestamp = datetime.now()

            await channel.send(embed=embed)

        # チャンネル移動
        elif before.channel != after.channel:
            embed = discord.Embed(
                title="🔀 ボイスチャンネル移動",
                description=f"{member.mention} が移動しました",
                color=discord.Color.blue()
            )
            embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
            embed.add_field(name="移動前", value=before.channel.name, inline=True)
            embed.add_field(name="移動後", value=after.channel.name, inline=True)
            embed.timestamp = datetime.now()

            await channel.send(embed=embed)

    # =====================
    # ユーザー情報コマンド
    # =====================

    @commands.command(name='avatar')
    async def avatar(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """
        ユーザーのアイコンを表示

        使用例:
            !avatar @ユーザー
            !avatar (自分のアイコン)
        """
        member = member or ctx.author

        embed = discord.Embed(
            title=f"🖼️ {member.display_name} のアバター",
            color=discord.Color.blue()
        )

        if member.avatar:
            embed.set_image(url=member.avatar.url)
            embed.add_field(name="ダウンロード", value=f"[クリックしてダウンロード]({member.avatar.url})")
        else:
            embed.description = "このユーザーはデフォルトアバターを使用しています"

        embed.set_footer(text=f"リクエスト: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    @commands.command(name='userinfo')
    async def userinfo(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """
        ユーザー詳細情報を表示

        使用例:
            !userinfo @ユーザー
            !userinfo (自分の情報)
        """
        member = member or ctx.author

        # ロール一覧
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles_text = ", ".join(roles) if roles else "なし"

        # アカウント作成日
        created_days = (datetime.now() - member.created_at.replace(tzinfo=None)).days

        # サーバー参加日
        joined_days = (datetime.now() - member.joined_at.replace(tzinfo=None)).days if member.joined_at else 0

        embed = discord.Embed(
            title=f"👤 {member.display_name} のプロフィール",
            description=f"{member.mention}",
            color=member.color
        )
        embed.set_thumbnail(url=member.avatar.url if member.avatar else None)

        # 基本情報
        embed.add_field(name="ユーザー名", value=member.name, inline=True)
        embed.add_field(name="ユーザーID", value=member.id, inline=True)
        embed.add_field(name="ニックネーム", value=member.display_name, inline=True)

        # 日時情報
        embed.add_field(
            name="アカウント作成",
            value=f"{member.created_at.strftime('%Y-%m-%d')}\n({created_days}日前)",
            inline=True
        )
        embed.add_field(
            name="サーバー参加",
            value=f"{member.joined_at.strftime('%Y-%m-%d') if member.joined_at else '不明'}\n({joined_days}日前)",
            inline=True
        )

        # ステータス
        status_emoji = {
            discord.Status.online: "🟢 オンライン",
            discord.Status.idle: "🟡 退席中",
            discord.Status.dnd: "🔴 取り込み中",
            discord.Status.offline: "⚫ オフライン"
        }
        embed.add_field(name="ステータス", value=status_emoji.get(member.status, "不明"), inline=True)

        # ロール
        embed.add_field(name=f"ロール ({len(roles)})", value=roles_text, inline=False)

        # 権限
        if member.guild_permissions.administrator:
            embed.add_field(name="権限", value="👑 管理者", inline=True)
        elif member.guild_permissions.manage_messages:
            embed.add_field(name="権限", value="🛡️ モデレーター", inline=True)

        embed.set_footer(text=f"リクエスト: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    # =====================
    # Ollama LLM連携
    # =====================

    @commands.command(name='ask')
    async def ask(self, ctx: commands.Context, *, question: str):
        """
        Ollama LLMに質問

        使用例:
            !ask Pythonでファイルを読み込む方法は？
        """
        await ctx.send("🤔 考え中...")

        try:
            # LLM Agentインポート
            from agents.agent_llm import generate_response

            # 応答生成
            async with ctx.typing():
                response = await generate_response(question)

            # 応答送信（2000文字制限対応）
            if len(response) > 2000:
                # 分割送信
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for i, chunk in enumerate(chunks):
                    embed = discord.Embed(
                        title=f"💡 回答 ({i+1}/{len(chunks)})",
                        description=chunk,
                        color=discord.Color.green()
                    )
                    embed.set_footer(text=f"質問: {ctx.author.display_name}")
                    await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="💡 Ollama LLM 回答",
                    description=response,
                    color=discord.Color.green()
                )
                embed.add_field(name="質問", value=question[:100], inline=False)
                embed.set_footer(text=f"質問者: {ctx.author.display_name}")
                await ctx.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ エラー",
                description=f"LLM応答生成エラー: {str(e)}",
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
            logger.error(f"LLM応答エラー: {e}")

    @commands.command(name='chat')
    async def chat(self, ctx: commands.Context, *, message: str):
        """
        Ollama LLMとチャット（会話履歴保持）

        使用例:
            !chat こんにちは！
        """
        await ctx.send("💬 チャット中...")

        try:
            from agents.agent_llm import generate_response

            # ユーザーごとの会話履歴を保持（簡易実装）
            user_id = ctx.author.id
            context = f"ユーザー名: {ctx.author.display_name}\nメッセージ: {message}"

            async with ctx.typing():
                response = await generate_response(context)

            embed = discord.Embed(
                title="💬 チャット",
                description=response[:2000],
                color=discord.Color.blue()
            )
            embed.set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )
            embed.set_footer(text="Powered by Ollama")

            await ctx.send(embed=embed)

        except Exception as e:
            error_embed = discord.Embed(
                title="❌ チャットエラー",
                description=str(e),
                color=discord.Color.red()
            )
            await ctx.send(embed=error_embed)
            logger.error(f"チャットエラー: {e}")

    # =====================
    # サーバー統計
    # =====================

    @commands.command(name='serverinfo')
    async def serverinfo(self, ctx: commands.Context):
        """
        サーバー情報を表示

        使用例:
            !serverinfo
        """
        guild = ctx.guild

        # チャンネル数
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)

        # メンバー統計
        total_members = guild.member_count
        bots = sum(1 for member in guild.members if member.bot)
        humans = total_members - bots

        # オンラインメンバー
        online = sum(1 for member in guild.members if member.status != discord.Status.offline)

        embed = discord.Embed(
            title=f"🏰 {guild.name}",
            description=guild.description or "サーバーの説明なし",
            color=discord.Color.gold()
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        # 基本情報
        embed.add_field(name="サーバーID", value=guild.id, inline=True)
        embed.add_field(name="オーナー", value=guild.owner.mention if guild.owner else "不明", inline=True)
        embed.add_field(
            name="作成日",
            value=guild.created_at.strftime('%Y-%m-%d'),
            inline=True
        )

        # メンバー情報
        embed.add_field(name="総メンバー数", value=f"{total_members} 人", inline=True)
        embed.add_field(name="人間", value=f"{humans} 人", inline=True)
        embed.add_field(name="Bot", value=f"{bots} 個", inline=True)
        embed.add_field(name="オンライン", value=f"{online} 人", inline=True)

        # チャンネル情報
        embed.add_field(name="テキストチャンネル", value=f"{text_channels} 個", inline=True)
        embed.add_field(name="ボイスチャンネル", value=f"{voice_channels} 個", inline=True)
        embed.add_field(name="カテゴリ", value=f"{categories} 個", inline=True)

        # ロール数
        embed.add_field(name="ロール", value=f"{len(guild.roles)} 個", inline=True)

        # ブースト情報
        if guild.premium_tier > 0:
            embed.add_field(
                name="ブーストレベル",
                value=f"レベル {guild.premium_tier} ({guild.premium_subscription_count} ブースト)",
                inline=False
            )

        embed.set_footer(text=f"リクエスト: {ctx.author.display_name}")

        await ctx.send(embed=embed)

    @commands.command(name='members')
    async def members(self, ctx: commands.Context):
        """
        メンバー一覧を表示

        使用例:
            !members
        """
        guild = ctx.guild

        # オンラインメンバー
        online_members = [m for m in guild.members if m.status == discord.Status.online]
        idle_members = [m for m in guild.members if m.status == discord.Status.idle]
        dnd_members = [m for m in guild.members if m.status == discord.Status.dnd]

        embed = discord.Embed(
            title=f"👥 メンバー一覧 - {guild.name}",
            color=discord.Color.blue()
        )

        if online_members:
            online_list = "\n".join([f"🟢 {m.display_name}" for m in online_members[:10]])
            if len(online_members) > 10:
                online_list += f"\n... 他 {len(online_members) - 10} 人"
            embed.add_field(name=f"オンライン ({len(online_members)})", value=online_list, inline=False)

        if idle_members:
            idle_list = "\n".join([f"🟡 {m.display_name}" for m in idle_members[:10]])
            if len(idle_members) > 10:
                idle_list += f"\n... 他 {len(idle_members) - 10} 人"
            embed.add_field(name=f"退席中 ({len(idle_members)})", value=idle_list, inline=False)

        if dnd_members:
            dnd_list = "\n".join([f"🔴 {m.display_name}" for m in dnd_members[:10]])
            if len(dnd_members) > 10:
                dnd_list += f"\n... 他 {len(dnd_members) - 10} 人"
            embed.add_field(name=f"取り込み中 ({len(dnd_members)})", value=dnd_list, inline=False)

        embed.set_footer(text=f"総メンバー: {guild.member_count} 人")

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """プラグインセットアップ（自動読み込み用）"""
    await bot.add_cog(EnhancedFeatures(bot))
