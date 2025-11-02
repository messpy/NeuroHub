#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
main.py

ファイル一覧表示ツール
-----------------------
- argparse による CLI サポート（--help が自動生成）
- -a  : 隠しファイルも表示
- -l  : 詳細表示（ファイルサイズ・モード・最終更新日時）
- -R  : 再帰的にディレクトリを走査
- デフォルトではカレントディレクトリを表示
- 外部パッケージは一切使用しない

テストを想定した実装で、実行環境に依存しないように配慮しています。
"""

import os
import sys
import stat
import argparse
import time
from datetime import datetime

def human_readable_size(size_bytes: int) -> str:
    """
    バイト数を人が読みやすいサイズ文字列に変換する。
    例: 1024 -> '1.0K', 1048576 -> '1.0M'
    """
    if size_bytes == 0:
        return "0B"
    units = ["B", "K", "M", "G", "T", "P", "E"]
    idx = 0
    size = float(size_bytes)
    while size >= 1024 and idx < len(units) - 1:
        size /= 1024
        idx += 1
    return f"{size:.1f}{units[idx]}"

def format_mode(mode: int) -> str:
    """
    stat.filemode の結果を返す。Python 3.4+ で標準に含まれる。
    例: 0o100755 -> '-rwxr-xr-x'
    """
    return stat.filemode(mode)

def list_dir(path: str, show_all: bool, long_format: bool, recursive: bool, prefix: str = "") -> None:
    """
    ディレクトリ内のファイル・サブディレクトリを表示する。
    再帰的に走査する場合は `recursive` が True。
    """
    try:
        entries = os.listdir(path)
    except PermissionError:
        print(f"{prefix}Permission denied: {path}", file=sys.stderr)
        return
    except FileNotFoundError:
        print(f"{prefix}No such file or directory: {path}", file=sys.stderr)
        return

    entries.sort()
    for entry in entries:
        # 隠しファイルを除外する（ドットで始まる）
        if not show_all and entry.startswith('.'):
            continue
        full_path = os.path.join(path, entry)
        try:
            stat_result = os.lstat(full_path)
        except OSError as e:
            print(f"{prefix}{entry}\tError: {e}", file=sys.stderr)
            continue

        if long_format:
            mode = format_mode(stat_result.st_mode)
            n_links = stat_result.st_nlink
            size = human_readable_size(stat_result.st_size)
            mtime = datetime.fromtimestamp(stat_result.st_mtime).strftime("%Y-%m-%d %H:%M")
            print(f"{prefix}{mode} {n_links:3} {size:>6} {mtime} {entry}")
        else:
            print(f"{prefix}{entry}")

        # 再帰的にディレクトリを走査
        if recursive and os.path.isdir(full_path) and not os.path.islink(full_path):
            # 子ディレクトリの先頭にパスを付ける
            print(f"{prefix}{full_path}/")
            list_dir(full_path, show_all, long_format, recursive, prefix=prefix + "    ")

def parse_arguments():
    """
    argparse でコマンドライン引数を解析する。
    """
    parser = argparse.ArgumentParser(
        description="シンプルなファイル一覧表示ツール",
        epilog="例: python main.py -l -R ./",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="表示したいファイルやディレクトリ（省略可: 現在のディレクトリ）",
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help="ドットで始まる隠しファイルも表示する",
    )
    parser.add_argument(
        "-l",
        "--long",
        action="store_true",
        help="詳細情報（ファイルサイズ・モード・更新日時）を表示",
    )
    parser.add_argument(
        "-R",
        "--recursive",
        action="store_true",
        help="サブディレクトリを再帰的に表示",
    )
    return parser.parse_args()

def main():
    args = parse_arguments()
    for path in args.paths:
        if not os.path.exists(path):
            print(f"Error: No such file or directory: {path}", file=sys.stderr)
            continue

        # ディレクトリを直接渡された場合はその中身をリストする
        if os.path.isdir(path) and not os.path.islink(path):
            if not args.long:
                # ディレクトリ名を表示
                print(f"{path}/")
            list_dir(path, args.all, args.long, args.recursive, prefix="    ")
        else:
            # 単一ファイルの場合はその情報のみ表示
            try:
                stat_result = os.lstat(path)
            except OSError as e:
                print(f"Error accessing {path}: {e}", file=sys.stderr)
                continue
            entry = os.path.basename(path)
            if args.long:
                mode = format_mode(stat_result.st_mode)
                n_links = stat_result.st_nlink
                size = human_readable_size(stat_result.st_size)
                mtime = datetime.fromtimestamp(stat_result.st_mtime).strftime("%Y-%m-%d %H:%M")
                print(f"{mode} {n_links:3} {size:>6} {mtime} {entry}")
            else:
                print(entry)

if __name__ == "__main__":
    main()