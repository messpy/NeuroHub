#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_discord_bot.py

NeuroHub Discord Bot 起動スクリプト
"""

import os
import sys
import logging
from pathlib import Path

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.discord.bot_core import run_bot
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/discord_bot.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Discord Bot起動"""
    logger.info("=" * 50)
    logger.info("🤖 NeuroHub Discord Bot 起動中...")
    logger.info("=" * 50)

    # Discord Bot Tokenチェック
    token = os.getenv('DISCORD_BOT_TOKEN')
    if not token or token == 'YOUR_DISCORD_BOT_TOKEN_HERE':
        logger.error("❌ DISCORD_BOT_TOKEN が設定されていません！")
        logger.error("1. https://discord.com/developers/applications でBotを作成")
        logger.error("2. Bot タブでトークンを取得")
        logger.error("3. .env ファイルの DISCORD_BOT_TOKEN にトークンを設定")
        return 1

    try:
        run_bot(token)
    except KeyboardInterrupt:
        logger.info("✅ Bot を正常終了しました")
    except Exception as e:
        logger.error(f"❌ Bot実行エラー: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
