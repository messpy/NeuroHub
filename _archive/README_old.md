# NeuroHub - AI-Powered Development Assistant

**🧠 Linux最適化されたマルチLLMプロバイダー対応の高度なGit & 開発支援ツールセット**

NeuroHubは、AI駆動のコミットメッセージ生成、自動化されたワークフロー、インテリジェントなコマンド実行を提供するLinux環境に最適化された包括的な開発支援プラットフォームです。

> **🐧 Linux推奨**: このプロジェクトはLinux環境での使用を前提として設計されています。
> Windows環境では [WSL2](https://docs.microsoft.com/windows/wsl/) の使用を強く推奨します。

## 🌟 主要機能

### 🤖 完全実装済み
- **git_smart_agent**: AI駆動のコミットメッセージ生成と対話型Git操作
- **llm_agent**: 3プロバイダー統合管理（Gemini、HuggingFace、Ollama）
- **git_commit_ai**: 軽量コマンドラインツール
- **weather_agent**: APIキー不要の天気予報ツール
- **web_agent**: Webページ解析とLLM Q&A

### ⚠️ 部分実装
- **command_agent**: 基本実装済み（インターフェース調整中）
- **config_agent**: 設定管理機能

### 🔧 アーキテクチャ特徴
- **Linux最適化**: Unix形式パス、権限管理、環境変数対応
- **マルチプロバイダー**: 自動フォールバック機能
- **統一API**: 一貫したインターフェース
- **独立ユーティリティ**: services/agent/による軽量ツール群

## 🚀 Linux環境クイックスタート

### 1. 自動セットアップ（推奨）

```bash
# プロジェクトクローン
git clone https://github.com/messpy/NeuroHub.git
cd NeuroHub

# Linux環境自動セットアップ
chmod +x setup_neurohub_linux.sh
./setup_neurohub_linux.sh
```
cd NeuroHub

# 依存関係インストール
pip install -r requirements.txt

# データベース初期化
python setup_database.py
```

### 2. 環境設定

`.env` ファイルを作成：

```bash
# Gemini API（必須）
GEMINI_API_KEY=your_gemini_api_key_here

# HuggingFace（必須）
HUGGINGFACE_API_KEY=your_huggingface_token_here

# Ollama（オプション - ローカル）
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. 基本使用方法

```bash
# 🎯 AI コミットメッセージ生成（コマンドライン）
./tools/git_commit_ai

# 🤖 GitSmartAgent（高機能・対話型）
python agents/git_smart_agent.py

# � LLM プロバイダーテスト
python -c "
from agents.llm_agent import LLMAgent, LLMRequest
agent = LLMAgent()
req = LLMRequest(prompt='こんにちは、テストです')
print(agent.generate_text(req).content)
"
```

## 🧪 テスト実行

```bash
# 全プロバイダー接続テスト
python tests/test_comprehensive_working.py

# 統合テスト
python tests/test_integration_comprehensive.py

# 全テスト実行
python -m pytest tests/ -v
```

## 📋 API キー取得方法

1. **Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **HuggingFace**: [HuggingFace Settings](https://huggingface.co/settings/tokens)
3. **Ollama**: [公式サイト](https://ollama.ai/)からローカルインストール

## 🎯 使用例

### Git コミット自動化

```bash
# ファイル変更
echo "新機能追加" >> feature.py

# AI コミットメッセージ生成
python agents/git_smart_agent.py

# 出力例:
# ✅ AI生成メッセージ: "feat: Add new feature implementation"
# 📝 ファイル分類完了: 3個のファイルを分析
# 🔄 コミット実行しますか？ [y/N]: y
```

### マルチプロバイダー LLM

```python
from agents.llm_agent import LLMAgent, LLMRequest

agent = LLMAgent()

# シンプルな生成
request = LLMRequest(
    prompt="Pythonでフィボナッチ数列を生成する関数を書いて"
)

response = agent.generate_text(request)
print(f"Provider: {response.provider}")
print(f"Content: {response.content}")

# プロバイダー指定
response = agent.generate_text(request, preferred_provider="gemini")
```

## 🏗️ プロジェクト構造

```
NeuroHub/
├── agents/                    # 🤖 Pythonエージェント
│   ├── git_smart_agent.py    # AI Git統合
│   ├── llm_agent.py          # LLM管理・選択
│   ├── config_agent.py       # 設定管理
│   └── command_agent.py      # コマンド実行
├── tools/                     # 🛠️ 独立ツール
│   └── git_commit_ai         # 軽量コミット支援
├── services/                  # 🔧 コアサービス
│   ├── llm/                  # LLMプロバイダー
│   ├── db/                   # データベース管理
│   └── mcp/                  # MCP統合（計画）
├── config/                    # ⚙️ 設定ファイル
│   ├── llm_config.yaml       # LLM設定
│   ├── agent_config.yaml     # エージェント設定
│   └── prompt_templates.yaml # プロンプトテンプレート
├── tests/                     # 🧪 テストスイート
├── docs/                     # 📚 ドキュメント
│   ├── INTERFACE_DESIGN.md   # 詳細設計
│   └── TESTING.md            # テスト文書
└── data/                     # � データディレクトリ
```

## � 実装状況

### ✅ 完全動作確認済み
- **LLMAgent**: 3プロバイダー統合・自動フォールバック
- **GitSmartAgent**: AIコミットメッセージ生成
- **プロバイダー接続**: Gemini、HuggingFace、Ollama すべて動作
- **履歴管理**: SQLite + FTS5検索
- **git_commit_ai**: コマンドラインツール

### ⚠️ 調整中
- **CommandAgent**: インターフェース最適化
- **ConfigAgent**: 設定自動生成

### � 開発中
- **REST API**: FastAPI基盤
- **WebUI**: ブラウザインターフェース
- **MCP統合**: Model Context Protocol

## 📊 パフォーマンス

| プロバイダー | レスポンス時間 | 特徴 |
|-------------|---------------|------|
| Gemini | ~1.0秒 | 安定・高品質 |
| HuggingFace | ~0.3秒 | 高速レスポンス |
| Ollama | ~1.6秒 | ローカル・プライベート |

## 🤝 コントリビューション

1. フォーク
2. フィーチャーブランチ作成: `git checkout -b feature/amazing-feature`
3. コミット: `git commit -m 'Add amazing feature'`
4. プッシュ: `git push origin feature/amazing-feature`
5. プルリクエスト作成

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🆘 サポート

- **Issues**: [GitHub Issues](https://github.com/messpy/NeuroHub/issues)
- **Documentation**: [docs/](docs/) フォルダ
- **Examples**: [tests/](tests/) フォルダのテストコード

---

**🚀 Ready to boost your development workflow with AI? Get started now!**
