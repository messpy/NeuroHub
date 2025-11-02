#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Janken Game CLI テスト
"""

import pytest
import sqlite3
import os
from pathlib import Path
from janken_game_cli import DatabaseManager, JankenGame, CLI


@pytest.fixture
def test_db():
    """テスト用データベース"""
    db_path = "test_janken.db"
    db = DatabaseManager(db_path)
    yield db
    # テスト後クリーンアップ
    if os.path.exists(db_path):
        os.remove(db_path)


class TestDatabaseManager:
    """DatabaseManager テスト"""

    def test_database_init(self, test_db):
        """データベース初期化テスト"""
        conn = sqlite3.connect(test_db.db_path)
        cursor = conn.cursor()

        # テーブル存在確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}

        assert 'users' in tables
        assert 'user_stats' in tables
        assert 'game_history' in tables

        conn.close()

    def test_user_registration(self, test_db):
        """ユーザー登録テスト"""
        success, message = test_db.register_user("test_user1")
        assert success is True
        assert "登録しました" in message

        # ユーザー取得
        user = test_db.get_user("test_user1")
        assert user is not None
        assert user['username'] == "test_user1"

    def test_duplicate_user(self, test_db):
        """重複ユーザー登録テスト"""
        test_db.register_user("test_user1")
        success, message = test_db.register_user("test_user1")

        assert success is False
        assert "既に使用されています" in message

    def test_user_not_found(self, test_db):
        """存在しないユーザー取得テスト"""
        user = test_db.get_user("nonexistent_user")
        assert user is None


class TestJankenGame:
    """JankenGame テスト"""

    def test_game_logic_win(self):
        """勝利判定テスト"""
        assert JankenGame.judge('rock', 'scissors') == 'win'
        assert JankenGame.judge('scissors', 'paper') == 'win'
        assert JankenGame.judge('paper', 'rock') == 'win'

    def test_game_logic_lose(self):
        """敗北判定テスト"""
        assert JankenGame.judge('rock', 'paper') == 'lose'
        assert JankenGame.judge('scissors', 'rock') == 'lose'
        assert JankenGame.judge('paper', 'scissors') == 'lose'

    def test_game_logic_draw(self):
        """引き分け判定テスト"""
        assert JankenGame.judge('rock', 'rock') == 'draw'
        assert JankenGame.judge('paper', 'paper') == 'draw'
        assert JankenGame.judge('scissors', 'scissors') == 'draw'

    def test_computer_choice(self):
        """コンピューター選択テスト"""
        choice = JankenGame.get_computer_choice()
        assert choice in JankenGame.CHOICES

    def test_invalid_choice(self, test_db):
        """無効な選択テスト"""
        test_db.register_user("test_user1")
        success, message = JankenGame.play(test_db, "test_user1", "invalid_choice")

        assert success is False
        assert "無効な選択" in message

    def test_user_not_found_in_play(self, test_db):
        """存在しないユーザーでのプレイテスト"""
        success, message = JankenGame.play(test_db, "nonexistent_user", "rock")

        assert success is False
        assert "見つかりません" in message


class TestStatsCalculation:
    """統計計算テスト"""

    def test_stats_calculation(self, test_db):
        """統計情報計算テスト"""
        test_db.register_user("test_user1")
        user = test_db.get_user("test_user1")

        # 5回勝利
        for _ in range(5):
            test_db.save_game(user['id'], 'rock', 'scissors', 'win')
            test_db.update_stats(user['id'], 'win')

        # 3回敗北
        for _ in range(3):
            test_db.save_game(user['id'], 'rock', 'paper', 'lose')
            test_db.update_stats(user['id'], 'lose')

        # 2回引き分け
        for _ in range(2):
            test_db.save_game(user['id'], 'rock', 'rock', 'draw')
            test_db.update_stats(user['id'], 'draw')

        # 統計取得
        stats = test_db.get_stats(user['id'])

        assert stats['total_games'] == 10
        assert stats['wins'] == 5
        assert stats['losses'] == 3
        assert stats['draws'] == 2
        assert stats['win_rate'] == 50.0  # 5/10 * 100


class TestHistory:
    """履歴取得テスト"""

    def test_history_retrieval(self, test_db):
        """履歴取得テスト"""
        test_db.register_user("test_user1")
        user = test_db.get_user("test_user1")

        # 5回プレイ
        for _ in range(5):
            test_db.save_game(user['id'], 'rock', 'scissors', 'win')

        # 履歴取得（最新3件）
        history = test_db.get_history(user['id'], limit=3)

        assert len(history) == 3
        assert all(item['user_choice'] == 'rock' for item in history)
        assert all(item['computer_choice'] == 'scissors' for item in history)


class TestRanking:
    """ランキングテスト"""

    def test_ranking(self, test_db):
        """ランキングテスト"""
        # 3人のユーザー登録
        users = []
        for i in range(1, 4):
            test_db.register_user(f"user{i}")
            user = test_db.get_user(f"user{i}")
            users.append(user)

        # user1: 3勝0敗 (勝率100%)
        for _ in range(3):
            test_db.save_game(users[0]['id'], 'rock', 'scissors', 'win')
            test_db.update_stats(users[0]['id'], 'win')

        # user2: 5勝5敗 (勝率50%)
        for _ in range(5):
            test_db.save_game(users[1]['id'], 'rock', 'scissors', 'win')
            test_db.update_stats(users[1]['id'], 'win')
        for _ in range(5):
            test_db.save_game(users[1]['id'], 'rock', 'paper', 'lose')
            test_db.update_stats(users[1]['id'], 'lose')

        # user3: 1勝9敗 (勝率10%)
        for _ in range(1):
            test_db.save_game(users[2]['id'], 'rock', 'scissors', 'win')
            test_db.update_stats(users[2]['id'], 'win')
        for _ in range(9):
            test_db.save_game(users[2]['id'], 'rock', 'paper', 'lose')
            test_db.update_stats(users[2]['id'], 'lose')

        # ランキング取得
        ranking = test_db.get_ranking(limit=3)

        assert len(ranking) == 3
        assert ranking[0]['username'] == 'user1'  # 勝率100%
        assert ranking[1]['username'] == 'user2'  # 勝率50%
        assert ranking[2]['username'] == 'user3'  # 勝率10%


class TestFullGameFlow:
    """統合テスト"""

    def test_full_game_flow(self, test_db):
        """全体フロー統合テスト（登録→プレイ→統計確認）"""
        # 1. ユーザー登録
        success, message = test_db.register_user("integration_user")
        assert success is True

        # 2. ユーザー取得
        user = test_db.get_user("integration_user")
        assert user is not None

        # 3. ゲームプレイ
        success, message = JankenGame.play(test_db, "integration_user", "rock")
        assert success is True

        # 4. 統計確認
        stats = test_db.get_stats(user['id'])
        assert stats['total_games'] == 1
        assert stats['wins'] + stats['losses'] + stats['draws'] == 1

        # 5. 履歴確認
        history = test_db.get_history(user['id'], limit=10)
        assert len(history) == 1

    def test_multiple_games(self, test_db):
        """複数ゲームプレイテスト"""
        test_db.register_user("multi_user")

        # 10回プレイ
        for _ in range(10):
            JankenGame.play(test_db, "multi_user", "rock")

        user = test_db.get_user("multi_user")
        stats = test_db.get_stats(user['id'])

        assert stats['total_games'] == 10

    def test_multiple_users(self, test_db):
        """複数ユーザー対応テスト"""
        # 5人のユーザー登録
        for i in range(1, 6):
            test_db.register_user(f"user{i}")
            JankenGame.play(test_db, f"user{i}", "rock")

        # ランキング確認
        ranking = test_db.get_ranking(limit=5)
        assert len(ranking) == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
