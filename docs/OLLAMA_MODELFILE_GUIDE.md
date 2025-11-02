# Ollama Modelfile ビルドガイド

## 概要

NeuroHubでは、Ollama Modelfileを使用してカスタムモデルを作成できます。
READMEのサンプルコードを事前にモデルに埋め込むことで、より正確なコード生成が可能になります。

## Modelfileとは

Modelfileは、Ollamaでカスタムモデルを定義するための設定ファイルです。
以下の要素を含めることができます：

- **FROM**: ベースとなるモデル（例: `qwen2.5-coder:7b`）
- **SYSTEM**: システムプロンプト（モデルの役割や事前知識）
- **PARAMETER**: 温度、top_p、top_kなどのパラメータ
- **TEMPLATE**: プロンプトテンプレート

## 利用可能なModelfile

### 1. DatabaseManagerアシスタント (`neurohub-db-assistant`)

**ファイル**: `modelfiles/db_sample_assistant.Modelfile`

**用途**: READMEのDatabaseManagerサンプルコードを参照してDB操作コードを生成

**特徴**:
- DatabaseManagerクラスの完全なコードが事前にシステムプロンプトに含まれている
- データベース操作のベストプラクティスを理解している
- 実行可能な完全なコードを生成（import文、エラーハンドリング含む）
- 表形式の見やすい出力を生成

## ビルド方法

### Windows (PowerShell)

```powershell
# 基本ビルド
.\build_ollama_model.ps1 -ModelfileKey db

# ビルド + テスト実行
.\build_ollama_model.ps1 -ModelfileKey db -Test
```

### Linux/Mac/WSL (Bash)

```bash
# 実行権限付与
chmod +x build_ollama_model.sh

# 基本ビルド
./build_ollama_model.sh

# ビルド + テスト実行
./build_ollama_model.sh --test
```

### Python経由

```bash
# 基本ビルド
python build_ollama_model.py db

# ビルド + テスト実行
python build_ollama_model.py db --test
```

## 使用方法

### 1. コマンドラインから直接使用

```bash
ollama run neurohub-db-assistant "productsテーブル(id, name, price)を作成して、3件データを挿入して、価格が1000円以上のものを取得するコードを書いて"
```

### 2. LLMAgentから使用

```python
from agents.llm_agent import LLMAgent, LLMRequest

# カスタムモデルを指定
llm = LLMAgent(provider='ollama', model='neurohub-db-assistant')

# リクエスト作成
request = LLMRequest(
    prompt="employeesテーブル(id, name, department, salary)を作成して、部署ごとの平均給与を取得するコードを書いて",
    request_type="code_generation",
    max_tokens=4000,
    temperature=0.2
)

# コード生成
result = llm.generate_text(request)

if result.is_success:
    print(result.content)
```

### 3. スクリプトから使用

```python
import subprocess

prompt = "ordersテーブルとcustomersテーブルをJOINして取得するコードを書いて"
result = subprocess.run(
    ["ollama", "run", "neurohub-db-assistant", prompt],
    capture_output=True,
    text=True
)

print(result.stdout)
```

## カスタムModelfileの作成

新しいModelfileを作成する手順：

### 1. Modelfileを作成

`modelfiles/your_custom.Modelfile` を作成：

```dockerfile
FROM qwen2.5-coder:7b

SYSTEM """あなたは専門的なアシスタントです。

# ここにサンプルコードや事前知識を記述

## コード生成ルール
1. 実行可能なコードのみを生成
2. エラーハンドリングを含める
3. ```python で囲む
"""

PARAMETER temperature 0.2
PARAMETER top_p 0.9
PARAMETER num_ctx 8192
```

### 2. ビルドスクリプトに追加

`build_ollama_model.py` または `.ps1` / `.sh` に定義を追加：

```python
available_modelfiles = {
    "db": {...},
    "custom": {
        "path": "modelfiles/your_custom.Modelfile",
        "name": "your-custom-model",
        "description": "あなたのカスタムモデルの説明"
    }
}
```

### 3. ビルド実行

```bash
python build_ollama_model.py custom --test
```

## モデル管理

### モデル一覧表示

```bash
ollama list
```

### モデル削除

```bash
ollama rm neurohub-db-assistant
```

### モデル詳細表示

```bash
ollama show neurohub-db-assistant
```

## トラブルシューティング

### ollamaコマンドが見つからない

**Windows**:
1. Ollamaをインストール: https://ollama.com/
2. インストール後、PowerShellを再起動

**Linux/Mac**:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### モデルビルドが失敗する

1. ベースモデルがダウンロード済みか確認:
   ```bash
   ollama pull qwen2.5-coder:7b
   ```

2. Modelfileの構文を確認（FROMは必須）

3. システムプロンプトの引用符が正しいか確認

### モデルの応答が遅い

- より小さいモデルを使用: `FROM qwen2.5-coder:3b`
- `num_ctx`を小さくする（デフォルト: 8192）
- GPUを使用している場合はCUDA/ROCmのセットアップを確認

## ベストプラクティス

### 1. システムプロンプトの設計

✅ **Good**:
```
SYSTEM """あなたはPythonの専門家です。

## サンプルコード
[具体的なコード例]

## ルール
1. 実行可能なコードを生成
2. エラーハンドリングを含める
"""
```

❌ **Bad**:
```
SYSTEM "Pythonコードを書いてください"
```

### 2. 温度設定

- **コード生成**: `temperature 0.2` (低い = 決定的)
- **説明文生成**: `temperature 0.7` (高い = 創造的)

### 3. コンテキストサイズ

- **短いコード**: `num_ctx 2048`
- **長いコード・複雑な要求**: `num_ctx 8192`

## 参考リンク

- [Ollama公式ドキュメント](https://github.com/ollama/ollama)
- [Modelfile リファレンス](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [NeuroHub README](../README.md)
- [サンプルコードガイド](SEARCH_DB_GUIDE.md)
