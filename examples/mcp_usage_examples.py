#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroHub MCP エージェント - 実践的使用例

このファイルは、ユーザーがMCPエージェントを効果的に使用するための
実際のコード例とベストプラクティスを示します。

使用前準備:
1. WSL環境の準備: wsl --install
2. NeuroHubのaidevブランチで作業: git checkout aidev
3. 依存関係インストール: pip install -r requirements.txt
"""

import sys
from pathlib import Path

# NeuroHubプロジェクトルートを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.agent_mcp import MCPAgent, MCPRequest


class MCPUsageExamples:
    """MCP エージェント使用例集"""
    
    def __init__(self):
        """
        MCPエージェントを初期化
        
        注意: このクラスは実際のMCPAgentを初期化します。
        デモ用途以外では、必要に応じて初期化してください。
        """
        print("🚀 MCP エージェント初期化中...")
        self.agent = MCPAgent()
        print("✅ 初期化完了")
    
    def example_1_simple_code_generation(self):
        """
        例1: シンプルなコード生成
        
        目的: 基本的な計算機能を持つPythonスクリプトを生成
        特徴: 品質検証有効、自動デバッグ有効
        """
        print("\n" + "="*50)
        print("📝 例1: シンプルなコード生成")
        print("="*50)
        
        # リクエスト作成
        request = MCPRequest(
            mode='generate',
            prompt="""
            基本的な四則演算を行う計算機を作成してください。
            
            要件:
            - 2つの数値と演算子（+, -, *, /）を引数で受け取る
            - コマンドライン実行: python calc.py 10 + 5
            - 結果を表示: "10 + 5 = 15"
            - エラーハンドリング（ゼロ除算、不正な演算子）
            - ヘルプ機能（--help）
            """,
            language='python',
            validate=True,      # 品質検証必須
            auto_debug=True,    # 自動修正必須
            temperature=0.1     # 安定性重視
        )
        
        print("🎯 リクエスト内容:")
        print(f"  モード: {request.mode}")
        print(f"  言語: {request.language}")
        print(f"  品質検証: {request.validate}")
        print(f"  自動デバッグ: {request.auto_debug}")
        
        # 実行
        print("\n⚡ MCPエージェント実行中...")
        result = self.agent.execute(request)
        
        # 結果表示
        self._display_result(result, "シンプル計算機")
        
        return result
    
    def example_2_project_generation(self):
        """
        例2: 完全なプロジェクト生成
        
        目的: FlaskベースのTodoアプリプロジェクトを生成
        特徴: フルプロジェクト構造、設計書、テストコード含む
        """
        print("\n" + "="*50)
        print("🏗️ 例2: 完全なプロジェクト生成")
        print("="*50)
        
        request = MCPRequest(
            mode='project',
            prompt="""
            FlaskベースのTodoアプリケーションプロジェクトを作成してください。
            
            機能要件:
            - Todo項目のCRUD操作（作成、読み取り、更新、削除）
            - Webインターフェース（HTML + Bootstrap）
            - データベース連携（SQLite）
            - RESTful API エンドポイント
            
            技術要件:
            - Flask 2.0+
            - SQLAlchemy ORM
            - Bootstrap 5 UI
            - Jinja2 テンプレート
            
            プロジェクト構造:
            - main.py: エントリーポイント
            - models/: データモデル
            - views/: ルート定義
            - templates/: HTMLテンプレート
            - static/: CSS/JS
            - config/: 設定ファイル
            """,
            project_name='todo_web_app',
            framework='flask',
            language='python',
            validate=True,
            auto_debug=True,
            max_tokens=6000  # プロジェクト生成は大きなコンテキストが必要
        )
        
        print("🎯 プロジェクト生成設定:")
        print(f"  プロジェクト名: {request.project_name}")
        print(f"  フレームワーク: {request.framework}")
        print(f"  最大トークン: {request.max_tokens}")
        
        print("\n⚡ MCPエージェント実行中（プロジェクト生成は時間がかかります...）")
        result = self.agent.execute(request)
        
        self._display_result(result, "Todo Webアプリ")
        
        return result
    
    def example_3_debug_mode(self):
        """
        例3: デバッグモード
        
        目的: 既存のバグのあるコードを分析・修正
        特徴: エラー検出、修正提案、改善案提示
        """
        print("\n" + "="*50)
        print("🔧 例3: デバッグモード")
        print("="*50)
        
        # バグのあるサンプルコード
        buggy_code = '''
import argparse

def main():
    parser = argparse.ArgumentParser(description="計算機")
    parser.add_argument("num1", type=float, help="第1数値")
    parser.add_argument("operator", choices=["+", "-", "*", "/"])
    parser.add_argument("num2", type=float, help="第2数値")
    
    args = parser.parse_args()
    
    # ❌ バグ: show_historyは定義されていない
    if args.show_history:
        print("履歴を表示します")
    
    # ❌ バグ: result変数が未定義の場合がある
    if args.operator == "+":
        result = args.num1 + args.num2
    elif args.operator == "-":
        result = args.num1 - args.num2
    # ❌ バグ: 乗算と除算が未実装
    
    print(f"結果: {result}")  # ❌ バグ: resultが未定義の可能性

if __name__ == "__main__":
    main()
'''
        
        request = MCPRequest(
            mode='debug',
            prompt=f"""
            以下のPythonコードにはいくつかのバグがあります。
            問題を特定し、修正版を提供してください。
            
            バグのあるコード:
            {buggy_code}
            
            期待する修正:
            1. 未定義属性エラーの修正
            2. 未実装機能の完成
            3. エラーハンドリングの追加
            4. コード品質の改善
            """,
            language='python',
            validate=True,
            auto_debug=True
        )
        
        print("🎯 デバッグ対象:")
        print("  - 未定義属性エラー (args.show_history)")
        print("  - 未実装機能 (乗算・除算)")
        print("  - 未定義変数 (result)")
        
        print("\n⚡ MCPエージェント実行中...")
        result = self.agent.execute(request)
        
        self._display_result(result, "デバッグ・修正版")
        
        return result
    
    def example_4_quality_focused_generation(self):
        """
        例4: 品質重視の生成
        
        目的: 最高品質のコード生成（85%以上の品質スコア目標）
        特徴: 厳格な検証、複数回の自動修正、詳細なテスト
        """
        print("\n" + "="*50)
        print("💎 例4: 品質重視の生成")
        print("="*50)
        
        request = MCPRequest(
            mode='generate',
            prompt="""
            高品質なファイル管理システムを作成してください。
            
            機能要件:
            - ファイル・ディレクトリの一覧表示
            - ファイルのコピー、移動、削除
            - ディレクトリの作成、削除
            - ファイル検索機能
            - 権限チェック
            
            品質要件:
            - 完全なエラーハンドリング
            - ユニットテスト対応設計
            - ログ機能
            - 設定ファイル対応
            - ドキュメント文字列完備
            - 型ヒント使用
            
            技術要件:
            - argparseによるCLI
            - pathlib使用
            - logging設定
            - JSON設定ファイル
            """,
            language='python',
            validate=True,
            auto_debug=True,
            temperature=0.05,    # 最低創造性（最高安定性）
            use_hints=True       # ヒント使用
        )
        
        print("🎯 品質重視設定:")
        print(f"  温度設定: {request.temperature} (最高安定性)")
        print(f"  ヒント使用: {request.use_hints}")
        print(f"  目標品質スコア: 85%以上")
        
        print("\n⚡ MCPエージェント実行中...")
        result = self.agent.execute(request)
        
        self._display_result(result, "高品質ファイル管理システム")
        
        # 品質スコア確認
        if result.quality_score >= 85:
            print("🎉 目標品質スコア達成！")
        else:
            print(f"⚠️ 品質スコア不足: {result.quality_score}% < 85%")
            
        return result
    
    def example_5_wsl_execution_test(self):
        """
        例5: WSL環境での実行テスト
        
        目的: 生成されたコードをWSL環境で実際に実行してテスト
        特徴: クロスプラットフォーム実行、実際の動作確認
        """
        print("\n" + "="*50)
        print("🐧 例5: WSL環境実行テスト")
        print("="*50)
        
        # シンプルなHello Worldを生成
        request = MCPRequest(
            mode='generate',
            prompt="""
            WSL環境での実行テスト用のHello Worldプログラムを作成してください。
            
            要件:
            - プログラム起動時に環境情報を表示
            - 現在時刻の表示
            - システム情報の取得（OS、Python版）
            - コマンドライン引数でメッセージをカスタマイズ可能
            - 実行例: python hello.py "カスタムメッセージ"
            """,
            language='python',
            validate=True,
            auto_debug=True
        )
        
        print("🎯 WSL実行テスト用コード生成...")
        result = self.agent.execute(request)
        
        if result.success and result.output_path:
            print(f"\n🐧 WSL実行テスト開始:")
            print(f"生成ファイル: {result.output_path}")
            
            # WSLコマンド構築
            wsl_path = result.output_path.replace('C:\\', '/mnt/c/').replace('\\', '/')
            wsl_command = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && python3 \'{wsl_path}\'"'
            
            print(f"実行コマンド: {wsl_command}")
            print("\n📋 実行結果:")
            
            # 実際の実行（デモ用に表示のみ）
            print("💡 実際の実行は以下のコマンドで行えます:")
            print(f"   {wsl_command}")
            print("   wsl bash -c \"cd /mnt/c/Users/kenny/sandbox/NeuroHub && python3 'generated_file.py' 'テストメッセージ'\"")
        
        self._display_result(result, "WSL実行テスト用Hello World")
        
        return result
    
    def _display_result(self, result, title: str):
        """
        実行結果を整理して表示
        
        Args:
            result: MCPエージェントの実行結果
            title: 結果のタイトル
        """
        print(f"\n📊 === {title} 実行結果 ===")
        
        # 基本情報
        print(f"✅ 実行成功: {result.success}")
        if hasattr(result, 'quality_score'):
            print(f"📈 品質スコア: {result.quality_score}%")
        
        # 出力パス
        if hasattr(result, 'output_path') and result.output_path:
            print(f"📁 出力パス: {result.output_path}")
        
        # プロバイダー情報
        if hasattr(result, 'provider'):
            print(f"🤖 使用プロバイダー: {result.provider}")
        
        # テスト結果
        if hasattr(result, 'test_results') and result.test_results:
            print(f"🧪 テスト結果:")
            for test in result.test_results:
                status = "✅" if test.get('success', False) else "❌"
                test_name = test.get('test_case', 'Unknown Test')
                print(f"   {status} {test_name}")
        
        # エラー情報
        if hasattr(result, 'validation_errors') and result.validation_errors:
            print(f"⚠️ 検証エラー: {len(result.validation_errors)}件")
            for error in result.validation_errors[:3]:  # 最初の3件のみ表示
                print(f"   - {error}")
        
        # メタデータ
        if hasattr(result, 'metadata') and result.metadata:
            print(f"📋 メタデータ:")
            for key, value in result.metadata.items():
                print(f"   {key}: {value}")
        
        print("-" * 50)


def main():
    """
    MCP エージェント使用例の実行
    
    実行方法:
    1. WSL環境準備: wsl --install
    2. NeuroHub環境: cd /mnt/c/Users/kenny/sandbox/NeuroHub
    3. 実行: python3 examples/mcp_usage_examples.py
    """
    print("🌟 NeuroHub MCP エージェント - 実践的使用例")
    print("=" * 60)
    
    try:
        # 使用例クラス初期化
        examples = MCPUsageExamples()
        
        print("\n📋 利用可能な使用例:")
        print("1. シンプルなコード生成（計算機）")
        print("2. 完全なプロジェクト生成（Todo Webアプリ）")
        print("3. デバッグモード（バグ修正）")
        print("4. 品質重視の生成（ファイル管理システム）")
        print("5. WSL環境実行テスト（Hello World）")
        
        # ユーザー入力
        choice = input("\n実行したい例の番号を入力してください (1-5, またはEnterで全実行): ").strip()
        
        if choice == "1":
            examples.example_1_simple_code_generation()
        elif choice == "2":
            examples.example_2_project_generation()
        elif choice == "3":
            examples.example_3_debug_mode()
        elif choice == "4":
            examples.example_4_quality_focused_generation()
        elif choice == "5":
            examples.example_5_wsl_execution_test()
        else:
            # 全例実行
            print("\n🚀 全ての使用例を実行します...")
            examples.example_1_simple_code_generation()
            examples.example_2_project_generation()
            examples.example_3_debug_mode()
            examples.example_4_quality_focused_generation()
            examples.example_5_wsl_execution_test()
        
        print("\n🎉 使用例実行完了！")
        print("\n💡 ヒント:")
        print("- 生成されたファイルは services/mcp/generated_projects/ に保存されます")
        print("- WSL環境での実行: wsl bash -c \"cd /mnt/c/Users/kenny/sandbox/NeuroHub && python3 file.py\"")
        print("- 詳細なガイド: docs/USER_MCP_GUIDE.md を参照してください")
        
    except Exception as e:
        print(f"❌ エラーが発生しました: {e}")
        print("💡 解決方法:")
        print("1. WSL環境が正しくセットアップされているか確認")
        print("2. NeuroHubのaidevブランチで作業しているか確認")
        print("3. 依存関係がインストールされているか確認: pip install -r requirements.txt")


if __name__ == "__main__":
    main()