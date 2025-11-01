#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM実行履歴とデバッグ情報のDBスキーマ定義
"""

# LLM実行履歴テーブル
LLM_HISTORY_SCHEMA = {
    # 既存テーブル
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
    """,

    # 新規: ユーザー情報テーブル
    "users": """
    CREATE TABLE IF NOT EXISTS users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE,
        full_name TEXT,
        preferred_provider TEXT DEFAULT 'ollama',  -- デフォルトプロバイダー
        provider_config TEXT,    -- JSON形式のプロバイダー設定
        settings TEXT,           -- JSON形式のユーザー設定
        api_keys TEXT,           -- JSON形式の暗号化されたAPIキー
        usage_stats TEXT,        -- JSON形式の使用統計
        last_login DATETIME,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """,

    # 新規: 知識データベーステーブル
    "knowledge_base": """
    CREATE TABLE IF NOT EXISTS knowledge_base (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        category TEXT,           -- 'code', 'docs', 'faq', 'tutorial'
        tags TEXT,               -- カンマ区切りのタグ
        source_type TEXT,        -- 'manual', 'auto', 'import'
        source_file TEXT,        -- 元ファイルパス
        language TEXT,           -- プログラミング言語
        relevance_score REAL,    -- 関連度スコア（0.0-1.0）
        usage_count INTEGER DEFAULT 0,
        user_id TEXT,
        is_public BOOLEAN DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
    """,

    # 新規: 関連質問テーブル
    "related_questions": """
    CREATE TABLE IF NOT EXISTS related_questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_id INTEGER,
        question TEXT NOT NULL,
        answer TEXT,
        question_type TEXT,      -- 'common', 'troubleshooting', 'howto'
        difficulty_level INTEGER DEFAULT 1,  -- 1-5の難易度
        tags TEXT,               -- カンマ区切りのタグ
        usage_count INTEGER DEFAULT 0,
        user_id TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (knowledge_id) REFERENCES knowledge_base(id),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
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
    ],
    "users": [
        "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login)",
        "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
    ],
    "knowledge_base": [
        "CREATE INDEX IF NOT EXISTS idx_knowledge_title ON knowledge_base(title)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_category ON knowledge_base(category)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_tags ON knowledge_base(tags)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_language ON knowledge_base(language)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_relevance ON knowledge_base(relevance_score)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_user ON knowledge_base(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_knowledge_public ON knowledge_base(is_public)",
    ],
    "related_questions": [
        "CREATE INDEX IF NOT EXISTS idx_questions_knowledge ON related_questions(knowledge_id)",
        "CREATE INDEX IF NOT EXISTS idx_questions_type ON related_questions(question_type)",
        "CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON related_questions(difficulty_level)",
        "CREATE INDEX IF NOT EXISTS idx_questions_user ON related_questions(user_id)",
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
    """,
    "knowledge_base_fts": """
    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_base_fts USING fts5(
        title,
        content,
        tags,
        content='knowledge_base',
        content_rowid='id'
    )
    """,
    "related_questions_fts": """
    CREATE VIRTUAL TABLE IF NOT EXISTS related_questions_fts USING fts5(
        question,
        answer,
        tags,
        content='related_questions',
        content_rowid='id'
    )
    """
}
