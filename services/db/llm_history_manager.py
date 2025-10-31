#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM履歴管理とDB検索ツール
LLMが簡単にコマンドや履歴を検索できるインターフェース
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from .sqlite_craud import SQLiteCRAUD
from .llm_history_schema import LLM_HISTORY_SCHEMA, LLM_HISTORY_INDICES, LLM_FTS_SCHEMA


class LLMHistoryManager:
    """LLM実行履歴とコマンド履歴の管理クラス"""

    def __init__(self, db_path: str = "neurohub_llm.db"):
        self.db_path = db_path
        self.crud = SQLiteCRAUD(db_path)
        self.current_session_id = None
        self._init_db()

    def _init_db(self):
        """DBの初期化"""
        # スキーマとインデックスを作成
        self.crud.create_tables(LLM_HISTORY_SCHEMA, LLM_HISTORY_INDICES)
        self.crud.create_tables(LLM_FTS_SCHEMA)

    def start_session(self, session_type: str = "interactive", user_id: str = None) -> str:
        """新しいセッションを開始"""
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id

        self.crud.insert("llm_sessions", {
            "session_id": session_id,
            "session_type": session_type,
            "user_id": user_id,
            "start_time": datetime.now().isoformat()
        })

        return session_id

    def end_session(self, session_id: str = None):
        """セッションを終了"""
        if not session_id:
            session_id = self.current_session_id

        if session_id:
            # セッション統計を計算
            stats = self.get_session_stats(session_id)
            self.crud.update_where("llm_sessions",
                {"session_id": session_id},
                {
                    "end_time": datetime.now().isoformat(),
                    "total_requests": stats["total_requests"],
                    "total_tokens": stats["total_tokens"],
                    "success_rate": stats["success_rate"]
                }
            )

            if session_id == self.current_session_id:
                self.current_session_id = None

    def log_llm_request(self,
                       provider: str,
                       model: str,
                       prompt_text: str,
                       response_text: str = "",
                       status_code: int = 200,
                       success: bool = True,
                       error_message: str = None,
                       response_time_ms: int = None,
                       token_counts: Dict[str, int] = None,
                       debug_level: int = 1,
                       debug_info: Dict[str, Any] = None,
                       request_type: str = "general",
                       user_context: str = None) -> int:
        """LLMリクエストをログに記録"""

        token_counts = token_counts or {}
        debug_info = debug_info or {}

        data = {
            "session_id": self.current_session_id,
            "provider": provider,
            "model": model,
            "request_type": request_type,
            "prompt_text": prompt_text,
            "response_text": response_text,
            "status_code": status_code,
            "success": success,
            "error_message": error_message,
            "response_time_ms": response_time_ms,
            "token_count_input": token_counts.get("input"),
            "token_count_output": token_counts.get("output"),
            "token_count_total": token_counts.get("total"),
            "debug_level": debug_level,
            "debug_info": json.dumps(debug_info, ensure_ascii=False),
            "user_context": user_context,
            "timestamp": datetime.now().isoformat()
        }

        return self.crud.insert("llm_history", data)

    def log_command_execution(self,
                            command_line: str,
                            working_directory: str = None,
                            exit_code: int = None,
                            stdout_text: str = "",
                            stderr_text: str = "",
                            execution_time_ms: int = None,
                            user_id: str = None,
                            context_info: Dict[str, Any] = None) -> int:
        """コマンド実行履歴をログに記録"""

        data = {
            "session_id": self.current_session_id,
            "command_line": command_line,
            "working_directory": working_directory,
            "exit_code": exit_code,
            "stdout_text": stdout_text,
            "stderr_text": stderr_text,
            "execution_time_ms": execution_time_ms,
            "user_id": user_id,
            "context_info": json.dumps(context_info or {}, ensure_ascii=False),
            "timestamp": datetime.now().isoformat()
        }

        return self.crud.insert("command_history", data)

    def search_llm_history(self,
                          query: str = None,
                          provider: str = None,
                          success_only: bool = None,
                          debug_level: int = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        """LLM履歴を検索"""

        where_conditions = {}
        if provider:
            where_conditions["provider"] = provider
        if success_only is not None:
            where_conditions["success"] = success_only
        if debug_level is not None:
            where_conditions["debug_level"] = debug_level

        # 全文検索クエリがある場合
        if query:
            # FTS5テーブルで検索
            fts_sql = """
            SELECT llm_history.* FROM llm_history_fts
            JOIN llm_history ON llm_history.id = llm_history_fts.rowid
            WHERE llm_history_fts MATCH ?
            """
            params = [query]

            # 追加条件を適用
            if where_conditions:
                where_parts = []
                for k, v in where_conditions.items():
                    where_parts.append(f"llm_history.{k} = ?")
                    params.append(v)
                fts_sql += " AND " + " AND ".join(where_parts)

            fts_sql += " ORDER BY llm_history.timestamp DESC LIMIT ?"
            params.append(limit)

            return self.crud.execute_sql(fts_sql, params)
        else:
            # 通常の検索
            return self.crud.select_where(
                "llm_history",
                where_conditions,
                order="timestamp DESC",
                limit=limit
            )

    def search_command_history(self,
                             query: str = None,
                             exit_code: int = None,
                             limit: int = 50) -> List[Dict[str, Any]]:
        """コマンド履歴を検索"""

        where_conditions = {}
        if exit_code is not None:
            where_conditions["exit_code"] = exit_code

        if query:
            # FTS5テーブルで検索
            fts_sql = """
            SELECT command_history.* FROM command_history_fts
            JOIN command_history ON command_history.id = command_history_fts.rowid
            WHERE command_history_fts MATCH ?
            """
            params = [query]

            if where_conditions:
                where_parts = []
                for k, v in where_conditions.items():
                    where_parts.append(f"command_history.{k} = ?")
                    params.append(v)
                fts_sql += " AND " + " AND ".join(where_parts)

            fts_sql += " ORDER BY command_history.timestamp DESC LIMIT ?"
            params.append(limit)

            return self.crud.execute_sql(fts_sql, params)
        else:
            return self.crud.select_where(
                "command_history",
                where_conditions,
                order="timestamp DESC",
                limit=limit
            )

    def get_session_stats(self, session_id: str) -> Dict[str, Any]:
        """セッション統計を取得"""

        # リクエスト数と成功率
        total_requests = self.crud.count("llm_history", {"session_id": session_id})
        successful_requests = self.crud.count("llm_history", {
            "session_id": session_id,
            "success": True
        })

        success_rate = successful_requests / total_requests if total_requests > 0 else 0.0

        # トークン使用量
        token_sql = """
        SELECT SUM(token_count_total) as total_tokens,
               AVG(response_time_ms) as avg_response_time
        FROM llm_history
        WHERE session_id = ? AND token_count_total IS NOT NULL
        """
        token_stats = self.crud.execute_sql(token_sql, [session_id])
        total_tokens = token_stats[0]["total_tokens"] if token_stats else 0
        avg_response_time = token_stats[0]["avg_response_time"] if token_stats else 0

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "success_rate": success_rate,
            "total_tokens": total_tokens or 0,
            "avg_response_time": avg_response_time or 0
        }

    def get_provider_stats(self, days: int = 7) -> List[Dict[str, Any]]:
        """プロバイダー別統計を取得"""

        sql = """
        SELECT provider,
               COUNT(*) as total_requests,
               SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_requests,
               AVG(response_time_ms) as avg_response_time,
               SUM(token_count_total) as total_tokens
        FROM llm_history
        WHERE timestamp >= datetime('now', '-{} days')
        GROUP BY provider
        ORDER BY total_requests DESC
        """.format(days)

        return self.crud.execute_sql(sql)

    def export_session_report(self, session_id: str, format: str = "json") -> str:
        """セッションレポートを出力"""

        session_info = self.crud.select_where("llm_sessions", {"session_id": session_id})
        if not session_info:
            return "{}"

        session_info = session_info[0]
        stats = self.get_session_stats(session_id)
        llm_history = self.search_llm_history(limit=1000)  # セッション内全て
        command_history = self.search_command_history(limit=1000)

        report = {
            "session_info": dict(session_info),
            "statistics": stats,
            "llm_history": [dict(row) for row in llm_history],
            "command_history": [dict(row) for row in command_history]
        }

        if format == "json":
            return json.dumps(report, ensure_ascii=False, indent=2)
        else:
            return str(report)


# LLM用の簡単検索コマンド関数
def search_llm_logs(query: str, provider: str = None, limit: int = 10) -> str:
    """LLMが使いやすい検索関数"""
    manager = LLMHistoryManager()
    results = manager.search_llm_history(query, provider, limit=limit)

    if not results:
        return f"検索結果なし: '{query}'"

    output = []
    for i, row in enumerate(results, 1):
        output.append(f"{i}. [{row['provider']}] {row['timestamp']}")
        output.append(f"   プロンプト: {row['prompt_text'][:100]}...")
        output.append(f"   レスポンス: {row['response_text'][:100]}...")
        output.append(f"   成功: {'✅' if row['success'] else '❌'}")
        output.append("")

    return "\n".join(output)


def search_commands(query: str, limit: int = 10) -> str:
    """LLMが使いやすいコマンド検索関数"""
    manager = LLMHistoryManager()
    results = manager.search_command_history(query, limit=limit)

    if not results:
        return f"コマンド検索結果なし: '{query}'"

    output = []
    for i, row in enumerate(results, 1):
        output.append(f"{i}. {row['timestamp']}")
        output.append(f"   コマンド: {row['command_line']}")
        output.append(f"   終了コード: {row['exit_code']}")
        if row['stderr_text']:
            output.append(f"   エラー: {row['stderr_text'][:100]}...")
        output.append("")

    return "\n".join(output)
