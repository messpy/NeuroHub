"""
Ollama Modelfile動的生成システム
用途に応じてModelfileを生成し、ollamaモデルをビルド
"""
from pathlib import Path
from typing import Dict, Optional
import subprocess
import sys

class ModelfileGenerator:
    """Modelfile動的生成クラス"""

    def __init__(self):
        self.base_model = "qwen2.5-coder:7b"
        self.modelfiles_dir = Path("modelfiles")
        self.modelfiles_dir.mkdir(exist_ok=True)

    def generate_mcp_modelfile(self,
                               rules_file: str = "docs/MCP_CODING_RULES.md",
                               output_name: str = "mcp_code_assistant") -> Path:
        """
        MCP専用Modelfileを生成

        Args:
            rules_file: MCPコーディングルールファイルのパス
            output_name: 出力Modelfile名

        Returns:
            生成されたModelfileのパス
        """
        rules_path = Path(rules_file)

        if not rules_path.exists():
            raise FileNotFoundError(f"ルールファイルが見つかりません: {rules_file}")

        # ルールファイルを読み込み
        with open(rules_path, 'r', encoding='utf-8') as f:
            rules_content = f.read()

        # Modelfile生成
        modelfile_content = f'''# MCP Auto Code Generation Assistant
# MCPコーディングルールに基づいたコード生成アシスタント

FROM {self.base_model}

# システムプロンプト: MCPルール準拠
SYSTEM """あなたはMCP自動プロジェクト生成システムの専門コード生成アシスタントです。

## 絶対ルール

1. input()は絶対に使用禁止（自動テストがタイムアウトするため）
2. 必ずargparseを使用してCLI実装
3. --test, --help オプションを必ず実装
4. 標準ライブラリのみ使用
5. エラーハンドリング必須
6. 実行可能な完全なコードを生成
7. rm, sudo コマンドは絶対に使用禁止

## 禁止パターン

- input()の使用
- 外部ライブラリ（pip install必要）
- 対話的な入力待ち
- while True: + input()のループ
- rm コマンド（ファイル削除は pathlib.Path.unlink() または os.remove() を使用）
- sudo コマンド
- os.system() による危険なシェルコマンド実行

## 推奨パターン

- argparse.ArgumentParser()を使用
- --test オプションでテストケース実行
- --help オプションは自動生成される
- pathlib.Pathでファイル操作
- loggingでログ出力
- ファイル削除は Path.unlink() または os.remove()

## コード構造テンプレート

すべてのCLIアプリケーションは以下の構造に従う:

1. import文（argparse, sys, pathlibなど）
2. main()関数を定義
3. ArgumentParser作成
4. --testオプション追加
5. args.testでテストケース分岐
6. if __name__ == "__main__": main()

## 出力形式

Pythonコードのみを出力。説明文は不要。必ず実行可能な完全なコードを返す。
"""

# 温度設定: コード生成に最適化
PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER top_k 40

# コンテキストウィンドウ
PARAMETER num_ctx 8192

# 停止トークン
PARAMETER stop "```\\n\\n"
'''

        # Modelfileを保存
        output_path = self.modelfiles_dir / f"{output_name}.Modelfile"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)

        print(f"✅ Modelfile生成成功: {output_path}")
        return output_path

    def generate_db_modelfile(self,
                              readme_path: str = "generated_projects/テキストエディタ_cli/README.md",
                              output_name: str = "db_sample_assistant") -> Path:
        """
        データベース操作用Modelfileを生成

        Args:
            readme_path: サンプルコードを含むREADMEのパス
            output_name: 出力Modelfile名

        Returns:
            生成されたModelfileのパス
        """
        readme = Path(readme_path)

        if not readme.exists():
            raise FileNotFoundError(f"READMEが見つかりません: {readme_path}")

        # READMEからサンプルコードセクションを抽出
        with open(readme, 'r', encoding='utf-8') as f:
            readme_content = f.read()

        # データベース操作部分を抽出
        db_sample_start = readme_content.find("### データベース操作のサンプル")
        db_sample_end = readme_content.find("### ファイル操作のサンプル")

        if db_sample_start == -1:
            raise ValueError("READMEにデータベースサンプルが見つかりません")

        db_sample = readme_content[db_sample_start:db_sample_end] if db_sample_end != -1 else readme_content[db_sample_start:]

        # Modelfile生成
        modelfile_content = f'''# Database Sample Code Assistant
# READMEのDatabaseManagerサンプルコードを参照

FROM {self.base_model}

SYSTEM """あなたはデータベース操作のコード生成アシスタントです。

以下のREADMEサンプルコードを参照してデータベース操作コードを生成します。

---
{db_sample}
---

## コード生成ルール
1. 必ずDatabaseManagerクラスを使用
2. 実行可能な完全なコードを生成
3. エラーハンドリングを含める
4. テーブル形式で見やすく表示
5. 最後にdb.close()を実行

## 出力形式
```pythonで囲んでコードのみ出力してください。
"""

PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
'''

        output_path = self.modelfiles_dir / f"{output_name}.Modelfile"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(modelfile_content)

        print(f"✅ Modelfile生成成功: {output_path}")
        return output_path

    def build_model(self, modelfile_path: Path, model_name: str) -> bool:
        """
        Modelfileからollamaモデルをビルド

        Args:
            modelfile_path: Modelfileのパス
            model_name: 作成するモデル名

        Returns:
            成功フラグ
        """
        if not modelfile_path.exists():
            print(f"❌ エラー: Modelfileが見つかりません: {modelfile_path}")
            return False

        print(f"\n{'='*80}")
        print(f"🔨 Ollamaモデルビルド")
        print(f"{'='*80}")
        print(f"📄 Modelfile: {modelfile_path}")
        print(f"🏷️  モデル名: {model_name}")
        print(f"{'-'*80}")

        try:
            # ollama createコマンド実行
            cmd = ["ollama", "create", model_name, "-f", str(modelfile_path)]
            print(f"🚀 実行コマンド: {' '.join(cmd)}")
            print(f"{'-'*80}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8'
            )

            if result.returncode == 0:
                print(f"\n✅ モデルビルド成功!")
                print(f"{'-'*80}")
                print("出力:")
                print(result.stdout)
                print(f"{'-'*80}")
                return True
            else:
                print(f"\n❌ モデルビルド失敗")
                print(f"{'-'*80}")
                print("エラー出力:")
                print(result.stderr)
                print(f"{'-'*80}")
                return False

        except FileNotFoundError:
            print(f"\n❌ エラー: ollamaコマンドが見つかりません")
            print("Ollamaがインストールされているか確認してください")
            return False
        except Exception as e:
            print(f"\n❌ 予期しないエラー: {e}")
            return False

    def generate_and_build(self,
                          purpose: str = "mcp",
                          model_name: Optional[str] = None,
                          **kwargs) -> bool:
        """
        Modelfileを生成してビルドまで一括実行

        Args:
            purpose: 用途 ("mcp", "db", "custom")
            model_name: モデル名（Noneの場合は自動生成）
            **kwargs: generate_*_modelfile()への追加引数

        Returns:
            成功フラグ
        """
        try:
            # 用途に応じてModelfile生成
            if purpose == "mcp":
                modelfile_path = self.generate_mcp_modelfile(**kwargs)
                model_name = model_name or "neurohub-mcp-assistant"
            elif purpose == "db":
                modelfile_path = self.generate_db_modelfile(**kwargs)
                model_name = model_name or "neurohub-db-assistant"
            else:
                raise ValueError(f"未対応の用途: {purpose}")

            # モデルビルド
            return self.build_model(modelfile_path, model_name)

        except Exception as e:
            print(f"❌ エラー: {e}")
            return False


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Ollama Modelfile動的生成＆ビルド")
    parser.add_argument("--purpose", type=str, default="mcp",
                       choices=["mcp", "db"],
                       help="用途 (mcp: MCP専用, db: DB操作)")
    parser.add_argument("--model-name", type=str,
                       help="モデル名（省略時は自動生成）")
    parser.add_argument("--rules-file", type=str,
                       default="docs/MCP_CODING_RULES.md",
                       help="MCPルールファイル（purpose=mcpのみ）")
    parser.add_argument("--readme-path", type=str,
                       default="generated_projects/テキストエディタ_cli/README.md",
                       help="READMEパス（purpose=dbのみ）")
    parser.add_argument("--build", action="store_true",
                       help="Modelfile生成後にビルドも実行")

    args = parser.parse_args()

    generator = ModelfileGenerator()

    kwargs = {}
    if args.purpose == "mcp":
        kwargs["rules_file"] = args.rules_file
    elif args.purpose == "db":
        kwargs["readme_path"] = args.readme_path

    if args.build:
        # 生成＆ビルド
        success = generator.generate_and_build(
            purpose=args.purpose,
            model_name=args.model_name,
            **kwargs
        )
        sys.exit(0 if success else 1)
    else:
        # 生成のみ
        if args.purpose == "mcp":
            modelfile_path = generator.generate_mcp_modelfile(**kwargs)
        elif args.purpose == "db":
            modelfile_path = generator.generate_db_modelfile(**kwargs)

        print(f"\n使用方法:")
        print(f"  ollama create {args.model_name or 'モデル名'} -f {modelfile_path}")


if __name__ == "__main__":
    main()
