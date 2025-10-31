#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations
import csv
import io
import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

Row = Dict[str, Any]
Schema = Dict[str, str]                # {table_name: CREATE TABLE ...}
IndexDefs = Dict[str, Sequence[str]]   # {table_name: ["CREATE INDEX ...", ...]}

class SQLiteCRAUD:
    """
    汎用 CRAUD + α for SQLite:
      - create_tables(schema, indices)
      - insert / bulk_insert / upsert / bulk_upsert
      - select_where / get_by_id / count / execute_sql
      - update_where / delete_where
      - import_jsonl / export_jsonl / import_csv / export_csv
      - fts_insert / fts_rebuild / fts_search (FTS5)
      - vacuum / analyze
    すべてプレースホルダ実行。whereは dict または (sql, params)。
    """

    def __init__(self, db_path: str, pragmas: Optional[Mapping[str, Union[str, int]]] = None):
        self.db_path = db_path
        self.pragmas = dict(pragmas or {
            "journal_mode": "WAL",
            "synchronous": 1,
            "foreign_keys": 1,
            "temp_store": 2,
            "mmap_size": 50_000_000,
        })

    @contextmanager
    def connect(self):
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        try:
            for k, v in self.pragmas.items():
                con.execute(f"PRAGMA {k}={v};")
            yield con
            con.commit()
        finally:
            con.close()

    # ---------- Schema ----------
    def create_tables(self, schema: Schema, indices: Optional[IndexDefs] = None) -> None:
        with self.connect() as con:
            for _, ddl in schema.items():
                con.execute(ddl)
            for _, idx_list in (indices or {}).items():
                for idx in idx_list:
                    con.execute(idx)

    # ---------- Helpers ----------
    @staticmethod
    def _cols_vals(data: Mapping[str, Any]) -> Tuple[str, str, Tuple[Any, ...]]:
        cols = list(data.keys())
        placeholders = ", ".join(["?"] * len(cols))
        collist = ", ".join(cols)
        vals = tuple(data[c] for c in cols)
        return collist, placeholders, vals

    @staticmethod
    def _where_clause(where: Optional[Union[Mapping[str, Any], Tuple[str, Sequence[Any]]]]) -> Tuple[str, Tuple[Any, ...]]:
        if where is None:
            return "", tuple()
        if isinstance(where, tuple):
            sql, params = where
            return f" WHERE {sql}", tuple(params)
        parts = []
        params: List[Any] = []
        for k, v in where.items():
            if v is None:
                parts.append(f"{k} IS NULL")
            else:
                parts.append(f"{k} = ?")
                params.append(v)
        return (" WHERE " + " AND ".join(parts)) if parts else "", tuple(params)

    # ---------- Create ----------
    def insert(self, table: str, data: Mapping[str, Any]) -> int:
        cols, ph, vals = self._cols_vals(data)
        sql = f"INSERT INTO {table} ({cols}) VALUES ({ph})"
        with self.connect() as con:
            cur = con.execute(sql, vals)
            return int(cur.lastrowid)

    def bulk_insert(self, table: str, rows: Iterable[Mapping[str, Any]]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        cols = list(rows[0].keys())
        ph = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({ph})"
        vals = [tuple(r.get(c) for c in cols) for r in rows]
        with self.connect() as con:
            cur = con.executemany(sql, vals)
            return cur.rowcount or 0

    # ---------- Upsert ----------
    def upsert(self, table: str, data: Mapping[str, Any], conflict_cols: Sequence[str]) -> int:
        cols = list(data.keys())
        cols_str = ", ".join(cols)
        ph = ", ".join(["?"] * len(cols))
        update_set = ", ".join([f"{c}=excluded.{c}" for c in cols if c not in conflict_cols])
        conflict = ", ".join(conflict_cols)
        sql = (
            f"INSERT INTO {table} ({cols_str}) VALUES ({ph}) "
            f"ON CONFLICT({conflict}) DO UPDATE SET {update_set}"
        )
        with self.connect() as con:
            cur = con.execute(sql, tuple(data[c] for c in cols))
            return int(cur.lastrowid)

    def bulk_upsert(self, table: str, rows: Iterable[Mapping[str, Any]], conflict_cols: Sequence[str]) -> int:
        rows = list(rows)
        if not rows:
            return 0
        cols = list(rows[0].keys())
        cols_str = ", ".join(cols)
        ph = ", ".join(["?"] * len(cols))
        update_set = ", ".join([f"{c}=excluded.{c}" for c in cols if c not in conflict_cols])
        conflict = ", ".join(conflict_cols)
        sql = (
            f"INSERT INTO {table} ({cols_str}) VALUES ({ph}) "
            f"ON CONFLICT({conflict}) DO UPDATE SET {update_set}"
        )
        vals = [tuple(r.get(c) for c in cols) for r in rows]
        with self.connect() as con:
            cur = con.executemany(sql, vals)
            return cur.rowcount or 0

    # ---------- Read ----------
    def get_by_id(self, table: str, id_col: str, id_val: Any) -> Optional[Row]:
        sql = f"SELECT * FROM {table} WHERE {id_col} = ? LIMIT 1"
        with self.connect() as con:
            cur = con.execute(sql, (id_val,))
            row = cur.fetchone()
            return dict(row) if row else None

    def select_where(
        self,
        table: str,
        where: Optional[Union[Mapping[str, Any], Tuple[str, Sequence[Any]]]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        columns: Optional[Sequence[str]] = None,
    ) -> List[Row]:
        cols = ", ".join(columns) if columns else "*"
        wh, params = self._where_clause(where)
        ob = f" ORDER BY {order_by}" if order_by else ""
        lm = f" LIMIT {limit}" if limit else ""
        of = f" OFFSET {offset}" if offset else ""
        sql = f"SELECT {cols} FROM {table}{wh}{ob}{lm}{of}"
        with self.connect() as con:
            cur = con.execute(sql, params)
            return [dict(r) for r in cur.fetchall()]

    # ---------- Update ----------
    def update_where(self, table: str, data: Mapping[str, Any],
                     where: Optional[Union[Mapping[str, Any], Tuple[str, Sequence[Any]]]]) -> int:
        set_parts = []
        params: List[Any] = []
        for k, v in data.items():
            set_parts.append(f"{k} = ?")
            params.append(v)
        set_sql = ", ".join(set_parts)
        wh, wh_params = self._where_clause(where)
        sql = f"UPDATE {table} SET {set_sql}{wh}"
        with self.connect() as con:
            cur = con.execute(sql, tuple(params) + wh_params)
            return cur.rowcount or 0

    # ---------- Delete ----------
    def delete_where(self, table: str, where: Optional[Union[Mapping[str, Any], Tuple[str, Sequence[Any]]]]) -> int:
        wh, params = self._where_clause(where)
        sql = f"DELETE FROM {table}{wh}"
        with self.connect() as con:
            cur = con.execute(sql, params)
            return cur.rowcount or 0

    # ---------- Utility ----------
    def count(self, table: str, where: Optional[Union[Mapping[str, Any], Tuple[str, Sequence[Any]]]] = None) -> int:
        wh, params = self._where_clause(where)
        sql = f"SELECT COUNT(*) AS c FROM {table}{wh}"
        with self.connect() as con:
            cur = con.execute(sql, params)
            return int(cur.fetchone()["c"])

    def execute_sql(self, sql: str, params: Sequence[Any] = ()) -> List[Row]:
        with self.connect() as con:
            cur = con.execute(sql, params)
            try:
                return [dict(r) for r in cur.fetchall()]
            except sqlite3.ProgrammingError:
                return []

    # ---------- Import / Export ----------
    def import_jsonl(self, table: str, jsonl: str, upsert_on: Optional[Sequence[str]] = None) -> int:
        rows = []
        for line in io.StringIO(jsonl):
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
        if upsert_on:
            return self.bulk_upsert(table, rows, upsert_on)
        return self.bulk_insert(table, rows)

    def export_jsonl(self, table: str, where=None, columns: Optional[Sequence[str]] = None) -> str:
        out = io.StringIO()
        for r in self.select_where(table, where=where, columns=columns):
            out.write(json.dumps(r, ensure_ascii=False))
            out.write("\n")
        return out.getvalue()

    def import_csv(self, table: str, csv_text: str, upsert_on: Optional[Sequence[str]] = None) -> int:
        reader = csv.DictReader(io.StringIO(csv_text))
        rows = list(reader)
        if upsert_on:
            return self.bulk_upsert(table, rows, upsert_on)
        return self.bulk_insert(table, rows)

    def export_csv(self, table: str, where=None, columns: Optional[Sequence[str]] = None) -> str:
        rows = self.select_where(table, where=where, columns=columns)
        if not rows:
            return ""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
        return output.getvalue()

    # ---------- FTS5 helpers ----------
    def fts_insert(self, artifact_id: int, text: str) -> None:
        with self.connect() as con:
            con.execute("INSERT INTO artifacts_fts(artifact_id, text) VALUES (?, ?)", (artifact_id, text))

    def fts_rebuild(self) -> None:
        with self.connect() as con:
            con.execute("INSERT INTO artifacts_fts(artifacts_fts) VALUES ('rebuild')")

    def fts_search(self, query: str, limit: int = 20) -> List[Row]:
        sql = "SELECT artifact_id, snippet(artifacts_fts, 1, '[', ']', '…', 8) AS snippet FROM artifacts_fts WHERE artifacts_fts MATCH ? LIMIT ?"
        with self.connect() as con:
            cur = con.execute(sql, (query, limit))
            return [dict(r) for r in cur.fetchall()]

    # ---------- Maintenance ----------
    def vacuum(self):
        with self.connect() as con:
            con.execute("VACUUM")

    def analyze(self):
        with self.connect() as con:
            con.execute("ANALYZE")

# ---------------- Default schema ----------------
DEFAULT_SCHEMA: Schema = {
    "llm_providers": """
    CREATE TABLE IF NOT EXISTS llm_providers (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      base_url TEXT,
      enabled INTEGER NOT NULL DEFAULT 1,
      health_status TEXT NOT NULL DEFAULT 'ok',
      last_checked_at TEXT
    );
    """,
    "llm_models": """
    CREATE TABLE IF NOT EXISTS llm_models (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      provider_id INTEGER NOT NULL REFERENCES llm_providers(id) ON DELETE CASCADE,
      model_name TEXT NOT NULL,
      family TEXT,
      context_window INTEGER,
      modality TEXT,
      supports_tools INTEGER DEFAULT 0,
      supports_vision INTEGER DEFAULT 0,
      availability TEXT NOT NULL DEFAULT 'ok',
      default_params_json TEXT,
      models_extra_json TEXT,
      created_at TEXT DEFAULT (datetime('now')),
      model_params_b INTEGER,
      disk_size_mb INTEGER,
      vram_req_mb INTEGER,
      quant_default TEXT,
      UNIQUE(provider_id, model_name)
    );
    """,
    "llm_calls": """
    CREATE TABLE IF NOT EXISTS llm_calls (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      provider_id INTEGER NOT NULL REFERENCES llm_providers(id),
      model_id INTEGER NOT NULL REFERENCES llm_models(id),
      request_id TEXT,
      endpoint TEXT,
      started_at TEXT NOT NULL DEFAULT (datetime('now')),
      ended_at TEXT,
      latency_ms INTEGER,
      attempt INTEGER NOT NULL DEFAULT 1,
      retry_of_call_id INTEGER REFERENCES llm_calls(id),
      status TEXT NOT NULL,
      http_status INTEGER,
      error_code TEXT,
      error_message_short TEXT,
      is_retryable INTEGER,
      prompt_tokens INTEGER,
      completion_tokens INTEGER,
      total_tokens INTEGER,
      input_chars INTEGER,
      output_chars INTEGER,
      cost_micro INTEGER,
      temperature REAL,
      top_p REAL,
      top_k INTEGER,
      max_tokens INTEGER,
      seed INTEGER,
      stop_json TEXT,
      provider_extra_json TEXT,
      notes TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    "artifacts": """
    CREATE TABLE IF NOT EXISTS artifacts (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      kind TEXT NOT NULL,
      content_hash TEXT NOT NULL UNIQUE,
      mime TEXT,
      bytes_size INTEGER,
      store_path TEXT,
      ref_uri TEXT,
      created_at TEXT NOT NULL DEFAULT (datetime('now'))
    );
    """,
    "artifacts_fts": """
    CREATE VIRTUAL TABLE IF NOT EXISTS artifacts_fts USING fts5(
      artifact_id UNINDEXED,
      text
    );
    """,
    "model_tags": """
    CREATE TABLE IF NOT EXISTS model_tags (
      model_id INTEGER NOT NULL REFERENCES llm_models(id) ON DELETE CASCADE,
      tag TEXT NOT NULL,
      UNIQUE(model_id, tag)
    );
    """,
    "model_capabilities": """
    CREATE TABLE IF NOT EXISTS model_capabilities (
      model_id INTEGER NOT NULL REFERENCES llm_models(id) ON DELETE CASCADE,
      key TEXT NOT NULL,
      value TEXT,
      UNIQUE(model_id, key)
    );
    """
}

DEFAULT_INDICES: IndexDefs = {
    "llm_calls": [
        "CREATE INDEX IF NOT EXISTS idx_llm_calls_created ON llm_calls(created_at DESC)",
        "CREATE INDEX IF NOT EXISTS idx_llm_calls_status ON llm_calls(status)",
        "CREATE INDEX IF NOT EXISTS idx_llm_calls_provider_model ON llm_calls(provider_id, model_id)",
        "CREATE INDEX IF NOT EXISTS idx_llm_calls_http ON llm_calls(http_status)"
    ],
    "llm_models": [
        "CREATE INDEX IF NOT EXISTS idx_llm_models_avail ON llm_models(availability)",
        "CREATE INDEX IF NOT EXISTS idx_llm_models_family ON llm_models(family)"
    ],
    "model_tags": [
        "CREATE INDEX IF NOT EXISTS idx_model_tags_tag ON model_tags(tag)"
    ],
}
