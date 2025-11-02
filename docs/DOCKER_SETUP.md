# NeuroHub Docker セットアップガイド

## 🐳 Dockerとは

Dockerは、アプリケーションとその依存関係を**コンテナ**という単位でパッケージ化する技術です。

### NeuroHubでDockerを使うメリット

1. **環境構築が超簡単** 🚀
   - 複雑な手順が `docker-compose up` 1コマンドに
   - Python venv、Ollama、依存関係が全て自動セットアップ

2. **どこでも同じ環境** 🌍
   - Windows、Linux、Raspberry Piで完全に同じ動作
   - 「私の環境では動くのに...」問題の解消

3. **ラズパイ対応** 🥧
   - ARM64/ARM32アーキテクチャ自動対応
   - リソース制限設定で安定動作

---

## 📋 必要なもの

### Windows環境
- Docker Desktop for Windows
- WSL2有効化

### Raspberry Pi環境
- Docker Engine
- Docker Compose

---

## 🚀 クイックスタート

### 1. Docker Desktop インストール（Windows）

```powershell
# Docker Desktop公式サイトからダウンロード・インストール
# https://www.docker.com/products/docker-desktop

# インストール確認
docker --version
docker-compose --version
```

### 2. Raspberry Pi用インストール

```bash
# Docker インストール（ラズパイ）
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# 現在のユーザーをdockerグループに追加
sudo usermod -aG docker $USER

# Docker Compose インストール
sudo apt-get update
sudo apt-get install docker-compose-plugin

# 確認
docker --version
docker compose version
```

### 3. NeuroHub起動

```bash
# リポジトリクローン（まだの場合）
git clone https://github.com/messpy/NeuroHub.git
cd NeuroHub

# .envファイル作成（API Keyを設定）
cp .env.example .env
# エディタで.envを編集してAPI Keyを入力

# Docker Composeで起動
docker-compose up -d

# ログ確認
docker-compose logs -f neurohub
```

**これだけで完了！** 🎉

---

## ⚙️ 設定ファイル

### .env（API Key設定）

```env
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here

# HuggingFace API
HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# Discord Bot（オプション）
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here

# ログレベル
LOG_LEVEL=INFO
```

### docker-compose.yml（既に作成済み）

2つのサービスを起動：
- **ollama**: Ollamaサーバー（ポート11434）
- **neurohub**: NeuroHubメインアプリ（ポート8000）

---

## 🔧 よく使うコマンド

### 起動・停止

```bash
# 起動（バックグラウンド）
docker-compose up -d

# 停止
docker-compose down

# 再起動
docker-compose restart

# 完全削除（データも削除）
docker-compose down -v
```

### ログ確認

```bash
# 全サービスのログ
docker-compose logs -f

# NeuroHubのログのみ
docker-compose logs -f neurohub

# Ollamaのログのみ
docker-compose logs -f ollama
```

### コンテナ内でコマンド実行

```bash
# NeuroHubコンテナに入る
docker-compose exec neurohub bash

# Pythonスクリプト実行
docker-compose exec neurohub python3 test_hello_llm.py

# テスト実行
docker-compose exec neurohub pytest tests/ -v
```

### Ollamaモデル管理

```bash
# モデル一覧
docker-compose exec ollama ollama list

# モデルダウンロード
docker-compose exec ollama ollama pull qwen2.5:0.5b-instruct

# モデル削除
docker-compose exec ollama ollama rm <model_name>
```

---

## 🥧 Raspberry Pi固有の設定

### メモリ・CPU制限

`docker-compose.yml`で既に設定済み：

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'      # 最大2コア使用
      memory: 2G       # 最大2GB RAM
    reservations:
      cpus: '0.5'      # 最低0.5コア確保
      memory: 512M     # 最低512MB RAM
```

### 推奨スペック

| モデル | 推奨 | 最小 |
|--------|------|------|
| Raspberry Pi 4 (4GB) | ✅ 推奨 | - |
| Raspberry Pi 4 (2GB) | ⚠️ 可能 | - |
| Raspberry Pi 3B+ | ❌ 非推奨 | 軽量モデルのみ |

### ラズパイでの起動例

```bash
# Raspberry Pi OS (Debian Bookworm)
cd ~/NeuroHub

# メモリ節約モードで起動
docker-compose up -d

# 軽量モデル使用
docker-compose exec ollama ollama pull qwen2.5:0.5b-instruct
```

---

## 🔍 トラブルシューティング

### 1. "Cannot connect to Docker daemon"

```bash
# Dockerサービス起動
sudo systemctl start docker

# 自動起動設定
sudo systemctl enable docker
```

### 2. "Permission denied" エラー

```bash
# dockerグループに追加
sudo usermod -aG docker $USER

# 再ログイン必要
exit
# 再度SSHまたはターミナル起動
```

### 3. メモリ不足（ラズパイ）

```bash
# スワップ領域追加
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# CONF_SWAPSIZE=2048 に変更
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

### 4. Ollama接続エラー

```bash
# Ollamaコンテナ状態確認
docker-compose ps ollama

# Ollamaヘルスチェック
docker-compose exec ollama curl -f http://localhost:11434/api/tags
```

---

## 📊 Docker vs venv 比較

| 項目 | Docker | Python venv |
|------|--------|-------------|
| **セットアップ** | ⭐⭐⭐⭐⭐ 超簡単 | ⭐⭐⭐ 中程度 |
| **環境統一** | ⭐⭐⭐⭐⭐ 完璧 | ⭐⭐ OS依存 |
| **ラズパイ対応** | ⭐⭐⭐⭐⭐ 自動 | ⭐⭐⭐ 手動設定 |
| **メモリ使用** | ⭐⭐⭐ やや多い | ⭐⭐⭐⭐⭐ 最小 |
| **デバッグ** | ⭐⭐⭐ コンテナ内 | ⭐⭐⭐⭐⭐ 直接 |
| **本番運用** | ⭐⭐⭐⭐⭐ 最適 | ⭐⭐⭐ 手動管理 |

### 推奨使い分け

- **開発中**: venv（デバッグしやすい）
- **本番運用**: Docker（安定・簡単）
- **ラズパイ**: Docker（環境統一）
- **チーム共有**: Docker（環境差異なし）

---

## 🔄 アップデート手順

```bash
# 最新コード取得
git pull origin aidev

# イメージ再ビルド
docker-compose build

# 再起動
docker-compose up -d

# 古いイメージ削除（オプション）
docker image prune -f
```

---

## 🛠️ 開発者向け

### カスタムDockerfile

```dockerfile
# 開発用追加パッケージ
FROM python:3.12-slim-bookworm

# ... 既存の設定 ...

# 開発ツール追加
RUN pip install ipython jupyter black ruff mypy
```

### ボリュームマウント

```yaml
# docker-compose.override.yml（Git除外推奨）
version: '3.8'
services:
  neurohub:
    volumes:
      # ホストのコードを直接マウント（開発用）
      - ./agents:/app/agents
      - ./services:/app/services
```

---

## 📖 参考リンク

- [Docker公式ドキュメント](https://docs.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Ollama Docker](https://hub.docker.com/r/ollama/ollama)
- [Raspberry Pi + Docker](https://docs.docker.com/engine/install/debian/)

---

*最終更新: 2025年11月2日*
