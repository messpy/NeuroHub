#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_commands.py

LLM連携コマンドプラグイン
- LLM応答生成
- ナレッジベース検索
- 会話履歴管理
"""

import discord
from discord.ext import commands

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase
from services.db.knowledge_manager import KnowledgeManager


class LLMCommands(PluginBase, commands.Cog):
    """LLM連携コマンド"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.description = "LLM連携機能コマンド"
        self.version = "1.0.0"
        self.km = KnowledgeManager(bot.db)

    @commands.command(name='llm')
    async def llm_query(self, ctx: commands.Context, *, query: str):
        """LLMに質問"""
        async with ctx.typing():
            response = await self.bot._call_llm(query, ctx.author.id)

            embed = discord.Embed(
                title="🤖 LLM応答",
                description=response,
                color=discord.Color.blue()
            )
            embed.set_footer(text=f"質問: {query[:50]}...")

            await ctx.send(embed=embed)

    @commands.command(name='knowledge')
    async def knowledge_search(self, ctx: commands.Context, *, query: str):
        """ナレッジベース検索"""
        results = self.km.search_knowledge(query, limit=5)

        if not results:
            await ctx.send("❌ 該当するナレッジが見つかりませんでした。")
            return

        embed = discord.Embed(
            title=f"📚 ナレッジベース検索結果: {query}",
            color=discord.Color.green()
        )

        for idx, result in enumerate(results[:3], 1):
            embed.add_field(
                name=f"{idx}. {result['title']}",
                value=result['content'][:100] + "..." if len(result['content']) > 100 else result['content'],
                inline=False
            )

        embed.set_footer(text=f"全{len(results)}件中 上位3件を表示")
        await ctx.send(embed=embed)

    @commands.command(name='knowledge_add')
    @commands.has_permissions(manage_messages=True)
    async def knowledge_add(self, ctx: commands.Context, title: str, *, content: str):
        """ナレッジベースに追加（管理者のみ）"""
        knowledge_id = self.km.add_knowledge(
            title=title,
            content=content,
            category='discord',
            tags='discord,bot',
            user_id=ctx.author.id
        )

        if knowledge_id > 0:
            await ctx.send(f"✅ ナレッジを追加しました（ID: {knowledge_id}）")
        else:
            await ctx.send("❌ ナレッジの追加に失敗しました。")


async def setup(bot: commands.Bot):
    """プラグインセットアップ"""
    await bot.add_cog(LLMCommands(bot))
