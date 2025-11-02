# MCP (Model Context Protocol) モジュール

## 📋 概要

MCPモジュールは、弱いLLMでもエラーなしで動作する自動プロジェクト生成システムです。

## 🎯 主要機能

※設計機能がない。
設計をしてやること。
エラーの場合は検索機能を使用する
構文エラーの場合は終わらない様にする。
DB作成の時はサンプルコードを取ってくる様にする

構文エラーの場合は
### 1. 自動プロジェクト生成 (`auto_project_generator.py`)
- CLIアプリケーション自動生成
- テストコード自動生成
- README自動作成

### 2. 自動デバッグ (`auto_debugger.py`)
- 構文エラー自動修正
- 5回連続エラー防止機構
- 複数の修正手法自動切り替え

### 3. バックグラウンドLLMサポート (`background_llm_support.py`)
- 並行タスク実行
- 知識ベース自動検索
- Web検索統合

### 4. プロジェクトバリデーション (`advanced_project_validator.py`)
- コード品質チェック
- テスト実行
- セキュリティチェック

## 📁 ディレクトリ構造
 
※ 設計担当がない。
プロジェクト命名のファイルがない
要約用のファイルがない。コーディングの長さやプログラムによって関数名などを取得するもの

```
services/mcp/
├── README.md                          # このファイル
├── CODING_RULES.md                    # コーディングルール（詳細版）
├── CONFIG.md                          # 設定ガイド
├── TEMPLATE.md                        # プロジェクトテンプレート
├── core.py                            # MCPコア機能
├── mcp_enhanced.py                    # MCP強化版
├── auto_project_generator.py          # プロジェクト自動生成
├── auto_debugger.py                   # 自動デバッグ
├── background_llm_support.py          # バックグラウンドLLMサポート
├── advanced_project_validator.py      # プロジェクトバリデーション
├── weak_llm_support.py                # 弱いLLM対応
├── weak_llm_integrated_test.py        # 統合テスト
├── prompt_optimizer.py                # プロンプト最適化
├── llm_investigator.py                # LLM調査機能
├── cmd_exec.py                        # コマンド実行
├── natureremo_agent.py                # Nature Remo連携 ※いらない。NatureRemoは別のサービスなので
├── ai_prj_coding.py                   # AIプロジェクトコーディング
├── utils.py                           # ユーティリティ関数
└── challenges/                        # チャレンジ課題
    └── mcp_health_check.py            # ヘルスチェック
```

## 🚀 使用方法

### 基本的な使用例

```python
from services.mcp.auto_project_generator import AutoProjectGenerator

# プロジェクト生成
generator = AutoProjectGenerator()
project_path = generator.generate_project(
    project_name="my_calculator_cli",
    description="シンプルな計算機アプリ"
)

# 自動デバッグ
from services.mcp.auto_debugger import AutoDebugger

debugger = AutoDebugger()
result = debugger.debug_project(project_path)
```

### CLI使用例

```bash
# WSL環境で実行
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && \
  source venv_linux/bin/activate && \
  python3 -m services.mcp.auto_project_generator --name 'calculator_cli' --test"
```

## 📖 ドキュメント

- **[CODING_RULES.md](./CODING_RULES.md)**: コーディング規約とベストプラクティス
- **[CONFIG.md](./CONFIG.md)**: 設定ファイルガイド
- **[TEMPLATE.md](./TEMPLATE.md)**: プロジェクトテンプレート

## 🔧 設定

### LLM設定

MCPは以下のLLMプロバイダーに対応：

- **Ollama**: ローカル実行、高速
- **Gemini**: 高品質、1日250回制限
- **HuggingFace**: 無料、Router API使用

設定は `config/llm_config.yaml` または `services/ai/config/llm_config.yaml` で管理。

### 環境変数

```bash
# .env ファイル
GEMINI_API_KEY=your_key
HUGGINGFACE_API_KEY=your_key
OLLAMA_BASE_URL=http://localhost:11434
```

## 🧪 テスト

```bash
# WSL環境で全テスト実行
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && \
  source venv_linux/bin/activate && \
  python3 -m pytest tests/mcp_challenges/ -v"
```

## 🛠️ トラブルシューティング

### よくある問題

1. **input()でタイムアウト**
   - 解決: argparseを使用、`--test`オプション実装

2. **構文エラーが直らない**
   - 解決: 5回連続エラー時に手法自動切り替え

3. **LLMのレート制限**
   - 解決: プロバイダー自動切り替え機能使用

## 📚 関連ドキュメント

- [docs/MCP_GUIDE.md](../../docs/MCP_GUIDE.md): MCP全体ガイド
- [docs/MCP_ENHANCEMENT.md](../../docs/MCP_ENHANCEMENT.md): MCP強化機能
- [docs/OLLAMA_MODELFILE_GUIDE.md](../../docs/OLLAMA_MODELFILE_GUIDE.md): Modelfile作成

## 🔄 更新履歴

- **2025-11-02**: 初版作成
  - services/llm → services/ai リネーム対応
  - ドキュメント構造整理
