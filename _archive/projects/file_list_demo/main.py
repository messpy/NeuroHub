#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ファイル一覧表示ツール - MCP デモ

このツールは指定されたディレクトリのファイル一覧を表示する
シンプルなMCP (Model Context Protocol) ツールのデモです。
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import json
import time


def list_files(directory: str, recursive: bool = False, show_hidden: bool = False,
               filter_ext: str = None, sort_by: str = "name") -> List[Dict[str, Any]]:
    """
    指定されたディレクトリのファイル一覧を取得

    Args:
        directory: 対象ディレクトリのパス
        recursive: サブディレクトリも含めるかどうか
        show_hidden: 隠しファイルも表示するかどうか
        filter_ext: 拡張子でフィルタ（例: ".py", ".txt"）
        sort_by: ソート方法（"name", "size", "modified"）

    Returns:
        ファイル情報のリスト
    """
    files_info = []
    target_path = Path(directory).resolve()

    if not target_path.exists():
        raise FileNotFoundError(f"ディレクトリが見つかりません: {directory}")

    if not target_path.is_dir():
        raise NotADirectoryError(f"指定されたパスはディレクトリではありません: {directory}")

    # ファイル取得のパターンを決定
    if recursive:
        pattern = "**/*"
    else:
        pattern = "*"

    for item in target_path.glob(pattern):
        # 隠しファイルの処理
        if not show_hidden and item.name.startswith('.'):
            continue

        # 拡張子フィルタ
        if filter_ext and not item.name.lower().endswith(filter_ext.lower()):
            continue

        try:
            stat = item.stat()
            file_info = {
                "name": item.name,
                "path": str(item.relative_to(target_path)),
                "absolute_path": str(item),
                "type": "directory" if item.is_dir() else "file",
                "size": stat.st_size if item.is_file() else None,
                "modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
                "permissions": oct(stat.st_mode)[-3:],
            }

            # ファイルの場合は追加情報
            if item.is_file():
                file_info["extension"] = item.suffix

            files_info.append(file_info)

        except (OSError, PermissionError) as e:
            # アクセス権限のないファイルはスキップ
            print(f"警告: {item} にアクセスできません: {e}", file=sys.stderr)
            continue

    # ソート
    if sort_by == "size":
        files_info.sort(key=lambda x: x.get("size", 0) or 0, reverse=True)
    elif sort_by == "modified":
        files_info.sort(key=lambda x: x["modified"], reverse=True)
    else:  # name
        files_info.sort(key=lambda x: x["name"].lower())

    return files_info


def format_file_size(size_bytes: int) -> str:
    """ファイルサイズを人間が読みやすい形式でフォーマット"""
    if size_bytes is None:
        return "-"

    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def print_file_list(files_info: List[Dict[str, Any]], output_format: str = "table"):
    """ファイル一覧を指定された形式で出力"""

    if not files_info:
        print("ファイルが見つかりませんでした。")
        return

    if output_format == "json":
        print(json.dumps(files_info, ensure_ascii=False, indent=2))
        return

    if output_format == "csv":
        print("名前,タイプ,サイズ,更新日時,パス")
        for info in files_info:
            size_str = format_file_size(info.get("size"))
            print(f'"{info["name"]}","{info["type"]}","{size_str}","{info["modified"]}","{info["path"]}"')
        return

    # table形式（デフォルト）
    print(f"{'名前':<30} {'タイプ':<10} {'サイズ':<10} {'更新日時':<20} {'パス'}")
    print("=" * 90)

    for info in files_info:
        name = info["name"][:28] + ".." if len(info["name"]) > 30 else info["name"]
        file_type = info["type"]
        size_str = format_file_size(info.get("size"))
        modified = info["modified"]
        path = info["path"][:30] + ".." if len(info["path"]) > 32 else info["path"]

        print(f"{name:<30} {file_type:<10} {size_str:<10} {modified:<20} {path}")


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="ファイル一覧表示ツール - MCP デモ",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python main.py                          # 現在のディレクトリのファイル一覧
  python main.py /home/user/documents     # 指定ディレクトリのファイル一覧
  python main.py -r                       # 再帰的にサブディレクトリも含める
  python main.py -a                       # 隠しファイルも表示
  python main.py --filter .py             # Python ファイルのみ表示
  python main.py --sort size              # ファイルサイズ順でソート
  python main.py --format json            # JSON 形式で出力
        """
    )

    parser.add_argument(
        "directory",
        nargs="?",
        default=".",
        help="対象ディレクトリのパス（デフォルト: 現在のディレクトリ）"
    )

    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="サブディレクトリも再帰的に表示"
    )

    parser.add_argument(
        "-a", "--all",
        action="store_true",
        help="隠しファイル（.で始まるファイル）も表示"
    )

    parser.add_argument(
        "--filter",
        help="拡張子でフィルタ（例: .py, .txt）"
    )

    parser.add_argument(
        "--sort",
        choices=["name", "size", "modified"],
        default="name",
        help="ソート方法（デフォルト: name）"
    )

    parser.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="出力形式（デフォルト: table）"
    )

    parser.add_argument(
        "--count",
        action="store_true",
        help="ファイル数のみ表示"
    )

    parser.add_argument(
        "--version",
        action="version",
        version="ファイル一覧表示ツール v1.0.0"
    )

    args = parser.parse_args()

    try:
        # ファイル一覧取得
        files_info = list_files(
            directory=args.directory,
            recursive=args.recursive,
            show_hidden=args.all,
            filter_ext=args.filter,
            sort_by=args.sort
        )

        # ファイル数のみ表示の場合
        if args.count:
            file_count = len([f for f in files_info if f["type"] == "file"])
            dir_count = len([f for f in files_info if f["type"] == "directory"])
            print(f"ファイル数: {file_count}, ディレクトリ数: {dir_count}, 合計: {len(files_info)}")
            return

        # 結果の表示
        print(f"ディレクトリ: {os.path.abspath(args.directory)}")
        print(f"ファイル数: {len(files_info)}")
        print()

        print_file_list(files_info, args.format)

    except (FileNotFoundError, NotADirectoryError, PermissionError) as e:
        print(f"エラー: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n処理が中断されました。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
