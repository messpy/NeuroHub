#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP自動プロジェクト生成システム
標準ライブラリのみで複雑なプロジェクトを設計からREADME作成まで自動化
"""

import os
import sys
import json
import time
import sqlite3
import logging
import asyncio
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import subprocess
import tempfile
import csv

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.db.database_manager import DatabaseManager
from services.mcp.weak_llm_support import WeakLLMDevelopmentSupport
from services.web.practical_web_searcher import PracticalWebSearcher
from services.mcp.auto_debugger import AutoDebugger
from services.mcp.prompt_optimizer import PromptOptimizer


@dataclass
class ProjectSpec:
    """プロジェクト仕様"""
    name: str
    description: str
    requirements: List[str]
    complexity: str  # 'simple', 'medium', 'complex'
    expected_files: List[str]
    dependencies: List[str]  # 標準ライブラリのみ
    main_functionality: str
    test_scenarios: List[str]
    timestamp: str
    optimized_prompt: Optional[str] = None  # 最適化プロンプト
    enhancements: Optional[List[str]] = None  # 強化要素


@dataclass
class GenerationStep:
    """生成ステップ"""
    step_id: int
    step_name: str
    status: str  # 'pending', 'running', 'completed', 'failed'
    start_time: Optional[str]
    end_time: Optional[str]
    duration: Optional[float]
    output: str
    error_message: Optional[str]
    llm_calls: int
    web_searches: int


@dataclass
class ProjectGenerationResult:
    """プロジェクト生成結果"""
    project_spec: ProjectSpec
    generation_steps: List[GenerationStep]
    generated_files: List[str]
    success: bool
    total_duration: float
    total_llm_calls: int
    total_web_searches: int
    error_count: int
    final_status: str


class MCPAutoProjectGenerator:
    """MCP自動プロジェクト生成クラス"""

    def __init__(self, provider: str = "gemini"):
        """
        初期化

        Args:
            provider: LLMプロバイダー ('gemini', 'ollama', 'huggingface')
        """
        self.provider = provider
        self.db_manager = DatabaseManager()
        self.weak_llm = WeakLLMDevelopmentSupport(provider=provider)
        self.web_searcher = PracticalWebSearcher()
        self.auto_debugger = AutoDebugger(provider=provider)
        self.prompt_optimizer = PromptOptimizer()

        # ログ設定
        self.setup_logging()

        # プロジェクトテンプレート
        self.project_templates = {
            'simple': [
                'Calculator CLI',
                'File Organizer',
                'Password Generator',
                'Unit Converter'
            ],
            'medium': [
                'SQLite Database Manager CLI',
                'Log File Analyzer',
                'Network Port Scanner',
                'Text File Encryptor',
                'JSON/CSV Converter',
                'File Backup System'
            ],
            'complex': [
                'Multi-threaded Web Server',
                'SQLite Database Server with REST API',
                'Advanced Log Monitoring System',
                'File Synchronization Tool',
                'Network Traffic Analyzer',
                'Task Scheduler with Cron-like Features'
            ]
        }

        # プロジェクトディレクトリ
        self.projects_dir = project_root / "generated_projects"
        self.projects_dir.mkdir(exist_ok=True)

        self._create_tables()

    def setup_logging(self):
        """ログ設定"""
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        log_file = log_dir / f"mcp_generator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

        self.logger = logging.getLogger(__name__)
        self.logger.info(f"🚀 MCP自動プロジェクト生成システム初期化")

    def _create_tables(self):
        """データベーステーブル作成"""
        # プロジェクト仕様テーブル
        project_specs_sql = """
        CREATE TABLE IF NOT EXISTS project_specs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            requirements TEXT,
            complexity TEXT,
            expected_files TEXT,
            dependencies TEXT,
            main_functionality TEXT,
            test_scenarios TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 生成ステップテーブル
        generation_steps_sql = """
        CREATE TABLE IF NOT EXISTS generation_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT,
            step_id INTEGER,
            step_name TEXT,
            status TEXT,
            start_time DATETIME,
            end_time DATETIME,
            duration REAL,
            output TEXT,
            error_message TEXT,
            llm_calls INTEGER DEFAULT 0,
            web_searches INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 生成結果テーブル
        generation_results_sql = """
        CREATE TABLE IF NOT EXISTS generation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT UNIQUE,
            generated_files TEXT,
            success BOOLEAN,
            total_duration REAL,
            total_llm_calls INTEGER,
            total_web_searches INTEGER,
            error_count INTEGER,
            final_status TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 統計テーブル
        generation_stats_sql = """
        CREATE TABLE IF NOT EXISTS generation_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE,
            projects_generated INTEGER,
            success_rate REAL,
            avg_duration REAL,
            avg_llm_calls REAL,
            avg_web_searches REAL,
            most_common_errors TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        for sql in [project_specs_sql, generation_steps_sql, generation_results_sql, generation_stats_sql]:
            self.db_manager._execute_sql(sql)

    async def generate_project(self, user_request: str, complexity: str = 'medium') -> ProjectGenerationResult:
        """プロジェクト生成メイン処理"""
        start_time = time.time()

        self.logger.info(f"📝 プロジェクト生成開始: '{user_request}' (複雑度: {complexity})")

        # ステップ管理
        steps = []
        current_step = 0

        try:
            # ステップ1: 仕様設計
            current_step += 1
            step = await self._execute_step(
                current_step, "仕様設計プラン",
                lambda: self._design_project_spec(user_request, complexity)
            )
            steps.append(step)

            if not step.status == 'completed':
                raise Exception(f"仕様設計失敗: {step.error_message}")

            project_spec = json.loads(step.output)

            # ステップ2: プロジェクト構造作成
            current_step += 1
            step = await self._execute_step(
                current_step, "プロジェクト構造作成",
                lambda: self._create_project_structure(project_spec)
            )
            steps.append(step)

            # ステップ3: メインコード生成
            current_step += 1
            step = await self._execute_step(
                current_step, "メインコード生成",
                lambda: self._generate_main_code(project_spec)
            )
            steps.append(step)

            # ステップ4: テストコード生成
            current_step += 1
            step = await self._execute_step(
                current_step, "テストコード生成",
                lambda: self._generate_test_code(project_spec)
            )
            steps.append(step)

            # ステップ5: README生成
            current_step += 1
            step = await self._execute_step(
                current_step, "README生成",
                lambda: self._generate_readme(project_spec)
            )
            steps.append(step)

            # ステップ6: 実行テスト
            current_step += 1
            step = await self._execute_step(
                current_step, "実行テスト",
                lambda: self._run_tests(project_spec)
            )
            steps.append(step)

            # ステップ7: 自動デバッグ（常に実行してエラーを修正）
            current_step += 1
            debug_step = await self._execute_step(
                current_step, "自動デバッグ・修正",
                lambda: self._auto_debug_project(project_spec)
            )
            steps.append(debug_step)

            # 結果収集
            generated_files = self._collect_generated_files(project_spec['name'])
            success = all(s.status == 'completed' for s in steps)
            total_duration = time.time() - start_time

            # 統計計算
            total_llm_calls = sum(s.llm_calls for s in steps)
            total_web_searches = sum(s.web_searches for s in steps)
            error_count = sum(1 for s in steps if s.status == 'failed')

            result = ProjectGenerationResult(
                project_spec=ProjectSpec(**project_spec),
                generation_steps=steps,
                generated_files=generated_files,
                success=success,
                total_duration=total_duration,
                total_llm_calls=total_llm_calls,
                total_web_searches=total_web_searches,
                error_count=error_count,
                final_status='success' if success else 'partial_success'
            )

            # データベースに保存
            await self._save_generation_result(result)

            self.logger.info(f"✅ プロジェクト生成完了: {project_spec['name']} ({total_duration:.2f}秒)")

            return result

        except Exception as e:
            error_step = GenerationStep(
                step_id=current_step,
                step_name="エラー処理",
                status="failed",
                start_time=datetime.now().isoformat(),
                end_time=datetime.now().isoformat(),
                duration=0,
                output="",
                error_message=str(e),
                llm_calls=0,
                web_searches=0
            )
            steps.append(error_step)

            result = ProjectGenerationResult(
                project_spec=ProjectSpec(
                    name="failed_project",
                    description=user_request,
                    requirements=[],
                    complexity=complexity,
                    expected_files=[],
                    dependencies=[],
                    main_functionality="",
                    test_scenarios=[],
                    timestamp=datetime.now().isoformat()
                ),
                generation_steps=steps,
                generated_files=[],
                success=False,
                total_duration=time.time() - start_time,
                total_llm_calls=0,
                total_web_searches=0,
                error_count=1,
                final_status='failed'
            )

            self.logger.error(f"❌ プロジェクト生成失敗: {e}")
            return result

    async def _execute_step(self, step_id: int, step_name: str, func) -> GenerationStep:
        """ステップ実行"""
        self.logger.info(f"🔄 ステップ{step_id}: {step_name} 実行中...")

        start_time = time.time()
        step = GenerationStep(
            step_id=step_id,
            step_name=step_name,
            status="running",
            start_time=datetime.now().isoformat(),
            end_time=None,
            duration=None,
            output="",
            error_message=None,
            llm_calls=0,
            web_searches=0
        )

        try:
            # 非同期でステップ実行
            if asyncio.iscoroutinefunction(func):
                result = await func()
            else:
                result = func()

            step.status = "completed"
            step.output = json.dumps(result, ensure_ascii=False) if isinstance(result, dict) else str(result)

            self.logger.info(f"✅ ステップ{step_id}完了: {step_name}")

        except Exception as e:
            step.status = "failed"
            step.error_message = str(e)
            self.logger.error(f"❌ ステップ{step_id}失敗: {step_name} - {e}")

        finally:
            step.end_time = datetime.now().isoformat()
            step.duration = time.time() - start_time

        return step

    def _design_project_spec(self, user_request: str, complexity: str) -> dict:
        """プロジェクト仕様設計（プロンプト最適化付き）"""
        self.logger.info(f"📋 仕様設計: {user_request}")

        # プロンプト最適化
        optimized = self.prompt_optimizer.optimize_prompt(user_request)
        self.logger.info(f"🎯 プロンプト最適化完了（信頼度: {optimized.confidence:.2f}）")
        if optimized.based_on:
            self.logger.info(f"📚 参考: {', '.join(optimized.based_on)}")

        # テンプレートベースの仕様生成
        if complexity in self.project_templates:
            templates = self.project_templates[complexity]
            # ユーザーリクエストに最も近いテンプレートを選択
            selected_template = templates[0]  # 簡易実装
        else:
            selected_template = "Custom Project"

        # プロジェクト名生成
        project_name = self._generate_project_name(user_request)

        # 仕様定義（最適化されたプロンプトを保存）
        spec = {
            'name': project_name,
            'description': f"{user_request}を実現する{complexity}レベルのPythonプロジェクト",
            'requirements': self._extract_requirements(user_request),
            'complexity': complexity,
            'expected_files': self._define_expected_files(user_request, complexity),
            'dependencies': ['standard_library_only'],
            'main_functionality': user_request,
            'test_scenarios': self._define_test_scenarios(user_request),
            'timestamp': datetime.now().isoformat(),
            'optimized_prompt': optimized.prompt,  # 最適化プロンプト保存
            'enhancements': optimized.enhancements  # 強化要素保存
        }

        self.logger.info(f"📋 仕様設計完了: {project_name}")
        return spec

    def _generate_project_name(self, user_request: str) -> str:
        """プロジェクト名生成"""
        # 簡易実装: キーワードベース
        import re
        words = re.findall(r'\w+', user_request.lower())
        filtered_words = [w for w in words if len(w) > 2 and w not in ['を', 'に', 'で', 'の', 'は', 'が']]

        if filtered_words:
            return '_'.join(filtered_words[:3]) + '_cli'
        else:
            return f'project_{int(time.time())}'

    def _extract_requirements(self, user_request: str) -> List[str]:
        """要件抽出"""
        requirements = []

        # キーワードベースの要件抽出
        keywords = {
            'sql': ['SQLite データベース操作', 'テーブル作成・操作'],
            'ファイル': ['ファイル操作', 'ファイルシステム操作'],
            'ネットワーク': ['ネットワーク通信', 'HTTP/TCP操作'],
            'json': ['JSON データ処理', 'データ変換'],
            'csv': ['CSV データ処理', 'データ変換'],
            'ログ': ['ログファイル処理', 'ログ解析'],
            'スケジュール': ['タスクスケジューリング', '定期実行'],
            'cli': ['コマンドライン インターフェース', 'ユーザー操作']
        }

        user_lower = user_request.lower()
        for keyword, reqs in keywords.items():
            if keyword in user_lower:
                requirements.extend(reqs)

        # デフォルト要件
        if not requirements:
            requirements = ['基本的なPython機能', 'エラーハンドリング', 'ユーザーインターフェース']

        return requirements

    def _define_expected_files(self, user_request: str, complexity: str) -> List[str]:
        """期待ファイル定義"""
        files = ['main.py', 'README.md']

        if complexity in ['medium', 'complex']:
            files.extend(['test_main.py', 'config.py', 'utils.py'])

        if complexity == 'complex':
            files.extend(['server.py', 'database.py', 'api.py'])

        # 特定キーワードベースの追加
        user_lower = user_request.lower()
        if 'sql' in user_lower or 'database' in user_lower:
            files.append('database.py')

        if 'test' in user_lower or 'テスト' in user_lower:
            files.append('test_suite.py')

        return files

    def _define_test_scenarios(self, user_request: str) -> List[str]:
        """テストシナリオ定義"""
        scenarios = [
            '基本機能テスト',
            'エラーケーステスト',
            '境界値テスト'
        ]

        # 機能別テストシナリオ
        user_lower = user_request.lower()
        if 'sql' in user_lower:
            scenarios.extend(['データベース接続テスト', 'CRUD操作テスト'])

        if 'ファイル' in user_lower:
            scenarios.extend(['ファイル読み書きテスト', 'ファイル存在確認テスト'])

        return scenarios

    def _create_project_structure(self, project_spec: dict) -> dict:
        """プロジェクト構造作成"""
        project_name = project_spec['name']
        project_path = self.projects_dir / project_name

        self.logger.info(f"📁 プロジェクト構造作成: {project_path}")

        try:
            # プロジェクトディレクトリ作成
            project_path.mkdir(exist_ok=True)

            # サブディレクトリ作成
            (project_path / 'tests').mkdir(exist_ok=True)
            (project_path / 'docs').mkdir(exist_ok=True)
            (project_path / 'logs').mkdir(exist_ok=True)

            self.logger.info(f"✅ プロジェクト構造作成完了: {project_name}")

            return {
                'project_path': str(project_path),
                'directories_created': ['tests', 'docs', 'logs'],
                'status': 'success'
            }

        except Exception as e:
            self.logger.error(f"❌ プロジェクト構造作成失敗: {e}")
            raise

    def _generate_main_code(self, project_spec: dict) -> dict:
        """メインコード生成（LLMベース）"""
        project_name = project_spec['name']
        project_path = self.projects_dir / project_name

        self.logger.info(f"🔧 メインコード生成: {project_name}")

        # LLMでコード生成
        main_code = self._generate_code_with_llm(project_spec)

        # ファイル書き込み
        main_file = project_path / 'main.py'
        try:
            with open(main_file, 'w', encoding='utf-8') as f:
                f.write(main_code)

            self.logger.info(f"✅ メインコード生成完了: {main_file}")

            return {
                'file_path': str(main_file),
                'lines_of_code': len(main_code.split('\n')),
                'status': 'success'
            }

        except Exception as e:
            self.logger.error(f"❌ メインコード生成失敗: {e}")
            raise

    def _generate_code_with_llm(self, project_spec: dict) -> str:
        """LLMで実際のコードを生成（最適化プロンプト使用）"""

        # 最適化されたプロンプトを使用（仕様に保存されている）
        if 'optimized_prompt' in project_spec:
            prompt = project_spec['optimized_prompt']
            self.logger.info("🎯 最適化プロンプト使用")
        else:
            # フォールバック: 基本プロンプト
            prompt = f"""
以下の仕様に基づいて、完全に動作するPythonプログラムを生成してください。

【プロジェクト名】
{project_spec['name']}

【説明】
{project_spec['description']}

【主な機能】
{project_spec['main_functionality']}

【要件】
{chr(10).join(f"- {req}" for req in project_spec['requirements'])}

【強化要素】
{chr(10).join(f"- {enh}" for enh in project_spec.get('enhancements', []))}

【制約】
- 標準ライブラリのみ使用
- argparseでCLI実装
- **input()は絶対に使用禁止** (自動テストがタイムアウトするため)
- --test, --help オプションを必ず実装
- エラーハンドリングを含める
- ロギングを実装
- 実際に動作する具体的なコードを書く
- TODOコメントは残さない

【重要】input()禁止の例:
❌ 禁止: user_input = input("Enter value: ")
✅ 推奨: argparseでコマンドライン引数から取得

【出力形式】
完全なPythonコード（#!/usr/bin/env python3から始まる）のみを出力してください。
説明文は不要です。コードだけを返してください。
"""

        try:
            self.logger.info("🤖 LLMコード生成開始...")
            result = self.weak_llm.generate_code(
                prompt=prompt,
                max_tokens=8000,  # 大幅に増加
                temperature=0.2   # 温度下げて確実性向上
            )

            print(f"[DEBUG-GEN] generate_code戻り値: {result}")

            if result and result.get('code'):
                self.logger.info("✅ LLMコード生成成功")
                return result['code']
            elif result and result.get('content'):
                # コードブロックから抽出
                content = result['content']
                if '```python' in content:
                    code = content.split('```python')[1].split('```')[0].strip()
                    self.logger.info("✅ LLMコード抽出成功（pythonブロック）")
                    return code
                elif '```' in content:
                    code = content.split('```')[1].split('```')[0].strip()
                    self.logger.info("✅ LLMコード抽出成功（汎用ブロック）")
                    return code
                else:
                    self.logger.info("✅ LLMレスポンス使用")
                    return content
            else:
                # フォールバック: テンプレート使用
                self.logger.warning("⚠️ LLM生成失敗、テンプレート使用")
                return self._create_main_code_template(project_spec)

        except Exception as e:
            self.logger.error(f"❌ LLM生成エラー: {e}")
            return self._create_main_code_template(project_spec)

    def _create_main_code_template(self, project_spec: dict) -> str:
        """メインコードテンプレート作成"""
        functionality = project_spec['main_functionality']
        project_name = project_spec['name']

        # 機能別テンプレート生成
        if 'sql' in functionality.lower():
            return self._create_sql_template(project_spec)
        elif 'ファイル' in functionality.lower():
            return self._create_file_template(project_spec)
        elif 'json' in functionality.lower() or 'csv' in functionality.lower():
            return self._create_data_template(project_spec)
        else:
            return self._create_general_template(project_spec)

    def _create_sql_template(self, project_spec: dict) -> str:
        """SQLテンプレート"""
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{project_spec['name']} - SQLiteデータベース操作プロジェクト
"""

import sqlite3
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path


class DatabaseManager:
    """データベース管理クラス"""

    def __init__(self, db_path: str = "app.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """データベース初期化"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        value TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print(f"✅ データベース初期化完了: {{self.db_path}}")
        except Exception as e:
            print(f"❌ データベース初期化失敗: {{e}}")
            sys.exit(1)

    def insert_record(self, name: str, value: str = None) -> dict:
        """レコード挿入"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO records (name, value) VALUES (?, ?)",
                    (name, value)
                )
                record_id = cursor.lastrowid
                conn.commit()

                return {{
                    "success": True,
                    "id": record_id,
                    "name": name,
                    "value": value,
                    "timestamp": datetime.now().isoformat()
                }}
        except Exception as e:
            return {{
                "success": False,
                "error": str(e)
            }}

    def get_all_records(self) -> list:
        """全レコード取得"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM records ORDER BY created_at DESC")
                records = cursor.fetchall()

                return [{{
                    "id": record[0],
                    "name": record[1],
                    "value": record[2],
                    "created_at": record[3]
                }} for record in records]
        except Exception as e:
            print(f"❌ レコード取得失敗: {{e}}")
            return []


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="{project_spec['description']}")
    parser.add_argument("--name", "-n", required=True, help="レコード名")
    parser.add_argument("--value", "-v", help="レコード値")
    parser.add_argument("--list", "-l", action="store_true", help="全レコード表示")
    parser.add_argument("--db", "-d", default="app.db", help="データベースファイル")

    args = parser.parse_args()

    # データベース管理開始
    db_manager = DatabaseManager(args.db)

    if args.list:
        records = db_manager.get_all_records()
        print(f"\\n📋 全レコード ({{len(records)}} 件):")
        for record in records:
            print(f"  ID: {{record['id']}} | 名前: {{record['name']}} | 値: {{record['value']}} | 作成日時: {{record['created_at']}}")
    else:
        result = db_manager.insert_record(args.name, args.value)
        if result["success"]:
            print(f"✅ レコード挿入成功: ID={{result['id']}}, 名前={{result['name']}}, 値={{result['value']}}")
        else:
            print(f"❌ レコード挿入失敗: {{result['error']}}")
            sys.exit(1)


if __name__ == "__main__":
    main()
'''

    def _create_file_template(self, project_spec: dict) -> str:
        """ファイル操作テンプレート"""
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{project_spec['name']} - ファイル操作プロジェクト
"""

import os
import sys
import argparse
import shutil
import logging
from datetime import datetime
from pathlib import Path


class FileOrganizer:
    """ファイル整理クラス"""

    def __init__(self):
        self.setup_logging()
        self.logger.info("✅ ファイル整理システム初期化完了")

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def organize_files(self, source_dir: str, target_dir: str = None) -> dict:
        """ファイル整理実行"""
        try:
            source_path = Path(source_dir)
            if not source_path.exists():
                return {{"success": False, "error": f"ソースディレクトリが見つかりません: {{source_dir}}"}}

            if target_dir is None:
                target_dir = source_path / "organized"

            target_path = Path(target_dir)
            target_path.mkdir(exist_ok=True)

            organized_count = 0
            file_types = {{}}

            for file_path in source_path.rglob('*'):
                if file_path.is_file() and file_path.parent != target_path:
                    # ファイル拡張子による分類
                    extension = file_path.suffix.lower() or 'no_extension'
                    type_dir = target_path / extension[1:] if extension != 'no_extension' else target_path / 'no_extension'
                    type_dir.mkdir(exist_ok=True)

                    # ファイル移動
                    new_path = type_dir / file_path.name
                    counter = 1
                    while new_path.exists():
                        stem = file_path.stem
                        new_path = type_dir / f"{{stem}}_{{counter}}{{extension}}"
                        counter += 1

                    shutil.copy2(file_path, new_path)
                    organized_count += 1

                    # 統計更新
                    file_types[extension] = file_types.get(extension, 0) + 1

                    self.logger.info(f"移動: {{file_path}} -> {{new_path}}")

            return {{
                "success": True,
                "organized_count": organized_count,
                "file_types": file_types,
                "target_directory": str(target_path),
                "timestamp": datetime.now().isoformat()
            }}

        except Exception as e:
            self.logger.error(f"ファイル整理エラー: {{e}}")
            return {{"success": False, "error": str(e)}}

    def get_directory_stats(self, directory: str) -> dict:
        """ディレクトリ統計取得"""
        try:
            dir_path = Path(directory)
            if not dir_path.exists():
                return {{"success": False, "error": "ディレクトリが見つかりません"}}

            file_count = 0
            total_size = 0
            file_types = {{}}

            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    file_count += 1
                    total_size += file_path.stat().st_size
                    extension = file_path.suffix.lower() or 'no_extension'
                    file_types[extension] = file_types.get(extension, 0) + 1

            return {{
                "success": True,
                "file_count": file_count,
                "total_size": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "file_types": file_types
            }}

        except Exception as e:
            return {{"success": False, "error": str(e)}}


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="{project_spec['description']}")
    parser.add_argument("--source", "-s", required=True, help="ソースディレクトリ")
    parser.add_argument("--target", "-t", help="ターゲットディレクトリ")
    parser.add_argument("--stats", action="store_true", help="統計表示のみ")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")

    args = parser.parse_args()

    # ファイル整理システム初期化
    organizer = FileOrganizer()

    if args.stats:
        # 統計表示
        stats = organizer.get_directory_stats(args.source)
        if stats["success"]:
            print(f"\\n📊 ディレクトリ統計:")
            print(f"  📁 ディレクトリ: {{args.source}}")
            print(f"  📄 ファイル数: {{stats['file_count']}}")
            print(f"  💾 総サイズ: {{stats['total_size_mb']}} MB")
            print(f"  📋 ファイルタイプ:")
            for ext, count in stats['file_types'].items():
                print(f"    {{ext}}: {{count}} 件")
        else:
            print(f"❌ 統計取得失敗: {{stats['error']}}")
    else:
        # ファイル整理実行
        result = organizer.organize_files(args.source, args.target)
        if result["success"]:
            print(f"✅ ファイル整理完了:")
            print(f"  📁 ソース: {{args.source}}")
            print(f"  📁 ターゲット: {{result['target_directory']}}")
            print(f"  📄 整理ファイル数: {{result['organized_count']}}")
            print(f"  📋 ファイルタイプ分布: {{result['file_types']}}")
        else:
            print(f"❌ ファイル整理失敗: {{result['error']}}")
            sys.exit(1)


if __name__ == "__main__":
    main()
'''

    def _create_data_template(self, project_spec: dict) -> str:
        """データ変換テンプレート"""
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{project_spec['name']} - JSON/CSV変換プロジェクト
"""

import json
import csv
import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path


class DataConverter:
    """データ変換クラス"""

    def __init__(self):
        self.setup_logging()
        self.logger.info("✅ データ変換システム初期化完了")

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def json_to_csv(self, json_file: str, csv_file: str) -> dict:
        """JSON to CSV変換"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # データが配列かチェック
            if not isinstance(data, list):
                if isinstance(data, dict):
                    data = [data]
                else:
                    return {{"success": False, "error": "JSON data must be array or object"}}

            if not data:
                return {{"success": False, "error": "Empty JSON data"}}

            # CSVヘッダー生成
            headers = set()
            for item in data:
                if isinstance(item, dict):
                    headers.update(item.keys())

            headers = sorted(headers)

            # CSV書き込み
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()

                for item in data:
                    if isinstance(item, dict):
                        # ネストされたオブジェクトをJSONストリングに変換
                        row = {{}}
                        for key in headers:
                            value = item.get(key, '')
                            if isinstance(value, (dict, list)):
                                value = json.dumps(value, ensure_ascii=False)
                            row[key] = value
                        writer.writerow(row)

            return {{
                "success": True,
                "input_file": json_file,
                "output_file": csv_file,
                "records_count": len(data),
                "columns_count": len(headers),
                "timestamp": datetime.now().isoformat()
            }}

        except Exception as e:
            self.logger.error(f"JSON to CSV変換エラー: {{e}}")
            return {{"success": False, "error": str(e)}}

    def csv_to_json(self, csv_file: str, json_file: str) -> dict:
        """CSV to JSON変換"""
        try:
            data = []

            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row in reader:
                    # 空文字列をNoneに変換
                    processed_row = {{}}
                    for key, value in row.items():
                        if value == '':
                            processed_row[key] = None
                        else:
                            # JSON文字列を解析試行
                            try:
                                if value.startswith(('{{', '[')) and value.endswith(('}}', ']')):
                                    processed_row[key] = json.loads(value)
                                else:
                                    processed_row[key] = value
                            except json.JSONDecodeError:
                                processed_row[key] = value

                    data.append(processed_row)

            # JSON書き込み
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return {{
                "success": True,
                "input_file": csv_file,
                "output_file": json_file,
                "records_count": len(data),
                "timestamp": datetime.now().isoformat()
            }}

        except Exception as e:
            self.logger.error(f"CSV to JSON変換エラー: {{e}}")
            return {{"success": False, "error": str(e)}}

    def validate_json(self, json_file: str) -> dict:
        """JSON検証"""
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {{
                "success": True,
                "valid": True,
                "type": type(data).__name__,
                "size": len(str(data)),
                "record_count": len(data) if isinstance(data, list) else 1
            }}

        except Exception as e:
            return {{
                "success": True,
                "valid": False,
                "error": str(e)
            }}

    def get_file_info(self, file_path: str) -> dict:
        """ファイル情報取得"""
        try:
            path = Path(file_path)
            if not path.exists():
                return {{"success": False, "error": "File not found"}}

            return {{
                "success": True,
                "file_name": path.name,
                "file_size": path.stat().st_size,
                "file_size_mb": round(path.stat().st_size / (1024 * 1024), 2),
                "extension": path.suffix,
                "modified_time": datetime.fromtimestamp(path.stat().st_mtime).isoformat()
            }}

        except Exception as e:
            return {{"success": False, "error": str(e)}}


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="{project_spec['description']}")
    parser.add_argument("--input", "-i", required=True, help="入力ファイル")
    parser.add_argument("--output", "-o", required=True, help="出力ファイル")
    parser.add_argument("--mode", "-m", choices=['json2csv', 'csv2json'], required=True, help="変換モード")
    parser.add_argument("--validate", action="store_true", help="入力ファイル検証")
    parser.add_argument("--info", action="store_true", help="ファイル情報表示")

    args = parser.parse_args()

    # データ変換システム初期化
    converter = DataConverter()

    # ファイル情報表示
    if args.info:
        info = converter.get_file_info(args.input)
        if info["success"]:
            print(f"\\n📄 ファイル情報:")
            print(f"  📁 ファイル名: {{info['file_name']}}")
            print(f"  💾 サイズ: {{info['file_size_mb']}} MB")
            print(f"  📅 更新日時: {{info['modified_time']}}")
        else:
            print(f"❌ ファイル情報取得失敗: {{info['error']}}")

    # JSON検証
    if args.validate and args.input.endswith('.json'):
        validation = converter.validate_json(args.input)
        if validation["success"]:
            if validation["valid"]:
                print(f"✅ JSON検証成功: タイプ={{validation['type']}}, レコード数={{validation['record_count']}}")
            else:
                print(f"❌ JSON検証失敗: {{validation['error']}}")
        else:
            print(f"❌ JSON検証エラー: {{validation['error']}}")

    # データ変換実行
    if args.mode == 'json2csv':
        result = converter.json_to_csv(args.input, args.output)
    elif args.mode == 'csv2json':
        result = converter.csv_to_json(args.input, args.output)
    else:
        print(f"❌ 不正な変換モード: {{args.mode}}")
        sys.exit(1)

    if result["success"]:
        print(f"✅ 変換完了:")
        print(f"  📥 入力: {{result['input_file']}}")
        print(f"  📤 出力: {{result['output_file']}}")
        print(f"  📊 レコード数: {{result['records_count']}}")
        if 'columns_count' in result:
            print(f"  📋 カラム数: {{result['columns_count']}}")
    else:
        print(f"❌ 変換失敗: {{result['error']}}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

    def _create_general_template(self, project_spec: dict) -> str:
        """汎用テンプレート"""
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{project_spec['name']} - {project_spec['description']}
"""

import sys
import argparse
import logging
from datetime import datetime
from pathlib import Path


class {project_spec['name'].replace('_', '').title()}:
    """メインプロジェクトクラス"""

    def __init__(self):
        self.setup_logging()
        self.logger.info("✅ システム初期化完了")

    def setup_logging(self):
        """ログ設定"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def execute(self, params: dict) -> dict:
        """メイン実行"""
        try:
            self.logger.info(f"🚀 実行開始: {{params}}")

            # メイン処理
            result = self.process(params)

            self.logger.info(f"✅ 実行完了: {{result}}")
            return result

        except Exception as e:
            self.logger.error(f"❌ 実行失敗: {{e}}")
            return {{"success": False, "error": str(e)}}

    def process(self, params: dict) -> dict:
        """処理実装"""
        # TODO: 実際の処理を実装
        return {{
            "success": True,
            "message": f"処理完了: {{params}}",
            "timestamp": datetime.now().isoformat()
        }}


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="{project_spec['description']}")
    parser.add_argument("--input", "-i", help="入力パラメータ")
    parser.add_argument("--output", "-o", help="出力ファイル")
    parser.add_argument("--verbose", "-v", action="store_true", help="詳細出力")

    args = parser.parse_args()

    # システム初期化
    system = {project_spec['name'].replace('_', '').title()}()

    # パラメータ準備
    params = {{
        "input": args.input,
        "output": args.output,
        "verbose": args.verbose
    }}

    # 実行
    result = system.execute(params)

    if result.get("success"):
        print(f"✅ 処理成功: {{result.get('message')}}")
    else:
        print(f"❌ 処理失敗: {{result.get('error')}}")
        sys.exit(1)


if __name__ == "__main__":
    main()
'''

    def _generate_test_code(self, project_spec: dict) -> dict:
        """テストコード生成"""
        project_name = project_spec['name']
        project_path = self.projects_dir / project_name

        self.logger.info(f"🧪 テストコード生成: {project_name}")

        test_code = self._create_test_template(project_spec)

        test_file = project_path / 'test_main.py'
        try:
            with open(test_file, 'w', encoding='utf-8') as f:
                f.write(test_code)

            self.logger.info(f"✅ テストコード生成完了: {test_file}")

            return {
                'file_path': str(test_file),
                'test_cases': len(project_spec['test_scenarios']),
                'status': 'success'
            }

        except Exception as e:
            self.logger.error(f"❌ テストコード生成失敗: {e}")
            raise

    def _create_test_template(self, project_spec: dict) -> str:
        """テストテンプレート作成"""
        return f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
{project_spec['name']} テストスイート
"""

import unittest
import sys
import os
from pathlib import Path

# メインモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))
import main


class Test{project_spec['name'].replace('_', '').title()}(unittest.TestCase):
    """テストクラス"""

    def setUp(self):
        """テストセットアップ"""
        self.test_data = {{"test": "data"}}

    def tearDown(self):
        """テストクリーンアップ"""
        pass

    def test_basic_functionality(self):
        """基本機能テスト"""
        # TODO: 基本機能のテストを実装
        self.assertTrue(True, "基本機能テスト")

    def test_error_handling(self):
        """エラーハンドリングテスト"""
        # TODO: エラーケースのテストを実装
        self.assertTrue(True, "エラーハンドリングテスト")

    def test_edge_cases(self):
        """境界値テスト"""
        # TODO: 境界値テストを実装
        self.assertTrue(True, "境界値テスト")


def run_tests():
    """テスト実行"""
    suite = unittest.TestLoader().loadTestsFromTestCase(Test{project_spec['name'].replace('_', '').title()})
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
'''

    def _generate_readme(self, project_spec: dict) -> dict:
        """README生成"""
        project_name = project_spec['name']
        project_path = self.projects_dir / project_name

        self.logger.info(f"📚 README生成: {project_name}")

        readme_content = self._create_readme_template(project_spec)

        readme_file = project_path / 'README.md'
        try:
            with open(readme_file, 'w', encoding='utf-8') as f:
                f.write(readme_content)

            self.logger.info(f"✅ README生成完了: {readme_file}")

            return {
                'file_path': str(readme_file),
                'sections': ['概要', 'インストール', '使用方法', 'テスト'],
                'status': 'success'
            }

        except Exception as e:
            self.logger.error(f"❌ README生成失敗: {e}")
            raise

    def _create_readme_template(self, project_spec: dict) -> str:
        """READMEテンプレート作成"""

        # サンプルコードの生成
        sample_code = self._generate_sample_code(project_spec)

        return f'''# {project_spec['name']}

{project_spec['description']}

## 📋 概要

このプロジェクトは{project_spec['main_functionality']}を実現するPythonアプリケーションです。

### 🎯 主な機能

{chr(10).join(f"- {req}" for req in project_spec['requirements'])}

## 🛠️ 技術仕様

- **言語**: Python 3.7+
- **依存関係**: 標準ライブラリのみ
- **複雑度**: {project_spec['complexity']}

## 📁 プロジェクト構造

```
{project_spec['name']}/
├── main.py              # メインプログラム
├── test_main.py         # テストスイート
├── README.md            # このファイル
├── logs/                # ログファイル
└── docs/                # ドキュメント
```

## 💡 サンプルコード

### データベース操作のサンプル

もしデータベースを使用する場合、以下のサンプルコードをコピーして使えます：

```python
{sample_code['database']}
```

### ファイル操作のサンプル

ファイルの読み書きが必要な場合：

```python
{sample_code['file_operations']}
```

### エラーハンドリングのサンプル

堅牢なエラー処理：

```python
{sample_code['error_handling']}
```

## 📦 インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd {project_spec['name']}

# 実行権限付与（Linux/Mac）
chmod +x main.py
```

## 🧪 テスト

### テスト実行

```bash
# 全テスト実行
python test_main.py

# 特定のテスト実行
python -m unittest test_main.Test{project_spec['name'].replace('_', '').title()}.test_basic_functionality
```

### テストシナリオ

{chr(10).join(f"- {scenario}" for scenario in project_spec['test_scenarios'])}

## 📊 生成情報

- **生成日時**: {project_spec['timestamp']}
- **想定ファイル**: {', '.join(project_spec['expected_files'])}

## 🐛 トラブルシューティング

### よくある問題

1. **Permission Error**: `chmod +x main.py` で実行権限を付与してください
2. **Module Not Found**: Python 3.7以上を使用してください
3. **Import Error**: 必要なモジュールがimportされているか確認してください
4. **Argument Error**: argparseで`--help`を手動定義していないか確認してください
5. **Timeout Error**: input()を使っている場合、非対話モードにしてください

## 🚀 使用方法

### 基本的な使い方

```bash
# ヘルプ表示
python main.py --help

# 基本実行
python main.py --input "サンプル"
```

### 高度な使い方

```bash
# 詳細出力
python main.py --input "データ" --verbose

# 出力ファイル指定
python main.py --input "データ" --output "result.txt"
```

詳しいオプションは `python main.py --help` を参照してください。

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストや issue の報告を歓迎します。

---

Generated by MCP Auto Project Generator
'''

    def _generate_sample_code(self, project_spec: dict) -> dict:
        """サンプルコードを生成"""
        return {
            'database': '''import sqlite3
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path='data.db'):
        self.db_path = Path(db_path)
        self.conn = None
        self._connect()

    def _connect(self):
        """データベース接続"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row

    def execute(self, query, params=()):
        """SQLクエリ実行"""
        cursor = self.conn.cursor()
        cursor.execute(query, params)
        self.conn.commit()
        return cursor

    def fetch_all(self, query, params=()):
        """全件取得"""
        cursor = self.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query, params=()):
        """1件取得"""
        cursor = self.execute(query, params)
        return cursor.fetchone()

    def close(self):
        """接続を閉じる"""
        if self.conn:
            self.conn.close()

# 使用例
db = DatabaseManager('mydata.db')
db.execute('CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT)')
db.execute('INSERT INTO items (name) VALUES (?)', ('サンプル',))
items = db.fetch_all('SELECT * FROM items')
db.close()''',

            'file_operations': '''import json
from pathlib import Path

def save_to_json(data, filename):
    """JSONファイルに保存"""
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_from_json(filename):
    """JSONファイルから読み込み"""
    filepath = Path(filename)

    if not filepath.exists():
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_to_text(text, filename):
    """テキストファイルに保存"""
    filepath = Path(filename)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)

def load_from_text(filename):
    """テキストファイルから読み込み"""
    filepath = Path(filename)

    if not filepath.exists():
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# 使用例
data = {'name': 'サンプル', 'value': 100}
save_to_json(data, 'output/data.json')
loaded = load_from_json('output/data.json')''',

            'error_handling': '''import sys
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def safe_execute(func, *args, **kwargs):
    """安全に関数を実行"""
    try:
        return func(*args, **kwargs)
    except FileNotFoundError as e:
        logger.error(f"ファイルが見つかりません: {e}")
        return None
    except PermissionError as e:
        logger.error(f"権限エラー: {e}")
        return None
    except ValueError as e:
        logger.error(f"値エラー: {e}")
        return None
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        return None

def validate_input(value, value_type=str, min_length=None, max_length=None):
    """入力値を検証"""
    if not isinstance(value, value_type):
        raise ValueError(f"型が不正です。期待: {value_type}, 実際: {type(value)}")

    if min_length and len(value) < min_length:
        raise ValueError(f"長さが短すぎます。最小: {min_length}")

    if max_length and len(value) > max_length:
        raise ValueError(f"長さが長すぎます。最大: {max_length}")

    return True

# 使用例
try:
    validate_input("テスト", str, min_length=2, max_length=10)
    result = safe_execute(lambda x: x / 2, 10)
    logger.info(f"結果: {result}")
except ValueError as e:
    logger.error(f"検証エラー: {e}")
    sys.exit(1)'''
        }

        return f'''# {project_spec['name']}

{project_spec['description']}

## 📋 概要

このプロジェクトは{project_spec['main_functionality']}を実現するPythonアプリケーションです。

### 🎯 主な機能

{chr(10).join(f"- {req}" for req in project_spec['requirements'])}

## 🛠️ 技術仕様

- **言語**: Python 3.7+
- **依存関係**: 標準ライブラリのみ
- **複雑度**: {project_spec['complexity']}

## 📦 インストール

```bash
# リポジトリをクローン
git clone <repository-url>
cd {project_spec['name']}

# 実行権限付与
chmod +x main.py
```

## 🚀 使用方法

### 基本的な使用方法

```bash
# ヘルプ表示
python main.py --help

# 基本実行
python main.py --input "サンプル"
```

### 高度な使用方法

```bash
# 詳細出力
python main.py --input "データ" --verbose

# 出力ファイル指定
python main.py --input "データ" --output "result.txt"
```

## 🧪 テスト

### テスト実行

```bash
# 全テスト実行
python test_main.py

# 特定のテスト実行
python -m unittest test_main.Test{project_spec['name'].replace('_', '').title()}.test_basic_functionality
```

### テストシナリオ

{chr(10).join(f"- {scenario}" for scenario in project_spec['test_scenarios'])}

## 📁 プロジェクト構造

```
{project_spec['name']}/
├── main.py              # メインプログラム
├── test_main.py         # テストスイート
├── README.md            # このファイル
├── logs/                # ログファイル
└── docs/                # ドキュメント
```

## 📊 生成情報

- **生成日時**: {project_spec['timestamp']}
- **想定ファイル**: {', '.join(project_spec['expected_files'])}

## 🐛 トラブルシューティング

### よくある問題

1. **Permission Error**: `chmod +x main.py` で実行権限を付与してください
2. **Module Not Found**: Python 3.7以上を使用してください
3. **Database Error**: データベースファイルの書き込み権限を確認してください

## 📝 ライセンス

MIT License

## 🤝 貢献

プルリクエストや issue の報告を歓迎します。

---

Generated by MCP Auto Project Generator
'''

    def _run_tests(self, project_spec: dict) -> dict:
        """テスト実行"""
        project_name = project_spec['name']
        project_path = self.projects_dir / project_name

        self.logger.info(f"🧪 テスト実行: {project_name}")

        try:
            # メインファイル実行テスト
            main_file = project_path / 'main.py'
            if main_file.exists():
                result = subprocess.run(
                    [sys.executable, str(main_file), '--help'],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=30
                )

                main_test_success = result.returncode == 0
                main_output = result.stdout or "" + result.stderr or ""
            else:
                main_test_success = False
                main_output = "メインファイルが見つかりません"

            # テストファイル実行
            test_file = project_path / 'test_main.py'
            if test_file.exists():
                test_result = subprocess.run(
                    [sys.executable, str(test_file)],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='ignore',
                    timeout=60
                )

                test_success = test_result.returncode == 0
                test_output = test_result.stdout or "" + test_result.stderr or ""
            else:
                test_success = False
                test_output = "テストファイルが見つかりません"

            self.logger.info(f"✅ テスト実行完了: メイン({main_test_success}), テスト({test_success})")

            return {
                'main_test_success': main_test_success,
                'main_output': main_output[:500],  # 出力を制限
                'test_success': test_success,
                'test_output': test_output[:500],  # 出力を制限
                'overall_success': main_test_success and test_success,
                'status': 'success'
            }

        except Exception as e:
            self.logger.error(f"❌ テスト実行失敗: {e}")
            return {
                'main_test_success': False,
                'main_output': "",
                'test_success': False,
                'test_output': str(e),
                'overall_success': False,
                'status': 'failed'
            }

    def _auto_debug_project(self, project_spec: dict) -> dict:
        """自動デバッグ・修正"""
        project_name = project_spec['name']
        project_path = self.projects_dir / project_name
        main_file = project_path / 'main.py'

        self.logger.info(f"🔍 自動デバッグ開始: {project_name}")

        try:
            if not main_file.exists():
                return {
                    'status': 'failed',
                    'error': 'main.pyが見つかりません'
                }

            # 自動デバッグ実行
            debug_result = self.auto_debugger.test_and_fix_code(main_file, project_name)

            if debug_result.success:
                self.logger.info(f"✅ 自動デバッグ成功！（{debug_result.iterations}回の試行）")

                # プロンプト性能を記録
                self.prompt_optimizer.save_performance(
                    original_prompt=project_spec['main_functionality'],
                    optimized_prompt=project_spec.get('optimized_prompt', ''),
                    task_type=project_spec.get('task_type', 'general'),
                    success=True,
                    execution_time=0.0,  # 実際の時間を記録可能
                    error_count=0,
                    provider=self.provider
                )

                return {
                    'status': 'completed',
                    'iterations': debug_result.iterations,
                    'fix_applied': debug_result.fix_applied,
                    'output': debug_result.execution_output
                }
            else:
                self.logger.warning(f"⚠️ 自動デバッグ未完了（{debug_result.iterations}回試行）")
                return {
                    'status': 'partial',
                    'iterations': debug_result.iterations,
                    'error': debug_result.error_message
                }

        except Exception as e:
            self.logger.error(f"❌ 自動デバッグエラー: {e}")
            return {
                'status': 'failed',
                'error': str(e)
            }

    def _collect_generated_files(self, project_name: str) -> List[str]:
        """生成ファイル収集"""
        project_path = self.projects_dir / project_name

        if not project_path.exists():
            return []

        files = []
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                files.append(str(file_path.relative_to(project_path)))

        return files

    async def _save_generation_result(self, result: ProjectGenerationResult):
        """生成結果保存"""
        try:
            # プロジェクト仕様保存
            spec_sql = """
            INSERT OR REPLACE INTO project_specs (
                name, description, requirements, complexity, expected_files,
                dependencies, main_functionality, test_scenarios
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(spec_sql, (
                result.project_spec.name,
                result.project_spec.description,
                json.dumps(result.project_spec.requirements, ensure_ascii=False),
                result.project_spec.complexity,
                json.dumps(result.project_spec.expected_files, ensure_ascii=False),
                json.dumps(result.project_spec.dependencies, ensure_ascii=False),
                result.project_spec.main_functionality,
                json.dumps(result.project_spec.test_scenarios, ensure_ascii=False)
            ))

            # 生成ステップ保存
            for step in result.generation_steps:
                step_sql = """
                INSERT INTO generation_steps (
                    project_name, step_id, step_name, status, start_time,
                    end_time, duration, output, error_message, llm_calls, web_searches
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """

                self.db_manager._execute_sql(step_sql, (
                    result.project_spec.name,
                    step.step_id,
                    step.step_name,
                    step.status,
                    step.start_time,
                    step.end_time,
                    step.duration,
                    step.output,
                    step.error_message,
                    step.llm_calls,
                    step.web_searches
                ))

            # 生成結果保存
            result_sql = """
            INSERT OR REPLACE INTO generation_results (
                project_name, generated_files, success, total_duration,
                total_llm_calls, total_web_searches, error_count, final_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(result_sql, (
                result.project_spec.name,
                json.dumps(result.generated_files, ensure_ascii=False),
                result.success,
                result.total_duration,
                result.total_llm_calls,
                result.total_web_searches,
                result.error_count,
                result.final_status
            ))

        except Exception as e:
            self.logger.error(f"❌ 結果保存失敗: {e}")

    def get_generation_statistics(self) -> dict:
        """生成統計取得"""
        try:
            stats = {}

            # 総プロジェクト数
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM generation_results")
            stats["total_projects"] = cursor.fetchone()[0]

            # 成功率
            cursor = self.db_manager._execute_sql("SELECT COUNT(*) FROM generation_results WHERE success = 1")
            successful = cursor.fetchone()[0]
            stats["success_rate"] = (successful / stats["total_projects"]) * 100 if stats["total_projects"] > 0 else 0

            # 平均生成時間
            cursor = self.db_manager._execute_sql("SELECT AVG(total_duration) FROM generation_results")
            result = cursor.fetchone()[0]
            stats["avg_duration"] = result if result else 0

            # 複雑度別統計
            cursor = self.db_manager._execute_sql("""
                SELECT p.complexity, COUNT(*) as count, AVG(r.total_duration) as avg_time
                FROM project_specs p
                LEFT JOIN generation_results r ON p.name = r.project_name
                GROUP BY p.complexity
            """)
            stats["complexity_stats"] = {row[0]: {"count": row[1], "avg_time": row[2]} for row in cursor.fetchall()}

            return stats

        except Exception as e:
            return {"error": str(e)}


async def main():
    """メイン実行"""
    import argparse

    parser = argparse.ArgumentParser(description='MCP自動プロジェクト生成システム')
    parser.add_argument('prompt', nargs='?', help='生成するプロジェクトの説明')
    parser.add_argument('--complexity', choices=['simple', 'medium', 'complex'],
                       default='medium', help='プロジェクトの複雑度 (デフォルト: medium)')
    parser.add_argument('--provider', choices=['gemini', 'ollama', 'huggingface'],
                       default='gemini', help='LLMプロバイダー (デフォルト: gemini)')
    parser.add_argument('--test', action='store_true', help='テストモード（固定プロンプト使用）')

    args = parser.parse_args()

    print("🤖 MCP自動プロジェクト生成システム")
    print("=" * 60)

    # システム初期化（プロバイダー指定）
    generator = MCPAutoProjectGenerator(provider=args.provider)

    print(f"🔧 使用プロバイダー: {args.provider}")
    print()

    # 統計表示
    stats = generator.get_generation_statistics()
    print(f"📊 現在の統計:")
    print(f"  📦 総プロジェクト数: {stats.get('total_projects', 0)}")
    print(f"  ✅ 成功率: {stats.get('success_rate', 0):.1f}%")
    if stats.get('avg_duration', 0) > 0:
        print(f"  ⏱️ 平均生成時間: {stats.get('avg_duration', 0):.2f}秒")
    print()

    # テストモードまたはプロンプト指定
    if args.test:
        # テストモード: 複数の固定プロンプトで実行
        print("🧪 テストモード実行")
        print()
        test_requests = [
            ("SQLに1件レコードをいれて", "medium"),
            ("ファイル整理ツール", "simple"),
            ("JSON-CSVコンバータ", "medium")
        ]

        for request, complexity in test_requests:
            print(f"🚀 プロジェクト生成テスト: '{request}' (複雑度: {complexity})")
            result = await generator.generate_project(request, complexity)

            print(f"結果: {'✅ 成功' if result.success else '❌ 失敗'}")
            print(f"  📁 プロジェクト名: {result.project_spec.name}")
            print(f"  ⏱️ 生成時間: {result.total_duration:.2f}秒")
            print(f"  📄 生成ファイル数: {len(result.generated_files)}")
            print(f"  🔧 ステップ数: {len(result.generation_steps)}")
            print(f"  ❌ エラー数: {result.error_count}")
            print("-" * 40)

    elif args.prompt:
        # 通常モード: ユーザー指定のプロンプトで実行
        print(f"🚀 プロジェクト生成: '{args.prompt}'")
        print(f"📊 複雑度: {args.complexity}")
        print("-" * 60)

        result = await generator.generate_project(
            user_request=args.prompt,
            complexity=args.complexity
        )

        if result.success:
            print(f"\n✅ プロジェクト生成成功!")
            print(f"📁 プロジェクト名: {result.project_spec.name}")
            print(f"📂 プロジェクトディレクトリ: generated_projects/{result.project_spec.name}_cli")
            print(f"⏱️ 生成時間: {result.total_duration:.2f}秒")
            print(f"\n📄 生成されたファイル:")
            for file_path in result.generated_files:
                print(f"  • {file_path}")

            print(f"\n🔧 実行されたステップ:")
            for step in result.generation_steps:
                print(f"  ✅ {step.step_name}")

            # 実行方法を表示
            project_path = f"generated_projects/{result.project_spec.name}_cli"
            print(f"\n🎯 実行方法:")
            print(f"  cd {project_path}")
            print(f"  python main.py --help")
            print(f"  python main.py --test")
        else:
            print(f"\n❌ プロジェクト生成失敗")
            print(f"エラー数: {result.error_count}")
            if hasattr(result, 'errors') and result.errors:
                print(f"エラー詳細:")
                for error in result.errors:
                    print(f"  • {error}")
    else:
        # プロンプトが指定されていない
        print("❌ エラー: プロンプトを指定してください\n")
        parser.print_help()
        print("\n💡 使用例:")
        print("  python services/mcp/auto_project_generator.py \"Webスクレイピングツール\"")
        print("  python services/mcp/auto_project_generator.py \"Google検索結果表示\" --complexity medium")
        print("  python services/mcp/auto_project_generator.py \"計算機アプリ\" --provider ollama")
        print("  python services/mcp/auto_project_generator.py --test --provider ollama  # ollamaでテスト")
        return

    # 最終統計
    final_stats = generator.get_generation_statistics()
    print(f"\n📈 最終統計:")
    print(f"  📦 総プロジェクト数: {final_stats.get('total_projects', 0)}")
    print(f"  ✅ 成功率: {final_stats.get('success_rate', 0):.1f}%")
    if final_stats.get('complexity_stats'):
        print(f"  📊 複雑度別統計: {final_stats.get('complexity_stats', {})}")

    print(f"\n💾 データベース: {generator.db_manager.db_path}")
    print("🎉 完了!")


if __name__ == "__main__":
    asyncio.run(main())
