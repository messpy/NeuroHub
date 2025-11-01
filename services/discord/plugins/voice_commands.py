#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
voice_commands.py

音声機能コマンドプラグイン
- ボイスチャンネル参加/退出
- TTS（Text-to-Speech）
- 音声認識
"""

import discord
from discord.ext import commands

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase


class VoiceCommands(PluginBase, commands.Cog):
    """音声機能コマンド"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.description = "音声チャンネル機能コマンド"
        self.version = "1.0.0"

    @commands.command(name='join')
    async def join(self, ctx: commands.Context):
        """ボイスチャンネルに参加"""
        if not ctx.author.voice:
            await ctx.send("❌ ボイスチャンネルに接続してください。")
            return

        channel = ctx.author.voice.channel
        voice_client = await self.bot.voice_manager.join_voice_channel(channel)

        if voice_client:
            await ctx.send(f"✅ {channel.name} に参加しました！")
        else:
            await ctx.send("❌ ボイスチャンネルへの参加に失敗しました。")

    @commands.command(name='leave')
    async def leave(self, ctx: commands.Context):
        """ボイスチャンネルから退出"""
        guild_id = ctx.guild.id
        success = await self.bot.voice_manager.leave_voice_channel(guild_id)

        if success:
            await ctx.send("👋 ボイスチャンネルから退出しました。")
        else:
            await ctx.send("❌ ボイスチャンネルに接続されていません。")

    @commands.command(name='tts')
    async def tts(self, ctx: commands.Context, *, text: str):
        """テキストを音声で読み上げ"""
        guild_id = ctx.guild.id

        if not self.bot.voice_manager.is_connected(guild_id):
            await ctx.send("❌ ボイスチャンネルに接続してください。`!join` で参加できます。")
            return

        await ctx.send(f"🔊 読み上げ中: {text[:50]}...")
        success = await self.bot.voice_manager.text_to_speech(guild_id, text)

        if not success:
            await ctx.send("❌ 読み上げに失敗しました。gTTSがインストールされているか確認してください。")

    @commands.command(name='volume')
    async def volume(self, ctx: commands.Context, volume: int):
        """音量を変更（0-100）"""
        guild_id = ctx.guild.id

        if not self.bot.voice_manager.is_connected(guild_id):
            await ctx.send("❌ ボイスチャンネルに接続されていません。")
            return

        volume_float = max(0, min(100, volume)) / 100.0
        success = await self.bot.voice_manager.set_volume(guild_id, volume_float)

        if success:
            await ctx.send(f"🔊 音量を {volume}% に設定しました。")
        else:
            await ctx.send("❌ 音量の変更に失敗しました。")


async def setup(bot: commands.Bot):
    """プラグインセットアップ"""
    await bot.add_cog(VoiceCommands(bot))
