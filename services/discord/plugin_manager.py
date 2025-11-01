#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugin_manager.py

Discord Bot プラグインマネージャー
- プラグインの動的ロード/アンロード
- 依存関係管理
- プラグイン設定管理
"""

import os
import sys
import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Type

from discord.ext import commands

logger = logging.getLogger(__name__)


class PluginBase:
    """プラグイン基底クラス"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "プラグインの説明なし"
        self.version = "1.0.0"
        self.enabled = True

    async def on_load(self):
        """プラグインロード時に実行"""
        pass

    async def on_unload(self):
        """プラグインアンロード時に実行"""
        pass

    async def on_enable(self):
        """プラグイン有効化時に実行"""
        pass

    async def on_disable(self):
        """プラグイン無効化時に実行"""
        pass


class PluginManager:
    """
    プラグインマネージャー

    機能:
    - プラグインの動的ロード/アンロード
    - プラグイン依存関係管理
    - プラグイン設定保存/読み込み
    - プラグイン状態管理
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_paths: Dict[str, str] = {}
        self.plugin_configs: Dict[str, Dict[str, Any]] = {}

        # プラグインディレクトリ
        self.plugin_dir = Path(__file__).parent / "plugins"
        self.plugin_dir.mkdir(exist_ok=True)

        logger.info("🔌 PluginManager 初期化完了")

    async def load_plugin(self, plugin_path: str) -> bool:
        """
        プラグインをロード

        Args:
            plugin_path: プラグインのパス（モジュール名 or ファイルパス）

        Returns:
            bool: 成功したらTrue
        """
        try:
            # モジュール名を取得
            if plugin_path.endswith('.py'):
                module_name = Path(plugin_path).stem
            else:
                module_name = plugin_path

            # すでにロード済みならスキップ
            if module_name in self.plugins:
                logger.warning(f"⚠️ プラグイン {module_name} は既にロードされています")
                return False

            # モジュールをインポート
            if plugin_path.endswith('.py'):
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                module = importlib.import_module(f"services.discord.plugins.{module_name}")

            # プラグインクラスを検索
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, PluginBase) and obj != PluginBase:
                    plugin_class = obj
                    break

            if not plugin_class:
                logger.error(f"❌ {module_name} にプラグインクラスが見つかりません")
                return False

            # プラグインインスタンス化
            plugin = plugin_class(self.bot)

            # Cogとして追加（Discord.py拡張機能）
            if isinstance(plugin, commands.Cog):
                await self.bot.add_cog(plugin)

            # プラグイン登録
            self.plugins[module_name] = plugin
            self.plugin_paths[module_name] = plugin_path

            # on_loadコールバック実行
            await plugin.on_load()

            logger.info(f"✅ プラグイン {module_name} をロードしました")
            return True

        except Exception as e:
            logger.error(f"❌ プラグイン {plugin_path} のロードに失敗: {e}")
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        プラグインをアンロード

        Args:
            plugin_name: プラグイン名

        Returns:
            bool: 成功したらTrue
        """
        try:
            if plugin_name not in self.plugins:
                logger.warning(f"⚠️ プラグイン {plugin_name} はロードされていません")
                return False

            plugin = self.plugins[plugin_name]

            # on_unloadコールバック実行
            await plugin.on_unload()

            # Cogとして削除
            if isinstance(plugin, commands.Cog):
                await self.bot.remove_cog(plugin.qualified_name)

            # プラグイン削除
            del self.plugins[plugin_name]
            del self.plugin_paths[plugin_name]

            logger.info(f"✅ プラグイン {plugin_name} をアンロードしました")
            return True

        except Exception as e:
            logger.error(f"❌ プラグイン {plugin_name} のアンロードに失敗: {e}")
            return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        プラグインをリロード

        Args:
            plugin_name: プラグイン名

        Returns:
            bool: 成功したらTrue
        """
        if plugin_name not in self.plugins:
            return False

        plugin_path = self.plugin_paths[plugin_name]

        success = await self.unload_plugin(plugin_name)
        if not success:
            return False

        return await self.load_plugin(plugin_path)

    async def load_all_plugins(self) -> int:
        """
        プラグインディレクトリから全プラグインをロード

        Returns:
            int: ロードしたプラグイン数
        """
        loaded_count = 0

        if not self.plugin_dir.exists():
            logger.warning("⚠️ プラグインディレクトリが存在しません")
            return 0

        for plugin_file in self.plugin_dir.glob("*.py"):
            if plugin_file.stem.startswith("_"):
                continue

            if await self.load_plugin(str(plugin_file)):
                loaded_count += 1

        logger.info(f"📦 {loaded_count}個のプラグインをロードしました")
        return loaded_count

    async def unload_all_plugins(self) -> int:
        """
        全プラグインをアンロード

        Returns:
            int: アンロードしたプラグイン数
        """
        plugin_names = list(self.plugins.keys())
        unloaded_count = 0

        for plugin_name in plugin_names:
            if await self.unload_plugin(plugin_name):
                unloaded_count += 1

        logger.info(f"📦 {unloaded_count}個のプラグインをアンロードしました")
        return unloaded_count

    async def enable_plugin(self, plugin_name: str) -> bool:
        """プラグインを有効化"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]
        plugin.enabled = True
        await plugin.on_enable()
        logger.info(f"✅ プラグイン {plugin_name} を有効化しました")
        return True

    async def disable_plugin(self, plugin_name: str) -> bool:
        """プラグインを無効化"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]
        plugin.enabled = False
        await plugin.on_disable()
        logger.info(f"⏸️ プラグイン {plugin_name} を無効化しました")
        return True

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """プラグインを取得"""
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> Dict[str, PluginBase]:
        """全プラグインを取得"""
        return self.plugins.copy()

    def get_plugin_info(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """プラグイン情報を取得"""
        plugin = self.plugins.get(plugin_name)
        if not plugin:
            return None

        return {
            'name': plugin.name,
            'description': plugin.description,
            'version': plugin.version,
            'enabled': plugin.enabled,
            'path': self.plugin_paths.get(plugin_name, 'unknown')
        }

    def get_all_plugin_info(self) -> List[Dict[str, Any]]:
        """全プラグイン情報を取得"""
        return [
            self.get_plugin_info(name)
            for name in self.plugins.keys()
        ]
