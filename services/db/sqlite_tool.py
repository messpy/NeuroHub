#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import sys
from pathlib import Path

from services.db.sqlite_craud import (
    SQLiteCRAUD, DEFAULT_SCHEMA, DEFAULT_INDICES
)

def read_text_or_stdin(path_or_dash: str) -> str:
    if path_or_dash in ("-", "", None):
        return sys.stdin.read()
    return Path(path_or_dash).read_text(encoding="utf-8")

def main():
    ap = argparse.ArgumentParser(description="NeuroHub SQLite Utility (extended)")
    ap.add_argument("db_path", nargs="?", default="./neurohub_llm.db", help="DB path (default: ./neurohub_llm.db)")

    sub = ap.add_subparsers(dest="cmd")

    # init
    p = sub.add_parser("init", help="Create tables and indices")
    p.add_argument("--schema-json", help="Schema JSON file (optional)")
    p.add_argument("--indices-json", help="Indices JSON file (optional)")

    # list/describe
    sub.add_parser("tables", help="List tables")
    p = sub.add_parser("describe", help="Describe table columns")
    p.add_argument("table")

    # select/count/sql
    p = sub.add_parser("select", help="Select rows")
    p.add_argument("table")
    p.add_argument("--where", help='JSON dict or "-" for stdin')
    p.add_argument("--columns", help="Comma-separated columns")
    p.add_argument("--order", help="ORDER BY")
    p.add_argument("--limit", type=int)
    p.add_argument("--offset", type=int)
    p.add_argument("--pretty", action="store_true")

    p = sub.add_parser("count", help="Count rows")
    p.add_argument("table")
    p.add_argument("--where", help='JSON dict or "-" for stdin')

    p = sub.add_parser("sql", help="Execute raw SQL")
    p.add_argument("--query", help='SQL string or "-" for stdin')
    p.add_argument("--params", help='Params as JSON list')

    # insert/upsert/update/delete
    p = sub.add_parser("insert", help="Insert one or many (JSON or JSONL)")
    p.add_argument("table")
    p.add_argument("--data", help='JSON object or "-" (stdin)')
    p.add_argument("--jsonl", help='Path or "-" (stdin) for JSONL bulk')
    p.add_argument("--csv", help='CSV path or "-" (stdin) for bulk')

    p = sub.add_parser("upsert", help="Upsert one or many (need --on cols)")
    p.add_argument("table")
    p.add_argument("--on", required=True, help="Comma-separated conflict cols")
    p.add_argument("--data", help='JSON object or "-" (stdin)')
    p.add_argument("--jsonl", help='Path or "-" (stdin) for JSONL bulk')
    p.add_argument("--csv", help='CSV path or "-" (stdin) for bulk')

    p = sub.add_parser("update", help="Update where")
    p.add_argument("table")
    p.add_argument("--data", required=True, help='JSON object or "-" (stdin)')
    p.add_argument("--where", help='JSON dict or "-" for stdin')

    p = sub.add_parser("delete", help="Delete where")
    p.add_argument("table")
    p.add_argument("--where", help='JSON dict or "-" for stdin')

    # export/import
    p = sub.add_parser("export", help="Export table")
    p.add_argument("table")
    p.add_argument("--where", help='JSON dict or "-" for stdin')
    p.add_argument("--columns", help="Comma-separated columns")
    p.add_argument("--format", choices=["jsonl", "csv"], default="jsonl")

    p = sub.add_parser("import", help="Import into table")
    p.add_argument("table")
    p.add_argument("--format", choices=["jsonl", "csv"], required=True)
    p.add_argument("--file", required=True, help='Path or "-" for stdin')
    p.add_argument("--on", help="Comma-separated upsert conflict cols")

    # fts
    p = sub.add_parser("fts-search", help="FTS search on artifacts_fts")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("fts-rebuild", help="FTS rebuild")

    # maintenance
    sub.add_parser("vacuum", help="VACUUM")
    sub.add_parser("analyze", help="ANALYZE")

    # reports
    p = sub.add_parser("report", help="Canned reports")
    p.add_argument("name", choices=["calls_summary", "errors_recent", "model_top"])
    p.add_argument("--limit", type=int, default=10)

    args = ap.parse_args()
    db = SQLiteCRAUD(args.db_path)

    # dispatch
    if args.cmd == "init":
        schema = DEFAULT_SCHEMA
        indices = DEFAULT_INDICES
        if args.schema_json:
            schema = json.loads(Path(args.schema_json).read_text(encoding="utf-8"))
        if args.indices_json:
            indices = json.loads(Path(args.indices_json).read_text(encoding="utf-8"))
        db.create_tables(schema, indices)
        print(f"[OK] initialized: {args.db_path}")
        return

    if args.cmd == "tables":
        rows = db.execute_sql("SELECT name FROM sqlite_master WHERE type IN ('table','view') ORDER BY name")
        print(json.dumps([r["name"] for r in rows], ensure_ascii=False, indent=2))
        return

    if args.cmd == "describe":
        sql = f"PRAGMA table_info({args.table})"
        rows = db.execute_sql(sql)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    if args.cmd == "select":
        where = None
        if args.where:
            where_text = read_text_or_stdin(args.where) if args.where == "-" else args.where
            where = json.loads(where_text)
        cols = args.columns.split(",") if args.columns else None
        rows = db.select_where(args.table, where=where, order_by=args.order, limit=args.limit, offset=args.offset, columns=cols)
        print(json.dumps(rows, ensure_ascii=False, indent=2 if args.pretty else None))
        return

    if args.cmd == "count":
        where = None
        if args.where:
            where_text = read_text_or_stdin(args.where) if args.where == "-" else args.where
            where = json.loads(where_text)
        print(db.count(args.table, where))
        return

    if args.cmd == "sql":
        q = read_text_or_stdin(args.query) if args.query == "-" else (args.query or sys.stdin.read())
        params = json.loads(args.params) if args.params else []
        rows = db.execute_sql(q, params)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    if args.cmd == "insert":
        if args.data:
            obj = json.loads(read_text_or_stdin(args.data) if args.data == "-" else args.data)
            print(db.insert(args.table, obj))
            return
        if args.jsonl:
            txt = read_text_or_stdin(args.jsonl)
            print(db.import_jsonl(args.table, txt))
            return
        if args.csv:
            txt = read_text_or_stdin(args.csv)
            print(db.import_csv(args.table, txt))
            return
        ap.error("insert: --data or --jsonl or --csv is required")

    if args.cmd == "upsert":
        on = [c.strip() for c in args.on.split(",") if c.strip()]
        if args.data:
            obj = json.loads(read_text_or_stdin(args.data) if args.data == "-" else args.data)
            print(db.upsert(args.table, obj, on))
            return
        if args.jsonl:
            txt = read_text_or_stdin(args.jsonl)
            print(db.import_jsonl(args.table, txt, upsert_on=on))
            return
        if args.csv:
            txt = read_text_or_stdin(args.csv)
            print(db.import_csv(args.table, txt, upsert_on=on))
            return
        ap.error("upsert: one of --data/--jsonl/--csv is required")

    if args.cmd == "update":
        data = json.loads(read_text_or_stdin(args.data) if args.data == "-" else args.data)
        where = None
        if args.where:
            where = json.loads(read_text_or_stdin(args.where) if args.where == "-" else args.where)
        print(db.update_where(args.table, data, where))
        return

    if args.cmd == "delete":
        where = None
        if args.where:
            where = json.loads(read_text_or_stdin(args.where) if args.where == "-" else args.where)
        print(db.delete_where(args.table, where))
        return

    if args.cmd == "export":
        where = None
        if args.where:
            where = json.loads(read_text_or_stdin(args.where) if args.where == "-" else args.where)
        cols = args.columns.split(",") if args.columns else None
        if args.format == "jsonl":
            print(db.export_jsonl(args.table, where=where, columns=cols), end="")
        else:
            print(db.export_csv(args.table, where=where, columns=cols), end="")
        return

    if args.cmd == "import":
        txt = read_text_or_stdin(args.file)
        on = [c.strip() for c in (args.on or "").split(",") if c.strip()] or None
        if args.format == "jsonl":
            print(db.import_jsonl(args.table, txt, upsert_on=on))
        else:
            print(db.import_csv(args.table, txt, upsert_on=on))
        return

    if args.cmd == "fts-search":
        rows = db.fts_search(args.query, limit=args.limit)
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return

    if args.cmd == "fts-rebuild":
        db.fts_rebuild()
        print("[OK] FTS rebuild requested")
        return

    if args.cmd == "vacuum":
        db.vacuum()
        print("[OK] VACUUM")
        return

    if args.cmd == "analyze":
        db.analyze()
        print("[OK] ANALYZE")
        return

    if args.cmd == "report":
        if args.name == "calls_summary":
            q = """
            SELECT provider_id, model_id,
                   COUNT(*) AS calls,
                   SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END) AS ok_calls,
                   ROUND(AVG(latency_ms),1) AS avg_ms,
                   SUM(total_tokens) AS sum_tokens,
                   SUM(cost_micro) AS sum_cost_micro,
                   MAX(created_at) AS last_call
            FROM llm_calls
            GROUP BY provider_id, model_id
            ORDER BY ok_calls DESC, sum_tokens DESC
            LIMIT ?
            """
            rows = db.execute_sql(q, (args.limit,))
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return
        if args.name == "errors_recent":
            q = """
            SELECT id, provider_id, model_id, http_status, status, error_code, error_message_short, created_at
            FROM llm_calls
            WHERE status!='ok'
            ORDER BY created_at DESC
            LIMIT ?
            """
            rows = db.execute_sql(q, (args.limit,))
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return
        if args.name == "model_top":
            q = """
            SELECT model_id,
                   COUNT(*) AS calls,
                   SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END) AS ok_calls,
                   ROUND(100.0*SUM(CASE WHEN status='ok' THEN 1 ELSE 0 END)/COUNT(*),2) AS ok_rate,
                   ROUND(AVG(latency_ms),1) AS avg_ms,
                   SUM(total_tokens) AS sum_tokens
            FROM llm_calls
            GROUP BY model_id
            ORDER BY ok_rate DESC, calls DESC
            LIMIT ?
            """
            rows = db.execute_sql(q, (args.limit,))
            print(json.dumps(rows, ensure_ascii=False, indent=2))
            return
        print("unknown report")
        return

    ap.print_help()

if __name__ == "__main__":
    main()
