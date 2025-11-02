#!/bin/bash
# start_discord_bot.sh
# Discord Bot 起動スクリプト

cd /mnt/c/Users/kenny/sandbox/NeuroHub
source venv_linux/bin/activate

echo "🤖 Discord Bot 起動中..."
python3 services/discord/bot_core.py
