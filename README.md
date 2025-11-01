# NeuroHub - Linux環境向け高度なGit & AI開発支援ツール

**🐧 Linux最適化されたマルチLLMプロバイダー対応開発支援プラットフォーム**

NeuroHubは、AI駆動のコミットメッセージ生成、自動化されたワークフロー、インテリジェントなコマンド実行を提供するLinux環境に最適化された包括的な開発支援プラットフォームです。

## 🌟 主要機能

### 🤖 統合AIエージェント（agents/）
- **git_smart_agent**: AI駆動のコミットメッセージ生成と対話型Git操作
- **llm_agent**: 3プロバイダー統合管理（Gemini、HuggingFace、Ollama）
- **command_agent**: 安全なコマンド実行とログ管理
- **config_agent**: 設定管理とYAML生成

### 🛠️ 独立ユーティリティ（services/agent/）
- **weather_agent**: APIキー不要の天気予報ツール
- **web_agent**: Webページ解析とLLM Q&A
- **agent_cli**: 統一CLIインターフェース

### 🔧 コマンドラインツール（tools/）
- **git_commit_ai**: 軽量Gitコミット支援
- **project_organizer**: プロジェクト構造管理

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

### 2. 手動セットアップ

```bash
# 依存関係インストール（Ubuntu/Debian）
sudo apt update && sudo apt install -y python3 python3-pip python3-venv git

# Python仮想環境作成
python3 -m venv venv_linux
source venv_linux/bin/activate

# 依存関係インストール
pip install --upgrade pip
pip install -r requirements.txt

# データベース初期化
python3 setup_database.py
```

### 3. 環境設定

`.env` ファイルを作成：

```bash
# 必須: Gemini API Key
GEMINI_API_KEY=your_gemini_api_key_here

# 必須: HuggingFace API Key
HUGGINGFACE_API_KEY=your_huggingface_token_here

# オプション: Ollama（ローカル）
OLLAMA_BASE_URL=http://localhost:11434
```

## 🎯 基本的な使用方法

### AIエージェント（統合機能）

```bash
# 仮想環境アクティベート
source venv_linux/bin/activate

# AI Git統合（対話型）
python3 agents/git_smart_agent.py

# LLMプロバイダーテスト
python3 agents/llm_agent.py

# 設定管理
python3 agents/config_agent.py
```

### 独立ユーティリティ

```bash
# 天気予報（APIキー不要）
python3 services/agent/weather_agent.py
python3 services/agent/weather_agent.py "Tokyo"

# Webページ解析
python3 services/agent/web_agent.py https://example.com "要約して"

# 統一CLI
python3 services/agent/agent_cli.py weather Tokyo
python3 services/agent/agent_cli.py web https://example.com "質問"
```

### コマンドラインツール

```bash
# 軽量Gitコミット支援
./tools/git_commit_ai

# プロジェクト整理
python3 tools/project_organizer.py
```

## 🧪 テスト実行

```bash
# 全プロバイダー統合テスト
python3 tests/test_comprehensive_working.py

# 全テストスイート
python3 -m pytest tests/ -v

# Linuxテストランナー
chmod +x tests/run_tests_linux.sh
./tests/run_tests_linux.sh
```

## 📋 API Key取得方法

1. **Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **HuggingFace**: [HuggingFace Settings](https://huggingface.co/settings/tokens)
3. **Ollama**: [公式サイト](https://ollama.ai/)からインストール

```bash
# Ollama インストール（Linux）
curl -fsSL https://ollama.com/install.sh | sh
ollama serve &
ollama pull qwen2.5:1.5b-instruct
```

## 🏗️ プロジェクト構造

```
NeuroHub/
├── agents/                    # 🤖 統合AIエージェント
│   ├── git_smart_agent.py    # AI Git統合
│   ├── llm_agent.py          # マルチLLM管理
│   ├── command_agent.py      # コマンド実行
│   └── config_agent.py       # 設定管理
├── services/                  # 🔧 マイクロサービス
│   ├── agent/                # 独立ユーティリティ
│   │   ├── weather_agent.py  # 天気予報
│   │   ├── web_agent.py      # Web解析
│   │   └── agent_cli.py      # 統一CLI
│   ├── llm/                  # LLMプロバイダー
│   └── db/                   # データベース管理
├── tools/                     # 🛠️ コマンドラインツール
│   ├── git_commit_ai         # 軽量Gitツール
│   └── project_organizer.py  # プロジェクト管理
├── config/                    # ⚙️ 設定ファイル
├── tests/                     # 🧪 テストスイート
├── docs/                     # 📚 ドキュメント
└── venv_linux/               # 🐧 Linux仮想環境
```

## 📊 実装状況

### ✅ 完全動作確認済み（Linux）
- **LLMAgent**: 3プロバイダー統合・自動フォールバック
- **git_smart_agent**: AIコミットメッセージ生成
- **プロバイダー接続**: Gemini、HuggingFace、Ollama
- **weather_agent**: IP位置推定＋天気予報
- **web_agent**: Webページ解析＋LLM Q&A

### ⚠️ 調整中
- **command_agent**: インターフェース最適化
- **config_agent**: 設定自動生成

### 🐧 Linux最適化
- **パス区切り**: Unix形式（/）統一
- **権限管理**: chmod、実行権限対応
- **環境変数**: ~/.bashrc自動設定
- **パッケージ管理**: apt、pip要求

## 📈 パフォーマンス（Linux環境）

| プロバイダー | レスポンス時間 | 特徴 |
|-------------|---------------|------|
| Gemini | ~1.0秒 | 安定・高品質 |
| HuggingFace | ~0.3秒 | 高速レスポンス |
| Ollama | ~1.6秒 | ローカル・プライベート |

## 🎯 使用例

### AI Git統合ワークフロー

```bash
# ファイル編集
echo "new feature" >> feature.py

# AI統合Gitワークフロー
python3 agents/git_smart_agent.py
# → ファイル分析
# → コミットメッセージ生成
# → 対話型確認
# → 自動コミット
```

### 天気予報統合

```bash
# IP位置推定天気
python3 services/agent/weather_agent.py

# 都市指定
python3 services/agent/weather_agent.py "Tokyo"

# 詳細予報
python3 services/agent/weather_agent.py --lat 35.68 --lon 139.76 --forecast hourly
```

### Web解析統合

```bash
# ページ要約
python3 services/agent/web_agent.py https://example.com "3行で要約"

# 価格確認
python3 services/agent/web_agent.py https://shop.example.com "価格は？"
```

## 🛠️ 開発者向け

### テスト実行

```bash
# 統合テスト
python3 tests/test_comprehensive_working.py

# 個別テスト
python3 tests/test_llm_agent_updated.py
python3 tests/test_integration_comprehensive.py

# テストカバレッジ
python3 -m pytest tests/ --cov=agents --cov=services
```

### デバッグ

```bash
# LLMプロバイダー直接テスト
python3 -c "from agents.llm_agent import LLMAgent; print(LLMAgent().check_provider_status())"

# Git状態確認
python3 -c "from agents.git_smart_agent import GitSmartAgent; print(GitSmartAgent().get_git_status())"
```

## 🤝 コントリビューション

1. フォーク
2. フィーチャーブランチ作成: `git checkout -b feature/amazing-feature`
3. テスト実行: `python3 -m pytest tests/ -v`
4. コミット: `./tools/git_commit_ai` または `python3 agents/git_smart_agent.py`
5. プッシュ: `git push origin feature/amazing-feature`
6. プルリクエスト作成

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🆘 サポート

- **Issues**: [GitHub Issues](https://github.com/messpy/NeuroHub/issues)
- **Documentation**: [docs/](docs/) フォルダ
- **Linux Setup**: `./setup_neurohub_linux.sh`

---

**🐧 Ready to boost your Linux development workflow with AI? Get started now!**
