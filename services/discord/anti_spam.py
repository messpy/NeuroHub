#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anti_spam.py

Discord Bot 荒らし対策マネージャー
- レート制限（メッセージ頻度制限）
- 重複メッセージ検出
- スパムパターン検出
- 自動タイムアウト/ミュート
"""

import time
import logging
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, deque
from datetime import datetime, timedelta

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class AntiSpamManager:
    """
    荒らし対策マネージャー

    機能:
    - メッセージレート制限
    - 重複メッセージ検出
    - スパムパターン検出（URL連投、絵文字スパム等）
    - 自動タイムアウト/警告
    - ホワイトリスト/ブラックリスト管理
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot

        # ユーザーごとのメッセージ履歴（dequeで最新N件のみ保持）
        self.user_messages: Dict[int, deque] = defaultdict(lambda: deque(maxlen=20))

        # ユーザーごとの違反カウント
        self.violation_counts: Dict[int, int] = defaultdict(int)

        # ホワイトリスト（管理者・モデレーター等）
        self.whitelist: set = set()

        # ブラックリスト（永久BAN対象）
        self.blacklist: set = set()

        # 設定
        self.config = {
            'max_messages_per_minute': 10,  # 1分間の最大メッセージ数
            'max_duplicate_messages': 3,     # 同一メッセージの最大回数
            'max_mentions_per_message': 5,   # 1メッセージあたりの最大メンション数
            'max_emoji_per_message': 10,     # 1メッセージあたりの最大絵文字数
            'timeout_duration': 60,          # タイムアウト時間（秒）
            'violation_threshold': 3,        # 違反回数の閾値（超えるとタイムアウト）
            'url_spam_threshold': 5,         # URL連投の閾値
            'caps_lock_threshold': 0.7       # 大文字比率の閾値（70%以上で警告）
        }

        logger.info("🛡️ AntiSpamManager 初期化完了")

    async def check_spam(self, message: discord.Message) -> bool:
        """
        スパムチェック

        Args:
            message: チェック対象メッセージ

        Returns:
            bool: スパムならTrue（メッセージを破棄）
        """
        user_id = message.author.id

        # ホワイトリストユーザーはスキップ
        if user_id in self.whitelist:
            return False

        # ブラックリストユーザーは即ブロック
        if user_id in self.blacklist:
            await self._handle_blacklist_user(message)
            return True

        # 管理者・Botはスキップ
        if message.author.guild_permissions.administrator or message.author.bot:
            return False

        # 各種スパムチェック
        is_spam = False
        violation_reasons = []

        # 1. レート制限チェック
        if await self._check_rate_limit(message):
            violation_reasons.append("メッセージ頻度超過")
            is_spam = True

        # 2. 重複メッセージチェック
        if await self._check_duplicate_messages(message):
            violation_reasons.append("重複メッセージ")
            is_spam = True

        # 3. メンションスパムチェック
        if await self._check_mention_spam(message):
            violation_reasons.append("メンションスパム")
            is_spam = True

        # 4. 絵文字スパムチェック
        if await self._check_emoji_spam(message):
            violation_reasons.append("絵文字スパム")
            is_spam = True

        # 5. URLスパムチェック
        if await self._check_url_spam(message):
            violation_reasons.append("URLスパム")
            is_spam = True

        # 6. 大文字スパムチェック
        if await self._check_caps_spam(message):
            violation_reasons.append("大文字スパム")
            is_spam = True

        # スパム検出時の処理
        if is_spam:
            await self._handle_spam_violation(message, violation_reasons)
            return True

        # メッセージ履歴に追加
        self.user_messages[user_id].append({
            'content': message.content,
            'timestamp': time.time()
        })

        return False

    async def _check_rate_limit(self, message: discord.Message) -> bool:
        """レート制限チェック"""
        user_id = message.author.id
        current_time = time.time()

        # 過去1分間のメッセージをカウント
        recent_messages = [
            msg for msg in self.user_messages[user_id]
            if current_time - msg['timestamp'] < 60
        ]

        return len(recent_messages) >= self.config['max_messages_per_minute']

    async def _check_duplicate_messages(self, message: discord.Message) -> bool:
        """重複メッセージチェック"""
        user_id = message.author.id
        content = message.content.strip().lower()

        if not content:
            return False

        # 過去のメッセージから同一内容をカウント
        duplicate_count = sum(
            1 for msg in self.user_messages[user_id]
            if msg['content'].strip().lower() == content
        )

        return duplicate_count >= self.config['max_duplicate_messages']

    async def _check_mention_spam(self, message: discord.Message) -> bool:
        """メンションスパムチェック"""
        mention_count = len(message.mentions) + len(message.role_mentions)
        return mention_count > self.config['max_mentions_per_message']

    async def _check_emoji_spam(self, message: discord.Message) -> bool:
        """絵文字スパムチェック"""
        # カスタム絵文字 + Unicode絵文字のカウント
        custom_emoji_count = len(message.content.split('<:')) - 1
        # 簡易的なUnicode絵文字カウント（完全ではない）
        unicode_emoji_count = sum(1 for char in message.content if ord(char) > 0x1F000)

        total_emoji = custom_emoji_count + unicode_emoji_count
        return total_emoji > self.config['max_emoji_per_message']

    async def _check_url_spam(self, message: discord.Message) -> bool:
        """URLスパムチェック"""
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, message.content)

        user_id = message.author.id
        recent_url_count = sum(
            1 for msg in self.user_messages[user_id]
            if re.search(url_pattern, msg['content'])
        )

        return len(urls) > 0 and recent_url_count >= self.config['url_spam_threshold']

    async def _check_caps_spam(self, message: discord.Message) -> bool:
        """大文字スパムチェック"""
        content = message.content

        # アルファベット文字のみ抽出
        alpha_chars = [c for c in content if c.isalpha()]

        if len(alpha_chars) < 10:  # 短いメッセージはスキップ
            return False

        caps_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
        return caps_ratio > self.config['caps_lock_threshold']

    async def _handle_spam_violation(self, message: discord.Message, reasons: List[str]):
        """スパム違反時の処理"""
        user_id = message.author.id
        self.violation_counts[user_id] += 1

        violation_count = self.violation_counts[user_id]

        # メッセージ削除
        try:
            await message.delete()
            logger.info(f"🗑️ スパムメッセージ削除: {message.author} - 理由: {', '.join(reasons)}")
        except discord.Forbidden:
            logger.warning("メッセージ削除権限がありません")

        # 警告メッセージ
        warning_msg = f"⚠️ {message.author.mention} スパム行為を検出しました（{', '.join(reasons)}）\n"
        warning_msg += f"違反回数: {violation_count}/{self.config['violation_threshold']}"

        if violation_count >= self.config['violation_threshold']:
            # タイムアウト実行
            await self._timeout_user(message.author, message.guild)
            warning_msg += f"\n🔇 {self.config['timeout_duration']}秒間のタイムアウトを実行しました。"

        await message.channel.send(warning_msg, delete_after=10)

    async def _timeout_user(self, member: discord.Member, guild: discord.Guild):
        """ユーザーをタイムアウト"""
        try:
            timeout_until = datetime.now() + timedelta(seconds=self.config['timeout_duration'])
            await member.timeout(timeout_until, reason="スパム行為")
            logger.info(f"🔇 タイムアウト実行: {member} - {self.config['timeout_duration']}秒")
        except discord.Forbidden:
            logger.warning(f"タイムアウト権限がありません: {member}")
        except Exception as e:
            logger.error(f"タイムアウト実行エラー: {e}")

    async def _handle_blacklist_user(self, message: discord.Message):
        """ブラックリストユーザーの処理"""
        try:
            await message.delete()
            await message.channel.send(
                f"🚫 {message.author.mention} はブラックリストに登録されています。",
                delete_after=5
            )
        except:
            pass

    def add_to_whitelist(self, user_id: int):
        """ホワイトリストに追加"""
        self.whitelist.add(user_id)
        logger.info(f"✅ ユーザー {user_id} をホワイトリストに追加")

    def remove_from_whitelist(self, user_id: int):
        """ホワイトリストから削除"""
        self.whitelist.discard(user_id)
        logger.info(f"❌ ユーザー {user_id} をホワイトリストから削除")

    def add_to_blacklist(self, user_id: int):
        """ブラックリストに追加"""
        self.blacklist.add(user_id)
        logger.info(f"🚫 ユーザー {user_id} をブラックリストに追加")

    def remove_from_blacklist(self, user_id: int):
        """ブラックリストから削除"""
        self.blacklist.discard(user_id)
        logger.info(f"✅ ユーザー {user_id} をブラックリストから削除")

    def reset_violations(self, user_id: int):
        """違反カウントをリセット"""
        self.violation_counts[user_id] = 0
        logger.info(f"🔄 ユーザー {user_id} の違反カウントをリセット")

    def get_user_stats(self, user_id: int) -> Dict[str, any]:
        """ユーザーの統計情報を取得"""
        return {
            'violations': self.violation_counts.get(user_id, 0),
            'message_count': len(self.user_messages.get(user_id, [])),
            'is_whitelisted': user_id in self.whitelist,
            'is_blacklisted': user_id in self.blacklist
        }
