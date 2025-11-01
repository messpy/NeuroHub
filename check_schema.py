#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
テーブル構造確認スクリプト
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.db.database_manager import DatabaseManager

def check_table_structure():
    db = DatabaseManager()

    try:
        tables = ['users', 'related_questions', 'llm_history']

        for table in tables:
            print(f"\n📋 {table} テーブル構造:")
            schema = db.get_schema(table)
            columns = schema.get('columns', [])

            for col in columns:
                print(f"  - {col['name']}: {col['type']}")

    finally:
        db.close()

if __name__ == "__main__":
    check_table_structure()
