#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vision_commands.py

Ollama画像認識・Vision機能プラグイン
- 画像添付でのLLM分析
- 画像説明生成
- OCR（文字認識）
- 画像分類
"""

import os
import base64
import asyncio
import aiohttp
import discord
from discord.ext import commands
from typing import Dict, List, Optional
from io import BytesIO

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.plugin_manager import PluginBase


class VisionCommands(PluginBase, commands.Cog):
    """Ollama Vision（画像認識）機能"""

    def __init__(self, bot: commands.Bot):
        super().__init__(bot)
        self.description = "Ollama画像認識・Vision機能"
        self.version = "1.0.0"

        # Vision対応モデル
        self.vision_models = [
            'llava',           # 最も一般的
            'llava:7b',
            'llava:13b',
            'llava:34b',
            'llava-phi3',      # 軽量版
            'moondream',       # 軽量Vision
            'bakllava',        # 多言語対応
        ]

        # Ollama API設定
        self.ollama_url = "http://localhost:11434"

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """画像付きメッセージの自動分析"""
        # Bot自身のメッセージは無視
        if message.author.bot:
            return

        # 画像添付があり、Botがメンションされた場合
        if message.attachments and self.bot.user in message.mentions:
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    await self._analyze_image_auto(message, attachment)
                    break

    @commands.command(name='vision')
    async def analyze_image(self, ctx: commands.Context, *, prompt: str = "この画像について詳しく説明してください"):
        """
        画像を分析（画像添付必須）
        使用例: !vision この画像に何が写っていますか？
        """
        if not ctx.message.attachments:
            await ctx.send("❌ 画像を添付してください。")
            return

        # 最初の画像を分析
        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await ctx.send("❌ 画像ファイルを添付してください。")
            return

        await self._analyze_image_with_prompt(ctx, attachment, prompt)

    @commands.command(name='ocr')
    async def extract_text(self, ctx: commands.Context):
        """
        画像からテキストを抽出（OCR）
        """
        if not ctx.message.attachments:
            await ctx.send("❌ 画像を添付してください。")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await ctx.send("❌ 画像ファイルを添付してください。")
            return

        prompt = "この画像に書かれているテキストを全て正確に読み取って、そのまま書き起こしてください。テキスト以外の説明は不要です。"
        await self._analyze_image_with_prompt(ctx, attachment, prompt)

    @commands.command(name='describe')
    async def describe_image(self, ctx: commands.Context):
        """
        画像の詳細説明を生成
        """
        if not ctx.message.attachments:
            await ctx.send("❌ 画像を添付してください。")
            return

        attachment = ctx.message.attachments[0]
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            await ctx.send("❌ 画像ファイルを添付してください。")
            return

        prompt = "この画像について、以下の観点から詳細に説明してください：\n1. 全体的な構成と雰囲気\n2. 主要な被写体や物体\n3. 色彩やライティング\n4. 背景や環境\n5. その他特徴的な要素"
        await self._analyze_image_with_prompt(ctx, attachment, prompt)

    @commands.command(name='vision_models')
    async def list_vision_models(self, ctx: commands.Context):
        """利用可能なVisionモデル一覧"""
        embed = discord.Embed(
            title="🔍 利用可能なVisionモデル",
            description="Ollamaで使用できる画像認識モデル一覧",
            color=discord.Color.green()
        )

        # 現在のモデル確認
        current_model = await self._get_current_vision_model()

        model_descriptions = {
            'llava': '最も一般的なVisionモデル',
            'llava:7b': 'LLaVA 7Bパラメータ版',
            'llava:13b': 'LLaVA 13Bパラメータ版（高精度）',
            'llava:34b': 'LLaVA 34Bパラメータ版（最高精度・重い）',
            'llava-phi3': 'LLaVA-Phi3（軽量版）',
            'moondream': 'Moondream（軽量・高速）',
            'bakllava': 'BakLLaVA（多言語対応）'
        }

        for model in self.vision_models:
            status = "✅ 使用中" if model == current_model else "⭕ 利用可能"
            description = model_descriptions.get(model, "画像認識モデル")
            embed.add_field(
                name=f"{status} {model}",
                value=description,
                inline=False
            )

        embed.set_footer(text="!vision_switch <model> でモデルを切り替え")
        await ctx.send(embed=embed)

    @commands.command(name='vision_switch')
    @commands.has_permissions(administrator=True)
    async def switch_vision_model(self, ctx: commands.Context, model: str):
        """Visionモデルを切り替え（管理者のみ）"""
        if model not in self.vision_models:
            await ctx.send(f"❌ 無効なモデル: {model}\n利用可能: {', '.join(self.vision_models)}")
            return

        # モデル切り替え（LLM設定を更新）
        success = await self._switch_to_vision_model(model)

        if success:
            await ctx.send(f"✅ Visionモデルを `{model}` に切り替えました。")
        else:
            await ctx.send(f"❌ モデル切り替えに失敗しました。Ollamaで `{model}` がインストールされているか確認してください。")

    @commands.command(name='vision_install')
    @commands.has_permissions(administrator=True)
    async def install_vision_model(self, ctx: commands.Context, model: str = 'llava'):
        """Visionモデルをインストール（管理者のみ）"""
        if model not in self.vision_models:
            await ctx.send(f"❌ 無効なモデル: {model}")
            return

        embed = discord.Embed(
            title="📦 Visionモデルインストール",
            description=f"`{model}` をインストールしています...",
            color=discord.Color.orange()
        )
        embed.add_field(name="注意", value="大きなモデルの場合、数GBのダウンロードが必要です", inline=False)

        status_msg = await ctx.send(embed=embed)

        # Ollamaでモデルをpull
        success = await self._install_ollama_model(model)

        if success:
            embed.color = discord.Color.green()
            embed.description = f"✅ `{model}` のインストールが完了しました！"
        else:
            embed.color = discord.Color.red()
            embed.description = f"❌ `{model}` のインストールに失敗しました。"

        await status_msg.edit(embed=embed)

    async def _analyze_image_auto(self, message: discord.Message, attachment: discord.Attachment):
        """画像の自動分析（メンション時）"""
        prompt = "この画像について簡潔に説明してください。"

        async with message.channel.typing():
            try:
                # 画像をダウンロード
                image_data = await attachment.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')

                # Ollama Vision API呼び出し
                response = await self._call_ollama_vision(prompt, image_base64)

                if response:
                    embed = discord.Embed(
                        title="🔍 画像分析結果",
                        description=response,
                        color=discord.Color.blue()
                    )
                    embed.set_thumbnail(url=attachment.url)
                    embed.set_footer(text=f"分析者: {message.author.display_name}")

                    await message.reply(embed=embed)
                else:
                    await message.reply("❌ 画像分析に失敗しました。Visionモデルが起動しているか確認してください。")

            except Exception as e:
                await message.reply(f"❌ エラーが発生しました: {str(e)}")

    async def _analyze_image_with_prompt(self, ctx: commands.Context, attachment: discord.Attachment, prompt: str):
        """プロンプト指定での画像分析"""
        async with ctx.typing():
            try:
                # 画像をダウンロード
                image_data = await attachment.read()
                image_base64 = base64.b64encode(image_data).decode('utf-8')

                # Ollama Vision API呼び出し
                response = await self._call_ollama_vision(prompt, image_base64)

                if response:
                    # 長いレスポンスの場合は分割
                    if len(response) > 2000:
                        chunks = [response[i:i+2000] for i in range(0, len(response), 2000)]

                        for i, chunk in enumerate(chunks):
                            embed = discord.Embed(
                                title=f"🔍 画像分析結果 ({i+1}/{len(chunks)})",
                                description=chunk,
                                color=discord.Color.blue()
                            )
                            if i == 0:
                                embed.set_thumbnail(url=attachment.url)
                            embed.set_footer(text=f"プロンプト: {prompt[:50]}...")
                            await ctx.send(embed=embed)
                    else:
                        embed = discord.Embed(
                            title="🔍 画像分析結果",
                            description=response,
                            color=discord.Color.blue()
                        )
                        embed.set_thumbnail(url=attachment.url)
                        embed.set_footer(text=f"プロンプト: {prompt[:50]}...")
                        await ctx.send(embed=embed)

                else:
                    await ctx.send("❌ 画像分析に失敗しました。Visionモデルが起動しているか確認してください。")

            except Exception as e:
                await ctx.send(f"❌ エラーが発生しました: {str(e)}")

    async def _call_ollama_vision(self, prompt: str, image_base64: str) -> Optional[str]:
        """Ollama Vision APIを呼び出し"""
        try:
            current_model = await self._get_current_vision_model()

            payload = {
                "model": current_model,
                "prompt": prompt,
                "images": [image_base64],
                "stream": False
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('response', '')
                    else:
                        return None

        except Exception as e:
            print(f"Ollama Vision API エラー: {e}")
            return None

    async def _get_current_vision_model(self) -> str:
        """現在のVisionモデルを取得"""
        # LLM設定から取得（デフォルトはllava）
        try:
            import yaml
            config_path = ROOT / "config" / "llm_config.yaml"
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Vision専用設定があるかチェック
                vision_model = config.get('llm', {}).get('providers', {}).get('ollama_vision', {}).get('model')
                if vision_model and vision_model in self.vision_models:
                    return vision_model

                # 通常のOllamaモデルがVision対応ならそれを使用
                ollama_model = config.get('llm', {}).get('providers', {}).get('ollama', {}).get('model', '')
                if ollama_model in self.vision_models:
                    return ollama_model

        except:
            pass

        return 'llava'  # デフォルト

    async def _switch_to_vision_model(self, model: str) -> bool:
        """Visionモデルに切り替え"""
        try:
            import yaml
            config_path = ROOT / "config" / "llm_config.yaml"

            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                # Ollama Visionプロバイダー設定を追加/更新
                config.setdefault('llm', {}).setdefault('providers', {})['ollama_vision'] = {
                    'enabled': True,
                    'model': model,
                    'api_url': self.ollama_url,
                    'max_tokens': 1000,
                    'temperature': 0.1,
                    'timeout': 60,
                    'priority': 2
                }

                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

                return True

        except Exception as e:
            print(f"Vision model switch error: {e}")

        return False

    async def _install_ollama_model(self, model: str) -> bool:
        """OllamaでVisionモデルをインストール"""
        try:
            payload = {"name": model}

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.ollama_url}/api/pull",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=600)  # 10分タイムアウト
                ) as response:
                    return response.status == 200

        except Exception as e:
            print(f"Ollama model install error: {e}")
            return False


async def setup(bot: commands.Bot):
    """プラグインセットアップ"""
    await bot.add_cog(VisionCommands(bot))
