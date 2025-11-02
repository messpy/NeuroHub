# NeuroHub 依存関係ガイド

## 📦 概要

NeuroHubは最小限の依存関係で動作するように設計されています。すべての依存関係は**無料のオープンソースライブラリ**です。

## 🔧 システム要件

### 最小要件
- **OS**: Linux, macOS, Windows (WSL推奨)
- **Python**: 3.9以上
- **メモリ**: 512MB以上
- **ストレージ**: 500MB以上

### 推奨要件
- **OS**: Linux (Ubuntu 20.04+) / macOS 12+
- **Python**: 3.12
- **メモリ**: 2GB以上
- **ストレージ**: 2GB以上（MCP生成プロジェクト用）

## 📚 Python依存関係

### 必須依存関係（15パッケージ）

#### 1. HTTP/API通信
```
requests>=2.28.0          # HTTP通信（LLM API呼び出し）
aiohttp>=3.8.0            # 非同期HTTP通信（Discord Bot用）
```

#### 2. 設定管理
```
PyYAML>=6.0               # YAML設定ファイル解析
python-dotenv>=0.21.0     # .env環境変数読み込み
```

#### 3. Web解析
```
beautifulsoup4>=4.11.0    # HTMLパース（Web Agent用）
lxml>=4.9.0               # 高速XML/HTMLパーサー
```

#### 4. LLM API
```
google-generativeai>=0.3.0  # Gemini API（無料: 1日250リクエスト）
openai>=1.0.0              # HuggingFace互換API（無料: 月間制限）
```

#### 5. テスト
```
pytest>=7.0.0             # ユニットテスト
pytest-cov>=4.0.0         # カバレッジ測定
```

#### 6. CLI
```
click>=8.0.0              # CLIフレームワーク
colorama>=0.4.0           # カラー出力（クロスプラットフォーム）
```

### オプション依存関係（Discord Bot用）

```
discord.py>=2.3.0         # Discord Bot開発
gTTS>=2.3.0              # Text-to-Speech
PyNaCl>=1.5.0            # 音声機能
```

### オプション依存関係（音声認識用）

```
SpeechRecognition>=3.10.0  # 音声認識
PyAudio>=0.2.13           # マイク入力
sounddevice>=0.4.6        # 音声デバイス制御
numpy>=1.24.0             # 音声データ処理
fuzzywuzzy>=0.18.0        # あいまい文字列マッチング
python-Levenshtein>=0.20.0 # 高速文字列比較
```

### 開発依存関係（requirements-dev.txt）

```
mypy>=1.0.0               # 型チェック
types-requests>=2.28.0    # requestsの型定義
types-PyYAML>=6.0.0       # PyYAMLの型定義
black>=23.0.0             # コードフォーマッター
flake8>=6.0.0             # Linter
```

## 🐧 システム依存関係

### Linux (Ubuntu/Debian)

```bash
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    sqlite3 \
    build-essential \
    portaudio19-dev
```

**説明**:
- `python3`, `python3-pip`, `python3-venv`: Python環境
- `git`: バージョン管理
- `curl`: HTTP通信テスト
- `sqlite3`: データベース管理
- `build-essential`: C拡張コンパイル用
- `portaudio19-dev`: PyAudio音声入力用

### macOS

```bash
brew install \
    python3 \
    git \
    curl \
    sqlite3 \
    portaudio
```

### Docker

Dockerを使用する場合、すべての依存関係は自動的にインストールされます:

```bash
docker-compose up -d
```

## 🔄 インストール方法

### 方法1: 自動（推奨）

```bash
# 統合セットアップスクリプト
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### 方法2: 手動

```bash
# 仮想環境作成
python3 -m venv venv_linux

# アクティベート
source venv_linux/bin/activate

# 依存関係インストール
pip install --upgrade pip
pip install -r requirements.txt

# 開発用（オプション）
pip install -r requirements-dev.txt
```

### 方法3: Docker

```bash
# Docker Composeで全て自動
docker-compose up -d
```

## 🎯 最小構成（LLM APIのみ）

Gemini APIのみ使用する最小構成:

```bash
pip install \
    requests \
    PyYAML \
    python-dotenv \
    google-generativeai
```

**環境変数**:
```bash
GEMINI_API_KEY=your_key_here
```

## 🚫 不要なもの

以下は**不要**です（内蔵またはオプション）:

- ❌ PostgreSQL, MySQL（SQLiteで十分）
- ❌ Redis（メモリキャッシュで対応）
- ❌ Node.js（Pythonのみ）
- ❌ Docker（ローカル実行可能）
- ❌ 有料API（すべて無料API）

## 🔍 依存関係チェック

```bash
# インストール済みパッケージ確認
pip list

# 必須パッケージチェック
python3 -c "
import requests, yaml, dotenv, bs4, pytest
print('✅ すべての必須パッケージがインストール済み')
"

# バージョン確認
python3 --version
git --version
sqlite3 --version
```

## 📊 サイズ比較

| 構成 | ディスク使用量 | メモリ使用量 |
|------|----------------|--------------|
| 最小構成（Gemini のみ） | ~100MB | ~256MB |
| 標準構成（全プロバイダー） | ~300MB | ~512MB |
| フル構成（音声認識込み） | ~500MB | ~1GB |
| Docker構成 | ~1.5GB | ~2GB |

## 🔧 トラブルシューティング

### PyAudioインストールエラー

**Linux**:
```bash
sudo apt install portaudio19-dev
pip install PyAudio
```

**macOS**:
```bash
brew install portaudio
pip install PyAudio
```

**Windows**:
```bash
# pipwin使用
pip install pipwin
pipwin install pyaudio
```

### SQLiteバージョンエラー

```bash
# SQLiteアップグレード（Linux）
sudo apt install sqlite3 libsqlite3-dev

# 確認
python3 -c "import sqlite3; print(sqlite3.sqlite_version)"
```

### Ollamaインストール

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# https://ollama.com/download からインストーラーダウンロード

# Docker
docker-compose up -d ollama
```

## 📖 関連ドキュメント

- [README.md](../README.md) - メインドキュメント
- [DOCKER_SETUP.md](DOCKER_SETUP.md) - Docker詳細ガイド
- [ARCHITECTURE_DESIGN.md](ARCHITECTURE_DESIGN.md) - アーキテクチャ設計
- [TESTING.md](TESTING.md) - テストガイド
