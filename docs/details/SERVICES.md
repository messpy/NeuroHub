# サービス詳細仕様

[← プロジェクト概要に戻る](../PROJECT_OVERVIEW.md)

---

## 📂 services/common/

### system_info.py

**機能**: PCスペックの自動検出とDB保存

**主要クラス**: `SystemInfoCollector`

**検出項目**:
- CPU: モデル名、コア数、周波数
- RAM: 総容量、利用可能容量
- GPU: モデル名、VRAM容量（NVIDIA対応）
- Disk: 総容量、空き容量
- OS: システム名、バージョン

**モデル推奨ロジック**:
```python
if ram >= 32GB and gpu_vram >= 8GB:
    → llama3.1:70b
elif ram >= 16GB and gpu_vram >= 4GB:
    → llama3.1:13b
elif ram >= 8GB:
    → llama3.1:8b
else:
    → qwen2.5:3b
```

**使用例**:
```bash
# スペック表示
python services/common/system_info.py --show

# DB保存
python services/common/system_info.py --save
```

**出力例**:
```
=== System Specifications ===
CPU: x86_64
CPU Cores: 16
RAM Total: 7.61 GB
RAM Available: 6.33 GB
GPU: NVIDIA GeForce RTX 4060 Laptop GPU
GPU VRAM: 8.00 GB
Disk Total: 1006.85 GB
Disk Free: 879.80 GB
OS: Linux 6.6.87.2-microsoft-standard-WSL2

Recommended Model: qwen2.5:3b
```

**DBテーブル**:
- `system_specs`: スペック履歴保存
- `ollama_models`: モデル情報管理

---

### venv_manager.py

**機能**: 仮想環境の自動管理

**主要クラス**: `VenvManager`

**機能一覧**:

1. **自動venv作成**
   - venv未存在時に自動作成
   - Python実行可能ファイルパス取得

2. **pip install検知**
   - コード内のpip installコマンド検出
   - パターン: `subprocess.run(['pip', 'install', 'pkg'])`
   - パターン: `os.system('pip install pkg')`
   - パターン: `!pip install pkg` (Jupyter)

3. **import検知**
   - import文解析
   - 欠落モジュール検出
   - 自動インストール

4. **venv内スクリプト実行**
   - venv Python使用
   - プロジェクトルートをcwdに設定

**使用例**:
```bash
# venv作成
python services/common/venv_manager.py --create

# パッケージインストール
python services/common/venv_manager.py --install requests

# requirements.txtからインストール
python services/common/venv_manager.py --requirements requirements.txt

# venv内でスクリプト実行
python services/common/venv_manager.py --run script.py

# コードファイルの依存関係チェック
python services/common/venv_manager.py --check-code mycode.py
```

**自動セットアップ**:
```python
from services.common.venv_manager import VenvManager

manager = VenvManager()
code = """
import requests
import numpy
"""

# 自動セットアップ（venv作成、パッケージインストール）
manager.auto_setup(code=code)
```

---

## 📂 services/llm/

### llm_common.py

**機能**: LLMプロバイダー共通機能

**主要機能**:

1. **環境設定読み込み**
   - `.env`ファイル自動読み込み
   - APIキー管理

2. **設定ファイル管理**
   - `config/config.yaml`読み込み
   - プロバイダー設定取得

3. **プロンプトテンプレート**
   - `config/prompt_templates.yaml`管理
   - テンプレート変数展開

4. **デバッグロガー**
   - デバッグレベル管理（0-3）
   - 統一ログフォーマット

**使用例**:
```python
from services.llm.llm_common import load_env_from_config, load_config

# 環境読み込み
load_env_from_config()

# 設定読み込み
config = load_config()

# プロンプトテンプレート取得
template = get_prompt_template('commit_message')
```

---

### provider_ollama.py

**機能**: Ollama LLMプロバイダー

**主要機能**:

1. **サーバー管理**
   - 自動起動・ヘルスチェック
   - タイムアウト対応

2. **モデル管理**
   - リスト取得
   - 自動pull
   - フォールバック対応

3. **Modelfileサポート**
   - カスタムモデル作成
   - パラメータ調整

4. **単体実行可能**
   - CLI完備
   - デバッグモード

**使用例**:
```bash
# テスト実行
python services/llm/provider_ollama.py --test

# モデルリスト
python services/llm/provider_ollama.py --list

# プロンプト実行
python services/llm/provider_ollama.py --model qwen2.5:3b --prompt "質問"

# MCPモデルビルド
python services/llm/provider_ollama.py --build-mcp-model --model-name neurohub-mcp
```

---

### modelfile_generator.py

**機能**: Ollama Modelfile動的生成

**主要クラス**: `ModelfileGenerator`

**生成タイプ**:

1. **MCP専用モデル**
   - `docs/MCP_CODING_RULES.md`埋め込み
   - input()禁止、argparse必須等のルール適用
   - モデル名: `neurohub-mcp-assistant`

2. **DB専用モデル**
   - `README.md`からサンプル抽出
   - SQLスニペット埋め込み
   - モデル名: `db-assistant`

**使用例**:
```python
from services.llm.modelfile_generator import ModelfileGenerator

gen = ModelfileGenerator()

# MCPモデル生成
modelfile = gen.generate_mcp_modelfile(
    base_model="qwen2.5:3b",
    output_path="neurohub-mcp.Modelfile"
)

# ビルド
gen.build_model("neurohub-mcp.Modelfile", "neurohub-mcp")
```

---

## 📂 services/mcp/

### auto_debugger.py

**機能**: 自動デバッグシステム

**主要機能**:

1. **5回連続エラー終了**
   - 連続失敗回数追跡
   - 5回で強制終了

2. **input()検出・修正**
   - コード解析
   - argparse置き換え提案

3. **エラーログ解析**
   - スタックトレース解析
   - 修正案生成

**設定**:
```python
MAX_CONTINUOUS_ERRORS = 5  # 連続エラー上限
```

---

### mcp_run.py

**機能**: MCP自動プロジェクト生成

**処理フロー**:
```
1. 設計書生成（design_generator.py）
2. コード生成（code_generator.py）
3. テスト生成（test_generator.py）
4. デバッグ（auto_debugger.py）
5. プロジェクト完成
```

**使用例**:
```bash
python services/mcp/mcp_run.py "ToDoリストCLIツール" --name todo_app
```

---

## 🔧 tools/ollama_setup.py

**機能**: Ollama完全自動セットアップ

**処理フロー**:

1. ✅ **Ollamaインストール確認**
   - `ollama --version`実行
   - 未インストール時は自動インストール（Linux/WSL）

2. 🚀 **サーバー起動**
   - `ollama serve`バックグラウンド実行
   - ヘルスチェック

3. 🔍 **スペック検出**
   - `SystemInfoCollector`使用
   - DB保存

4. 📊 **モデル推奨**
   - DB照会
   - スペックに応じた最適モデル選択

5. 📥 **モデルpull**
   - `ollama pull <model>`実行
   - 進捗表示

6. 📝 **Modelfile生成**
   - MCP_CODING_RULES.md埋め込み
   - カスタムパラメータ設定

7. 🔨 **モデルビルド**
   - `ollama create`実行
   - カスタムモデル作成

8. ✅ **検証**
   - テストプロンプト実行
   - 動作確認

**使用例**:
```bash
# 完全自動セットアップ
python tools/ollama_setup.py

# 確認のみ
python tools/ollama_setup.py --check-only

# スペック検出のみ
python tools/ollama_setup.py --specs-only

# カスタムモデル指定
python tools/ollama_setup.py --model llama3.1:8b
```

---

## 🔗 関連ドキュメント

- [PROJECT_OVERVIEW.md](../PROJECT_OVERVIEW.md) - プロジェクト概要
- [FILE_DESIGN.md](../FILE_DESIGN.md) - ファイル設計書
- [MCP_CODING_RULES.md](../MCP_CODING_RULES.md) - MCPコーディングルール

---

[← プロジェクト概要に戻る](../PROJECT_OVERVIEW.md)
