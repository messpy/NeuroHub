# NeuroHub

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

