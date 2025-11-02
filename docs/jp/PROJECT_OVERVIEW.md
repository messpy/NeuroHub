# NeuroHub プロジェクト概要

最終更新: 2025-11-02

---

## 🎯 プロジェクト概要

NeuroHubは、AI駆動型のスマートアシスタントシステムです。自然言語で指示を受け取り、適切なエージェントにルーティングして実行します。

**目標**: アレクサやGoogle Homeを超える、完全無料のオープンソーススマートアシスタント

---

## 📂 主要ディレクトリ構造

```
NeuroHub/
├── main.py                 # 🎯 メインエントリーポイント（意図判定・ルーティング）
├── agents/                 # 🤖 各種エージェント
├── services/               # 🛠️ バックエンドサービス
├── tools/                  # 🔧 ユーティリティツール
├── config/                 # ⚙️ 設定ファイル
├── docs/                   # 📚 ドキュメント
├── tests/                  # 🧪 テストコード
└── modelfiles/             # 🦙 Ollama Modelfile
```

---

## 🎯 メインエントリーポイント

### [main.py](../main.py)
**機能**: NeuroHubの中央制御システム

- **IntentDetector**: 自然言語から意図を自動判定
- **AgentRouter**: 適切なエージェントへ自動ルーティング

**使用例**:
```bash
python main.py "今日の天気は？"          # → weather_agent
python main.py "ファイル一覧ツール作成"   # → mcp_agent
python main.py "git statusを確認"       # → git_agent
```

**詳細**: [main.pyの仕様](#mainpy詳細)

---

## 🤖 エージェント (agents/)

### 📋 エージェント一覧

| エージェント | 機能 | 状態 |
|------------|------|------|
| [common.py](#agentscommonpy) | BaseAgentクラス、共通機能 | ✅ 完成 |
| [git_agent.py](#agentsgit_agentpy) | Git操作支援 | ✅ 完成 |
| [llm_agent.py](#agentsllm_agentpy) | LLM統合管理 | ✅ 完成 |
| [command_agent.py](#agentscommand_agentpy) | システムコマンド実行 | ✅ 完成 |
| [config_agent.py](#agentsconfig_agentpy) | 設定管理 | ✅ 完成 |
| [specialized/weather_agent.py](#weather_agent) | 天気情報取得 | ✅ 完成 |
| [specialized/web_agent.py](#web_agent) | Web検索 | 🔄 開発中 |
| [specialized/mcp_agent.py](#mcp_agent) | MCP開発自動化 | 🔄 開発中 |

### agents/common.py
**機能**: 全エージェントの基底クラス

- **BaseAgent**: 共通インターフェース
- **ロギング**: 統一ログ管理
- **設定管理**: YAML設定読み込み
- **エラーハンドリング**: 統一エラー処理

**詳細**: [agents/common.pyの仕様](#agentscommonpy詳細)

### agents/git_agent.py
**機能**: Git操作の自動化

- Git status確認
- コミットメッセージ自動生成（LLM使用）
- 自動コミット・プッシュ
- インタラクティブモード

**使用例**:
```bash
python agents/git_agent.py --status
python agents/git_agent.py --auto-commit
python agents/git_agent.py --interactive
```

**詳細**: [agents/git_agent.pyの仕様](#agentsgit_agentpy詳細)

### agents/llm_agent.py
**機能**: 複数LLMプロバイダーの統合管理

- マルチプロバイダー対応（Gemini, Ollama, HuggingFace）
- 自動フォールバック
- レート制限対応
- 履歴管理

**詳細**: [agents/llm_agent.pyの仕様](#agentsllm_agentpy詳細)

---

## 🛠️ サービス (services/)

### 📁 ディレクトリ構造

```
services/
├── common/              # 共通サービス
│   ├── system_info.py  # PCスペック検出
│   └── venv_manager.py # 仮想環境自動管理
├── llm/                # LLMサービス
│   ├── llm_common.py   # LLM共通機能
│   ├── provider_*.py   # 各種プロバイダー
│   └── modelfile_generator.py
├── mcp/                # MCP開発自動化
├── db/                 # データベース管理
└── discord/            # Discord Bot
```

### services/common/system_info.py
**機能**: システム情報の自動検出

- CPU/RAM/GPU検出
- Ollamaモデル推奨
- DB保存

**使用例**:
```bash
python services/common/system_info.py --show
python services/common/system_info.py --save
```

**詳細**: [system_info.pyの仕様](#system_infopy詳細)

### services/common/venv_manager.py
**機能**: 仮想環境の自動管理

- pip install自動検知
- venv自動作成
- importエラー自動対応

**詳細**: [venv_manager.pyの仕様](#venv_managerpy詳細)

### services/llm/
**機能**: LLMプロバイダー管理

- [provider_ollama.py](#provider_ollamapy): Ollama統合
- [provider_gemini.py](#provider_geminipy): Google Gemini統合
- [provider_huggingface.py](#provider_huggingfacepy): HuggingFace統合
- [modelfile_generator.py](#modelfile_generatorpy): Modelfile動的生成

**詳細**: [LLMサービスの仕様](#llmサービス詳細)

### services/mcp/
**機能**: Model Context Protocol - AI開発自動化

- [mcp_run.py](#mcp_runpy): プロジェクト自動生成
- [auto_debugger.py](#auto_debuggerpy): 自動デバッグ（5回連続終了）
- [design_generator.py](#design_generatorpy): 設計書自動生成

**詳細**: [MCPサービスの仕様](#mcpサービス詳細)

---

## 🔧 ツール (tools/)

### tools/ollama_setup.py
**機能**: Ollama完全自動セットアップ

1. Ollamaインストール確認・自動インストール
2. PCスペック検出→DB保存
3. 最適モデル選択・pull
4. Modelfile生成（MCP rules埋め込み）
5. カスタムモデルビルド

**使用例**:
```bash
python tools/ollama_setup.py                # 完全自動セットアップ
python tools/ollama_setup.py --check-only   # インストール確認のみ
python tools/ollama_setup.py --specs-only   # スペック検出のみ
```

**詳細**: [ollama_setup.pyの仕様](#ollama_setuppy詳細)

---

## ⚙️ 設定 (config/)

### 設定ファイル一覧

| ファイル | 用途 |
|---------|------|
| config.yaml | 全体設定 |
| llm_config.yaml | LLMプロバイダー設定 |
| agent_config.yaml | エージェント設定 |
| prompt_templates.yaml | プロンプトテンプレート |

**詳細**: [設定ファイルの仕様](#設定ファイル詳細)

---

## 📚 ドキュメント (docs/)

### 主要ドキュメント

| ドキュメント | 内容 |
|------------|------|
| [FILE_DESIGN.md](FILE_DESIGN.md) | ファイル設計書（60ファイル目標） |
| [TASK_MANAGEMENT.md](TASK_MANAGEMENT.md) | タスク管理・進捗追跡 |
| [MCP_CODING_RULES.md](MCP_CODING_RULES.md) | MCP自動コード生成ルール |
| [ARCHITECTURE_DESIGN.md](ARCHITECTURE_DESIGN.md) | アーキテクチャ設計 |
| [TESTING.md](TESTING.md) | テストガイド |

**詳細**: [ドキュメント一覧](#ドキュメント詳細)

---

## 🗄️ データベース

### neurohub_llm.db

**テーブル一覧**:

| テーブル | 用途 |
|---------|------|
| knowledge_base | SQLスニペット、FAQ保存 |
| llm_interactions | LLM履歴管理 |
| system_specs | PCスペック保存 |
| ollama_models | Ollamaモデル情報 |

**詳細**: [データベース設計](#データベース詳細)

---

## 🚀 クイックスタート

### 1. 初回セットアップ

```bash
# Ollama自動セットアップ
python tools/ollama_setup.py

# 依存パッケージインストール
pip install -r requirements.txt
```

### 2. 基本的な使い方

```bash
# 天気を聞く
python main.py "今日の天気は？"

# 開発タスク
python main.py "ToDoリストアプリを作成"

# Git操作
python main.py "変更内容をコミット"
```

### 3. 個別エージェント使用

```bash
# Git操作
python agents/git_agent.py --status

# LLM直接使用
python services/llm/llm_cli.py "質問内容"

# MCP開発
python services/mcp/mcp_run.py "プロジェクト説明"
```

---

## 📊 プロジェクト統計

- **総ファイル数**: ~150+ → 60ファイル目標（リファクタリング中）
- **対応エージェント**: 8種類
- **LLMプロバイダー**: 3種類（Gemini, Ollama, HuggingFace）
- **自動化レベル**: 高（venv自動作成、Ollama自動セットアップ等）
- **テストカバレッジ**: 向上中

---

## 🔗 詳細仕様へのリンク

### メインシステム

- [main.py詳細](#mainpy詳細)
- [IntentDetector仕様](#intentdetector仕様)
- [AgentRouter仕様](#agentrouter仕様)

### エージェント詳細

- [agents/common.py詳細](#agentscommonpy詳細)
- [agents/git_agent.py詳細](#agentsgit_agentpy詳細)
- [agents/llm_agent.py詳細](#agentsllm_agentpy詳細)
- [agents/command_agent.py詳細](#agentscommand_agentpy詳細)
- [agents/config_agent.py詳細](#agentsconfig_agentpy詳細)

### サービス詳細

- [system_info.py詳細](#system_infopy詳細)
- [venv_manager.py詳細](#venv_managerpy詳細)
- [LLMサービス詳細](#llmサービス詳細)
- [MCPサービス詳細](#mcpサービス詳細)

### ツール詳細

- [ollama_setup.py詳細](#ollama_setuppy詳細)

### 設定・ドキュメント

- [設定ファイル詳細](#設定ファイル詳細)
- [ドキュメント詳細](#ドキュメント詳細)
- [データベース詳細](#データベース詳細)

---

## 🎓 開発ガイド

### 新しいエージェントの追加

1. `agents/common.py`の`BaseAgent`を継承
2. `execute()`メソッドを実装
3. `main.py`のIntentDetectorにキーワード追加
4. `main.py`のAgentRouterにルーティング追加

詳細: [開発ガイド](DEVELOPMENT_GUIDE.md)（作成予定）

### テスト実行

```bash
# WSL環境で実行（必須）
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && python3 -m pytest tests/"
```

---

## 📝 最近の更新

### 2025-11-02

- ✅ main.py作成（意図判定・ルーティング）
- ✅ BaseAgent実装（agents/common.py）
- ✅ git_agent/weather_agentリファクタリング
- ✅ system_info.py作成（PCスペック検出）
- ✅ venv_manager.py作成（仮想環境自動管理）
- ✅ ollama_setup.py作成（完全自動セットアップ）
- ✅ FILE_DESIGN.md作成（60ファイル目標）

詳細: [TASK_MANAGEMENT.md](TASK_MANAGEMENT.md)

---

*このドキュメントは自動生成されています。詳細は各リンク先のファイルを参照してください。*
