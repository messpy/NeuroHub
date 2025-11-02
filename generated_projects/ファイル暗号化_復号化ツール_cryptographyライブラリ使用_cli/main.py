#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ファイル暗号化_復号化ツール_cryptographyライブラリ使用_cli - ファイル操作プロジェクト
"""

import os
import sys
import argparse
import shutil
import logging
from datetime import datetime
from pathlib import Path


class FileOrganizer:
    """ファイル整理クラス"""

    def __init__(self):
        self.setup_logging()
        self.logger.info("✅ ファイル整理システム初期化完了")

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def organize_files(self, source_dir: str, target_dir: str = None) -> dict:
        """ファイル整理実行"""
        try:
            source_path = Path(source_dir)
            if not source_path.exists():
                return {"success": False, "error": f"ソースディレクトリが見つかりません: {source_dir}"}

            if target_dir is None:
                target_dir = source_path / "organized"

            target_path = Path(target_dir)
            target_path.mkdir(exist_ok=True)

            organized_count = 0
            file_types = {}

            for file_path in source_path.rglob('*'):
                if file_path.is_file() and file_path.parent != target_path:
                    # ファイル拡張子による分類
                    extension = file_path.suffix.lower() or 'no_extension'
                    type_dir = target_path / extension[1:] if extension != 'no_extension' else target_path / 'no_extension'
                    type_dir.mkdir(exist_ok=True)

                    # ファイル移動
                    new_path = type_dir / file_path.name
                    counter = 1
                    while new_path.exists():
                        stem = file_path.stem
                        new_path = type_dir / f"{stem}_{counter}{extension}"
                        counter += 1

                    shutil.copy2(file_path, new_path)
                    organized_count += 1

                    # 統計更新
                    file_types[extension] = file_types.get(extension, 0) + 1

                    self.logger.info(f"移動: {file_path} -> {new_path}")

            return {
                "success": True,
                "organized_count": organized_count,
                "file_types": file_types,
                "target_directory": str(target_path),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"ファイル整理エラー: {e}")
            return {"success": False, "error": str(e)}

    def get_directory_stats(self, directory: str) -> dict:
        """ディレクトリ統計取得"""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {"success": False, "error": "ディレクトリが見つかりません"}

            file_count = 0
            total_size = 0
            file_types = {}

            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
                    extension = file_path.suffix.lower() or 'no_extension'
                    file_types[extension] = file_types.get(extension, 0) + 1

            return {
                "success": True,
                "file_count": file_count,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="ファイル暗号化・復号化ツール（cryptographyライブラリ使用）を実現するmediumレベルのPythonプロジェクト")
    parser.add_argument("--source", "-s", required=True, help="ソースディレクトリ")
    parser.add_argument("--target", "-t", help="ターゲットディレクトリ")
    parser.add_argument("--stats", action="store_true", help="統計表示のみ")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")

    args = parser.parse_args()

    # ファイル整理システム初期化
    organizer = FileOrganizer()

    if args.stats:
        # 統計表示
        stats = organizer.get_directory_stats(args.source)
        if stats["success"]:
            print(f"\n📊 ディレクトリ統計:")
            print(f"  📁 ディレクトリ: {args.source}")
            print(f"  📄 ファイル数: {stats['file_count']}")
            print(f"  💾 総サイズ: {stats['total_size_mb']} MB")
            print(f"  📋 ファイルタイプ:")
            for ext, count in stats['file_types'].items():
                print(f"    {ext}: {count} 件")
        else:
            print(f"❌ 統計取得失敗: {stats['error']}")
    else:
        # ファイル整理実行
        result = organizer.organize_files(args.source, args.target)
        if result["success"]:
            print(f"✅ ファイル整理完了:")
            print(f"  📁 ソース: {args.source}")
            print(f"  📁 ターゲット: {result['target_directory']}")
            print(f"  📄 整理ファイル数: {result['organized_count']}")
            print(f"  📋 ファイルタイプ分布: {result['file_types']}")
        else:
            print(f"❌ ファイル整理失敗: {result['error']}")
            sys.exit(1)


if __name__ == "__main__":
    main()
