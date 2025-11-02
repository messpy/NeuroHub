#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
csv_json変換ツール_cli - JSON/CSV変換プロジェクト
"""

import json
import csv
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path


class DataConverter:
    """データ変換クラス"""

    def __init__(self):
        self.setup_logging()
        self.logger.info("✅ データ変換システム初期化完了")

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def json_to_csv(self, json_file: str, csv_file: str) -> dict:
        """JSON to CSV変換"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # データが配列かチェック
            if not isinstance(data, list):
                if isinstance(data, dict):
                    data = [data]
                else:
                    return {"success": False, "error": "JSON data must be array or object"}

            if not data:
                return {"success": False, "error": "Empty JSON data"}

            # CSVヘッダー生成
            headers = set()
            for item in data:
                if isinstance(item, dict):
                    headers.update(item.keys())

            headers = sorted(headers)

            # CSV書き込み
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for item in data:
                    if isinstance(item, dict):
                        # ネストされたオブジェクトをJSONストリングに変換
                        row = {}
                        for key in headers:
                            value = item.get(key, '')
                            if isinstance(value, (dict, list)):
                                value = json.dumps(value, ensure_ascii=False)
                            row[key] = value
                        writer.writerow(row)

            return {
                "success": True,
                "input_file": json_file,
                "output_file": csv_file,
                "records_count": len(data),
                "columns_count": len(headers),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"JSON to CSV変換エラー: {e}")
            return {"success": False, "error": str(e)}

    def csv_to_json(self, csv_file: str, json_file: str) -> dict:
        """CSV to JSON変換"""
        try:
            data = []

            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # 空文字列をNoneに変換
                    processed_row = {}
                    for key, value in row.items():
                        if value == '':
                            processed_row[key] = None
                        else:
                            # JSON文字列を解析試行
                            try:
                                if value.startswith(('{', '[')) and value.endswith(('}', ']')):
                                    processed_row[key] = json.loads(value)
                                else:
                                    processed_row[key] = value
                            except json.JSONDecodeError:
                                processed_row[key] = value

                    data.append(processed_row)

            # JSON書き込み
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return {
                "success": True,
                "input_file": csv_file,
                "output_file": json_file,
                "records_count": len(data),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"CSV to JSON変換エラー: {e}")
            return {"success": False, "error": str(e)}

    def validate_json(self, json_file: str) -> dict:
        """JSON検証"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "success": True,
                "valid": True,
                "type": type(data).__name__,
                "size": len(str(data)),
                "record_count": len(data) if isinstance(data, list) else 1
            }

        except Exception as e:
            return {
                "success": True,
                "valid": False,
                "error": str(e)
            }

    def get_file_info(self, file_path: str) -> dict:
        """ファイル情報取得"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {"success": False, "error": "File not found"}

            return {
                "success": True,
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
                "extension": path.suffix,
                "modified_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            }

        except Exception as e:
            return {"success": False, "error": str(e)}


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="CSV to JSON変換ツールを実現するsimpleレベルのPythonプロジェクト")
    parser.add_argument("--input", "-i", required=True, help="入力ファイル")
    parser.add_argument("--output", "-o", required=True, help="出力ファイル")
    parser.add_argument("--mode", "-m", choices=['json2csv', 'csv2json'], required=True, help="変換モード")
    parser.add_argument("--validate", action="store_true", help="入力ファイル検証")
    parser.add_argument("--info", action="store_true", help="ファイル情報表示")

    args = parser.parse_args()

    # データ変換システム初期化
    converter = DataConverter()

    # ファイル情報表示
    if args.info:
        info = converter.get_file_info(args.input)
        if info["success"]:
            print(f"\n📄 ファイル情報:")
            print(f"  📁 ファイル名: {info['file_name']}")
            print(f"  💾 サイズ: {info['file_size_mb']} MB")
            print(f"  📅 更新日時: {info['modified_time']}")
        else:
            print(f"❌ ファイル情報取得失敗: {info['error']}")

    # JSON検証
    if args.validate and args.input.endswith('.json'):
        validation = converter.validate_json(args.input)
        if validation["success"]:
            if validation["valid"]:
                print(f"✅ JSON検証成功: タイプ={validation['type']}, レコード数={validation['record_count']}")
            else:
                print(f"❌ JSON検証失敗: {validation['error']}")
        else:
            print(f"❌ JSON検証エラー: {validation['error']}")

    # データ変換実行
    if args.mode == 'json2csv':
        result = converter.json_to_csv(args.input, args.output)
    elif args.mode == 'csv2json':
        result = converter.csv_to_json(args.input, args.output)
    else:
        print(f"❌ 不正な変換モード: {args.mode}")
        sys.exit(1)

    if result["success"]:
        print(f"✅ 変換完了:")
        print(f"  📥 入力: {result['input_file']}")
        print(f"  📤 出力: {result['output_file']}")
        print(f"  📊 レコード数: {result['records_count']}")
        if 'columns_count' in result:
            print(f"  📋 カラム数: {result['columns_count']}")
    else:
        print(f"❌ 変換失敗: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
