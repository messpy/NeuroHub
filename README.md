# NeuroHub - 高度なAI統合Git & 開発支援プラットフォーム

**� マルチプロバイダーLLM統合・チャンク処理・安全な長文処理対応開発支援プラットフォーム**

NeuroHubは、AI駆動のコミットメッセージ生成、チャンク処理による長文対応、マルチプロバイダーLLM統合、安全なテキスト処理を提供する次世代開発支援プラットフォームです。

## 🌟 主要機能

### 🚀 最新機能（v1.0.0）
- **チャンク処理**: 長いテキストを安全に分割・並列処理
- **日本語対応テキスト折り返し**: 文字境界を考慮した安全な表示
- **マルチプロバイダー自動フォールバック**: 3プロバイダー間の自動切り替え
- **統一レスポンス形式**: 全LLMからの一貫した応答処理
- **安全なテキスト処理**: 入力検証・出力サニタイズ

### 🤖 統合AIエージェント（agents/）
- **git_smart_agent**: AI駆動のコミットメッセージ生成・ファイル分析・大規模変更対応
- **llm_agent**: 3プロバイダー統合管理（Gemini、HuggingFace、Ollama）・チャンク処理対応
- **command_agent**: 安全なコマンド実行とログ管理
- **config_agent**: 設定管理とYAML生成

### 🌐 MCP強化システム（services/mcp/）✨ NEW
- **mcp_enhanced**: データベース統合MCPサーバー・14種類のメソッド対応
- **llm_investigator**: LLM自発調査エージェント・複数エージェント協調
- **natureremo_agent**: NatureRemo API統合・スマートホーム制御
- **auto_project_generator**: 高度な自動プロジェクト生成・外部ライブラリ対応
- **advanced_validator**: 5回連続成功検証システム・統計レポート機能
- **標準フロー準拠**: MCPプロトコル完全対応・エラーハンドリング

### 💾 統合データベースシステム（services/db/）
- **database_manager**: 27テーブル統一CRUD操作・安全なSQL実行
- **knowledge_manager**: ナレッジベース管理・全文検索・関連質問
- **user_manager**: ユーザー管理・設定・認証
- **db_initializer**: テーブル自動作成・サンプルデータ投入

### 🛠️ 独立ユーティリティ（services/agent/）
- **weather_agent**: APIキー不要の天気予報ツール
- **web_agent**: Webページ解析とLLM Q&A
- **agent_cli**: 統一CLIインターフェース・チャンク処理コマンド

### 🔧 コマンドラインツール（tools/）
- **git_commit_ai**: 軽量Gitコミット支援
- **project_organizer**: プロジェクト構造管理

## 🚀 クイックスタート

### 方法1: Docker（推奨 - Windows/ラズパイ両対応）🐳

```bash
# プロジェクトクローン
git clone https://github.com/messpy/NeuroHub.git
cd NeuroHub

# .envファイル作成
cp .env.example .env
# エディタで.envを編集してAPI Keyを入力

# Docker Composeで起動（1コマンド！）
docker-compose up -d

# ログ確認
docker-compose logs -f neurohub
```

**メリット**:
- ⚡ 超簡単セットアップ
- 🌍 環境統一（Windows/Linux/ラズパイ）
- 🔒 安定動作

詳細: [DOCKER_SETUP.md](./docs/DOCKER_SETUP.md)

---

### 方法2: 自動セットアップ（従来の方法）

```bash
# プロジェクトクローン
git clone https://github.com/messpy/NeuroHub.git
cd NeuroHub

# 自動セットアップ（Linux）
chmod +x setup_neurohub_linux.sh
./setup_neurohub_linux.sh

# 自動セットアップ（Windows）
setup_neurohub_windows.bat
```

### 方法3: 手動セットアップ

```bash
# Python仮想環境作成
python3 -m venv venv_linux  # Linux
python -m venv venv         # Windows

# 仮想環境アクティベート
source venv_linux/bin/activate  # Linux
venv\Scripts\activate           # Windows

# 依存関係インストール
pip install --upgrade pip
pip install -r requirements.txt

# データベース初期化
python setup_database.py
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

### ⚡ LLMプロバイダー切り替え

```bash
# Ollamaに切り替え（ローカル・無料・推奨）
python -c "import yaml; from pathlib import Path; config_file = Path('config/llm_config.yaml'); config = yaml.safe_load(open(config_file, 'r', encoding='utf-8')); config.setdefault('llm', {}).setdefault('providers', {}).setdefault('ollama', {}).update({'enabled': True, 'model': 'qwen2.5:1.5b-instruct', 'api_url': 'http://localhost:11434', 'max_tokens': 500, 'temperature': 0.3, 'timeout': 30, 'priority': 1}); [config['llm']['providers'][p].update({'enabled': False}) for p in config['llm']['providers'] if p != 'ollama']; yaml.dump(config, open(config_file, 'w', encoding='utf-8'), allow_unicode=True, default_flow_style=False); print('✅ Ollamaに切り替えました')"

# LLMテスト（Ollama使用）
python agents/llm_agent.py --test "日本語で自己紹介してください" --provider ollama

# 現在の設定確認
python -c "import yaml; config = yaml.safe_load(open('config/llm_config.yaml', 'r', encoding='utf-8')); [print(f'{k}: {v.get(\"model\")} (enabled={v.get(\"enabled\")})') for k,v in config.get('llm', {}).get('providers', {}).items()]"
```

### AIエージェント（統合機能）

```bash
# 仮想環境アクティベート
source venv_linux/bin/activate  # Linux
venv\Scripts\activate           # Windows

# AI Git統合（対話型・大規模変更対応）
python agents/git_smart_agent.py

# LLMプロバイダーテスト（チャンク処理対応）
python agents/llm_agent.py

# チャンク処理機能の使用
python tools/agent_cli.py chunk --file large_file.txt --chunk-size 400
python tools/agent_cli.py chunk --text "長いテキスト内容..." --chunk-size 300

# 設定管理
python agents/config_agent.py
```

### 新機能: 🎤 音声トリガーシステム

```bash
# ライブラリインストール
pip install SpeechRecognition PyAudio fuzzywuzzy python-Levenshtein sounddevice numpy

# デモ起動（音声でAIと会話）
python tools/voice_ai_demo.py

# カスタムトリガーワード設定
python services/tts/voice_trigger.py --words "起動" "ニューロ" "AI"

# 設定を保存
python services/tts/voice_trigger.py --words "起動" --threshold 85 --save

# マイクテスト
python services/tts/voice_trigger.py --test-mic
```

**特徴:**
- 🎯 高精度音声認識（Google Speech Recognition）
- 🔧 あいまいマッチング（発音が近ければ自動補正）
- 🌐 多言語対応（日本語、英語、中国語など）
- 💾 設定保存・読み込み機能
- 📊 認識率・トリガー履歴の統計

詳細: [VOICE_TRIGGER_GUIDE.md](docs/VOICE_TRIGGER_GUIDE.md)

---

### 新機能: 🤖 Discord Bot（拡張性抜群！）

**拡張性抜群のモジュラー型Discord Bot！LLM連携、音声機能、荒らし対策を完備。**

```bash
# ライブラリインストール
pip install discord.py python-dotenv gTTS PyNaCl

# Discord Bot Token取得
# https://discord.com/developers/applications

# .envファイルにトークン設定
# DISCORD_BOT_TOKEN=YOUR_TOKEN_HERE

# Bot起動
python tools/run_discord_bot.py
```

**主な機能:**
- 🔌 **プラグインシステム**: 機能を簡単に追加可能
- 🤖 **LLM連携**: Ollama等のLLM統合、メンション応答
- 🎵 **音声機能**: ボイスチャンネル参加、TTS、音声認識（将来）
- 🛡️ **荒らし対策**: レート制限、スパム検出、自動タイムアウト
- 📚 **ナレッジベース**: データベース統合、検索機能
- 📊 **統計記録**: コマンド実行数、LLM履歴の自動記録

**基本コマンド:**
```bash
!ping                    # Bot応答速度確認
!info                    # Bot情報表示
@NeuroHub [質問]         # AIに質問
!knowledge [ワード]       # ナレッジベース検索
!join                    # ボイスチャンネル参加
!tts [テキスト]          # テキスト読み上げ
!plugin list             # プラグイン一覧（管理者）
```

詳細: **[DISCORD_BOT_GUIDE.md](docs/DISCORD_BOT_GUIDE.md)** ← 完全ガイド！

---

### 新機能: MCP強化システム

```python
# MCPサーバーの起動
from services.mcp.mcp_enhanced import EnhancedMCPServer
from services.db.database_manager import DatabaseManager

db_manager = DatabaseManager()
mcp_server = EnhancedMCPServer(db_manager)
await mcp_server.initialize()

# ナレッジベース操作
response = await mcp_server.handle_request({
    "method": "knowledge.add",
    "params": {
        "category": "機能",
        "content": "MCPシステムの使用方法",
        "metadata": {"author": "user1"}
    }
})

# LLM自発調査の実行
response = await mcp_server.handle_request({
    "method": "llm.investigate",
    "params": {
        "query": "最新のGit変更履歴",
        "max_depth": 2
    }
})
# 結果: {'confidence': 0.90, 'recommendations': [...]}

# 高度なプロジェクト自動生成（外部ライブラリ対応）
response = await mcp_server.handle_request({
    "method": "project.generate_advanced",
    "params": {
        "topic": "機械学習データ前処理パイプライン",
        "libraries": ["pandas", "numpy", "scikit-learn"],
        "complexity": "complex"
    }
})

# 5回連続成功検証テスト
response = await mcp_server.handle_request({
    "method": "validation.run_advanced_test",
    "params": {
        "target_success_count": 5,
        "include_external_libs": True,
        "report_detail": True
    }
})

# データベース統計の取得
response = await mcp_server.handle_request({
    "method": "database.get_stats",
    "params": {}
})
```

### 新機能: チャンク処理

```bash
# 長いファイルの分割処理
python tools/agent_cli.py chunk --file docs/long_document.md

# 大きなGit差分の処理
python agents/git_smart_agent.py  # 自動的にチャンク処理が適用

# カスタムチャンクサイズ
python tools/agent_cli.py chunk --text "..." --chunk-size 500 --provider gemini
```

### 安全なテキスト処理

```python
# Pythonスクリプト内での使用
from services.llm.llm_common import safe_text_wrap, truncate_text_safely

# 日本語対応テキスト折り返し
wrapped_text = safe_text_wrap("長い日本語テキスト...", max_width=80)

# 安全な切り詰め
short_text = truncate_text_safely("長いテキスト", max_length=100, suffix="...")
```

### 独立ユーティリティ

```bash
# 天気予報（APIキー不要）
python services/agent/weather_agent.py
python services/agent/weather_agent.py "Tokyo"

# Webページ解析
python services/agent/web_agent.py https://example.com "要約して"

# 統一CLI（チャンク処理対応）
python services/agent/agent_cli.py weather Tokyo
python services/agent/agent_cli.py web https://example.com "質問"
python services/agent/agent_cli.py chunk --file large_file.txt
```

### コマンドラインツール

```bash
# 軽量Gitコミット支援
./tools/git_commit_ai    # Linux
tools\git_commit_ai.bat  # Windows

# プロジェクト整理
python tools/project_organizer.py
```

## 🧪 テスト実行

```bash
# 全プロバイダー統合テスト
python tests/test_comprehensive_working.py

# チャンク処理テスト
python tests/test_llm_agent_updated.py

# 全テストスイート
python -m pytest tests/ -v

# Linux専用テストランナー
chmod +x tests/run_tests_linux.sh
./tests/run_tests_linux.sh

# Windows専用テストランナー
tests\run_tests.bat
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
│   ├── mcp/                  # 🌐 MCP強化システム ✨NEW
│   │   ├── mcp_enhanced.py   # MCPサーバー
│   │   ├── llm_investigator.py # LLM自発調査
│   │   └── natureremo_agent.py # スマートホーム
│   ├── db/                   # 💾 データベース管理
│   │   ├── database_manager.py # 統一CRUD
│   │   ├── knowledge_manager.py # ナレッジ管理
│   │   └── db_initializer.py   # DB初期化
│   └── llm/                  # LLMプロバイダー
├── tools/                     # 🛠️ コマンドラインツール
│   ├── git_commit_ai         # 軽量Gitツール
│   └── project_organizer.py  # プロジェクト管理
├── config/                    # ⚙️ 設定ファイル
├── tests/                     # 🧪 テストスイート
├── docs/                     # 📚 ドキュメント
│   ├── MCP_ENHANCEMENT.md    # MCP設計書 ✨NEW
│   ├── DATABASE_DESIGN.md    # DB設計書 ✨NEW
│   └── ARCHITECTURE_DESIGN.md # システム設計書
└── venv_linux/               # 🐧 Linux仮想環境
```

## 📊 実装状況

### ✅ 完全動作確認済み
- **MCP強化システム**: データベース統合・LLM自発調査・NatureRemo連携 ✨NEW
- **データベース管理**: 27テーブル統一CRUD・ナレッジベース・LLM履歴追跡 ✨NEW
- **LLMAgent**: 3プロバイダー統合・自動フォールバック・チャンク処理
- **git_smart_agent**: AIコミットメッセージ生成・大規模変更対応
- **プロバイダー接続**: Gemini、HuggingFace、Ollama
- **weather_agent**: IP位置推定＋天気予報
- **web_agent**: Webページ解析＋LLM Q&A
- **チャンク処理**: 長文分割・並列処理・結果統合
- **テキスト安全処理**: 日本語対応折り返し・切り詰め

### 🔄 最新改善（v1.0.0）
- **マルチプロバイダー戦略**: 自動フォールバック機能
- **チャンク処理アーキテクチャ**: 300-500文字単位の分散処理
- **日本語最適化**: 文字境界・句読点考慮の折り返し
- **統一レスポンス**: LLMResponse形式による一貫した処理
- **安全性向上**: 入力検証・出力サニタイズ

### ⚠️ 調整中
- **command_agent**: インターフェース最適化
- **config_agent**: 設定自動生成
- **全スクリプト安全化**: テキスト折り返し適用

### 🌐 クロスプラットフォーム対応
- **Linux**: 完全対応（推奨環境）
- **Windows**: 基本対応・PowerShell最適化
- **macOS**: 基本対応・追加テスト中

## 📈 パフォーマンス

| プロバイダー | レスポンス時間 | チャンク処理 | 特徴 |
|-------------|---------------|-------------|------|
| Gemini | ~1.0秒 | ✅ 対応 | 高品質・制限あり |
| HuggingFace | ~0.3秒 | ✅ 対応 | 高速・安定 |
| Ollama | ~1.6秒 | ✅ 対応 | ローカル・プライベート |

### チャンク処理性能
- **分割速度**: ~10MB/秒（日本語文字境界考慮）
- **並列処理**: 最大3チャンク同時処理
- **メモリ効率**: チャンク単位でのメモリ管理
- **エラー耐性**: 部分失敗時の継続処理

## 🎯 使用例

### AI Git統合ワークフロー（大規模変更対応）

```bash
# 100個のファイル編集後
git add .

# AI統合Gitワークフロー（自動チャンク処理）
python agents/git_smart_agent.py
# → 103ファイルを11カテゴリに自動分類
# → チャンク処理で大きな差分を分割
# → AIによる統合的なコミットメッセージ生成
# → 対話型確認・自動コミット
```

### チャンク処理による長文解析

```bash
# 大きなログファイルの解析
python tools/agent_cli.py chunk --file system.log --chunk-size 400
# → ファイルを400文字単位で分割
# → 各チャンクを並列処理
# → 結果を統合して要約

# 長いMarkdownドキュメントの処理
python agents/llm_agent.py --chunk-text "$(cat large_document.md)"
# → 自動的にチャンク分割
# → プロバイダー制限を超えるテキストも安全に処理
```

### 安全なテキスト表示

```python
# 日本語テキストの安全な折り返し
from services.llm.llm_common import safe_text_wrap

long_japanese = "これは非常に長い日本語のテキストです。" * 10
wrapped = safe_text_wrap(long_japanese, max_width=40)
print(wrapped)
# → 文字境界を考慮した自然な改行
```

### 天気予報統合

```bash
# IP位置推定天気
python services/agent/weather_agent.py

# 都市指定
python services/agent/weather_agent.py "Tokyo"

# 詳細予報
python services/agent/weather_agent.py --lat 35.68 --lon 139.76 --forecast hourly
```

### Web解析統合

```bash
# ページ要約（チャンク処理対応）
python services/agent/web_agent.py https://example.com "3行で要約"

# 長いページの詳細分析
python services/agent/web_agent.py https://longpage.com "詳細分析"
# → 自動的にチャンク分割されて処理

# 価格確認
python services/agent/web_agent.py https://shop.example.com "価格は？"
```

## 🛠️ 開発者向け

### テスト実行

```bash
# 統合テスト
python tests/test_comprehensive_working.py

# チャンク処理テスト
python tests/test_llm_agent_updated.py

# 個別テスト
python tests/test_integration_comprehensive.py

# テストカバレッジ
python -m pytest tests/ --cov=agents --cov=services
```

### デバッグ

```bash
# LLMプロバイダー直接テスト
python -c "from agents.llm_agent import LLMAgent; print(LLMAgent().check_provider_status())"

# チャンク処理デバッグ
python -c "from agents.llm_agent import LLMAgent; agent = LLMAgent(); print(agent.generate_text_chunked('長いテキスト', debug=True))"

# Git状態確認
python -c "from agents.git_smart_agent import GitSmartAgent; print(GitSmartAgent().get_git_status())"
```

## 🤝 コントリビューション

1. フォーク
2. フィーチャーブランチ作成: `git checkout -b feature/amazing-feature`
3. テスト実行: `python -m pytest tests/ -v`
4. コミット: `./tools/git_commit_ai` または `python agents/git_smart_agent.py`
5. プッシュ: `git push origin feature/amazing-feature`
6. プルリクエスト作成

## 📄 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 🆘 サポート

- **Issues**: [GitHub Issues](https://github.com/messpy/NeuroHub/issues)
- **Documentation**: [docs/](docs/) フォルダ
- **Linux Setup**: `./setup_neurohub_linux.sh`

---

**� Ready to boost your development workflow with AI? Get started now!**

### 新機能ハイライト（v1.0.0）
- ✅ **チャンク処理**: 長文を自動分割・並列処理・結果統合
- ✅ **日本語最適化**: 文字境界を考慮した安全なテキスト処理
- ✅ **マルチプロバイダー**: 3プロバイダー間の自動フォールバック
- ✅ **大規模変更対応**: 100+ファイルの自動分類・AI解析
- ✅ **安全性向上**: 入力検証・出力サニタイズ・エラー耐性

**詳細なアーキテクチャ情報**: [docs/ARCHITECTURE_DESIGN.md](docs/ARCHITECTURE_DESIGN.md)
**タスク管理**: [docs/TASK_MANAGEMENT.md](docs/TASK_MANAGEMENT.md)
