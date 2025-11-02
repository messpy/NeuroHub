# NeuroHub プロジェクト概要

## 🎯 プロジェクトビジョン

**NeuroHub**は、完全無料のオープンソースAIアシスタントプラットフォームです。AlexaやGoogle Homeなどのスマートスピーカーの上位互換を目指し、Pythonで実現可能な限界まで機能を実装しています。

### 目標
- 🤖 **複数LLM統合**: Ollama、Gemini、HuggingFaceを活用
- 🎙️ **音声対応**: 音声認識・音声合成による自然な対話
- 💬 **Discord Bot**: チャットボットとしても利用可能
- 🛠️ **自動化**: Git操作、プロジェクト生成、タスク管理を自動化
- 🌐 **完全無料**: すべて無料のAPI・ライブラリで構築
- 🔓 **オープンソース**: MITライセンスで公開

---

## 🏗️ システムアーキテクチャ

### 全体構成図

```
┌─────────────────────────────────────────────────────────────┐
│                        NeuroHub Core                         │
│                         (main.py)                            │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
┌───────▼──────┐ ┌──▼────────┐ ┌▼──────────────┐
│   Agents     │ │ Services  │ │    Tools      │
│              │ │           │ │               │
│ - LLM        │ │ - AI      │ │ - CLI         │
│ - Git        │ │ - DB      │ │ - Web Search  │
│ - Config     │ │ - Discord │ │ - Ollama Mgr  │
│ - Command    │ │ - MCP     │ │ - Monitoring  │
│ - Discord    │ │ - Common  │ │ - Cleanup     │
└──────────────┘ └───────────┘ └───────────────┘
        │            │            │
        └────────────┼────────────┘
                     │
        ┌────────────▼────────────┐
        │   Data & Config         │
        │                         │
        │ - SQLite Database       │
        │ - YAML Configurations   │
        │ - Environment Variables │
        └─────────────────────────┘
```

---

## 🤖 主要機能

### 1. LLMエージェント（agents/llm_agent.py）
**役割**: 複数のLLMプロバイダーを統合管理

#### 対応プロバイダー
- 🦙 **Ollama**: ローカルLLM（qwen2.5:0.5b-instruct等）
- 🌟 **Gemini**: Google AI（gemini-2.5-flash）
- 🤗 **HuggingFace**: Groq経由（openai/gpt-oss-20b:groq）

#### 主要機能
- プロバイダー自動切り替え
- モデル一覧取得・自動選択
- システムプロンプト管理
- 文字数制限・チャンク処理
- 日本語対応の安全なテキスト処理

**詳細**: [agents/llm/README.md](./agents/llm/README.md)

---

### 2. Gitエージェント（agents/git_agent.py, git_smart_agent.py）
**役割**: Git操作の自動化・コミットメッセージ生成

#### 主要機能
- **git_agent**: 基本的なGit操作（status, diff, commit, push）
- **git_smart_agent**: LLM連携によるスマートコミット
  - 変更差分の自動チャンク処理
  - LLM生成のコミットメッセージ
  - プロバイダー切り替え（Gemini→HuggingFace→Ollama）
  - 日本語コミットメッセージ生成

#### コミットメッセージ形式
```
feat(module): 変更の概要

✅ 実装内容:
- 機能1
- 機能2

📊 テスト結果:
- テスト名: 結果
```

**詳細**: [agents/git/README.md](./agents/git/README.md)

---

### 3. MCPエージェント（services/mcp/）
**役割**: 自動プロジェクト生成システム

#### 新フロー（2025/11/02実装）
```
ユーザープロンプト
    ↓
仕様正規化（JSON Schema）
    ↓
プロジェクト設計・計画生成
    ↓
スキャフォールド生成（Jinja2）
    ↓
テスト生成
    ↓
静的検証（ruff/mypy/bandit）
    ↓
ユニットテスト実行
    ↓
修正ループ
    ↓
README生成・成果物固定化
```

#### 主要モジュール
- **spec_normalizer.py**: 仕様正規化、JSON Schema検証
- **command_validator.py**: 禁止コマンド検知、代替案提示
- **project_designer.py**: プロジェクト構造・計画生成

**詳細**: [agents/mcp/README.md](./agents/mcp/README.md)

---

### 4. Discordエージェント（services/discord/）
**役割**: Discord Botとしての機能提供

#### 主要機能
- **bot_core.py**: Bot本体
- **plugin_manager.py**: プラグインシステム
- **voice_manager.py**: 音声トリガー管理
- **anti_spam.py**: スパム対策

#### 使用例
```python
# Discord Botの起動
python3 tools/run_discord_bot.py
```

**詳細**: [agents/discord/README.md](./agents/discord/README.md)

---

### 5. Configエージェント（agents/config_agent.py）
**役割**: 設定ファイル・環境変数の管理

#### 管理対象
- `config/config.yaml`: 全体設定
- `config/llm_config.yaml`: LLM設定
- `config/discord_config.yaml`: Discord設定
- `.env`: 環境変数（API Key等）

**詳細**: [agents/config/README.md](./agents/config/README.md)

---

### 6. Commandエージェント（agents/command_agent.py）
**役割**: シェルコマンドの実行・管理

#### 主要機能
- コマンド実行（WSL対応）
- セキュリティ検証
- 実行ログ記録
- タイムアウト処理

**詳細**: [agents/command/README.md](./agents/command/README.md)

---

## 🗄️ データベース設計

### 使用DB: SQLite3
**場所**: `neurohub_llm.db`

### 主要テーブル

#### 1. users（ユーザー情報）
| カラム | 型 | 説明 |
|--------|-----|------|
| user_id | INTEGER PRIMARY KEY | ユーザーID |
| username | TEXT | ユーザー名 |
| created_at | TEXT | 作成日時 |

#### 2. llm_history（LLM履歴）
| カラム | 型 | 説明 |
|--------|-----|------|
| id | INTEGER PRIMARY KEY | 履歴ID |
| provider | TEXT | プロバイダー名 |
| model | TEXT | モデル名 |
| prompt | TEXT | プロンプト |
| response | TEXT | 応答内容 |
| tokens | INTEGER | トークン数 |
| created_at | TEXT | 実行日時 |

#### 3. knowledge_base（知識ベース）
| カラム | 型 | 説明 |
|--------|-----|------|
| sql_id | TEXT PRIMARY KEY | SQL ID |
| sql_text | TEXT | SQL文 |
| description | TEXT | 説明 |
| category | TEXT | カテゴリ |

**詳細**: [DATABASE_DESIGN.md](./DATABASE_DESIGN.md)

---

## 🛠️ 技術スタック

### 言語・フレームワーク
- **Python 3.12**: メイン言語
- **pytest**: テストフレームワーク
- **ruff/mypy/bandit**: 静的解析

### LLMプロバイダー
- **Ollama**: ローカルLLM実行環境
- **Google Gemini API**: クラウドLLM
- **HuggingFace Inference API**: Groq経由

### データベース
- **SQLite3**: 軽量DB

### Discord
- **discord.py**: Discord Bot SDK

### その他
- **PyYAML**: YAML設定管理
- **python-dotenv**: 環境変数管理
- **requests**: HTTP通信

---

## 📁 ディレクトリ構造

```
NeuroHub/
├── agents/                 # エージェント層
│   ├── llm_agent.py       # LLMエージェント
│   ├── git_agent.py       # Gitエージェント
│   ├── git_smart_agent.py # スマートGitエージェント
│   ├── config_agent.py    # 設定エージェント
│   └── command_agent.py   # コマンドエージェント
├── services/              # サービス層
│   ├── ai/                # AI/LLMサービス
│   │   ├── provider_ollama.py
│   │   ├── provider_gemini.py
│   │   └── provider_huggingface.py
│   ├── db/                # データベースサービス
│   ├── discord/           # Discordサービス
│   └── mcp/               # MCPサービス
│       ├── spec_normalizer.py
│       ├── command_validator.py
│       └── project_designer.py
├── tools/                 # CLIツール
│   ├── agent_cli.py
│   ├── run_discord_bot.py
│   └── web_search_tool.py
├── config/                # 設定ファイル
│   ├── config.yaml
│   ├── llm_config.yaml
│   └── discord_config.yaml
├── tests/                 # テストコード
│   ├── test_hello_llm.py
│   └── test_mcp_workflow.py
├── docs/                  # ドキュメント
│   ├── jp/                # 日本語版
│   └── html/              # HTML版
├── main.py                # メインエントリーポイント
└── .env                   # 環境変数（要作成）
```

---

## 🚀 セットアップ・使用方法

### 1. 環境構築（WSL/Linux）

```bash
# リポジトリクローン
git clone https://github.com/messpy/NeuroHub.git
cd NeuroHub

# 仮想環境作成
python3 -m venv venv_linux
source venv_linux/bin/activate

# 依存関係インストール
pip install -r requirements.txt
```

### 2. 環境変数設定

`.env`ファイルを作成：

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# HuggingFace
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Discord（オプション）
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
```

### 3. Ollamaセットアップ

```bash
# Ollamaインストール（Linuxの場合）
curl -fsSL https://ollama.com/install.sh | sh

# 推奨モデルのダウンロード
ollama pull qwen2.5:0.5b-instruct
```

### 4. 実行例

#### LLMテスト
```bash
python3 test_hello_llm.py
```

#### MCPワークフローテスト
```bash
pytest tests/test_mcp_workflow.py -v -s
```

#### Discord Bot起動
```bash
python3 tools/run_discord_bot.py
```

---

## 🧪 テスト状況

### 最新テスト結果（2025/11/02）

| テストスイート | 結果 | 詳細 |
|--------------|------|------|
| test_hello_llm.py | 3/3 PASSED | Ollama/Gemini/HuggingFace動作確認 |
| test_mcp_workflow.py | 6/6 PASSED | MCP新フロー統合テスト |
| test_provider_ollama.py | 9/9 PASSED | Ollamaプロバイダーテスト |
| test_provider_gemini.py | 4/4 PASSED | Geminiプロバイダーテスト |
| test_provider_huggingface.py | 4/4 PASSED | HuggingFaceプロバイダーテスト |

**総合成功率**: 26/26 (100%) 🎉

---

## 📊 開発ロードマップ

### ✅ Phase 1: 基盤構築（完了）
- ✅ LLMプロバイダー統合
- ✅ Git自動化
- ✅ MCP基礎実装
- ✅ ドキュメント整備

### 🔄 Phase 2: 機能拡張（進行中）
- 🔄 MCP新フロー完全実装
- 🔄 Discord Bot機能拡張
- 🔄 音声認識・合成統合
- 🔄 知識ベースDB拡充

### 📋 Phase 3: 最適化（計画中）
- 📋 パフォーマンス最適化
- 📋 エラーハンドリング強化
- 📋 テストカバレッジ向上（目標80%）
- 📋 ドキュメント完全化

### 💡 Phase 4: 高度な機能（アイデア）
- 💡 マルチモーダル対応（画像・動画処理）
- 💡 WebUIダッシュボード
- 💡 プラグインエコシステム
- 💡 Docker対応

---

## 🤝 貢献ガイドライン

### 開発フロー
1. **ブランチ**: `aidev`で開発（mainへの直接コミット禁止）
2. **環境**: WSL/Linuxで実行
3. **テスト**: 必ず単体テスト・統合テストを実行
4. **コミット**: `docs/TASK_MANAGEMENT.md`を更新
5. **ドキュメント**: 変更内容をドキュメントに反映

### コーディング規約
- **PEP 8**: Python標準スタイルガイド準拠
- **型ヒント**: 関数シグネチャに型アノテーション必須
- **Docstring**: Google Style Docstring使用
- **静的解析**: ruff, mypy, bandit合格必須

---

## 📄 ライセンス

**MIT License**

Copyright (c) 2025 NeuroHub Project

---

## 📞 サポート・連絡先

- **GitHub**: [messpy/NeuroHub](https://github.com/messpy/NeuroHub)
- **Issues**: [GitHub Issues](https://github.com/messpy/NeuroHub/issues)
- **Discussions**: [GitHub Discussions](https://github.com/messpy/NeuroHub/discussions)

---

*最終更新: 2025年11月2日*
*バージョン: 1.0.0*
