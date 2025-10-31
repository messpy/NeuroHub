#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM実行履歴とデバッグ情報のDBスキーマ定義
"""

# LLM実行履歴テーブル
LLM_HISTORY_SCHEMA = {
    "llm_history": """
    CREATE TABLE IF NOT EXISTS llm_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        session_id TEXT,
        provider TEXT NOT NULL,  -- 'gemini', 'huggingface', 'ollama'
        model TEXT NOT NULL,
        request_type TEXT,       -- 'commit_message', 'code_generation', 'chat'
        prompt_text TEXT,
        response_text TEXT,
        status_code INTEGER,
        success BOOLEAN,
        error_message TEXT,
        response_time_ms INTEGER,
        token_count_input INTEGER,
        token_count_output INTEGER,
        token_count_total INTEGER,
        debug_level INTEGER DEFAULT 1,  -- 0-3のデバッグレベル
        debug_info TEXT,         -- JSON形式の詳細デバッグ情報
        metadata TEXT,           -- JSON形式の追加メタデータ
        user_context TEXT,       -- 実行時のコンテキスト情報
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,

    "command_history": """
    CREATE TABLE IF NOT EXISTS command_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        session_id TEXT,
        command_line TEXT NOT NULL,
        working_directory TEXT,
        exit_code INTEGER,
        stdout_text TEXT,
        stderr_text TEXT,
        execution_time_ms INTEGER,
        user_id TEXT,
        context_info TEXT,       -- JSON形式
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,

    "llm_sessions": """
    CREATE TABLE IF NOT EXISTS llm_sessions (
        session_id TEXT PRIMARY KEY,
        start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        end_time DATETIME,
        session_type TEXT,       -- 'interactive', 'batch', 'git_commit'
        total_requests INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        success_rate REAL,
        user_id TEXT,
        metadata TEXT,           -- JSON形式
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """
}

# インデックス定義
LLM_HISTORY_INDICES = {
    "llm_history": [
        "CREATE INDEX IF NOT EXISTS idx_llm_history_timestamp ON llm_history(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_llm_history_provider ON llm_history(provider)",
        "CREATE INDEX IF NOT EXISTS idx_llm_history_session ON llm_history(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_llm_history_success ON llm_history(success)",
        "CREATE INDEX IF NOT EXISTS idx_llm_history_debug ON llm_history(debug_level)",
    ],
    "command_history": [
        "CREATE INDEX IF NOT EXISTS idx_command_history_timestamp ON command_history(timestamp)",
        "CREATE INDEX IF NOT EXISTS idx_command_history_session ON command_history(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_command_history_exit_code ON command_history(exit_code)",
    ],
    "llm_sessions": [
        "CREATE INDEX IF NOT EXISTS idx_llm_sessions_start_time ON llm_sessions(start_time)",
        "CREATE INDEX IF NOT EXISTS idx_llm_sessions_type ON llm_sessions(session_type)",
    ]
}

# FTS5 全文検索テーブル
LLM_FTS_SCHEMA = {
    "llm_history_fts": """
    CREATE VIRTUAL TABLE IF NOT EXISTS llm_history_fts USING fts5(
        prompt_text,
        response_text,
        error_message,
        content='llm_history',
        content_rowid='id'
    )
    """,
    "command_history_fts": """
    CREATE VIRTUAL TABLE IF NOT EXISTS command_history_fts USING fts5(
        command_line,
        stdout_text,
        stderr_text,
        content='command_history',
        content_rowid='id'
    )
    """
}
