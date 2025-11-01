# NeuroHub - AI-Powered Development Assistant

**🧠 マルチLLMプロバイダー対応の高度なGit & 開発支援ツールセット**

NeuroHubは、AI駆動のコミットメッセージ生成、自動化されたワークフロー、インテリジェントなコマンド実行を提供する包括的な開発支援プラットフォームです。

## 🌟 主要機能

### 🤖 Pythonエージェントシステム
- **GitAgent**: AI駆動のコミットメッセージ生成と自動Git操作
- **LLMAgent**: マルチプロバイダーLLM管理（Gemini、HuggingFace、Ollama）
- **ConfigAgent**: 設定の自動検出・生成・最適化
- **CommandAgent**: 安全なコマンド実行と履歴管理

### 🛠️ 独立ツール
- **git_commit_ai**: シェルベースの軽量コミット支援ツール
- **LLMプロバイダー**: 統一APIでの多様なAIモデル連携
- **履歴管理**: SQLite + FTS5による高速検索対応データベース

### 🔧 アーキテクチャ特徴
- **独立性**: toolsフォルダのツールは完全に独立動作
- **統合性**: agentsフォルダで高機能な統合環境
- **拡張性**: モジュラー設計による容易な機能追加
- **安全性**: セーフモード、権限チェック、サンドボックス実行

## 🚀 クイックスタート

### 1. セットアップ

```bash
# プロジェクトクローン
git clone https://github.com/messpy/NeuroHub.git
cd NeuroHub

# 依存関係インストール
pip install -r requirements.txt

# データベース初期化
python setup_database.py

# 設定自動生成
python agents/config_agent.py --generate
```

### 2. 基本使用方法

```bash
# 🎯 AI コミットメッセージ生成（独立ツール）
tools/git_commit_ai

# 🤖 Python Gitエージェント（高機能）
python agents/git_agent.py --auto

# 🔧 対話型コマンド実行
python agents/command_agent.py --interactive

# 📊 LLM プロバイダーテスト
python agents/llm_agent.py --test "こんにちは"
```

## 📋 API キー設定

### 環境変数設定（`.env` ファイル推奨）

```bash
# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash-exp

# HuggingFace
HF_TOKEN=your_huggingface_token_here
HF_MODEL=meta-llama/Llama-3.2-3B-Instruct

# Ollama（ローカル）
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=qwen2.5:1.5b-instruct
```

### API キー取得方法

1. **Gemini**: [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **HuggingFace**: [HuggingFace Settings](https://huggingface.co/settings/tokens)
3. **Ollama**: ローカルインストール - [公式サイト](https://ollama.ai/)

## 🎯 使用例

### Git コミット自動化

```bash
# ファイル変更
echo "新機能追加" >> feature.py

# AI コミットメッセージ生成 + 自動コミット
python agents/git_agent.py --auto

# 出力例:
# ✅ コミット完了: ":add: feature.py 新機能実装"
```

### インタラクティブ Git 管理

```bash
python agents/git_agent.py --interactive

# Git状態確認、ファイル選択、メッセージ生成、レビュー、コミット
# までの全フローを対話的に実行
```

### マルチプロバイダー LLM

```python
from agents.llm_agent import LLMAgent, LLMRequest

agent = LLMAgent()

request = LLMRequest(
    prompt="Pythonでフィボナッチ数列を生成する関数を書いて",
    max_tokens=200,
    temperature=0.3
)

response = agent.generate_text(request)
print(response.content)
```

### セーフコマンド実行

```bash
python agents/command_agent.py git status
python agents/command_agent.py "python -m pytest tests/ -v"
python agents/command_agent.py --async-mode "python long_running_script.py"
```

## 🏗️ プロジェクト構造

```
NeuroHub/
├── agents/                    # 🤖 Pythonエージェント
│   ├── git_agent.py          # Git操作 + AI統合
│   ├── llm_agent.py          # LLM管理・選択
│   ├── config_agent.py       # 設定管理・最適化
│   └── command_agent.py      # セーフコマンド実行
├── tools/                     # 🛠️ 独立ツール
│   └── git_commit_ai         # 軽量コミット支援
├── services/                  # 🔧 コアサービス
│   ├── llm/                  # LLMプロバイダー
│   ├── db/                   # データベース管理
│   └── mcp/                  # MCP統合
├── config/                    # ⚙️ 設定ファイル
│   ├── llm_config.yaml       # LLM設定
│   ├── agent_config.yaml     # エージェント設定
│   └── prompt_templates.yaml # プロンプトテンプレート
├── tests/                     # 🧪 テストスイート
│   ├── agents/               # エージェントテスト
│   ├── services/             # サービステスト
│   └── tools/                # ツールテスト
└── docs/                     # 📚 ドキュメント
```

---

## 🛠️ Installation（環境準備）

> ※ Ubuntu / Debian / Raspberry Pi / WSL2 / macOS 共通
> （Windows の場合は WSL2 推奨）

### (1) Python（必須）

```bash
python3 --version
なければ：

Debian / Ubuntu

bash
コードをコピーする
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
仮想環境(任意推奨)

bash
コードをコピーする
python3 -m venv venv
source venv/bin/activate
依存ライブラリ導入：

bash
コードをコピーする
pip install -r requirements.txt
(2) Ollama インストール（ローカル LLM）
Linux

bash
コードをコピーする
curl -fsSL https://ollama.com/install.sh | sh
macOS

bash
コードをコピーする
brew install ollama
ollama run llama3
動作確認：

bash
コードをコピーする
curl http://localhost:11434/api/tags
(3) HuggingFace CLI（任意 / Web Agentで利用）
bash
コードをコピーする
pip install huggingface_hub
APIキー設定例：

bash
コードをコピーする
huggingface-cli login
（API不要なモデルのみ使用する場合は省略可）

✅ Usage（ツール実行例）
Weather Agent（天気・IP推定）
bash
コードをコピーする
python services/agent/agent_cli.py weather
都市名指定：

bash
コードをコピーする
python services/agent/agent_cli.py weather Osaka
24時間予報 + JSON：

bash
コードをコピーする
python services/agent/agent_cli.py weather -- \
  --lat 35.68 --lon 139.76 \
  --forecast hourly --hours 24 --json
出力保存：

bash
コードをコピーする
python services/agent/agent_cli.py weather "Tokyo" --output
Web Agent（URL解析 & LLM QA）
bash
コードをコピーする
python services/agent/agent_cli.py web \
  https://booth.pm/ja/items/7414326 \
  "価格は？" --pretty
⚙️ Components
bash
コードをコピーする
services/agent/
 ├ agent_cli.py        ← 入口（Web/Weather統一）
 ├ weather_agent.py    ← Weather実装
 └ web_agent.py        ← Web解析 & QA
📌 Git操作（開発向け）
すべての変更をステージから外す：

bash
コードをコピーする
git restore --staged .
特定ファイルのみ：

bash
コードをコピーする
git restore --staged services/agent/weather_agent.py
状態確認：

bash
コードをコピーする
git status
🚀 ポート採用とネットワーク
機能	通信先	備考
Weather	Open-Meteo, ip-api, Nominatim	すべて APIキー不要
Web Agent	Webページ(HTML)	LLM解析に依存

※ ローカルLLM（Ollama）使用時は localhost:11434

✅ Optional（強化予定）
優先	内容
1	Discordへ自動天気通知（systemd + webhook）
2	自然言語判定「今日雨？」 → weather_agent実行
3	位置情報：Wi-Fi SSIDで切り替え
4	予報グラフ画像生成


# NeuroHub

# -*- coding: utf-8 -*-

"""
weather_agent.py
- IPから自動位置推定（引数無しでOK）
- 現在気温 / 時間予報 / 日次予報
- 保存は --output 時のみ
- APIキー不要
"""

import sys
import argparse
import datetime
from typing import Dict, Any, Optional
import requests
import yaml
import json
import re
from pathlib import Path

UA = "NeuroHubWeather/1.0"
TIMEOUT = 8

#========================
# Util
#========================

def geolocate_by_ip(lang="ja") -> Dict[str, Any]:
    headers = {"User-Agent": UA}

    # ip-api.com（http）
    try:
        r = requests.get("http://ip-api.com/json", headers=headers, timeout=TIMEOUT)
        if r.ok:
            j = r.json()
            if j.get("status") == "success":
                return {
                    "lat": float(j["lat"]),
                    "lon": float(j["lon"]),
                    "query_name": j.get("city"),
                    "admin1": j.get("regionName"),
                    "country": j.get("country"),
                    "lang": lang,
                    "ip_geo": {
                        "source": "ip-api.com",
                        "ip": j.get("query"),
                        "city": j.get("city"),
                        "region": j.get("regionName"),
                        "org": j.get("org"),


# Weather Agent

ex)

python services/agent/web_agent.py https://github.com/messpy --prompt "これいくら？" --output

# IP推定：引数なし
python services/agent/weather_agent.py
# 都市名
python services/agent/weather_agent.py "Osaka"
# 座標・温度単位・24時間予報
python services/agent/weather_agent.py --lat 35.68 --lon 139.76 --unit f --forecast hourly --hours 24


# WEB Agent

ex)
python services/agent/web_agent.py https://www.python.org "要約して"

python services/agent/web_agent.py \
  https://booth.pm/ja/items/7414326 \
  "これいくら？" --pretty
python services/agent/web_agent.py \
  https://www.openai.com \
  "3行で要約して"
python services/agent/web_agent.py \
  https://ja.wikipedia.org/wiki/Git \
  "gitとは何？"

# JSON
python services/agent/web_agent.py \
  https://www.python.org \
  "要約" > result.json
cat result.json

printf "Python homepage\n" | \
python services/agent/web_agent.py https://www.python.org "Pythonとは？"

## 🧠 Agent CLI – How to Use

`agent_cli.py` は Web解析 & 天気情報（Weather/Web Agent）を
統一CLIから実行できます。

---

### ✔️ 前提：実行場所（プロジェクトルート）

```bash
cd ~/work/NeuroHub
🌦️ Weather Agent（天気）
引数なし → IPから現在地推定

bash
コードをコピーする
python services/agent/agent_cli.py weather
都市名指定

bash
コードをコピーする
python services/agent/agent_cli.py weather Osaka
座標指定（例：東京駅付近）

bash
コードをコピーする
python services/agent/agent_cli.py weather -- \
  --lat 35.68 --lon 139.76
24時間予報（JSON形式）

bash
コードをコピーする
python services/agent/agent_cli.py weather -- \
  --forecast hourly --hours 24 --json
保存（自動命名 / ./weather_logs）

bash
コードをコピーする
python services/agent/agent_cli.py weather "Tokyo" --output
🌐 Web Agent（URL解析 & Q&A）
BOOTHページの価格を聞く

bash
コードをコピーする
python services/agent/agent_cli.py web \
  https://booth.pm/ja/items/7414326 \
  "これいくら？" --pretty
Webページを3行で要約

bash
コードをコピーする
python services/agent/agent_cli.py web \
  https://www.python.org \
  "3行で要約して"
