#!/bin/bash
# Ollama Modelfile ビルドスクリプト (WSL/Linux用)

set -e

MODELFILE_PATH="modelfiles/db_sample_assistant.Modelfile"
MODEL_NAME="neurohub-db-assistant"

echo "================================================================================"
echo "🔨 Ollama カスタムモデルビルド (WSL/Linux)"
echo "================================================================================"
echo "📄 Modelfile: $MODELFILE_PATH"
echo "🏷️  モデル名: $MODEL_NAME"
echo "--------------------------------------------------------------------------------"

# Modelfileの存在確認
if [ ! -f "$MODELFILE_PATH" ]; then
    echo "❌ エラー: Modelfileが見つかりません: $MODELFILE_PATH"
    exit 1
fi

# Ollamaのインストール確認
if ! command -v ollama &> /dev/null; then
    echo "❌ エラー: ollamaコマンドが見つかりません"
    echo "Ollamaをインストールしてください:"
    echo "  curl -fsSL https://ollama.com/install.sh | sh"
    exit 1
fi

echo "🚀 モデルをビルド中..."
echo "--------------------------------------------------------------------------------"

# モデルビルド
ollama create "$MODEL_NAME" -f "$MODELFILE_PATH"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ モデルビルド成功!"
    echo "--------------------------------------------------------------------------------"

    # モデル一覧表示
    echo ""
    echo "📋 登録されているモデル一覧:"
    echo "--------------------------------------------------------------------------------"
    ollama list

    # テスト実行
    if [ "$1" == "--test" ]; then
        echo ""
        echo "================================================================================"
        echo "🧪 モデルテスト: $MODEL_NAME"
        echo "================================================================================"
        echo "プロンプト: usersテーブル(id, name, email)を作成して、2件データを挿入して、全件取得するコードを書いて"
        echo "--------------------------------------------------------------------------------"

        ollama run "$MODEL_NAME" "usersテーブル(id, name, email)を作成して、2件データを挿入して、全件取得するコードを書いて"
    fi

    echo ""
    echo "================================================================================"
    echo "🎉 完了!"
    echo "================================================================================"
    echo ""
    echo "使用方法:"
    echo "  ollama run $MODEL_NAME \"プロンプト\""
    echo ""
    echo "  または、LLMAgentで:"
    echo "    llm = LLMAgent(provider='ollama', model='$MODEL_NAME')"

else
    echo ""
    echo "❌ モデルビルド失敗"
    exit 1
fi
