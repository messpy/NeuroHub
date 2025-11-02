# NeuroHub 日本語ドキュメント

## 📚 ドキュメント構成

NeuroHubプロジェクトの全体的な設計書・技術ドキュメントです。

### 🌐 言語別ドキュメント
- **日本語版**: [docs/jp/](./README.md) (このディレクトリ)
- **英語版**: [docs/en/](../en/README.md)

### 📖 総合ドキュメント

| ドキュメント | 説明 | リンク |
|------------|------|--------|
| **プロジェクト概要** | NeuroHubの目的、アーキテクチャ、主要機能 | [OVERVIEW.md](./OVERVIEW.md) |
| **アーキテクチャ設計** | システム全体の設計思想、モジュール構成 | [ARCHITECTURE_DESIGN.md](./ARCHITECTURE_DESIGN.md) |
| **データベース設計** | DB構造、テーブル定義、ER図 | [DATABASE_DESIGN.md](./DATABASE_DESIGN.md) |
| **タスク管理** | 課題一覧、進捗状況、完了済みタスク | [TASK_MANAGEMENT.md](./TASK_MANAGEMENT.md) |
| **プロジェクト概要** | 機能概要、技術スタック | [PROJECT_OVERVIEW.md](./PROJECT_OVERVIEW.md) |

---

## 🤖 エージェント別設計書

### 1. LLMエージェント
**場所**: [agents/llm/](./agents/llm/)

| ドキュメント | 説明 |
|------------|------|
| [概要](./agents/llm/README.md) | LLMエージェントの役割と全体像 |
| [詳細設計](./agents/llm/DETAILED_DESIGN.md) | 内部構造、クラス設計、API仕様 |
| [プロバイダー設計](./agents/llm/PROVIDER_DESIGN.md) | Ollama/Gemini/HuggingFace統合設計 |
| [その他設計](./agents/llm/OTHER_DESIGNS.md) | 拡張機能、カスタマイズ設計 |

### 2. Gitエージェント
**場所**: [agents/git/](./agents/git/)

| ドキュメント | 説明 |
|------------|------|
| [概要](./agents/git/README.md) | Gitエージェントの役割と全体像 |
| [詳細設計](./agents/git/DETAILED_DESIGN.md) | git_agent, git_smart_agentの内部設計 |
| [コミット戦略](./agents/git/COMMIT_STRATEGY.md) | 自動コミット、チャンク処理設計 |
| [その他設計](./agents/git/OTHER_DESIGNS.md) | ブランチ管理、フックスクリプト設計 |

### 3. Configエージェント
**場所**: [agents/config/](./agents/config/)

| ドキュメント | 説明 |
|------------|------|
| [概要](./agents/config/README.md) | 設定管理エージェントの役割 |
| [詳細設計](./agents/config/DETAILED_DESIGN.md) | YAML/JSON設定管理、バリデーション |
| [環境変数設計](./agents/config/ENV_DESIGN.md) | .env管理、セキュリティ設計 |
| [その他設計](./agents/config/OTHER_DESIGNS.md) | 動的設定、プラグイン設定 |

### 4. Commandエージェント
**場所**: [agents/command/](./agents/command/)

| ドキュメント | 説明 |
|------------|------|
| [概要](./agents/command/README.md) | コマンド実行エージェントの役割 |
| [詳細設計](./agents/command/DETAILED_DESIGN.md) | コマンド実行、セキュリティ検証 |
| [実行戦略](./agents/command/EXECUTION_STRATEGY.md) | 並列実行、タイムアウト処理 |
| [その他設計](./agents/command/OTHER_DESIGNS.md) | スクリプト生成、ログ管理 |

### 5. Discordエージェント
**場所**: [agents/discord/](./agents/discord/)

| ドキュメント | 説明 |
|------------|------|
| [概要](./agents/discord/README.md) | Discord Botの役割と機能 |
| [詳細設計](./agents/discord/DETAILED_DESIGN.md) | Bot Core、プラグインシステム |
| [音声管理](./agents/discord/VOICE_DESIGN.md) | 音声トリガー、音声合成設計 |
| [その他設計](./agents/discord/OTHER_DESIGNS.md) | アンチスパム、権限管理 |

### 6. MCPエージェント
**場所**: [agents/mcp/](./agents/mcp/)

| ドキュメント | 説明 |
|------------|------|
| [概要](./agents/mcp/README.md) | 自動プロジェクト生成システム概要 |
| [詳細設計](./agents/mcp/DETAILED_DESIGN.md) | 仕様正規化、設計、検証フロー |
| [コーディングルール](./agents/mcp/CODING_RULES.md) | MCP開発規約、禁止コマンド |
| [その他設計](./agents/mcp/OTHER_DESIGNS.md) | テンプレート、Jinja2統合 |

---

## 🛠️ サービス別設計書

### AI/LLMサービス
**場所**: [services/](./services/)

| ドキュメント | 説明 |
|------------|------|
| [AI総合設計](./services/AI_SERVICE_DESIGN.md) | services/ai/の全体設計 |
| [プロバイダー仕様](./services/PROVIDER_SPECS.md) | Ollama/Gemini/HuggingFace仕様 |

### データベースサービス
| ドキュメント | 説明 |
|------------|------|
| [DB総合設計](./services/DB_SERVICE_DESIGN.md) | services/db/の全体設計 |
| [スキーマ定義](./services/DB_SCHEMA.md) | テーブル定義、インデックス設計 |

### MCPサービス
| ドキュメント | 説明 |
|------------|------|
| [MCP総合設計](./services/MCP_SERVICE_DESIGN.md) | services/mcp/の全体設計 |
| [新フロー設計](./services/MCP_NEW_FLOW.md) | 仕様正規化→設計→検証フロー |

---

## 🌐 HTML版ドキュメント

インタラクティブなナビゲーション付きHTML版ドキュメントは以下で閲覧できます：

📄 **[HTML版トップページ](../html/index.html)**

### HTML版の特徴
- 📑 サイドバーナビゲーション
- 🔍 全文検索機能
- 📱 レスポンシブデザイン
- 🎨 シンタックスハイライト
- 🔗 相互リンク自動生成

---

## 📝 ドキュメント作成・更新ガイドライン

### 新規ドキュメント作成時
1. 適切なディレクトリに配置
2. READMEに追加してリンク
3. HTML版を再生成（`python3 tools/generate_html_docs.py`）
4. Git commit

### ドキュメント更新時
1. 対応するMarkdownファイルを編集
2. 変更履歴を記録
3. HTML版を再生成
4. TASK_MANAGEMENT.mdに記録

---

## 🚀 クイックナビゲーション

### 初めての方
1. [プロジェクト概要](./OVERVIEW.md) - まずはここから
2. [アーキテクチャ設計](./ARCHITECTURE_DESIGN.md) - システム全体像
3. [タスク管理](./TASK_MANAGEMENT.md) - 現在の進捗確認

### 開発者向け
1. [エージェント別設計書](./agents/) - 各モジュールの詳細
2. [サービス設計書](./services/) - サービス層の仕様
3. [HTML版ドキュメント](../html/index.html) - 快適な閲覧

### 運用担当者向け
1. [データベース設計](./DATABASE_DESIGN.md) - DB管理情報
2. [Discord設定](./agents/discord/README.md) - Bot運用
3. [環境変数設計](./agents/config/ENV_DESIGN.md) - 環境設定

---

*最終更新: 2025年11月2日*
