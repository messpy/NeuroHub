#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reaction_commands.py

リアクション機能・DM機能プラグイン
- リアクション投票システム
- リアクション応答機能
- 個人DM送信
- ロール付与/削除（リアクション連動）
"""

import os
import discord
from discord.ext import commands
from typing import Dict, List, Optional

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase


class ReactionCommands(PluginBase, commands.Cog):
    """リアクション・DM機能コマンド"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.description = "リアクション応答・DM・投票機能"
        self.version = "1.0.0"

        # リアクション投票の管理
        self.active_polls: Dict[int, Dict] = {}  # message_id: poll_data

        # リアクションロール管理
        self.reaction_roles: Dict[str, int] = {}  # emoji: role_id

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """リアクション追加時の処理"""
        # Bot自身のリアクションは無視
        if user.bot:
            return

        message = reaction.message
        emoji = str(reaction.emoji)

        # 投票システムの処理
        if message.id in self.active_polls:
            await self._handle_poll_reaction(reaction, user, True)

        # リアクションロール機能
        if emoji in self.reaction_roles:
            await self._handle_reaction_role(reaction, user, True)

        # 特定のリアクション応答
        await self._handle_special_reactions(reaction, user)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, user: discord.User):
        """リアクション削除時の処理"""
        if user.bot:
            return

        message = reaction.message
        emoji = str(reaction.emoji)

        # 投票システムの処理
        if message.id in self.active_polls:
            await self._handle_poll_reaction(reaction, user, False)

        # リアクションロール削除
        if emoji in self.reaction_roles:
            await self._handle_reaction_role(reaction, user, False)

    @commands.command(name='poll')
    async def create_poll(self, ctx: commands.Context, question: str, *options):
        """
        投票を作成
        使用例: !poll "好きな色は？" "赤" "青" "緑"
        """
        if len(options) < 2:
            await ctx.send("❌ 選択肢は2つ以上必要です。")
            return

        if len(options) > 10:
            await ctx.send("❌ 選択肢は10個以下にしてください。")
            return

        # 投票用絵文字
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        # Embed作成
        embed = discord.Embed(
            title="📊 投票",
            description=question,
            color=discord.Color.blue()
        )

        poll_data = {
            'question': question,
            'options': list(options),
            'votes': {i: [] for i in range(len(options))},
            'creator': ctx.author.id
        }

        # 選択肢を追加
        for i, option in enumerate(options):
            embed.add_field(
                name=f"{number_emojis[i]} {option}",
                value="票数: 0",
                inline=False
            )

        embed.set_footer(text=f"作成者: {ctx.author.display_name}")

        message = await ctx.send(embed=embed)

        # リアクション追加
        for i in range(len(options)):
            await message.add_reaction(number_emojis[i])

        # 投票データを保存
        self.active_polls[message.id] = poll_data

    @commands.command(name='poll_end')
    async def end_poll(self, ctx: commands.Context, message_id: int):
        """投票を終了（投票作成者または管理者のみ）"""
        if message_id not in self.active_polls:
            await ctx.send("❌ 指定された投票が見つかりません。")
            return

        poll_data = self.active_polls[message_id]

        # 権限チェック
        if ctx.author.id != poll_data['creator'] and not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ 投票を終了する権限がありません。")
            return

        # 結果集計
        results = []
        total_votes = sum(len(votes) for votes in poll_data['votes'].values())

        for i, option in enumerate(poll_data['options']):
            vote_count = len(poll_data['votes'][i])
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            results.append(f"{i+1}. {option}: {vote_count}票 ({percentage:.1f}%)")

        # 結果表示
        embed = discord.Embed(
            title="📊 投票結果",
            description=poll_data['question'],
            color=discord.Color.green()
        )
        embed.add_field(name="結果", value="\n".join(results), inline=False)
        embed.add_field(name="総投票数", value=f"{total_votes}票", inline=True)

        await ctx.send(embed=embed)

        # 投票データを削除
        del self.active_polls[message_id]

    @commands.command(name='dm')
    async def send_dm(self, ctx: commands.Context, member: discord.Member, *, message: str):
        """
        指定ユーザーにDMを送信（管理者のみ）
        使用例: !dm @Kenny こんにちは
        """
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ 管理者のみ使用できます。")
            return

        try:
            # DM送信
            dm_embed = discord.Embed(
                title="📨 サーバーからのメッセージ",
                description=message,
                color=discord.Color.purple()
            )
            dm_embed.set_footer(text=f"送信者: {ctx.author.display_name} | サーバー: {ctx.guild.name}")

            await member.send(embed=dm_embed)

            # 送信確認
            await ctx.send(f"✅ {member.mention} にDMを送信しました。")

        except discord.Forbidden:
            await ctx.send(f"❌ {member.mention} にDMを送信できませんでした（DM無効化済み）。")
        except Exception as e:
            await ctx.send(f"❌ DM送信エラー: {str(e)}")

    @commands.command(name='broadcast')
    @commands.has_permissions(administrator=True)
    async def broadcast_dm(self, ctx: commands.Context, *, message: str):
        """
        全メンバーにDMを一斉送信（管理者のみ）
        使用例: !broadcast 重要なお知らせです
        """
        members = [m for m in ctx.guild.members if not m.bot]
        success_count = 0
        fail_count = 0

        # 確認メッセージ
        confirm_embed = discord.Embed(
            title="⚠️ 一斉DM送信確認",
            description=f"**{len(members)}人**にDMを送信しますか？\n\n**送信内容:**\n{message}",
            color=discord.Color.orange()
        )

        confirm_msg = await ctx.send(embed=confirm_embed)
        await confirm_msg.add_reaction('✅')
        await confirm_msg.add_reaction('❌')

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ['✅', '❌'] and reaction.message.id == confirm_msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == '❌':
                await ctx.send("❌ 一斉DM送信をキャンセルしました。")
                return

            # DM送信開始
            await ctx.send("📤 DM送信を開始します...")

            broadcast_embed = discord.Embed(
                title="📢 サーバーからの重要なお知らせ",
                description=message,
                color=discord.Color.blue()
            )
            broadcast_embed.set_footer(text=f"送信者: {ctx.author.display_name} | サーバー: {ctx.guild.name}")

            for member in members:
                try:
                    await member.send(embed=broadcast_embed)
                    success_count += 1
                except:
                    fail_count += 1

            # 結果報告
            result_embed = discord.Embed(
                title="📊 一斉DM送信結果",
                color=discord.Color.green()
            )
            result_embed.add_field(name="成功", value=f"{success_count}人", inline=True)
            result_embed.add_field(name="失敗", value=f"{fail_count}人", inline=True)
            result_embed.add_field(name="成功率", value=f"{success_count/(success_count+fail_count)*100:.1f}%", inline=True)

            await ctx.send(embed=result_embed)

        except asyncio.TimeoutError:
            await ctx.send("❌ タイムアウトしました。")

    @commands.command(name='reaction_role')
    @commands.has_permissions(administrator=True)
    async def setup_reaction_role(self, ctx: commands.Context, emoji: str, role: discord.Role):
        """
        リアクションロールを設定（管理者のみ）
        使用例: !reaction_role 🎮 @ゲーマー
        """
        self.reaction_roles[emoji] = role.id
        await ctx.send(f"✅ {emoji} → {role.mention} のリアクションロールを設定しました。")

    @commands.command(name='special_reaction')
    async def setup_special_reaction(self, ctx: commands.Context, emoji: str, *, response: str):
        """
        特殊リアクション応答を設定
        使用例: !special_reaction 👋 こんにちは！
        """
        # 簡易的な実装（実際はDBに保存）
        await ctx.send(f"✅ {emoji} リアクションに応答メッセージを設定しました: {response}")

    async def _handle_poll_reaction(self, reaction: discord.Reaction, user: discord.User, added: bool):
        """投票リアクションの処理"""
        message_id = reaction.message.id
        poll_data = self.active_polls[message_id]

        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
        emoji = str(reaction.emoji)

        if emoji in number_emojis:
            option_index = number_emojis.index(emoji)

            if added:
                # 重複投票防止
                for votes in poll_data['votes'].values():
                    if user.id in votes:
                        votes.remove(user.id)

                poll_data['votes'][option_index].append(user.id)
            else:
                if user.id in poll_data['votes'][option_index]:
                    poll_data['votes'][option_index].remove(user.id)

            # 投票結果を更新
            await self._update_poll_display(reaction.message, poll_data)

    async def _update_poll_display(self, message: discord.Message, poll_data: Dict):
        """投票表示を更新"""
        number_emojis = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']

        embed = discord.Embed(
            title="📊 投票",
            description=poll_data['question'],
            color=discord.Color.blue()
        )

        for i, option in enumerate(poll_data['options']):
            vote_count = len(poll_data['votes'][i])
            embed.add_field(
                name=f"{number_emojis[i]} {option}",
                value=f"票数: {vote_count}",
                inline=False
            )

        total_votes = sum(len(votes) for votes in poll_data['votes'].values())
        embed.set_footer(text=f"総投票数: {total_votes}")

        await message.edit(embed=embed)

    async def _handle_reaction_role(self, reaction: discord.Reaction, user: discord.User, added: bool):
        """リアクションロールの処理"""
        emoji = str(reaction.emoji)
        role_id = self.reaction_roles[emoji]

        guild = reaction.message.guild
        role = guild.get_role(role_id)
        member = guild.get_member(user.id)

        if role and member:
            try:
                if added:
                    await member.add_roles(role)
                else:
                    await member.remove_roles(role)
            except discord.Forbidden:
                pass  # 権限不足

    async def _handle_special_reactions(self, reaction: discord.Reaction, user: discord.User):
        """特殊リアクション応答の処理"""
        emoji = str(reaction.emoji)

        # 特定の絵文字に対する応答
        responses = {
            '👋': f"こんにちは、{user.mention}さん！",
            '❤️': f"{user.mention}さん、ありがとうございます！",
            '🎉': f"お疲れ様です、{user.mention}さん！",
            '🤖': f"{user.mention}さん、AIについて何か知りたいことはありますか？"
        }

        if emoji in responses:
            await reaction.message.channel.send(responses[emoji], delete_after=10)


async def setup(bot: commands.Bot):
    """プラグインセットアップ"""
    await bot.add_cog(ReactionCommands(bot))
