#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
remo_plugin.py

Discord Bot用 Nature Remo制御プラグイン

機能:
- 照明ON/OFF
- エアコン制御
- デバイス一覧表示
- センサー情報取得
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from json import loads

import discord
from discord.ext import commands

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase

logger = logging.getLogger(__name__)


class NatureRemoController:
    """Nature Remo API制御クラス"""

    def __init__(self, api_key: str):
        """
        Args:
            api_key: Nature Remo API Key
        """
        self.api_key = api_key
        self.base_url = "https://api.nature.global"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def get_appliances(self) -> list:
        """家電一覧を取得"""
        request = Request(f"{self.base_url}/1/appliances", headers=self.headers)

        try:
            with urlopen(request) as response:
                data = response.read()
                return loads(data)
        except HTTPError as e:
            logger.error(f"HTTP Error: {e.code}")
            logger.error(e.read().decode())
            return []

    def find_appliance(self, appliance_type: str, nickname: str) -> Optional[dict]:
        """
        家電を検索

        Args:
            appliance_type: 家電タイプ (LIGHT, TV, AC)
            nickname: 家電のニックネーム

        Returns:
            家電情報辞書、見つからない場合はNone
        """
        appliances = self.get_appliances()

        for device in appliances:
            if device.get("type") == appliance_type and device.get("nickname") == nickname:
                return device

        return None

    def get_light_buttons(self, device: dict) -> list:
        """照明のボタン一覧を取得"""
        if device.get("type") == "LIGHT" and "light" in device:
            return device["light"].get("buttons", [])
        return []

    def control_light(self, device_id: str, button_name: str) -> bool:
        """
        照明を制御

        Args:
            device_id: デバイスID
            button_name: ボタン名 (on, off等)

        Returns:
            成功: True、失敗: False
        """
        request = Request(
            f"{self.base_url}/1/appliances/{device_id}/light",
            headers=self.headers
        )

        data = urlencode({"button": button_name}).encode("utf-8")

        try:
            with urlopen(request, data) as response:
                logger.info(f"照明制御成功: {button_name}")
                return True
        except HTTPError as e:
            logger.error(f"HTTP Error: {e.code}")
            logger.error(e.read().decode())
            return False

    def light_on(self, nickname: str = "TAKIZUMI") -> tuple[bool, str]:
        """
        照明をON

        Args:
            nickname: 照明のニックネーム

        Returns:
            (成功/失敗, メッセージ)
        """
        device = self.find_appliance("LIGHT", nickname)

        if not device:
            return False, f"照明 '{nickname}' が見つかりません"

        buttons = self.get_light_buttons(device)

        # ONボタンを探す
        on_button = None
        for button in buttons:
            label = button.get("label", "").lower()
            if "on" in label or "オン" in label or "点灯" in label:
                on_button = button.get("name")
                break

        if not on_button:
            # 最初のボタンを使用
            if buttons:
                on_button = buttons[0].get("name")

        if not on_button:
            return False, "ONボタンが見つかりません"

        success = self.control_light(device["id"], on_button)
        message = f"💡 {nickname} をONにしました" if success else "照明ON失敗"
        return success, message

    def light_off(self, nickname: str = "TAKIZUMI") -> tuple[bool, str]:
        """
        照明をOFF

        Args:
            nickname: 照明のニックネーム

        Returns:
            (成功/失敗, メッセージ)
        """
        device = self.find_appliance("LIGHT", nickname)

        if not device:
            return False, f"照明 '{nickname}' が見つかりません"

        buttons = self.get_light_buttons(device)

        # OFFボタンを探す
        off_button = None
        for button in buttons:
            label = button.get("label", "").lower()
            if "off" in label or "オフ" in label or "消灯" in label:
                off_button = button.get("name")
                break

        if not off_button:
            # 2番目のボタンを使用（通常ON/OFFの順）
            if len(buttons) > 1:
                off_button = buttons[1].get("name")

        if not off_button:
            return False, "OFFボタンが見つかりません"

        success = self.control_light(device["id"], off_button)
        message = f"🌙 {nickname} をOFFにしました" if success else "照明OFF失敗"
        return success, message


class RemoPlugin(PluginBase, commands.Cog):
    """Nature Remo制御プラグイン"""

    def __init__(self, bot: commands.Bot):
        """
        Args:
            bot: Discord Botインスタンス
        """
        self.bot = bot
        self.remo_api_key = os.getenv('REMO_API')

        if not self.remo_api_key:
            logger.warning("⚠️ REMO_API が設定されていません - Nature Remo機能は無効です")
            self.controller = None
        else:
            self.controller = NatureRemoController(self.remo_api_key)
            logger.info("✅ Nature Remo制御プラグイン読み込み完了")

    @commands.group(name='remo', invoke_without_command=True)
    async def remo(self, ctx: commands.Context):
        """Nature Remo制御コマンド"""
        if not self.controller:
            await ctx.send("❌ Nature Remo APIが設定されていません")
            return

        embed = discord.Embed(
            title="🏠 Nature Remo 制御コマンド",
            description="スマートホーム制御コマンド一覧",
            color=discord.Color.green()
        )
        embed.add_field(
            name="!remo light on [名前]",
            value="照明をON（デフォルト: TAKIZUMI）",
            inline=False
        )
        embed.add_field(
            name="!remo light off [名前]",
            value="照明をOFF（デフォルト: TAKIZUMI）",
            inline=False
        )
        embed.add_field(
            name="!remo devices",
            value="登録されている家電一覧を表示",
            inline=False
        )

        await ctx.send(embed=embed)

    @remo.group(name='light', invoke_without_command=True)
    async def light(self, ctx: commands.Context):
        """照明制御コマンド"""
        await ctx.send("使い方: `!remo light on` または `!remo light off`")

    @light.command(name='on')
    async def light_on(self, ctx: commands.Context, nickname: str = "TAKIZUMI"):
        """
        照明をON

        使用例:
            !remo light on
            !remo light on リビング照明
        """
        if not self.controller:
            await ctx.send("❌ Nature Remo APIが設定されていません")
            return

        async with ctx.typing():
            success, message = self.controller.light_on(nickname)

            embed = discord.Embed(
                title="💡 照明制御",
                description=message,
                color=discord.Color.green() if success else discord.Color.red()
            )
            embed.set_footer(text=f"リクエスト: {ctx.author.display_name}")

            await ctx.send(embed=embed)

    @light.command(name='off')
    async def light_off(self, ctx: commands.Context, nickname: str = "TAKIZUMI"):
        """
        照明をOFF

        使用例:
            !remo light off
            !remo light off リビング照明
        """
        if not self.controller:
            await ctx.send("❌ Nature Remo APIが設定されていません")
            return

        async with ctx.typing():
            success, message = self.controller.light_off(nickname)

            embed = discord.Embed(
                title="🌙 照明制御",
                description=message,
                color=discord.Color.green() if success else discord.Color.red()
            )
            embed.set_footer(text=f"リクエスト: {ctx.author.display_name}")

            await ctx.send(embed=embed)

    @remo.command(name='devices')
    async def devices(self, ctx: commands.Context):
        """登録されている家電一覧を表示"""
        if not self.controller:
            await ctx.send("❌ Nature Remo APIが設定されていません")
            return

        async with ctx.typing():
            appliances = self.controller.get_appliances()

            if not appliances:
                await ctx.send("家電が登録されていません")
                return

            embed = discord.Embed(
                title="🏠 登録されている家電",
                description=f"合計 {len(appliances)} 台",
                color=discord.Color.blue()
            )

            for appliance in appliances:
                device_type = appliance.get("type", "不明")
                nickname = appliance.get("nickname", "名前なし")
                device_id = appliance.get("id", "ID不明")

                # 家電タイプに応じた絵文字
                emoji = {
                    "LIGHT": "💡",
                    "TV": "📺",
                    "AC": "❄️"
                }.get(device_type, "🔌")

                embed.add_field(
                    name=f"{emoji} {nickname}",
                    value=f"タイプ: {device_type}\nID: {device_id[:16]}...",
                    inline=False
                )

            embed.set_footer(text=f"リクエスト: {ctx.author.display_name}")
            await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """プラグインセットアップ（自動読み込み用）"""
    await bot.add_cog(RemoPlugin(bot))
