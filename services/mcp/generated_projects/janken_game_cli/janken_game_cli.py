#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Janken Game CLI - じゃんけんゲームCLI

SQLiteデータベースを使用したじゃんけんゲームアプリケーション
"""

import sqlite3
import argparse
import random
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple


class DatabaseManager:
    """データベース操作クラス"""

    def __init__(self, db_path: str = "janken_game.db"):
        """
        初期化

        Args:
            db_path: データベースファイルパス
        """
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """データベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # usersテーブル作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # user_statsテーブル作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_stats (
                user_id INTEGER PRIMARY KEY REFERENCES users(id),
                total_games INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0,
                draws INTEGER DEFAULT 0,
                win_rate REAL DEFAULT 0.0
            )
        ''')

        # game_historyテーブル作成
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER REFERENCES users(id),
                user_choice TEXT NOT NULL,
                computer_choice TEXT NOT NULL,
                result TEXT NOT NULL,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        conn.commit()
        conn.close()

    def register_user(self, username: str) -> Tuple[bool, str]:
        """
        ユーザー登録

        Args:
            username: ユーザー名

        Returns:
            (成功フラグ, メッセージ)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("INSERT INTO users (username) VALUES (?)", (username,))
            user_id = cursor.lastrowid

            # 統計情報初期化
            cursor.execute("""
                INSERT INTO user_stats (user_id, total_games, wins, losses, draws, win_rate)
                VALUES (?, 0, 0, 0, 0, 0.0)
            """, (user_id,))

            conn.commit()
            conn.close()

            return True, f"ユーザー '{username}' を登録しました。"

        except sqlite3.IntegrityError:
            return False, f"エラー: ユーザー名 '{username}' は既に使用されています。"
        except Exception as e:
            return False, f"エラー: {str(e)}"

    def get_user(self, username: str) -> Optional[Dict]:
        """
        ユーザー取得

        Args:
            username: ユーザー名

        Returns:
            ユーザー情報辞書 or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, username, created_at FROM users WHERE username = ?
        """, (username,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'id': row[0],
                'username': row[1],
                'created_at': row[2]
            }
        return None

    def save_game(self, user_id: int, user_choice: str, computer_choice: str, result: str) -> bool:
        """
        ゲーム結果を保存

        Args:
            user_id: ユーザーID
            user_choice: ユーザーの選択
            computer_choice: コンピューターの選択
            result: 結果 ('win', 'lose', 'draw')

        Returns:
            成功フラグ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO game_history (user_id, user_choice, computer_choice, result)
                VALUES (?, ?, ?, ?)
            """, (user_id, user_choice, computer_choice, result))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"エラー: ゲーム保存失敗 - {str(e)}")
            return False

    def update_stats(self, user_id: int, result: str) -> bool:
        """
        統計情報更新

        Args:
            user_id: ユーザーID
            result: 結果 ('win', 'lose', 'draw')

        Returns:
            成功フラグ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 統計取得
            cursor.execute("""
                SELECT total_games, wins, losses, draws
                FROM user_stats WHERE user_id = ?
            """, (user_id,))

            row = cursor.fetchone()
            if not row:
                return False

            total_games, wins, losses, draws = row

            # 更新
            total_games += 1
            if result == 'win':
                wins += 1
            elif result == 'lose':
                losses += 1
            else:
                draws += 1

            win_rate = (wins / total_games) * 100 if total_games > 0 else 0.0

            cursor.execute("""
                UPDATE user_stats
                SET total_games = ?, wins = ?, losses = ?, draws = ?, win_rate = ?
                WHERE user_id = ?
            """, (total_games, wins, losses, draws, win_rate, user_id))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"エラー: 統計更新失敗 - {str(e)}")
            return False

    def get_stats(self, user_id: int) -> Optional[Dict]:
        """
        統計情報取得

        Args:
            user_id: ユーザーID

        Returns:
            統計情報辞書 or None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.username, s.total_games, s.wins, s.losses, s.draws, s.win_rate
            FROM users u
            JOIN user_stats s ON u.id = s.user_id
            WHERE u.id = ?
        """, (user_id,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                'username': row[0],
                'total_games': row[1],
                'wins': row[2],
                'losses': row[3],
                'draws': row[4],
                'win_rate': row[5]
            }
        return None

    def get_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        対戦履歴取得

        Args:
            user_id: ユーザーID
            limit: 取得件数

        Returns:
            履歴リスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT user_choice, computer_choice, result, played_at
            FROM game_history
            WHERE user_id = ?
            ORDER BY played_at DESC
            LIMIT ?
        """, (user_id, limit))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'user_choice': row[0],
                'computer_choice': row[1],
                'result': row[2],
                'played_at': row[3]
            }
            for row in rows
        ]

    def get_ranking(self, limit: int = 10) -> List[Dict]:
        """
        ランキング取得

        Args:
            limit: 取得件数

        Returns:
            ランキングリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT u.username, s.win_rate, s.wins, s.total_games
            FROM users u
            JOIN user_stats s ON u.id = s.user_id
            WHERE s.total_games > 0
            ORDER BY s.win_rate DESC, s.wins DESC
            LIMIT ?
        """, (limit,))

        rows = cursor.fetchall()
        conn.close()

        return [
            {
                'rank': idx + 1,
                'username': row[0],
                'win_rate': row[1],
                'wins': row[2],
                'total_games': row[3]
            }
            for idx, row in enumerate(rows)
        ]


class JankenGame:
    """じゃんけんゲームロジッククラス"""

    CHOICES = ['rock', 'paper', 'scissors']
    CHOICE_NAMES = {
        'rock': 'グー',
        'paper': 'パー',
        'scissors': 'チョキ'
    }

    @staticmethod
    def get_computer_choice() -> str:
        """コンピューターの手を取得"""
        return random.choice(JankenGame.CHOICES)

    @staticmethod
    def judge(user_choice: str, computer_choice: str) -> str:
        """
        勝敗判定

        Args:
            user_choice: ユーザーの選択
            computer_choice: コンピューターの選択

        Returns:
            結果 ('win', 'lose', 'draw')
        """
        if user_choice == computer_choice:
            return 'draw'

        win_conditions = {
            'rock': 'scissors',
            'scissors': 'paper',
            'paper': 'rock'
        }

        if win_conditions[user_choice] == computer_choice:
            return 'win'
        else:
            return 'lose'

    @staticmethod
    def play(db: DatabaseManager, username: str, user_choice: str) -> Tuple[bool, str]:
        """
        ゲーム実行

        Args:
            db: データベースマネージャー
            username: ユーザー名
            user_choice: ユーザーの選択

        Returns:
            (成功フラグ, メッセージ)
        """
        # 選択肢検証
        if user_choice not in JankenGame.CHOICES:
            return False, f"無効な選択です。{', '.join(JankenGame.CHOICES)} から選んでください。"

        # ユーザー存在確認
        user = db.get_user(username)
        if not user:
            return False, f"ユーザー '{username}' が見つかりません。register コマンドで登録してください。"

        # ゲーム実行
        computer_choice = JankenGame.get_computer_choice()
        result = JankenGame.judge(user_choice, computer_choice)

        # 結果保存
        db.save_game(user['id'], user_choice, computer_choice, result)
        db.update_stats(user['id'], result)

        # 結果メッセージ
        result_messages = {
            'win': '🎉 勝ち！',
            'lose': '😢 負け...',
            'draw': '🤝 引き分け'
        }

        message = f"""
あなた: {JankenGame.CHOICE_NAMES[user_choice]} | コンピューター: {JankenGame.CHOICE_NAMES[computer_choice]}
結果: {result_messages[result]}
"""

        return True, message


class CLI:
    """CLIインターフェースクラス"""

    def __init__(self, db_path: str = "janken_game.db"):
        """初期化"""
        self.db = DatabaseManager(db_path)

    def register_command(self, args):
        """登録コマンド"""
        success, message = self.db.register_user(args.username)
        print(message)
        return 0 if success else 1

    def play_command(self, args):
        """プレイコマンド"""
        success, message = JankenGame.play(self.db, args.username, args.choice)
        print(message)
        return 0 if success else 1

    def stats_command(self, args):
        """統計コマンド"""
        user = self.db.get_user(args.username)
        if not user:
            print(f"ユーザー '{args.username}' が見つかりません。")
            return 1

        stats = self.db.get_stats(user['id'])
        if not stats:
            print("統計情報が見つかりません。")
            return 1

        print(f"\n=== {stats['username']} の統計 ===")
        print(f"総試合数: {stats['total_games']}")
        print(f"勝利: {stats['wins']}")
        print(f"敗北: {stats['losses']}")
        print(f"引き分け: {stats['draws']}")
        print(f"勝率: {stats['win_rate']:.1f}%\n")
        return 0

    def history_command(self, args):
        """履歴コマンド"""
        user = self.db.get_user(args.username)
        if not user:
            print(f"ユーザー '{args.username}' が見つかりません。")
            return 1

        history = self.db.get_history(user['id'], args.limit)
        if not history:
            print("対戦履歴がありません。")
            return 0

        print(f"\n=== {args.username} の対戦履歴 (最新{len(history)}件) ===")
        for item in history:
            result_emoji = {'win': '🎉', 'lose': '😢', 'draw': '🤝'}[item['result']]
            print(f"{result_emoji} {item['user_choice']} vs {item['computer_choice']} | {item['played_at']}")
        print()
        return 0

    def ranking_command(self, args):
        """ランキングコマンド"""
        ranking = self.db.get_ranking(args.limit)
        if not ranking:
            print("ランキングデータがありません。")
            return 0

        print(f"\n=== ランキング (上位{len(ranking)}名) ===")
        print(f"{'順位':<6}{'ユーザー名':<15}{'勝率':<10}{'勝利数':<8}{'総試合数':<8}")
        print("-" * 60)
        for entry in ranking:
            print(f"{entry['rank']:<6}{entry['username']:<15}{entry['win_rate']:.1f}%{entry['wins']:<8}{entry['total_games']:<8}")
        print()
        return 0


def main():
    """メイン実行"""
    parser = argparse.ArgumentParser(description="Janken Game CLI - じゃんけんゲーム")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # registerコマンド
    register_parser = subparsers.add_parser("register", help="新規ユーザー登録")
    register_parser.add_argument("--username", required=True, help="ユーザー名")

    # playコマンド
    play_parser = subparsers.add_parser("play", help="じゃんけん対戦")
    play_parser.add_argument("--username", required=True, help="ユーザー名")
    play_parser.add_argument("--choice", required=True, choices=JankenGame.CHOICES, help="手 (rock/paper/scissors)")

    # statsコマンド
    stats_parser = subparsers.add_parser("stats", help="統計情報表示")
    stats_parser.add_argument("--username", required=True, help="ユーザー名")

    # historyコマンド
    history_parser = subparsers.add_parser("history", help="対戦履歴表示")
    history_parser.add_argument("--username", required=True, help="ユーザー名")
    history_parser.add_argument("--limit", type=int, default=10, help="表示件数 (デフォルト: 10)")

    # rankingコマンド
    ranking_parser = subparsers.add_parser("ranking", help="ランキング表示")
    ranking_parser.add_argument("--limit", type=int, default=10, help="表示件数 (デフォルト: 10)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    cli = CLI()

    # コマンド実行
    command_map = {
        'register': cli.register_command,
        'play': cli.play_command,
        'stats': cli.stats_command,
        'history': cli.history_command,
        'ranking': cli.ranking_command
    }

    return command_map[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
