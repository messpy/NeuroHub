#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
四則演算ができるコマンドライン計算機_式を入力すると計算結果を表示する_cli - 四則演算ができるコマンドライン計算機。式を入力すると計算結果を表示するを実現するsimpleレベルのPythonプロジェクト
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path


class 四則演算ができるコマンドライン計算機式を入力すると計算結果を表示するCli:
    """メインプロジェクトクラス"""

    def __init__(self):
        self.setup_logging()
        self.logger.info("✅ システム初期化完了")

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def execute(self, params: dict) -> dict:
        """メイン実行"""
        try:
            self.logger.info(f"🚀 実行開始: {params}")

            # メイン処理
            result = self.process(params)

            self.logger.info(f"✅ 実行完了: {result}")
            return result

        except Exception as e:
            self.logger.error(f"❌ 実行失敗: {e}")
            return {"success": False, "error": str(e)}

    def calculate(self, expression: str) -> float:
        """
        計算式を評価して結果を返す

        Args:
            expression: 計算式（例: "2+3", "10*5-2"）

        Returns:
            計算結果
        """
        # 安全な評価のため、許可する文字のみをチェック
        allowed_chars = "0123456789+-*/.()\t\n\r "
        if not all(c in allowed_chars for c in expression):
            raise ValueError("無効な文字が含まれています。数字と演算子(+, -, *, /, (, ))のみ使用可能です。")

        try:
            # eval()で計算（安全性チェック済み）
            result = eval(expression)
            return float(result)
        except ZeroDivisionError:
            raise ValueError("ゼロ除算エラー")
        except Exception as e:
            raise ValueError(f"計算エラー: {e}")

    def process(self, params: dict) -> dict:
        """処理実装"""
        expression = params.get("input")

        if not expression:
            return {
                "success": False,
                "error": "計算式を入力してください（例: --input \"2+3\"）"
            }

        try:
            result = self.calculate(expression)
            return {
                "success": True,
                "expression": expression,
                "result": result,
                "message": f"{expression} = {result}",
                "timestamp": datetime.now().isoformat()
            }
        except ValueError as e:
            return {
                "success": False,
                "expression": expression,
                "error": str(e)
            }


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="四則演算ができるコマンドライン計算機。式を入力すると計算結果を表示するを実現するsimpleレベルのPythonプロジェクト")
    parser.add_argument("--input", "-i", help="入力パラメータ")
    parser.add_argument("--output", "-o", help="出力ファイル")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")

    args = parser.parse_args()

    # システム初期化
    system = 四則演算ができるコマンドライン計算機式を入力すると計算結果を表示するCli()

    # パラメータ準備
    params = {
        "input": args.input,
        "output": args.output,
        "verbose": args.verbose
    }

    # 実行
    result = system.execute(params)

    if result.get("success"):
        print(f"\n🧮 計算結果")
        print(f"  式: {result.get('expression')}")
        print(f"  答え: {result.get('result')}")
        print(f"\n✅ {result.get('message')}")
    else:
        print(f"❌ エラー: {result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
