# NeuroHub MCP (Model Context Protocol) システム

## 概要

NeuroHubには強力なMCP（Model Context Protocol）システムが実装されており、自然言語からコマンド生成、プロジェクト自動生成、テスト実行など、開発プロセスの自動化を支援します。

## MCPシステムの構成

### コアコンポーネント

```
services/mcp/
├── core.py              # 共通ユーティリティ・LLM呼び出し
├── mcp_run.py           # メインオーケストレーター
├── mcp_spec.py          # 設計YAML生成
├── mcp_codegen.py       # コード生成
├── mcp_test.py          # 自動テスト実行
└── cmd_exec.py          # コマンド実行・自然言語処理
```

### 主要機能

1. **自動プロジェクト生成** - 自然言語の要件からプロジェクト作成
2. **コマンド実行** - 自然言語からコマンド生成・実行
3. **自動テスト** - 生成されたツールの自動テスト
4. **設計管理** - YAML形式でのプロジェクト設計管理

## 使用方法

### 1. 自動プロジェクト生成（mcp_run.py）

```bash
# 基本的な使用方法
python3 services/mcp/mcp_run.py "ファイル一覧表示ツール" --name file_list_tool

# 言語を指定
python3 services/mcp/mcp_run.py "データ変換ツール" --name data_converter --lang python

# リトライ回数を指定
python3 services/mcp/mcp_run.py "ログ解析ツール" --rounds 3
```

**プロセス**:
1. 設計YAML生成 (mcp_spec.py)
2. コード生成 (mcp_codegen.py)
3. 自動テスト (mcp_test.py)
4. 失敗時は設計からリトライ

### 2. コマンド実行（cmd_exec.py）

```bash
# 直接コマンド実行
python3 services/mcp/cmd_exec.py --cmd "ls -la" --no-explain

# 自然言語からコマンド生成（LLM必要）
python3 services/mcp/cmd_exec.py "ファイル一覧を表示して"

# 特定の成功パターンを指定
python3 services/mcp/cmd_exec.py "IPアドレスを確認" --success-pattern '\d+\.\d+\.\d+\.\d+'

# JSON形式の出力を分割解説
python3 services/mcp/cmd_exec.py "プロセス一覧" --explain-chunks
```

### 3. 手動テスト実行

```bash
# 設計YAMLからテスト実行
python3 services/mcp/mcp_test.py --design logs/ai_prj/project_design.yaml

# シンプルなテストツール（LLM不要）
python3 simple_mcp_test.py projects/your_project
```

## 実践例

### ファイル一覧表示ツールの作成

1. **手動作成の場合**:
```bash
# プロジェクトディレクトリ作成
mkdir -p projects/file_list_demo

# main.pyとREADME.mdを作成
# （作成済みの例: projects/file_list_demo/）
```

2. **動作確認**:
```bash
cd projects/file_list_demo
python3 main.py --help
python3 main.py --format json
python3 main.py --filter .py
```

3. **テスト実行**:
```bash
python3 simple_mcp_test.py projects/file_list_demo
```

### 結果例:
```
🚀 Starting MCP Tool Test
============================================================
🧪 Test: help
   Result: ✅ RC=0 (expected 0)
🧪 Test: run
   Result: ✅ RC=0 (expected 0)
🧪 Test: count
   Result: ✅ RC=0 (expected 0)
============================================================
Overall Status: ✅ SUCCESS
```

## 設計YAML形式

```yaml
project: project_name
timestamp: 20251101-084800
prompt: "プロジェクトの説明"
language: python
expected_behavior:
  summary: "プロンプト要件に沿ったCLIを提供すること。"
  keywords:
    - "期待されるキーワード"
  regex:
    - '\d+ KB'  # 期待される正規表現パターン
files_plan:
  - "main.py"
  - "README.md"
tests:
  - name: "help"
    cmd: "python main.py --help"
    expect_rc: "0"
  - name: "run"
    cmd: "python main.py"
    expect_rc: "0"
rollback:
  enabled: true
  strategy: "snapshot_before_build"
```

## LLM設定

### 必要な設定

```yaml
# config/config.yaml
llm:
  providers:
    ollama:
      enabled: 1
      host: http://127.0.0.1:11434
      model: qwen2.5:1.5b-instruct
    gemini:
      enabled: 0
      model: gemini-1.5-flash
    huggingface:
      enabled: 0
      model: meta-llama/Llama-3.1-8B-Instruct
  default_provider: ollama
```

### 環境変数
```bash
export OLLAMA_HOST=http://127.0.0.1:11434
export PYTHONPATH=/path/to/NeuroHub
```

## エラーハンドリング

### 一般的な問題と解決策

1. **LLM接続エラー**:
```bash
[fatal] いずれのモデルでも ping に失敗しました
```
**解決**: Ollamaサーバーの起動確認、設定ファイルの確認

2. **Python実行エラー**:
```bash
/bin/sh: 1: python: not found
```
**解決**: `python3`を使用、または仮想環境の有効化

3. **モジュールインポートエラー**:
```bash
ImportError: attempted relative import with no known parent package
```
**解決**: `PYTHONPATH`環境変数の設定

## ベストプラクティス

### 1. プロジェクト作成
- 明確で具体的な要件記述
- 段階的な機能追加
- 適切なテストケースの定義

### 2. テスト設計
- 基本的な動作確認（--help, 基本実行）
- エッジケースの考慮
- 出力形式の検証

### 3. セキュリティ
- sudoコマンドの制限
- 破壊的操作の禁止
- 入力値の検証

## 拡張可能性

### カスタムMCPツールの作成

1. **新しいプロバイダーの追加**:
```python
# services/mcp/custom_provider.py
class CustomMCPProvider:
    def generate_code(self, spec):
        # カスタムロジック
        pass
```

2. **テンプレートの拡張**:
```yaml
# templates/custom_template.yaml
project_template:
  language: python
  framework: fastapi
  structure:
    - "main.py"
    - "requirements.txt"
    - "Dockerfile"
```

3. **CI/CD統合**:
```yaml
# .github/workflows/mcp-test.yml
name: MCP Tool Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Test MCP tools
        run: python3 simple_mcp_test.py projects/
```

## 関連ツール

- **agents/**: エージェントベースの自動化
- **services/llm/**: LLMプロバイダー管理
- **tests/**: 単体テストフレームワーク

## まとめ

NeuroHubのMCPシステムは、開発プロセスの自動化を強力にサポートします。自然言語からの要件定義、自動コード生成、テスト実行までを一貫して提供し、開発効率の大幅な向上を実現します。

LLMを使用した高度な機能と、LLMなしでも動作するシンプルな機能の両方を提供することで、様々な環境と要件に対応できる柔軟性を持っています。
