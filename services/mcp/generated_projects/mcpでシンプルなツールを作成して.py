#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from datetime import datetime
import logging
from pathlib import Path


def setup_logger():
    """ロギング設定"""
    log_file_path = "logger.log"
    log_level = logging.INFO  # 日付：最小でもOK

    logger = logging.getLogger(__name__)
    handler = logging.FileHandler(log_file_path, mode="a")
    handler.setLevel(log_level)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    return logger


def parse_args():
    """命令行パラメータの取得"""
    parser = argparse.ArgumentParser(description="CSV/JSONデータの変換ツール")
    subparsers = parser.add_subparsers(dest='command')

    # CSVファイルを生成する子スコープ
    csv_parser = subparsers.add_parser('csv', help='CSVデータからJSONに変換')
    csv_parser.add_argument('--input-file', required=True, type=Path)
    csv_parser.set_defaults(func=convert_csv)

    # JSONデータベースに保存する設定の子スコープ
    json_config_parser = subparsers.add_parser('json-config', help="JSONデータベースに保存")
    json_config_parser.add_argument('--database-name', default="default_db", type=str)
    json_config_parser.set_defaults(func=save_json_config)

    return parser.parse_args()


def convert_csv(input_file: Path, output_file: str):
    """CSVファイルからJSONデータを生成する"""
    with input_file.open("r") as f:
        content = f.read()

    # データ変換
    json_data = {
        'input': content,
        'output': output_file.name
    }

    print(json.dumps(json_data, ensure_ascii=False))


def save_json_config(output_file: str):
    """JSONデータベースに保存する"""
    with open(output_file, "w") as f:
        f.write("default_db")

    # 生成したCSVファイルが存在しない場合は追加する
if not Path('csv_output.csv').exists():
        with open('csv_output.csv', 'a') as f:
            f.write("\n")
        sys.exit()

# ディレクティブの設定
    logger = setup_logger()