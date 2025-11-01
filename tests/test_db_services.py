#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_db_services.py - データベース関連サービスのユニットテスト
"""

import pytest
import tempfile
import sqlite3
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from services.db.llm_history_manager import LLMHistoryManager
    from services.db.llm_history_schema import create_tables, get_schema_version
except ImportError as e:
    print(f"Import error: {e}")
    # フォールバック定義
    class LLMHistoryManager:
        def __init__(self, db_path=":memory:"):
            self.db_path = db_path

        def create_session(self):
            return "test_session_id"

        def end_session(self, session_id):
            pass

        def log_llm_request(self, session_id, provider, prompt, response, success, error=None):
            pass

        def search_history(self, query, limit=10):
            return []

    def create_tables(db_path):
        pass

    def get_schema_version(db_path):
        return "1.0"


class TestLLMHistorySchema:
    """LLM履歴スキーマのテストクラス"""

    @pytest.fixture
    def temp_db(self):
        """一時データベース"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        os.unlink(path)

    def test_create_tables_success(self, temp_db):
        """テーブル作成成功テスト"""
        conn = sqlite3.connect(temp_db)

        try:
            create_tables(conn)

            # テーブル存在確認
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            expected_tables = [
                'llm_sessions',
                'llm_history',
                'command_logs',
                'system_info'
            ]

            for table in expected_tables:
                assert table in tables, f"Table {table} not found"

        finally:
            conn.close()

    def test_get_schema_version(self, temp_db):
        """スキーマバージョン取得テスト"""
        conn = sqlite3.connect(temp_db)

        try:
            create_tables(conn)
            version = get_schema_version(conn)

            assert isinstance(version, str)
            assert len(version) > 0

        finally:
            conn.close()

    def test_fts_index_creation(self, temp_db):
        """FTS インデックス作成テスト"""
        conn = sqlite3.connect(temp_db)

        try:
            create_tables(conn)

            # FTSテーブル存在確認
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE name='llm_history_fts'")
            result = cursor.fetchone()

            assert result is not None, "FTS table not created"

        finally:
            conn.close()


class TestLLMHistoryManager:
    """LLM履歴マネージャーのテストクラス"""

    @pytest.fixture
    def temp_history_manager(self):
        """一時履歴マネージャー"""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            manager = LLMHistoryManager(db_path=db_path)
            yield manager
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_init(self, temp_history_manager):
        """初期化テスト"""
        assert hasattr(temp_history_manager, 'db_path')
        assert hasattr(temp_history_manager, 'current_session_id')
        assert temp_history_manager.db_path.exists()

    def test_create_session(self, temp_history_manager):
        """セッション作成テスト"""
        session_id = temp_history_manager.create_session("test_agent")

        assert session_id is not None
        assert len(session_id) > 0

        # データベース確認
        conn = sqlite3.connect(temp_history_manager.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM llm_sessions WHERE session_id = ?", (session_id,))
            session = cursor.fetchone()

            assert session is not None
            assert session[1] == session_id  # session_id カラム
            assert session[2] == "test_agent"  # agent_name カラム

        finally:
            conn.close()

    def test_end_session(self, temp_history_manager):
        """セッション終了テスト"""
        session_id = temp_history_manager.create_session("test_agent")

        success = temp_history_manager.end_session(session_id)
        assert success is True

        # データベース確認
        conn = sqlite3.connect(temp_history_manager.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT end_time FROM llm_sessions WHERE session_id = ?", (session_id,))
            end_time = cursor.fetchone()[0]

            assert end_time is not None

        finally:
            conn.close()

    def test_log_llm_request(self, temp_history_manager):
        """LLMリクエストログテスト"""
        session_id = temp_history_manager.create_session("test_agent")

        log_id = temp_history_manager.log_llm_request(
            session_id=session_id,
            provider="gemini",
            model="gemini-pro",
            prompt="Test prompt",
            response="Test response",
            is_success=True,
            response_time=1.5,
            token_usage={"input": 10, "output": 5},
            debug_info={"test": "info"}
        )

        assert log_id is not None
        assert log_id > 0

        # データベース確認
        conn = sqlite3.connect(temp_history_manager.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM llm_history WHERE id = ?", (log_id,))
            record = cursor.fetchone()

            assert record is not None
            assert record[2] == session_id  # session_id
            assert record[3] == "gemini"    # provider
            assert record[4] == "gemini-pro" # model
            assert record[5] == "Test prompt" # prompt

        finally:
            conn.close()

    def test_log_command_execution(self, temp_history_manager):
        """コマンド実行ログテスト"""
        log_id = temp_history_manager.log_command_execution(
            command="echo test",
            exit_code=0,
            duration=0.5,
            output_size=100,
            success=True,
            error_message=None
        )

        assert log_id is not None
        assert log_id > 0

        # データベース確認
        conn = sqlite3.connect(temp_history_manager.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM command_logs WHERE id = ?", (log_id,))
            record = cursor.fetchone()

            assert record is not None
            assert record[1] == "echo test"  # command
            assert record[2] == 0           # exit_code
            assert record[6] == 1           # success (1 = True)

        finally:
            conn.close()

    def test_search_history(self, temp_history_manager):
        """履歴検索テスト"""
        session_id = temp_history_manager.create_session("test_agent")

        # テストデータ挿入
        temp_history_manager.log_llm_request(
            session_id=session_id,
            provider="gemini",
            model="gemini-pro",
            prompt="Python コード生成してください",
            response="def hello(): print('Hello')",
            is_success=True
        )

        temp_history_manager.log_llm_request(
            session_id=session_id,
            provider="ollama",
            model="llama",
            prompt="JavaScript 関数作成",
            response="function test() { return 'test'; }",
            is_success=True
        )

        # 検索実行
        results = temp_history_manager.search_history("Python", limit=10)

        assert len(results) >= 1
        assert any("Python" in result[5] for result in results)  # prompt カラム

    def test_get_provider_stats(self, temp_history_manager):
        """プロバイダー統計テスト"""
        session_id = temp_history_manager.create_session("test_agent")

        # テストデータ挿入
        for i in range(5):
            temp_history_manager.log_llm_request(
                session_id=session_id,
                provider="gemini",
                model="gemini-pro",
                prompt=f"Test prompt {i}",
                response=f"Test response {i}",
                is_success=i < 4,  # 1つは失敗
                response_time=1.0 + i * 0.1
            )

        stats = temp_history_manager.get_provider_stats(days=1)

        assert len(stats) >= 1

        gemini_stats = next((s for s in stats if s['provider'] == 'gemini'), None)
        assert gemini_stats is not None
        assert gemini_stats['total_requests'] == 5
        assert gemini_stats['successful_requests'] == 4
        assert gemini_stats['avg_response_time'] > 0

    def test_get_session_summary(self, temp_history_manager):
        """セッション概要取得テスト"""
        session_id = temp_history_manager.create_session("test_agent")

        # テストデータ挿入
        temp_history_manager.log_llm_request(
            session_id=session_id,
            provider="gemini",
            model="gemini-pro",
            prompt="Test prompt",
            response="Test response",
            is_success=True,
            token_usage={"input": 10, "output": 5}
        )

        summary = temp_history_manager.get_session_summary(session_id)

        assert summary is not None
        assert summary['session_id'] == session_id
        assert summary['agent_name'] == "test_agent"
        assert summary['total_requests'] == 1
        assert summary['successful_requests'] == 1
        assert summary['total_tokens'] == 15

    def test_cleanup_old_sessions(self, temp_history_manager):
        """古いセッションクリーンアップテスト"""
        # 古いセッション作成（タイムスタンプを過去に設定）
        old_session = temp_history_manager.create_session("old_agent")

        # データベースで直接タイムスタンプを過去に更新
        conn = sqlite3.connect(temp_history_manager.db_path)
        try:
            old_timestamp = time.time() - (31 * 24 * 3600)  # 31日前
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE llm_sessions SET start_time = ? WHERE session_id = ?",
                (old_timestamp, old_session)
            )
            conn.commit()
        finally:
            conn.close()

        # 新しいセッション作成
        new_session = temp_history_manager.create_session("new_agent")

        # クリーンアップ実行（30日より古いものを削除）
        deleted_count = temp_history_manager.cleanup_old_sessions(days=30)

        assert deleted_count >= 1

        # 古いセッションが削除され、新しいセッションが残っていることを確認
        conn = sqlite3.connect(temp_history_manager.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id FROM llm_sessions")
            remaining_sessions = [row[0] for row in cursor.fetchall()]

            assert old_session not in remaining_sessions
            assert new_session in remaining_sessions

        finally:
            conn.close()

    def test_database_backup(self, temp_history_manager):
        """データベースバックアップテスト"""
        # テストデータ作成
        session_id = temp_history_manager.create_session("backup_test")
        temp_history_manager.log_llm_request(
            session_id=session_id,
            provider="gemini",
            model="gemini-pro",
            prompt="Backup test",
            response="Backup response",
            is_success=True
        )

        # バックアップ作成
        backup_path = temp_history_manager.create_backup()

        assert backup_path is not None
        assert backup_path.exists()
        assert backup_path.suffix == '.db'

        # バックアップファイルが正常なSQLiteデータベースであることを確認
        backup_conn = sqlite3.connect(backup_path)
        try:
            cursor = backup_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM llm_sessions")
            session_count = cursor.fetchone()[0]

            assert session_count >= 1

        finally:
            backup_conn.close()

        # バックアップファイル削除
        backup_path.unlink()


class TestDatabaseIntegration:
    """データベース統合テスト"""

    def test_full_workflow(self):
        """完全ワークフローテスト"""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)

        try:
            # 1. マネージャー初期化
            manager = LLMHistoryManager(db_path=db_path)

            # 2. セッション作成
            session_id = manager.create_session("integration_test")
            assert session_id is not None

            # 3. LLMリクエストログ
            log_id = manager.log_llm_request(
                session_id=session_id,
                provider="gemini",
                model="gemini-pro",
                prompt="統合テストプロンプト",
                response="統合テストレスポンス",
                is_success=True,
                response_time=2.0,
                token_usage={"input": 20, "output": 15}
            )
            assert log_id > 0

            # 4. コマンドログ
            cmd_id = manager.log_command_execution(
                command="git status",
                exit_code=0,
                duration=1.0,
                output_size=200,
                success=True
            )
            assert cmd_id > 0

            # 5. 検索
            search_results = manager.search_history("統合テスト")
            assert len(search_results) >= 1

            # 6. 統計
            stats = manager.get_provider_stats(days=1)
            assert len(stats) >= 1

            # 7. セッション概要
            summary = manager.get_session_summary(session_id)
            assert summary['total_requests'] == 1
            assert summary['successful_requests'] == 1

            # 8. セッション終了
            success = manager.end_session(session_id)
            assert success is True

        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
