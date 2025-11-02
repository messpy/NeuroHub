"""
Ollama Modelfileビルドスクリプト
カスタムモデルをModelfileから作成
"""
import subprocess
import sys
from pathlib import Path

def build_model(modelfile_path: str, model_name: str):
    """
    Modelfileからカスタムモデルをビルド

    Args:
        modelfile_path: Modelfileのパス
        model_name: 作成するモデル名
    """
    modelfile = Path(modelfile_path)

    if not modelfile.exists():
        print(f"❌ エラー: Modelfileが見つかりません: {modelfile_path}")
        return False

    print("=" * 80)
    print(f"🔨 Ollama カスタムモデルビルド")
    print("=" * 80)
    print(f"📄 Modelfile: {modelfile_path}")
    print(f"🏷️  モデル名: {model_name}")
    print("-" * 80)

    try:
        # ollama createコマンド実行
        cmd = ["ollama", "create", model_name, "-f", str(modelfile)]
        print(f"🚀 実行コマンド: {' '.join(cmd)}")
        print("-" * 80)

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )

        if result.returncode == 0:
            print("\n✅ モデルビルド成功!")
            print("-" * 80)
            print("出力:")
            print(result.stdout)
            print("-" * 80)

            # モデル一覧を表示
            print("\n📋 登録されているモデル一覧:")
            list_result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            print(list_result.stdout)

            return True
        else:
            print("\n❌ モデルビルド失敗")
            print("-" * 80)
            print("エラー出力:")
            print(result.stderr)
            print("-" * 80)
            return False

    except FileNotFoundError:
        print("\n❌ エラー: ollamaコマンドが見つかりません")
        print("Ollamaがインストールされているか確認してください")
        return False
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        return False

def test_model(model_name: str, test_prompt: str = None):
    """
    ビルドしたモデルをテスト

    Args:
        model_name: テストするモデル名
        test_prompt: テスト用プロンプト
    """
    if test_prompt is None:
        test_prompt = "usersテーブル(id, name, email)を作成して、2件データを挿入して、全件取得するコードを書いて"

    print("\n" + "=" * 80)
    print(f"🧪 モデルテスト: {model_name}")
    print("=" * 80)
    print(f"プロンプト: {test_prompt}")
    print("-" * 80)

    try:
        cmd = ["ollama", "run", model_name, test_prompt]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60
        )

        if result.returncode == 0:
            print("\n✅ モデル応答:")
            print("-" * 80)
            print(result.stdout)
            print("-" * 80)
            return True
        else:
            print("\n❌ モデル実行失敗")
            print(result.stderr)
            return False

    except subprocess.TimeoutExpired:
        print("\n⏱️ タイムアウト: 60秒以内に応答がありませんでした")
        return False
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        return False

if __name__ == "__main__":
    print("\n🤖 NeuroHub Ollama Modelfile ビルドシステム\n")

    # 利用可能なModelfile一覧
    modelfiles_dir = Path("modelfiles")
    available_modelfiles = {
        "db": {
            "path": "modelfiles/db_sample_assistant.Modelfile",
            "name": "neurohub-db-assistant",
            "description": "DatabaseManagerサンプルコード参照アシスタント"
        }
    }

    print("📋 利用可能なModelfile:")
    print("-" * 80)
    for key, info in available_modelfiles.items():
        print(f"  [{key}] {info['description']}")
        print(f"      ファイル: {info['path']}")
        print(f"      モデル名: {info['name']}")
        print()

    # ユーザー選択
    if len(sys.argv) > 1:
        choice = sys.argv[1]
    else:
        choice = input("ビルドするModelfileを選択 [db]: ").strip() or "db"

    if choice not in available_modelfiles:
        print(f"❌ エラー: '{choice}' は無効な選択です")
        sys.exit(1)

    selected = available_modelfiles[choice]

    # モデルビルド
    success = build_model(selected["path"], selected["name"])

    if success:
        # テスト実行するか確認
        if len(sys.argv) > 2 and sys.argv[2] == "--test":
            test_model(selected["name"])
        else:
            test_choice = input("\nモデルをテストしますか? [y/N]: ").strip().lower()
            if test_choice == 'y':
                test_model(selected["name"])

    print("\n" + "=" * 80)
    print("🎉 完了!")
    print("=" * 80)

    if success:
        print(f"\n使用方法:")
        print(f"  ollama run {selected['name']} \"プロンプト\"")
        print(f"\n  または、LLMAgentで provider='ollama', model='{selected['name']}' を指定")
