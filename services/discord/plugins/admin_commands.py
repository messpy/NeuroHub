#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
admin_commands.py

管理者コマンドプラグイン
- プラグイン管理
- 荒らし対策設定
- Bot設定管理
"""

import discord
from discord.ext import commands

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase


class AdminCommands(PluginBase, commands.Cog):
    """管理者コマンド"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.description = "管理者専用コマンド"
        self.version = "1.0.0"

    @commands.group(name='plugin')
    @commands.has_permissions(administrator=True)
    async def plugin(self, ctx: commands.Context):
        """プラグイン管理コマンド"""
        if ctx.invoked_subcommand is None:
            await ctx.send("使用方法: `!plugin [list|load|unload|reload]`")

    @plugin.command(name='list')
    async def plugin_list(self, ctx: commands.Context):
        """プラグイン一覧"""
        plugins_info = self.bot.plugin_manager.get_all_plugin_info()

        embed = discord.Embed(
            title="🔌 プラグイン一覧",
            color=discord.Color.blue()
        )

        for plugin_info in plugins_info:
            status = "✅ 有効" if plugin_info['enabled'] else "⏸️ 無効"
            embed.add_field(
                name=f"{plugin_info['name']} (v{plugin_info['version']})",
                value=f"{status}\n{plugin_info['description']}",
                inline=False
            )

        await ctx.send(embed=embed)

    @plugin.command(name='load')
    async def plugin_load(self, ctx: commands.Context, plugin_name: str):
        """プラグインを読み込み"""
        success = await self.bot.plugin_manager.load_plugin(plugin_name)

        if success:
            await ctx.send(f"✅ プラグイン `{plugin_name}` を読み込みました。")
        else:
            await ctx.send(f"❌ プラグイン `{plugin_name}` の読み込みに失敗しました。")

    @plugin.command(name='unload')
    async def plugin_unload(self, ctx: commands.Context, plugin_name: str):
        """プラグインを無効化"""
        success = await self.bot.plugin_manager.unload_plugin(plugin_name)

        if success:
            await ctx.send(f"✅ プラグイン `{plugin_name}` を無効化しました。")
        else:
            await ctx.send(f"❌ プラグイン `{plugin_name}` の無効化に失敗しました。")

    @plugin.command(name='reload')
    async def plugin_reload(self, ctx: commands.Context, plugin_name: str):
        """プラグインを再読み込み"""
        success = await self.bot.plugin_manager.reload_plugin(plugin_name)

        if success:
            await ctx.send(f"🔄 プラグイン `{plugin_name}` を再読み込みしました。")
        else:
            await ctx.send(f"❌ プラグイン `{plugin_name}` の再読み込みに失敗しました。")

    @commands.group(name='whitelist')
    @commands.has_permissions(administrator=True)
    async def whitelist(self, ctx: commands.Context):
        """ホワイトリスト管理"""
        if ctx.invoked_subcommand is None:
            await ctx.send("使用方法: `!whitelist [add|remove]`")

    @whitelist.command(name='add')
    async def whitelist_add(self, ctx: commands.Context, member: discord.Member):
        """ホワイトリストに追加"""
        self.bot.anti_spam.add_to_whitelist(member.id)
        await ctx.send(f"✅ {member.mention} をホワイトリストに追加しました。")

    @whitelist.command(name='remove')
    async def whitelist_remove(self, ctx: commands.Context, member: discord.Member):
        """ホワイトリストから削除"""
        self.bot.anti_spam.remove_from_whitelist(member.id)
        await ctx.send(f"❌ {member.mention} をホワイトリストから削除しました。")

    @commands.group(name='blacklist')
    @commands.has_permissions(administrator=True)
    async def blacklist(self, ctx: commands.Context):
        """ブラックリスト管理"""
        if ctx.invoked_subcommand is None:
            await ctx.send("使用方法: `!blacklist [add|remove]`")

    @blacklist.command(name='add')
    async def blacklist_add(self, ctx: commands.Context, member: discord.Member):
        """ブラックリストに追加"""
        self.bot.anti_spam.add_to_blacklist(member.id)
        await ctx.send(f"🚫 {member.mention} をブラックリストに追加しました。")

    @blacklist.command(name='remove')
    async def blacklist_remove(self, ctx: commands.Context, member: discord.Member):
        """ブラックリストから削除"""
        self.bot.anti_spam.remove_from_blacklist(member.id)
        await ctx.send(f"✅ {member.mention} をブラックリストから削除しました。")

    @commands.command(name='spam_stats')
    @commands.has_permissions(manage_messages=True)
    async def spam_stats(self, ctx: commands.Context, member: discord.Member = None):
        """スパム統計を表示"""
        member = member or ctx.author
        stats = self.bot.anti_spam.get_user_stats(member.id)

        embed = discord.Embed(
            title=f"📊 {member.display_name} のスパム統計",
            color=discord.Color.orange()
        )
        embed.add_field(name="違反回数", value=stats['violations'], inline=True)
        embed.add_field(name="メッセージ数", value=stats['message_count'], inline=True)
        embed.add_field(name="ホワイトリスト", value="✅" if stats['is_whitelisted'] else "❌", inline=True)
        embed.add_field(name="ブラックリスト", value="🚫" if stats['is_blacklisted'] else "✅", inline=True)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """プラグインセットアップ"""
    await bot.add_cog(AdminCommands(bot))
