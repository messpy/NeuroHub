#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
バックグラウンドLLM支援システム
開発中の自動調査、エラー解決、設計書生成などを背景で実行
"""

import os
import sys
import json
import time
import asyncio
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
from queue import Queue, Empty

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from agents.llm_agent import LLMAgent, LLMRequest
from services.db.database_manager import DatabaseManager
from services.system.system_info_collector import SystemInfoCollector


@dataclass
class BackgroundTask:
    """バックグラウンドタスク"""
    task_id: str
    task_type: str
    priority: int
    payload: dict
    context: dict
    callback: Optional[Callable] = None
    created_at: str = ""
    status: str = "pending"


@dataclass
class InvestigationResult:
    """調査結果"""
    topic: str
    findings: List[str]
    recommendations: List[str]
    code_examples: List[str]
    references: List[str]
    confidence: float
    timestamp: str


class BackgroundLLMSupport:
    """バックグラウンドLLM支援クラス"""

    def __init__(self):
        self.llm_agent = LLMAgent()
        self.db_manager = DatabaseManager()
        self.system_collector = SystemInfoCollector()

        # タスクキューとワーカー
        self.task_queue = Queue()
        self.result_queue = Queue()
        self.workers = []
        self.running = False

        # エラー監視
        self.error_patterns = self._load_error_patterns()
        self.last_error_check = time.time()

        # システム情報キャッシュ
        self.system_info = None
        self.last_system_update = 0

        self._create_tables()
        self._start_workers()

    def _create_tables(self):
        """バックグラウンドタスク用テーブル作成"""
        # バックグラウンドタスクテーブル
        tasks_sql = """
        CREATE TABLE IF NOT EXISTS background_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id TEXT UNIQUE NOT NULL,
            task_type TEXT NOT NULL,
            priority INTEGER DEFAULT 5,
            status TEXT DEFAULT 'pending',
            payload TEXT,
            context TEXT,
            result TEXT,
            error_message TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            completed_at DATETIME,
            execution_time REAL
        )
        """

        # 調査結果テーブル
        investigations_sql = """
        CREATE TABLE IF NOT EXISTS investigation_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            findings TEXT,
            recommendations TEXT,
            code_examples TEXT,
            references TEXT,
            confidence REAL,
            system_context TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # エラーパターンテーブル
        error_patterns_sql = """
        CREATE TABLE IF NOT EXISTS error_patterns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            error_type TEXT NOT NULL,
            pattern TEXT NOT NULL,
            solution TEXT,
            examples TEXT,
            frequency INTEGER DEFAULT 1,
            success_rate REAL DEFAULT 0.0,
            last_seen DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        # 設計書テーブル
        design_docs_sql = """
        CREATE TABLE IF NOT EXISTS design_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            document_type TEXT,
            related_files TEXT,
            system_requirements TEXT,
            auto_generated BOOLEAN DEFAULT TRUE,
            version INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """

        for sql in [tasks_sql, investigations_sql, error_patterns_sql, design_docs_sql]:
            self.db_manager._execute_sql(sql)

    def _start_workers(self):
        """ワーカープロセス開始"""
        self.running = True

        # メインワーカー
        main_worker = threading.Thread(target=self._main_worker, daemon=True)
        main_worker.start()
        self.workers.append(main_worker)

        # エラー監視ワーカー
        error_worker = threading.Thread(target=self._error_monitor, daemon=True)
        error_worker.start()
        self.workers.append(error_worker)

        # システム情報更新ワーカー
        system_worker = threading.Thread(target=self._system_monitor, daemon=True)
        system_worker.start()
        self.workers.append(system_worker)

    def _main_worker(self):
        """メインタスク処理ワーカー"""
        while self.running:
            try:
                # タスク取得（5秒でタイムアウト）
                task = self.task_queue.get(timeout=5)

                print(f"🔄 バックグラウンドタスク開始: {task.task_type}")
                start_time = time.time()

                # タスク実行
                result = self._execute_task(task)
                execution_time = time.time() - start_time

                # 結果保存
                self._save_task_result(task, result, execution_time)

                # コールバック実行
                if task.callback:
                    task.callback(result)

                print(f"✅ タスク完了: {task.task_type} ({execution_time:.2f}s)")

            except Empty:
                continue
            except Exception as e:
                print(f"❌ ワーカーエラー: {e}")
                continue

    def _error_monitor(self):
        """エラー監視ワーカー"""
        while self.running:
            try:
                time.sleep(10)  # 10秒間隔でチェック

                # 新しいエラーログをチェック
                self._check_new_errors()

                # システム状態チェック
                self._check_system_health()

            except Exception as e:
                print(f"❌ エラー監視エラー: {e}")
                continue

    def _system_monitor(self):
        """システム情報監視ワーカー"""
        while self.running:
            try:
                time.sleep(300)  # 5分間隔で更新

                # システム情報更新
                self._update_system_info()

                # パフォーマンス履歴記録
                self._record_performance()

            except Exception as e:
                print(f"❌ システム監視エラー: {e}")
                continue

    def _execute_task(self, task: BackgroundTask) -> dict:
        """タスク実行"""
        task_type = task.task_type
        payload = task.payload
        context = task.context

        if task_type == "investigate_topic":
            return self._investigate_topic(payload.get("topic"), context)

        elif task_type == "analyze_error":
            return self._analyze_error(payload.get("error"), context)

        elif task_type == "generate_design":
            return self._generate_design_document(payload.get("requirements"), context)

        elif task_type == "suggest_improvements":
            return self._suggest_code_improvements(payload.get("code"), context)

        elif task_type == "research_solution":
            return self._research_solution(payload.get("problem"), context)

        else:
            return {"error": f"Unknown task type: {task_type}"}

    def _investigate_topic(self, topic: str, context: dict) -> dict:
        """トピック調査"""
        try:
            # システム情報取得
            system_info = self._get_current_system_info()

            # 既存の調査結果検索
            existing_sql = """
            SELECT * FROM investigation_results
            WHERE topic LIKE ?
            ORDER BY timestamp DESC LIMIT 3
            """
            cursor = self.db_manager._execute_sql(existing_sql, (f"%{topic}%",))
            existing_results = cursor.fetchall()

            # LLMで調査実行
            investigation_prompt = self._build_investigation_prompt(topic, context, system_info, existing_results)

            llm_request = LLMRequest(
                prompt=investigation_prompt,
                system_message="あなたは詳細な技術調査を行う専門エージェントです。",
                request_type="investigation",
                max_tokens=1000,
                temperature=0.3,
                preferred_provider="gemini"  # 弱いLLM対応
            )

            response = self.llm_agent.process_request(llm_request)

            if response.success:
                # 結果パース
                result = self._parse_investigation_result(response.content, topic)

                # データベース保存
                self._save_investigation_result(result, system_info)

                return {
                    "success": True,
                    "result": result,
                    "raw_response": response.content
                }
            else:
                return {"success": False, "error": response.error_message}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _analyze_error(self, error: str, context: dict) -> dict:
        """エラー解析"""
        try:
            # エラーパターン検索
            pattern_sql = """
            SELECT * FROM error_patterns
            WHERE ? LIKE pattern OR pattern LIKE ?
            ORDER BY frequency DESC, success_rate DESC
            LIMIT 5
            """
            cursor = self.db_manager._execute_sql(pattern_sql, (error, f"%{error[:50]}%"))
            similar_patterns = cursor.fetchall()

            # システム情報取得
            system_info = self._get_current_system_info()

            # エラー解析プロンプト
            analysis_prompt = self._build_error_analysis_prompt(error, context, system_info, similar_patterns)

            llm_request = LLMRequest(
                prompt=analysis_prompt,
                system_message="あなたはエラー解析とデバッグの専門家です。実用的な解決策を提供してください。",
                request_type="error_analysis",
                max_tokens=800,
                temperature=0.2,
                preferred_provider="gemini"
            )

            response = self.llm_agent.process_request(llm_request)

            if response.success:
                # 解決策抽出
                solution = self._parse_error_solution(response.content)

                # エラーパターン更新/追加
                self._update_error_pattern(error, solution)

                return {
                    "success": True,
                    "solution": solution,
                    "similar_cases": len(similar_patterns),
                    "raw_response": response.content
                }
            else:
                return {"success": False, "error": response.error_message}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_design_document(self, requirements: str, context: dict) -> dict:
        """設計書生成"""
        try:
            # システム要件取得
            system_info = self._get_current_system_info()

            # 既存設計書参照
            existing_sql = """
            SELECT * FROM design_documents
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY created_at DESC LIMIT 3
            """
            cursor = self.db_manager._execute_sql(existing_sql, (f"%{requirements[:50]}%", f"%{requirements[:30]}%"))
            existing_docs = cursor.fetchall()

            # 設計書生成プロンプト
            design_prompt = self._build_design_prompt(requirements, context, system_info, existing_docs)

            llm_request = LLMRequest(
                prompt=design_prompt,
                system_message="あなたは詳細な技術設計書を作成する上級システムアーキテクトです。",
                request_type="design_generation",
                max_tokens=1500,
                temperature=0.4,
                preferred_provider="gemini"
            )

            response = self.llm_agent.process_request(llm_request)

            if response.success:
                # 設計書パース
                design_doc = self._parse_design_document(response.content, requirements)

                # データベース保存
                self._save_design_document(design_doc, system_info)

                return {
                    "success": True,
                    "design_document": design_doc,
                    "raw_response": response.content
                }
            else:
                return {"success": False, "error": response.error_message}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _suggest_code_improvements(self, code: str, context: dict) -> dict:
        """コード改善提案"""
        try:
            # システム情報とベストプラクティス取得
            system_info = self._get_current_system_info()

            # 類似コード検索
            similar_sql = """
            SELECT content FROM coding_patterns
            WHERE category IN ('best_practices', 'optimization')
            LIMIT 10
            """
            cursor = self.db_manager._execute_sql(similar_sql)
            best_practices = [row[0] for row in cursor.fetchall()]

            # コード改善プロンプト
            improvement_prompt = self._build_improvement_prompt(code, context, system_info, best_practices)

            llm_request = LLMRequest(
                prompt=improvement_prompt,
                system_message="あなたはコード品質とパフォーマンス最適化の専門家です。",
                request_type="code_improvement",
                max_tokens=1000,
                temperature=0.3,
                preferred_provider="gemini"
            )

            response = self.llm_agent.process_request(llm_request)

            if response.success:
                improvements = self._parse_improvement_suggestions(response.content)

                return {
                    "success": True,
                    "improvements": improvements,
                    "raw_response": response.content
                }
            else:
                return {"success": False, "error": response.error_message}

        except Exception as e:
            return {"success": False, "error": str(e)}

    def _research_solution(self, problem: str, context: dict) -> dict:
        """解決策研究"""
        try:
            # 複数ソースから情報収集
            sources = []

            # データベース検索
            db_results = self._search_database_solutions(problem)
            sources.append(("database", db_results))

            # コードベース検索
            code_results = self._search_codebase_solutions(problem)
            sources.append(("codebase", code_results))

            # 既存調査結果
            investigation_results = self._search_investigation_history(problem)
            sources.append(("investigations", investigation_results))

            # システム情報
            system_info = self._get_current_system_info()

            # 統合研究プロンプト
            research_prompt = self._build_research_prompt(problem, context, system_info, sources)

            llm_request = LLMRequest(
                prompt=research_prompt,
                system_message="あなたは多角的な技術研究を行う専門研究者です。",
                request_type="solution_research",
                max_tokens=1200,
                temperature=0.4,
                preferred_provider="gemini"
            )

            response = self.llm_agent.process_request(llm_request)

            if response.success:
                research_result = self._parse_research_result(response.content, problem)

                return {
                    "success": True,
                    "research": research_result,
                    "sources_consulted": len(sources),
                    "raw_response": response.content
                }
            else:
                return {"success": False, "error": response.error_message}

        except Exception as e:
            return {"success": False, "error": str(e)}

    # タスク追加メソッド
    def investigate_topic_async(self, topic: str, context: dict = None, callback: Callable = None):
        """トピック調査をバックグラウンドで実行"""
        task = BackgroundTask(
            task_id=f"investigate_{int(time.time())}",
            task_type="investigate_topic",
            priority=3,
            payload={"topic": topic},
            context=context or {},
            callback=callback,
            created_at=datetime.now().isoformat()
        )
        self.task_queue.put(task)
        return task.task_id

    def analyze_error_async(self, error: str, context: dict = None, callback: Callable = None):
        """エラー解析をバックグラウンドで実行"""
        task = BackgroundTask(
            task_id=f"error_{int(time.time())}",
            task_type="analyze_error",
            priority=1,  # 高優先度
            payload={"error": error},
            context=context or {},
            callback=callback,
            created_at=datetime.now().isoformat()
        )
        self.task_queue.put(task)
        return task.task_id

    def generate_design_async(self, requirements: str, context: dict = None, callback: Callable = None):
        """設計書生成をバックグラウンドで実行"""
        task = BackgroundTask(
            task_id=f"design_{int(time.time())}",
            task_type="generate_design",
            priority=4,
            payload={"requirements": requirements},
            context=context or {},
            callback=callback,
            created_at=datetime.now().isoformat()
        )
        self.task_queue.put(task)
        return task.task_id

    def suggest_improvements_async(self, code: str, context: dict = None, callback: Callable = None):
        """コード改善提案をバックグラウンドで実行"""
        task = BackgroundTask(
            task_id=f"improve_{int(time.time())}",
            task_type="suggest_improvements",
            priority=3,
            payload={"code": code},
            context=context or {},
            callback=callback,
            created_at=datetime.now().isoformat()
        )
        self.task_queue.put(task)
        return task.task_id

    def research_solution_async(self, problem: str, context: dict = None, callback: Callable = None):
        """解決策研究をバックグラウンドで実行"""
        task = BackgroundTask(
            task_id=f"research_{int(time.time())}",
            task_type="research_solution",
            priority=2,
            payload={"problem": problem},
            context=context or {},
            callback=callback,
            created_at=datetime.now().isoformat()
        )
        self.task_queue.put(task)
        return task.task_id

    # ヘルパーメソッド
    def _get_current_system_info(self) -> dict:
        """現在のシステム情報取得"""
        current_time = time.time()
        if not self.system_info or (current_time - self.last_system_update) > 300:
            self.system_info = self.system_collector.get_system_summary()
            self.last_system_update = current_time
        return self.system_info

    def _update_system_info(self):
        """システム情報更新"""
        try:
            system_info = self.system_collector.collect_system_info()
            if system_info:
                self.system_collector.save_system_info(system_info)

            dev_env = self.system_collector.collect_development_environment()
            if dev_env:
                self.system_collector.save_development_environment(dev_env)

        except Exception as e:
            print(f"❌ システム情報更新エラー: {e}")

    def _load_error_patterns(self) -> list:
        """エラーパターン読み込み"""
        try:
            cursor = self.db_manager._execute_sql("SELECT * FROM error_patterns ORDER BY frequency DESC")
            return cursor.fetchall()
        except:
            return []

    def _check_new_errors(self):
        """新しいエラーの監視"""
        # ログファイルチェック（簡易実装）
        log_dir = project_root / "logs"
        if log_dir.exists():
            for log_file in log_dir.glob("*.log"):
                try:
                    mtime = log_file.stat().st_mtime
                    if mtime > self.last_error_check:
                        self._analyze_log_file(log_file)
                except:
                    continue

        self.last_error_check = time.time()

    def _analyze_log_file(self, log_file: Path):
        """ログファイル解析"""
        try:
            content = log_file.read_text()
            lines = content.split('\n')

            for line in lines:
                if any(keyword in line.lower() for keyword in ['error', 'exception', 'traceback', 'failed']):
                    # エラーを自動解析キューに追加
                    self.analyze_error_async(line, {"source": "log_monitor", "file": str(log_file)})

        except Exception as e:
            print(f"❌ ログファイル解析エラー: {e}")

    def _check_system_health(self):
        """システム健康状態チェック"""
        try:
            # 簡易健康チェック
            import psutil

            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            if cpu_usage > 90:
                self.investigate_topic_async("高CPU使用率の原因調査", {"cpu_usage": cpu_usage})

            if memory.percent > 90:
                self.investigate_topic_async("高メモリ使用率の原因調査", {"memory_usage": memory.percent})

        except:
            pass

    def _record_performance(self):
        """パフォーマンス履歴記録"""
        try:
            import psutil

            # パフォーマンス情報収集
            cpu_usage = psutil.cpu_percent()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # データベース保存
            performance_sql = """
            INSERT INTO performance_history (
                system_id, cpu_usage, memory_usage, disk_usage, response_time
            ) VALUES (
                (SELECT MAX(id) FROM system_info), ?, ?, ?, ?
            )
            """

            self.db_manager._execute_sql(performance_sql, (
                cpu_usage,
                memory.percent,
                (disk.used / disk.total) * 100,
                0.0  # レスポンス時間は別途測定
            ))

        except Exception as e:
            print(f"❌ パフォーマンス記録エラー: {e}")

    # プロンプト構築メソッド群
    def _build_investigation_prompt(self, topic: str, context: dict, system_info: dict, existing_results: list) -> str:
        """調査プロンプト構築"""
        system_context = f"""
システム情報:
- プラットフォーム: {system_info.get('system', {}).get('platform', 'Unknown')}
- Python版: {system_info.get('system', {}).get('python_version', 'Unknown')}
- メモリ: {system_info.get('system', {}).get('memory_total', 0) // (1024**3)}GB
- プロジェクト: {system_info.get('environment', {}).get('project_path', 'Unknown')}
"""

        existing_context = ""
        if existing_results:
            existing_context = f"""
過去の関連調査結果:
{chr(10).join([f"- {r[1]}: {r[2][:100]}..." for r in existing_results[:3]])}
"""

        return f"""
以下のトピックについて詳細に調査してください:

トピック: {topic}

コンテキスト: {json.dumps(context, ensure_ascii=False, indent=2)}

{system_context}

{existing_context}

以下の形式で回答してください:
1. 概要: トピックの要約説明
2. 技術詳細: 具体的な技術内容
3. 実装方法: 実際のコード例やステップ
4. 注意点: 知っておくべき落とし穴や制限
5. 参考資料: 追加で調べるべきリソース
6. 推奨度: このアプローチの適用推奨度（1-10）

弱いLLMでも理解できるよう、具体的で実用的な内容を重視してください。
"""

    def _build_error_analysis_prompt(self, error: str, context: dict, system_info: dict, similar_patterns: list) -> str:
        """エラー解析プロンプト構築"""
        similar_context = ""
        if similar_patterns:
            similar_context = f"""
類似エラーパターン:
{chr(10).join([f"- {p[2]}: {p[3][:100]}..." for p in similar_patterns[:3]])}
"""

        return f"""
以下のエラーを解析して解決策を提案してください:

エラー内容:
{error}

発生コンテキスト: {json.dumps(context, ensure_ascii=False, indent=2)}

システム環境:
- OS: {system_info.get('system', {}).get('platform', 'Unknown')}
- Python: {system_info.get('system', {}).get('python_version', 'Unknown')}

{similar_context}

以下の形式で回答してください:
1. エラー原因: 何が問題なのか
2. 即座の解決策: すぐに試せる修正方法
3. 根本的解決: 再発防止のための対策
4. 確認手順: 解決を確認する方法
5. 代替手法: 他のアプローチ
6. 予防策: 今後同様のエラーを避ける方法

コピペで使える具体的なコードを含めてください。
"""

    def _build_design_prompt(self, requirements: str, context: dict, system_info: dict, existing_docs: list) -> str:
        """設計プロンプト構築"""
        return f"""
以下の要件に基づいて技術設計書を作成してください:

要件: {requirements}

コンテキスト: {json.dumps(context, ensure_ascii=False, indent=2)}

システム制約:
- プラットフォーム: {system_info.get('system', {}).get('platform', 'Unknown')}
- メモリ制限: {system_info.get('system', {}).get('memory_total', 0) // (1024**3)}GB
- 開発環境: {system_info.get('environment', {}).get('git_branch', 'main')}

設計書構成:
1. 概要: システムの目的と概要
2. アーキテクチャ: システム構成と関係
3. データ設計: データベース・データ構造
4. API設計: インターフェース仕様
5. セキュリティ: 認証・認可・データ保護
6. パフォーマンス: 性能要件と最適化
7. 実装計画: 開発ステップとスケジュール
8. テスト戦略: テスト方針と自動化
9. 運用計画: デプロイ・監視・保守

弱いLLMでも実装できるよう、具体的なコード例とステップを含めてください。
"""

    def _build_improvement_prompt(self, code: str, context: dict, system_info: dict, best_practices: list) -> str:
        """改善プロンプト構築"""
        practices_context = ""
        if best_practices:
            practices_context = f"""
関連ベストプラクティス:
{chr(10).join([f"- {p[:100]}..." for p in best_practices[:5]])}
"""

        return f"""
以下のコードを分析して改善提案してください:

コード:
```python
{code}
```

コンテキスト: {json.dumps(context, ensure_ascii=False, indent=2)}

{practices_context}

改善観点:
1. パフォーマンス: 実行速度・メモリ使用量
2. 可読性: コードの理解しやすさ
3. 保守性: 修正・拡張のしやすさ
4. セキュリティ: 脆弱性の有無
5. テスタビリティ: テストのしやすさ
6. エラーハンドリング: 例外処理の適切性

各改善点について:
- 問題点の説明
- 改善されたコード例
- 改善効果の説明
- 実装時の注意点

を提供してください。
"""

    def _build_research_prompt(self, problem: str, context: dict, system_info: dict, sources: list) -> str:
        """研究プロンプト構築"""
        sources_context = ""
        for source_type, data in sources:
            if data:
                sources_context += f"""
{source_type}からの情報:
{chr(10).join([f"- {str(item)[:100]}..." for item in data[:3]])}
"""

        return f"""
以下の問題について多角的に研究して解決策を提案してください:

問題: {problem}

コンテキスト: {json.dumps(context, ensure_ascii=False, indent=2)}

{sources_context}

研究観点:
1. 問題の本質: 根本的な課題は何か
2. 既存解決策: すでに存在するアプローチ
3. 新しいアプローチ: 革新的な解決方法
4. 実装可能性: 現実的な実装の難易度
5. コスト評価: 時間・リソースの見積もり
6. リスク分析: 潜在的な問題とその対策
7. 段階的実装: ステップバイステップの計画

弱いLLMでも理解・実装できる具体的な解決策を提示してください。
"""

    # 結果パースメソッド群
    def _parse_investigation_result(self, content: str, topic: str) -> InvestigationResult:
        """調査結果パース"""
        # 簡易パース（実際にはより詳細な解析が必要）
        lines = content.split('\n')

        findings = [line.strip() for line in lines if line.strip().startswith(('- ', '・', '1.', '2.'))]
        recommendations = [line.strip() for line in lines if '推奨' in line or 'おすすめ' in line]
        code_examples = [line.strip() for line in lines if 'def ' in line or 'class ' in line or 'import ' in line]
        references = [line.strip() for line in lines if 'http' in line or '.py' in line]

        return InvestigationResult(
            topic=topic,
            findings=findings[:10],
            recommendations=recommendations[:5],
            code_examples=code_examples[:5],
            references=references[:5],
            confidence=0.8,  # 固定値（実際には内容分析で決定）
            timestamp=datetime.now().isoformat()
        )

    def _parse_error_solution(self, content: str) -> dict:
        """エラー解決策パース"""
        return {
            "analysis": content[:500],
            "immediate_fix": "解決策を実装してください",  # 簡易実装
            "prevention": "予防策を実装してください",
            "confidence": 0.7,
            "full_content": content
        }

    def _parse_design_document(self, content: str, requirements: str) -> dict:
        """設計書パース"""
        return {
            "title": f"設計書: {requirements[:50]}",
            "content": content,
            "sections": content.split('\n\n'),
            "requirements": requirements,
            "estimated_complexity": "中程度",
            "timestamp": datetime.now().isoformat()
        }

    def _parse_improvement_suggestions(self, content: str) -> dict:
        """改善提案パース"""
        return {
            "suggestions": content.split('\n\n'),
            "priority": "中",
            "estimated_effort": "数時間",
            "impact": "中程度の改善",
            "full_content": content
        }

    def _parse_research_result(self, content: str, problem: str) -> dict:
        """研究結果パース"""
        return {
            "problem": problem,
            "analysis": content,
            "solutions": content.split('\n\n'),
            "feasibility": "実装可能",
            "timeline": "1-2週間",
            "full_content": content
        }

    # データベース保存メソッド群
    def _save_task_result(self, task: BackgroundTask, result: dict, execution_time: float):
        """タスク結果保存"""
        try:
            update_sql = """
            UPDATE background_tasks
            SET status = ?, result = ?, completed_at = CURRENT_TIMESTAMP, execution_time = ?
            WHERE task_id = ?
            """

            status = "completed" if result.get("success", False) else "failed"

            self.db_manager._execute_sql(update_sql, (
                status,
                json.dumps(result, ensure_ascii=False),
                execution_time,
                task.task_id
            ))

        except Exception as e:
            print(f"❌ タスク結果保存エラー: {e}")

    def _save_investigation_result(self, result: InvestigationResult, system_info: dict):
        """調査結果保存"""
        try:
            insert_sql = """
            INSERT INTO investigation_results (
                topic, findings, recommendations, code_examples,
                references, confidence, system_context
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                result.topic,
                json.dumps(result.findings, ensure_ascii=False),
                json.dumps(result.recommendations, ensure_ascii=False),
                json.dumps(result.code_examples, ensure_ascii=False),
                json.dumps(result.references, ensure_ascii=False),
                result.confidence,
                json.dumps(system_info, ensure_ascii=False)
            ))

        except Exception as e:
            print(f"❌ 調査結果保存エラー: {e}")

    def _update_error_pattern(self, error: str, solution: dict):
        """エラーパターン更新"""
        try:
            # 既存パターン検索
            search_sql = "SELECT id, frequency FROM error_patterns WHERE pattern LIKE ?"
            cursor = self.db_manager._execute_sql(search_sql, (f"%{error[:50]}%",))
            existing = cursor.fetchone()

            if existing:
                # 更新
                update_sql = """
                UPDATE error_patterns
                SET frequency = frequency + 1, solution = ?, last_seen = CURRENT_TIMESTAMP
                WHERE id = ?
                """
                self.db_manager._execute_sql(update_sql, (
                    json.dumps(solution, ensure_ascii=False),
                    existing[0]
                ))
            else:
                # 新規作成
                insert_sql = """
                INSERT INTO error_patterns (error_type, pattern, solution, frequency)
                VALUES (?, ?, ?, ?)
                """
                self.db_manager._execute_sql(insert_sql, (
                    "runtime_error",
                    error[:500],
                    json.dumps(solution, ensure_ascii=False),
                    1
                ))

        except Exception as e:
            print(f"❌ エラーパターン更新エラー: {e}")

    def _save_design_document(self, design_doc: dict, system_info: dict):
        """設計書保存"""
        try:
            insert_sql = """
            INSERT INTO design_documents (
                title, content, document_type, system_requirements
            ) VALUES (?, ?, ?, ?)
            """

            self.db_manager._execute_sql(insert_sql, (
                design_doc["title"],
                design_doc["content"],
                "auto_generated",
                json.dumps(system_info, ensure_ascii=False)
            ))

        except Exception as e:
            print(f"❌ 設計書保存エラー: {e}")

    # 検索メソッド群
    def _search_database_solutions(self, problem: str) -> list:
        """データベースから解決策検索"""
        try:
            search_sql = """
            SELECT content FROM coding_patterns
            WHERE content LIKE ? OR description LIKE ?
            LIMIT 5
            """
            cursor = self.db_manager._execute_sql(search_sql, (f"%{problem}%", f"%{problem}%"))
            return [row[0] for row in cursor.fetchall()]
        except:
            return []

    def _search_codebase_solutions(self, problem: str) -> list:
        """コードベースから解決策検索"""
        try:
            # プロジェクト内のファイルを検索（簡易実装）
            solutions = []
            for py_file in project_root.rglob("*.py"):
                try:
                    content = py_file.read_text()
                    if problem.lower() in content.lower():
                        solutions.append(f"{py_file.name}: {content[:200]}...")
                        if len(solutions) >= 5:
                            break
                except:
                    continue
            return solutions
        except:
            return []

    def _search_investigation_history(self, problem: str) -> list:
        """調査履歴検索"""
        try:
            search_sql = """
            SELECT topic, findings FROM investigation_results
            WHERE topic LIKE ? OR findings LIKE ?
            ORDER BY timestamp DESC LIMIT 3
            """
            cursor = self.db_manager._execute_sql(search_sql, (f"%{problem}%", f"%{problem}%"))
            return [f"{row[0]}: {row[1]}" for row in cursor.fetchall()]
        except:
            return []

    def get_task_status(self, task_id: str) -> dict:
        """タスク状況取得"""
        try:
            status_sql = "SELECT * FROM background_tasks WHERE task_id = ?"
            cursor = self.db_manager._execute_sql(status_sql, (task_id,))
            task = cursor.fetchone()

            if task:
                return {
                    "task_id": task[1],
                    "task_type": task[2],
                    "status": task[4],
                    "result": json.loads(task[6]) if task[6] else None,
                    "created_at": task[9],
                    "completed_at": task[10],
                    "execution_time": task[11]
                }
            else:
                return {"error": "Task not found"}

        except Exception as e:
            return {"error": str(e)}

    def get_recent_investigations(self, limit: int = 10) -> list:
        """最近の調査結果取得"""
        try:
            recent_sql = """
            SELECT * FROM investigation_results
            ORDER BY timestamp DESC LIMIT ?
            """
            cursor = self.db_manager._execute_sql(recent_sql, (limit,))
            return [dict(row) for row in cursor.fetchall()]
        except:
            return []

    def stop(self):
        """バックグラウンド処理停止"""
        self.running = False
        for worker in self.workers:
            worker.join(timeout=5)


def main():
    """テスト実行"""
    print("🚀 バックグラウンドLLM支援システム開始...")

    support = BackgroundLLMSupport()

    # テスト調査
    task_id = support.investigate_topic_async("Python pytest モック", {"context": "テスト実装中"})
    print(f"📋 調査タスク開始: {task_id}")

    # 結果待機
    time.sleep(10)

    # 結果確認
    status = support.get_task_status(task_id)
    print(f"📊 タスク状況: {status.get('status', 'unknown')}")

    # 最近の調査結果
    recent = support.get_recent_investigations(3)
    print(f"📚 最近の調査: {len(recent)}件")

    time.sleep(5)
    support.stop()


if __name__ == "__main__":
    main()
