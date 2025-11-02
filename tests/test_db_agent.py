#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Database Agent テスト
"""

import pytest
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.db_agent import DatabaseAgent, DBQueryResult


@pytest.fixture
def test_db_path(tmp_path):
    """テスト用データベースパス"""
    return str(tmp_path / "test.db")


@pytest.fixture
def db_agent(test_db_path, tmp_path):
    """DBエージェント"""
    # MCP用ヒントDBもtmp_pathに作成
    agent = DatabaseAgent(default_db=test_db_path)
    agent.mcp_hints_db = str(tmp_path / "mcp_hints_test.db")
    agent._init_mcp_hints_db()  # 再初期化
    return agent


class TestDatabaseAgent:
    """DatabaseAgent基本機能テスト"""
    
    def test_init(self, db_agent):
        """初期化テスト"""
        assert db_agent is not None
        assert db_agent.default_db is not None
        assert db_agent.mcp_hints_db is not None
    
    def test_get_db(self, db_agent, test_db_path):
        """DB接続取得テスト"""
        db = db_agent.get_db(test_db_path)
        assert db is not None
        
        # 2回目は同じインスタンス（キャッシュ）
        db2 = db_agent.get_db(test_db_path)
        assert db is db2
    
    def test_execute_query(self, db_agent, test_db_path):
        """クエリ実行テスト"""
        # テーブル作成
        result = db_agent.execute_query(
            test_db_path,
            "CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)"
        )
        assert result.success is True
        
        # データ挿入
        result = db_agent.execute_query(
            test_db_path,
            "INSERT INTO test (name) VALUES (?)",
            ("test_name",)
        )
        assert result.success is True
        
        # データ取得
        result = db_agent.execute_query(
            test_db_path,
            "SELECT * FROM test"
        )
        assert result.success is True
        assert result.row_count == 1
        assert result.data[0]['name'] == 'test_name'
    
    def test_list_tables(self, db_agent, test_db_path):
        """テーブル一覧取得テスト"""
        # テーブル作成
        db_agent.execute_query(test_db_path, "CREATE TABLE table1 (id INTEGER)")
        db_agent.execute_query(test_db_path, "CREATE TABLE table2 (id INTEGER)")
        
        # 一覧取得
        tables = db_agent.list_tables(test_db_path)
        assert 'table1' in tables
        assert 'table2' in tables
    
    def test_get_table_schema(self, db_agent, test_db_path):
        """スキーマ取得テスト"""
        # テーブル作成
        db_agent.execute_query(
            test_db_path,
            """CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        
        # スキーマ取得
        schema = db_agent.get_table_schema(test_db_path, 'users')
        assert schema is not None
        assert schema['table_name'] == 'users'
        assert 'CREATE TABLE users' in schema['schema_sql']
        assert len(schema['columns']) == 4
        
        # カラム名確認
        col_names = [col['name'] for col in schema['columns']]
        assert 'id' in col_names
        assert 'username' in col_names


class TestMCPHints:
    """MCPヒント機能テスト"""
    
    def test_add_hint(self, db_agent):
        """ヒント追加テスト"""
        success = db_agent.add_mcp_hint(
            category='database',
            keyword='SQLite CRUD',
            hint_text='SQLiteCRAUDクラスを使用してデータベース操作を行う',
            example_code='db = SQLiteCRAUD("test.db")',
            tags='database,sqlite,crud',
            priority=10
        )
        assert success is True
    
    def test_search_hints_by_keyword(self, db_agent):
        """キーワード検索テスト"""
        # ヒント追加
        db_agent.add_mcp_hint('database', 'SQLite', 'SQLiteを使う', priority=5)
        db_agent.add_mcp_hint('web', 'API', 'APIを作る', priority=3)
        
        # 検索
        results = db_agent.search_hints(keyword='SQLite')
        assert len(results) >= 1
        assert any('SQLite' in r['keyword'] for r in results)
    
    def test_search_hints_by_category(self, db_agent):
        """カテゴリ検索テスト"""
        # ヒント追加
        db_agent.add_mcp_hint('database', 'test1', 'hint1')
        db_agent.add_mcp_hint('database', 'test2', 'hint2')
        db_agent.add_mcp_hint('web', 'test3', 'hint3')
        
        # カテゴリ検索
        results = db_agent.search_hints(category='database')
        assert len(results) >= 2
        assert all(r['category'] == 'database' for r in results)
    
    def test_search_hints_priority_order(self, db_agent):
        """優先度順ソートテスト"""
        # 異なる優先度でヒント追加
        db_agent.add_mcp_hint('test', 'low', 'low priority', priority=1)
        db_agent.add_mcp_hint('test', 'high', 'high priority', priority=10)
        db_agent.add_mcp_hint('test', 'medium', 'medium priority', priority=5)
        
        # 検索
        results = db_agent.search_hints(category='test')
        assert len(results) >= 3
        
        # 優先度順にソートされているか確認
        priorities = [r['priority'] for r in results[:3]]
        assert priorities == sorted(priorities, reverse=True)


class TestCodeSnippets:
    """コードスニペット機能テスト"""
    
    def test_add_snippet(self, db_agent):
        """スニペット追加テスト"""
        success = db_agent.add_code_snippet(
            name='test_snippet',
            code='print("Hello, World!")',
            description='テストスニペット',
            category='example',
            tags='test,example'
        )
        assert success is True
    
    def test_get_snippet(self, db_agent):
        """スニペット取得テスト"""
        # ユニークな名前で追加
        snippet_name = 'hello_world_unique'
        db_agent.add_code_snippet(
            name=snippet_name,
            code='print("Hello")',
            description='Hello World'
        )
        
        # 取得（usage_countが1増える）
        snippet = db_agent.get_code_snippet(snippet_name)
        assert snippet is not None
        assert snippet['name'] == snippet_name
        assert snippet['code'] == 'print("Hello")'
        assert snippet['usage_count'] == 1  # 初回取得で1
        
        # 2回目取得（usage_count増加確認）
        snippet2 = db_agent.get_code_snippet(snippet_name)
        assert snippet2['usage_count'] == 2  # 2回目で2
    
    def test_snippet_upsert(self, db_agent):
        """スニペット更新テスト"""
        # 初回追加
        db_agent.add_code_snippet('test', 'code1', 'desc1')
        
        # 同じ名前で再追加（更新）
        db_agent.add_code_snippet('test', 'code2', 'desc2')
        
        # 取得
        snippet = db_agent.get_code_snippet('test')
        assert snippet['code'] == 'code2'
        assert snippet['description'] == 'desc2'


class TestSchemaRegistration:
    """スキーマ登録機能テスト"""
    
    def test_register_schema(self, db_agent, test_db_path):
        """スキーマ登録テスト"""
        # テーブル作成
        db_agent.execute_query(
            test_db_path,
            """CREATE TABLE products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL,
                stock INTEGER DEFAULT 0
            )"""
        )
        
        # データ挿入
        db_agent.execute_query(
            test_db_path,
            "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)",
            ("Product A", 1000.0, 10)
        )
        
        # スキーマ登録
        success = db_agent.register_db_schema(test_db_path, 'products')
        assert success is True
    
    def test_get_registered_schemas(self, db_agent, test_db_path):
        """登録済みスキーマ取得テスト"""
        # テーブル作成・登録
        db_agent.execute_query(test_db_path, "CREATE TABLE test1 (id INTEGER)")
        db_agent.execute_query(test_db_path, "CREATE TABLE test2 (id INTEGER)")
        
        db_agent.register_db_schema(test_db_path, 'test1')
        db_agent.register_db_schema(test_db_path, 'test2')
        
        # 取得
        schemas = db_agent.get_registered_schemas(test_db_path)
        assert len(schemas) == 2
        
        table_names = [s['table_name'] for s in schemas]
        assert 'test1' in table_names
        assert 'test2' in table_names


class TestIntegration:
    """統合テスト"""
    
    def test_full_workflow(self, db_agent, test_db_path):
        """全体フロー統合テスト"""
        # 1. テーブル作成
        result = db_agent.execute_query(
            test_db_path,
            """CREATE TABLE tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        )
        assert result.success is True
        
        # 2. データ挿入
        for i in range(5):
            db_agent.execute_query(
                test_db_path,
                "INSERT INTO tasks (title, status) VALUES (?, ?)",
                (f"Task {i+1}", 'pending' if i < 3 else 'completed')
            )
        
        # 3. スキーマ登録
        success = db_agent.register_db_schema(test_db_path, 'tasks')
        assert success is True
        
        # 4. データ検索
        result = db_agent.execute_query(
            test_db_path,
            "SELECT * FROM tasks WHERE status = ?",
            ('pending',)
        )
        assert result.success is True
        assert result.row_count == 3
        
        # 5. スキーマ確認
        schemas = db_agent.get_registered_schemas(test_db_path)
        assert len(schemas) == 1
        assert schemas[0]['table_name'] == 'tasks'
        
        # 6. MCPヒント追加
        db_agent.add_mcp_hint(
            'database',
            'Task management',
            'Use tasks table to manage TODO items',
            example_code='SELECT * FROM tasks WHERE status = "pending"'
        )
        
        # 7. ヒント検索
        hints = db_agent.search_hints(keyword='Task')
        assert len(hints) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
