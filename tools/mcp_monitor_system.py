#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP監視・評価システム
MCPにお題を与えて、生成されたコードの実行ログを監視・分析
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import logging

# プロジェクトパス追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class MCPMonitorSystem:
    """MCP監視・評価システム"""

    def __init__(self):
        self.log_dir = Path("logs/mcp_monitor")
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # ログ設定
        self.logger = logging.getLogger("MCPMonitor")
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(
            self.log_dir / f"mcp_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)

        # コンソール出力も追加
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 監視データ
        self.execution_logs = []
        self.task_results = []

    def create_coding_task(self, difficulty: str = "medium") -> Dict[str, Any]:
        """コーディング課題生成"""
        tasks = {
            "easy": [
                "FizzBuzz問題をPythonで実装",
                "ファイルの行数をカウントする関数",
                "リストの重複を除去する関数",
                "辞書をJSONファイルに保存する関数"
            ],
            "medium": [
                "subprocessとtkinterでシステム情報表示GUI",
                "CSVファイルを読み込んでグラフ作成（matplotlib使用）",
                "SQLiteデータベースCRUD操作のCLIツール",
                "ファイル暗号化・復号化ツール（cryptographyライブラリ使用）"
            ],
            "hard": [
                "非同期HTTPクライアント（aiohttp使用）",
                "機械学習データ前処理パイプライン（pandas+scikit-learn）",
                "RESTful APIサーバー（FastAPI+SQLAlchemy）",
                "リアルタイムチャットシステム（WebSocket使用）"
            ]
        }

        import random
        task_description = random.choice(tasks[difficulty])

        return {
            "id": f"task_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "difficulty": difficulty,
            "description": task_description,
            "created_at": datetime.now().isoformat(),
            "expected_files": ["main.py", "README.md"],
            "timeout": 300  # 5分タイムアウト
        }

    def execute_mcp_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """MCPに課題実行させる（auto_project_generator使用）"""
        task_start = time.time()

        self.logger.info(f"🎯 MCPタスク開始: {task['description']}")

        try:
            # auto_project_generatorを使用してプロジェクト生成
            from services.mcp.auto_project_generator import MCPAutoProjectGenerator

            self.logger.info("📝 MCPにコード生成を依頼中...")

            # MCP実行
            generation_start = time.time()
            generator = MCPAutoProjectGenerator()

            # 非同期関数を同期的に実行
            import asyncio
            result = asyncio.run(generator.generate_project(
                user_request=task['description'],
                complexity=task['difficulty']
            ))

            generation_time = time.time() - generation_start

            self.logger.info(f"⏱️ コード生成時間: {generation_time:.2f}秒")

            if not result.success:
                raise Exception(f"MCP生成失敗: エラー数={result.error_count}")

            # 生成されたファイルを確認
            project_dir = Path("generated_projects") / (result.project_spec.name + "_cli")
            if not project_dir.exists():
                # プロジェクト名の変形を試行
                possible_names = [
                    result.project_spec.name + "_cli",
                    result.project_spec.name,
                    result.project_spec.name.lower() + "_cli"
                ]
                for pname in possible_names:
                    test_dir = Path("generated_projects") / pname
                    if test_dir.exists():
                        project_dir = test_dir
                        break
                else:
                    # generated_projectsディレクトリ内を検索
                    gen_dir = Path("generated_projects")
                    if gen_dir.exists():
                        all_dirs = [d for d in gen_dir.iterdir() if d.is_dir()]
                        if all_dirs:
                            # 最新のディレクトリを使用
                            project_dir = max(all_dirs, key=lambda p: p.stat().st_mtime)
                            self.logger.info(f"📂 プロジェクトディレクトリ検出: {project_dir}")

                if not project_dir.exists():
                    raise Exception("プロジェクトディレクトリが作成されていません")

            generated_files = list(project_dir.rglob("*.py"))
            self.logger.info(f"📁 生成ファイル数: {len(generated_files)}")

            # 生成されたコードを実行テスト
            execution_results = self.test_generated_code(project_dir, task)

            task_time = time.time() - task_start

            result_dict = {
                "task_id": task['id'],
                "success": True,
                "generation_time": generation_time,
                "total_time": task_time,
                "generated_files": [str(f.relative_to(project_dir)) for f in generated_files],
                "execution_results": execution_results,
                "mcp_result": {
                    "project_name": result.project_name,
                    "files_generated": result.files_generated,
                    "steps_completed": [s.value for s in result.steps_completed]
                },
                "project_directory": str(project_dir)
            }

            self.logger.info(f"✅ タスク完了: {task_time:.2f}秒")
            return result_dict

        except Exception as e:
            task_time = time.time() - task_start
            error_result = {
                "task_id": task['id'],
                "success": False,
                "error": str(e),
                "total_time": task_time,
                "generation_time": 0,
                "generated_files": [],
                "execution_results": {}
            }

            self.logger.error(f"❌ タスク失敗: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return error_result

    def test_generated_code(self, project_dir: Path, task: Dict[str, Any]) -> Dict[str, Any]:
        """生成されたコードのテスト実行"""
        results = {
            "syntax_check": False,
            "execution_test": False,
            "output_captured": "",
            "error_messages": [],
            "file_analysis": {}
        }

        try:
            # 1. 構文チェック
            main_file = project_dir / "main.py"
            if main_file.exists():
                self.logger.info("🔍 構文チェック実行中...")

                syntax_result = subprocess.run([
                    sys.executable, "-m", "py_compile", str(main_file)
                ], capture_output=True, text=True, encoding='utf-8', errors='ignore')

                results["syntax_check"] = syntax_result.returncode == 0
                if syntax_result.returncode != 0:
                    results["error_messages"].append(f"構文エラー: {syntax_result.stderr}")
                    self.logger.warning(f"⚠️ 構文エラー: {syntax_result.stderr}")
                else:
                    self.logger.info("✅ 構文チェック成功")

            # 2. 実行テスト（ヘルプ表示のみ）
            if results["syntax_check"] and main_file.exists():
                self.logger.info("🚀 実行テスト開始（ヘルプ表示）...")

                exec_result = subprocess.run([
                    sys.executable, str(main_file), "--help"
                ], cwd=str(project_dir), capture_output=True, text=True,
                   timeout=30, encoding='utf-8', errors='ignore')

                results["execution_test"] = exec_result.returncode == 0
                results["output_captured"] = exec_result.stdout

                if exec_result.returncode != 0:
                    # ヘルプがない場合は通常実行を試行
                    self.logger.info("📋 通常実行を試行...")
                    exec_result2 = subprocess.run([
                        sys.executable, str(main_file)
                    ], cwd=str(project_dir), capture_output=True, text=True,
                       timeout=10, encoding='utf-8', errors='ignore')

                    results["execution_test"] = exec_result2.returncode == 0
                    results["output_captured"] = exec_result2.stdout

                    if exec_result2.returncode != 0:
                        results["error_messages"].append(f"実行エラー: {exec_result2.stderr}")
                        self.logger.warning(f"⚠️ 実行エラー: {exec_result2.stderr}")
                    else:
                        self.logger.info("✅ 実行テスト成功")
                else:
                    self.logger.info("✅ 実行テスト成功")

                if results["output_captured"]:
                    self.logger.info(f"📄 出力サンプル: {results['output_captured'][:200]}...")

            # 3. ファイル分析
            for file_path in project_dir.rglob("*.py"):
                try:
                    file_content = file_path.read_text(encoding='utf-8', errors='ignore')
                    results["file_analysis"][str(file_path.name)] = {
                        "lines": len(file_content.splitlines()),
                        "characters": len(file_content),
                        "imports": len([line for line in file_content.splitlines()
                                      if line.strip().startswith('import') or line.strip().startswith('from')])
                    }
                except Exception as e:
                    self.logger.warning(f"ファイル分析エラー {file_path.name}: {e}")

            return results

        except subprocess.TimeoutExpired:
            results["error_messages"].append("実行タイムアウト")
            self.logger.error("⏰ 実行タイムアウト")
            return results
        except Exception as e:
            results["error_messages"].append(f"テスト実行エラー: {e}")
            self.logger.error(f"💥 テスト実行エラー: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            return results

    def run_monitoring_session(self, num_tasks: int = 3, difficulty: str = "medium") -> Dict[str, Any]:
        """監視セッション実行"""
        session_start = time.time()
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        self.logger.info(f"🎬 MCP監視セッション開始: {session_id}")
        self.logger.info(f"📋 タスク数: {num_tasks}, 難易度: {difficulty}")

        session_results = {
            "session_id": session_id,
            "start_time": datetime.now().isoformat(),
            "tasks": [],
            "summary": {}
        }

        # タスク実行
        for i in range(num_tasks):
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"📝 タスク {i+1}/{num_tasks}")

            # 課題生成
            task = self.create_coding_task(difficulty)
            self.logger.info(f"🎯 課題: {task['description']}")

            # MCP実行
            result = self.execute_mcp_task(task)

            # 結果保存
            task_with_result = {**task, "result": result}
            session_results["tasks"].append(task_with_result)

            # 短時間待機（システム負荷軽減）
            time.sleep(1)

        # セッション統計
        session_time = time.time() - session_start
        session_results["end_time"] = datetime.now().isoformat()
        session_results["total_time"] = session_time

        # サマリー計算
        successful_tasks = [t for t in session_results["tasks"] if t["result"]["success"]]
        total_tasks = len(session_results["tasks"])

        session_results["summary"] = {
            "total_tasks": total_tasks,
            "successful_tasks": len(successful_tasks),
            "success_rate": (len(successful_tasks) / total_tasks * 100) if total_tasks > 0 else 0,
            "average_generation_time": sum(t["result"]["generation_time"] for t in session_results["tasks"]) / total_tasks if total_tasks > 0 else 0,
            "total_files_generated": sum(len(t["result"]["generated_files"]) for t in session_results["tasks"]),
            "syntax_success_rate": (sum(1 for t in session_results["tasks"] if t["result"]["execution_results"].get("syntax_check", False)) / total_tasks * 100) if total_tasks > 0 else 0,
            "execution_success_rate": (sum(1 for t in session_results["tasks"] if t["result"]["execution_results"].get("execution_test", False)) / total_tasks * 100) if total_tasks > 0 else 0
        }

        # 結果保存
        result_file = self.log_dir / f"{session_id}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(session_results, f, ensure_ascii=False, indent=2)

        self.logger.info(f"\n🎉 監視セッション完了!")
        self.logger.info(f"📊 成功率: {session_results['summary']['success_rate']:.1f}%")
        self.logger.info(f"📁 結果保存: {result_file}")

        return session_results

    def display_detailed_log(self, session_results: Dict[str, Any]):
        """詳細ログ表示"""
        print("\n" + "="*80)
        print("📊 MCP監視セッション詳細レポート")
        print("="*80)

        # セッション概要
        summary = session_results["summary"]
        print(f"\n🎯 セッションID: {session_results['session_id']}")
        print(f"⏱️ 実行時間: {session_results['total_time']:.2f}秒")
        print(f"📈 成功率: {summary['success_rate']:.1f}% ({summary['successful_tasks']}/{summary['total_tasks']})")
        print(f"🏗️ ファイル生成数: {summary['total_files_generated']}個")
        print(f"✅ 構文成功率: {summary['syntax_success_rate']:.1f}%")
        print(f"🚀 実行成功率: {summary['execution_success_rate']:.1f}%")
        print(f"⏱️ 平均生成時間: {summary['average_generation_time']:.2f}秒")

        print(f"\n{'='*80}")
        print("📋 タスク別詳細結果")
        print("="*80)

        # タスク別詳細
        for i, task in enumerate(session_results["tasks"], 1):
            result = task["result"]

            print(f"\n{'='*60}")
            print(f"🎯 タスク {i}: {task['description']}")
            print(f"📅 難易度: {task['difficulty']}")
            print(f"✅ 成功: {'Yes ✅' if result['success'] else 'No ❌'}")
            print(f"⏱️ 生成時間: {result['generation_time']:.2f}秒")
            print(f"⏱️ 総実行時間: {result['total_time']:.2f}秒")
            print(f"📁 生成ファイル数: {len(result['generated_files'])}個")

            if result["generated_files"]:
                print(f"📄 ファイル一覧:")
                for file in result['generated_files']:
                    print(f"   • {file}")

            # プロジェクトディレクトリ
            if "project_directory" in result:
                print(f"📂 プロジェクトパス: {result['project_directory']}")

            # 実行結果
            exec_results = result.get("execution_results", {})
            print(f"\n🔍 テスト結果:")
            print(f"   構文チェック: {'✅ 成功' if exec_results.get('syntax_check', False) else '❌ 失敗'}")
            print(f"   実行テスト: {'✅ 成功' if exec_results.get('execution_test', False) else '❌ 失敗'}")

            # エラーメッセージ
            if exec_results.get("error_messages"):
                print(f"\n❌ エラー詳細:")
                for error in exec_results["error_messages"]:
                    print(f"   • {error[:150]}")

            # 出力例
            if exec_results.get("output_captured"):
                output = exec_results["output_captured"]
                print(f"\n📄 プログラム出力:")
                print("─" * 60)
                print(output[:500])
                if len(output) > 500:
                    print("... (以下省略)")
                print("─" * 60)

            # ファイル分析
            if exec_results.get("file_analysis"):
                print(f"\n📊 コード分析:")
                for filename, analysis in exec_results["file_analysis"].items():
                    print(f"   📝 {filename}:")
                    print(f"      行数: {analysis['lines']}行")
                    print(f"      文字数: {analysis['characters']}文字")
                    print(f"      import数: {analysis['imports']}個")


def main():
    """メイン実行"""
    print("🤖 MCP監視・評価システム")
    print("="*60)
    print("NeuroHub = MCPの卵")
    print("このシステムでMCPの実装力を監視・評価します")
    print("="*60)

    # 監視システム初期化
    monitor = MCPMonitorSystem()

    # 監視セッション実行
    print("\n🚀 監視セッション開始...")
    session_results = monitor.run_monitoring_session(
        num_tasks=3,
        difficulty="medium"
    )

    # 詳細ログ表示
    monitor.display_detailed_log(session_results)

    print(f"\n{'='*80}")
    print(f"📋 詳細ログファイル: {monitor.log_dir}")
    print("🎉 MCP監視完了!")
    print("="*80)


if __name__ == "__main__":
    main()
