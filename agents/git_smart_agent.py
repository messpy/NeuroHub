#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Smart Agent - 高機能Git管理エージェント
- ファイル整理・統合
- 段階的コミット
- 自動プッシュ
- リモート設定支援
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.git_agent import GitAgent, GitStatus


@dataclass
class FileCategory:
    """ファイルカテゴリ情報"""
    name: str
    priority: int
    files: List[str]
    description: str
    should_merge: bool = False
    merge_target: Optional[str] = None


class GitSmartAgent(GitAgent):
    """スマートGit管理エージェント"""

    def __init__(self, config_path: str = None):
        super().__init__(config_path)
        self.repo_path = self.project_root  # repo_pathを設定
        self.cleanup_rules = self._load_cleanup_rules()

    def _load_cleanup_rules(self) -> Dict[str, Any]:
        """ファイル整理ルール"""
        return {
            "merge_patterns": {
                "test_*.py": "tests/",
                "*_test.py": "tests/",
                "debug_*.py": "_archive/debug/",
                "simple_*": "_archive/simple/",
                "validate_*.py": "_archive/validation/"
            },
            "delete_patterns": [
                "*.tmp",
                "*.bak",
                "__pycache__/*",
                "*.pyc",
                ".DS_Store"
            ],
            "priority_files": [
                "README.md",
                "requirements.txt",
                "setup.py",
                "config/*.yaml",
                "agents/__init__.py",
                "services/__init__.py"
            ]
        }

    def analyze_files(self) -> List[FileCategory]:
        """ファイルを分析してカテゴリ分け"""
        status = self.get_git_status()
        all_files = status.staged + status.modified + status.untracked

        categories = [
            FileCategory("critical", 1, [], "重要なコアファイル"),
            FileCategory("features", 2, [], "新機能・改善"),
            FileCategory("docs", 3, [], "ドキュメント"),
            FileCategory("tests", 4, [], "テスト関連", True, "tests/"),
            FileCategory("config", 5, [], "設定ファイル"),
            FileCategory("cleanup", 6, [], "整理・削除対象", True, "_archive/"),
            FileCategory("other", 7, [], "その他")
        ]

        # ファイル分類
        for file_path in all_files:
            path = Path(file_path)

            # カテゴリ判定
            if self._is_critical_file(file_path):
                categories[0].files.append(file_path)
            elif self._is_test_file(file_path):
                categories[3].files.append(file_path)
            elif self._is_doc_file(file_path):
                categories[2].files.append(file_path)
            elif self._is_config_file(file_path):
                categories[4].files.append(file_path)
            elif self._is_cleanup_file(file_path):
                categories[5].files.append(file_path)
            elif self._is_feature_file(file_path):
                categories[1].files.append(file_path)
            else:
                categories[6].files.append(file_path)

        return [cat for cat in categories if cat.files]

    def _is_critical_file(self, file_path: str) -> bool:
        """重要ファイル判定"""
        critical_patterns = [
            "__init__.py",
            "requirements.txt",
            "setup.py",
            "config.yaml",
            "llm_cli.py"
        ]
        return any(pattern in file_path for pattern in critical_patterns)

    def _is_test_file(self, file_path: str) -> bool:
        """テストファイル判定"""
        test_patterns = [
            "test_", "_test.py", "tests/",
            "debug_", "simple_", "validate_",
            "run_tests", "mcp_test"
        ]
        return any(pattern in file_path for pattern in test_patterns)

    def _is_doc_file(self, file_path: str) -> bool:
        """ドキュメントファイル判定"""
        return file_path.endswith(('.md', '.rst', '.txt')) and 'test' not in file_path.lower()

    def _is_config_file(self, file_path: str) -> bool:
        """設定ファイル判定"""
        config_patterns = [
            ".yaml", ".yml", ".json", ".cfg", ".ini",
            "config/", ".env"
        ]
        return any(pattern in file_path for pattern in config_patterns)

    def _is_cleanup_file(self, file_path: str) -> bool:
        """整理対象ファイル判定（正規表現使用）"""
        import re

        cleanup_patterns = [
            r'\.bak$',                    # .bakで終わる
            r'\.backup$',                 # .backupで終わる
            r'_backup\.',                 # _backup.を含む
            r'^test',                     # testで始まる
            r'TEST_',                     # TEST_を含む
            r'COMPLETION_',               # COMPLETION_を含む
            r'git_status_helper\.py$',    # 特定ファイル
            r'^fix_',                     # fix_で始まる
            r'^debug_',                   # debug_で始まる
            r'\.tmp$',                    # 一時ファイル
            r'\.old$',                    # 古いファイル
            r'_old\.',                    # _old.を含む
        ]

        return any(re.search(pattern, file_path, re.IGNORECASE) for pattern in cleanup_patterns)

    def _is_feature_file(self, file_path: str) -> bool:
        """機能ファイル判定"""
        feature_patterns = [
            "agents/", "services/", "tools/",
            ".py"
        ]
        return any(pattern in file_path for pattern in feature_patterns)

    def cleanup_files(self, dry_run: bool = True, interactive: bool = False) -> Dict[str, Any]:
        """ファイル整理実行"""
        actions = []

        # マージ対象を移動
        for category in self.analyze_files():
            if category.should_merge and category.merge_target:
                target_dir = self.project_root / category.merge_target

                for file_path in category.files:
                    source = self.project_root / file_path
                    if source.exists():
                        # 既に正しいディレクトリにある場合はスキップ
                        if str(source.parent) == str(target_dir):
                            continue

                            target = target_dir / Path(file_path).name

                            action = {
                                "type": "move",
                                "source": str(source.relative_to(self.project_root)),
                                "target": str(target.relative_to(self.project_root)),
                                "category": category.name,
                                "reason": f"{category.description} → {category.merge_target} ディレクトリに移動"
                            }
                            actions.append(action)        # 削除対象
        for pattern in self.cleanup_rules["delete_patterns"]:
            for file_path in self.project_root.glob(pattern):
                if file_path.exists() and file_path.relative_to(self.project_root) != Path("."):
                    action = {
                        "type": "delete",
                        "target": str(file_path.relative_to(self.project_root)),
                        "reason": f"不要ファイル（{pattern}パターン）"
                    }
                    actions.append(action)

        # 対話的確認
        if interactive and actions:
            actions = self._interactive_cleanup_confirmation(actions)

        # 実行
        if not dry_run and actions:
            for action in actions:
                self._execute_cleanup_action(action)

        return {
            "dry_run": dry_run,
            "actions": actions,
            "total_actions": len(actions)
        }

    def _interactive_cleanup_confirmation(self, actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """対話的整理確認"""
        print("\n" + "="*60)
        print("🧹 ファイル整理詳細確認")
        print("="*60)

        confirmed_actions = []

        # カテゴリ別にグループ化
        move_actions = [a for a in actions if a["type"] == "move"]
        delete_actions = [a for a in actions if a["type"] == "delete"]

        if move_actions:
            print(f"\n📦 移動対象: {len(move_actions)}件")
            print("-" * 40)

            for i, action in enumerate(move_actions, 1):
                print(f"\n[{i}/{len(move_actions)}] 📁 ファイル移動")
                print(f"   📄 ファイル: {action['source']}")
                print(f"   ➡️  移動先: {action['target']}")
                print(f"   💡 理由: {action['reason']}")

                # ファイル詳細情報
                source_path = self.project_root / action['source']
                if source_path.exists():
                    file_size = source_path.stat().st_size
                    print(f"   📊 サイズ: {file_size:,} bytes")

                    # ファイル内容プレビュー
                    if source_path.suffix in ['.py', '.md', '.txt', '.yaml', '.yml']:
                        try:
                            with open(source_path, 'r', encoding='utf-8') as f:
                                preview = f.read(200)
                                print(f"   👀 プレビュー: {preview[:100]}...")
                        except:
                            pass

                while True:
                    choice = input("\n   [y=移動する / n=スキップ / v=内容確認 / q=整理中止]: ").lower()

                    if choice == 'y':
                        confirmed_actions.append(action)
                        print("   ✅ 移動対象に追加")
                        break
                    elif choice == 'n':
                        print("   ⏭️  スキップ")
                        break
                    elif choice == 'v':
                        self._show_file_details(action['source'])
                    elif choice == 'q':
                        print("❌ 整理をキャンセルしました")
                        return []
                    else:
                        print("   ❓ y/n/v/q のいずれかを入力してください")

        if delete_actions:
            print(f"\n🗑️  削除対象: {len(delete_actions)}件")
            print("-" * 40)

            for i, action in enumerate(delete_actions, 1):
                print(f"\n[{i}/{len(delete_actions)}] 🗑️  ファイル削除")
                print(f"   📄 ファイル: {action['target']}")
                print(f"   💡 理由: {action['reason']}")

                # ファイル詳細情報
                target_path = self.project_root / action['target']
                if target_path.exists():
                    if target_path.is_file():
                        file_size = target_path.stat().st_size
                        print(f"   📊 サイズ: {file_size:,} bytes")
                    elif target_path.is_dir():
                        file_count = len(list(target_path.rglob("*")))
                        print(f"   📊 ディレクトリ内: {file_count}個のアイテム")

                while True:
                    choice = input("\n   [y=削除する / n=スキップ / v=内容確認 / q=整理中止]: ").lower()

                    if choice == 'y':
                        confirmed_actions.append(action)
                        print("   ✅ 削除対象に追加")
                        break
                    elif choice == 'n':
                        print("   ⏭️  スキップ")
                        break
                    elif choice == 'v':
                        self._show_file_details(action['target'])
                    elif choice == 'q':
                        print("❌ 整理をキャンセルしました")
                        return []
                    else:
                        print("   ❓ y/n/v/q のいずれかを入力してください")

        # 最終確認
        if confirmed_actions:
            print(f"\n📋 最終確認: {len(confirmed_actions)}件のアクションを実行")
            move_count = len([a for a in confirmed_actions if a["type"] == "move"])
            delete_count = len([a for a in confirmed_actions if a["type"] == "delete"])

            if move_count:
                print(f"   📦 移動: {move_count}件")
            if delete_count:
                print(f"   🗑️  削除: {delete_count}件")

            final_choice = input("\n実行しますか？ [y/N]: ").lower()
            if final_choice != 'y':
                print("❌ 整理をキャンセルしました")
                return []

        return confirmed_actions

    def _show_file_details(self, file_path: str):
        """ファイル詳細表示"""
        full_path = self.project_root / file_path

        print(f"\n📄 ファイル詳細: {file_path}")
        print("-" * 50)

        if not full_path.exists():
            print("❌ ファイルが存在しません")
            return

        # 基本情報
        stat = full_path.stat()
        print(f"📊 サイズ: {stat.st_size:,} bytes")
        print(f"📅 更新日: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}")

        # ファイル内容
        if full_path.is_file():
            try:
                if full_path.suffix in ['.py', '.md', '.txt', '.yaml', '.yml', '.json']:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read(1000)  # 最初の1000文字
                        print(f"\n📖 内容プレビュー:")
                        print("-" * 30)
                        print(content)
                        if len(content) == 1000:
                            print("... (省略)")
                elif full_path.suffix in ['.png', '.jpg', '.jpeg', '.gif']:
                    print("🖼️  画像ファイル")
                else:
                    print("📎 バイナリファイル")
            except Exception as e:
                print(f"❌ 読み込みエラー: {e}")
        elif full_path.is_dir():
            files = list(full_path.rglob("*"))
            print(f"📁 ディレクトリ: {len(files)}個のアイテム")
            for item in files[:10]:
                rel_item = item.relative_to(full_path)
                print(f"   - {rel_item}")
            if len(files) > 10:
                print(f"   ... 他 {len(files)-10}個")

        print("-" * 50)

    def _execute_cleanup_action(self, action: Dict[str, Any]):
        """整理アクション実行"""
        try:
            if action["type"] == "move":
                source_path = self.project_root / action["source"]
                target_path = self.project_root / action["target"]

                # ターゲットディレクトリ作成
                target_path.parent.mkdir(parents=True, exist_ok=True)

                # 移動実行
                shutil.move(str(source_path), str(target_path))
                print(f"   ✅ 移動完了: {action['source']} → {action['target']}")

            elif action["type"] == "delete":
                target_path = self.project_root / action["target"]

                if target_path.is_file():
                    target_path.unlink()
                    print(f"   ✅ 削除完了: {action['target']}")
                elif target_path.is_dir():
                    shutil.rmtree(target_path)
                    print(f"   ✅ ディレクトリ削除完了: {action['target']}")

        except Exception as e:
            print(f"   ❌ エラー: {action.get('source', action.get('target'))}: {e}")

    def _show_detailed_cleanup_preview(self, cleanup_result: Dict[str, Any]):
        """詳細整理プレビュー表示"""
        if cleanup_result['total_actions'] == 0:
            print("✨ 整理の必要なファイルはありません")
            return

        print(f"\n🧹 詳細整理プレビュー: {cleanup_result['total_actions']}件")
        print("=" * 60)

        # アクション種別でグループ化
        move_actions = [a for a in cleanup_result["actions"] if a["type"] == "move"]
        delete_actions = [a for a in cleanup_result["actions"] if a["type"] == "delete"]

        if move_actions:
            print(f"\n📦 移動対象: {len(move_actions)}件")
            print("-" * 40)
            for i, action in enumerate(move_actions, 1):
                print(f"{i:2d}. 📁 {action['source']}")
                print(f"     ➡️  {action['target']}")
                print(f"     💡 {action['reason']}")
                print()

        if delete_actions:
            print(f"\n🗑️  削除対象: {len(delete_actions)}件")
            print("-" * 40)
            for i, action in enumerate(delete_actions, 1):
                print(f"{i:2d}. 🗑️  {action['target']}")
                print(f"     💡 {action['reason']}")
                print()

    def show_cleanup_help(self):
        """整理ヘルプ表示"""
        print("""
🧹 Git Smart Agent - ファイル整理ヘルプ

📋 整理の目的:
  プロジェクトファイルを適切なディレクトリに配置し、
  不要ファイルを削除して、Gitリポジトリを清潔に保ちます。

📦 移動ルール:

  🔬 テストファイル → tests/
     - test_*.py, *_test.py
     - debug_*.py, simple_*.py
     - validate_*.py, fix_*.py
     理由: テスト関連ファイルを統一管理

  📚 ドキュメント → docs/
     - *.md, *.rst, *.txt（READMEなど）
     理由: ドキュメントの集約化

  📝 設定ファイル → config/
     - *.yaml, *.json, *.toml, *.ini
     理由: 設定ファイルの統一配置

  📂 古いファイル → archive/
     - *.backup, *_backup, *.old
     - outdated_*, legacy_*
     理由: 履歴保持しつつメイン領域を整理

🗑️  削除対象:
  - *.tmp, *.bak（一時ファイル）
  - __pycache__/（Python キャッシュ）
  - *.pyc（コンパイル済みPython）
  - .DS_Store（macOS システムファイル）
  - node_modules/（Node.js キャッシュ）

⚠️  注意事項:
  - 移動前にファイル内容を確認可能
  - 各アクションを個別に承認
  - いつでもキャンセル可能
  - Git履歴は保持されます

💡 おすすめワークフロー:
  1. cleanup でプレビュー確認
  2. 対話的に必要な整理のみ実行
  3. workflow で整理されたファイルをコミット
""")

    def interactive_cleanup_mode(self):
        """対話的整理モード"""
        print("🧹 対話的ファイル整理モード")
        print("コマンド: preview, interactive, help, back")

        max_iterations = 20  # 安全のための最大反復回数
        iteration_count = 0

        while iteration_count < max_iterations:
            iteration_count += 1
            try:
                command = input("\n🧹 > ").strip().lower()

                if command == "back" or command == "quit" or command == "q":
                    break
                elif command == "preview":
                    cleanup_result = self.cleanup_files(dry_run=True)
                    self._show_detailed_cleanup_preview(cleanup_result)
                elif command == "interactive":
                    cleanup_result = self.cleanup_files(dry_run=False, interactive=True)
                    if cleanup_result and cleanup_result['total_actions'] > 0:
                        print(f"✅ 整理完了: {cleanup_result['total_actions']}件処理")
                    else:
                        print("✨ 整理の必要なファイルはありませんでした")
                elif command == "help":
                    self.show_cleanup_help()
                elif command == "":
                    continue  # 空入力をスキップ
                else:
                    print("❓ 無効なコマンド。使用可能: preview, interactive, help, back")

            except KeyboardInterrupt:
                print("\n👋 対話的整理モード終了")
                break
            except EOFError:
                print("\n👋 入力終了により終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")
                print("💡 'back' で戻る、'help' でヘルプ表示")

        if iteration_count >= max_iterations:
            print("⚠️  最大反復回数に達しました。安全のため終了します。")

    def _check_remote_changes_on_startup(self):
        """起動時にリモートからの変更確認"""
        try:
            # リモート存在確認
            result = subprocess.run(
                ["git", "remote"],
                capture_output=True, text=True, cwd=self.repo_path
            )
            if not result.stdout.strip():
                print("ℹ️  リモートリポジトリが設定されていません")
                return

            print("🔍 リモートから変更をチェック中...")

            # フェッチ実行
            fetch_result = subprocess.run(
                ["git", "fetch", "--quiet"],
                capture_output=True, text=True, cwd=self.repo_path
            )

            if fetch_result.returncode != 0:
                print("⚠️  リモートへの接続に失敗しました")
                return

            # ローカルとリモートの差分確認
            diff_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD..@{u}"],
                capture_output=True, text=True, cwd=self.repo_path
            )

            if diff_result.returncode == 0:
                behind_count = int(diff_result.stdout.strip() or 0)
                if behind_count > 0:
                    print(f"📥 リモートに {behind_count} 個の新しいコミットがあります")
                    print("💡 'git pull' でマージできます")
                else:
                    print("✅ リモートと同期済み")
            else:
                print("ℹ️  リモート追跡ブランチが設定されていません")

        except Exception as e:
            print(f"⚠️  リモート確認でエラー: {e}")

    def check_remote_status(self) -> Dict[str, Any]:
        """リモートリポジトリ状態確認"""
        try:
            # リモート確認
            result = subprocess.run(
                "git remote -v",
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            if result.returncode != 0 or not result.stdout.strip():
                return {
                    "has_remote": False,
                    "remotes": [],
                    "suggestion": "リモートリポジトリが設定されていません"
                }

            # リモート解析
            remotes = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split()
                    if len(parts) >= 3:
                        remotes.append({
                            "name": parts[0],
                            "url": parts[1],
                            "type": parts[2]
                        })

            # ステータス確認
            status_result = subprocess.run(
                "git status --porcelain",
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            has_changes = bool(status_result.stdout.strip())

            # プッシュ可能性確認
            can_push = False
            ahead_count = 0

            try:
                ahead_result = subprocess.run(
                    "git rev-list --count @{u}..HEAD",
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root
                )
                if ahead_result.returncode == 0:
                    ahead_count = int(ahead_result.stdout.strip())
                    can_push = ahead_count > 0
            except:
                pass

            return {
                "has_remote": True,
                "remotes": remotes,
                "has_changes": has_changes,
                "can_push": can_push,
                "ahead_count": ahead_count
            }

        except Exception as e:
            return {
                "has_remote": False,
                "error": str(e),
                "suggestion": f"Git状態確認エラー: {e}"
            }

    def smart_commit_workflow(self, auto_push: bool = False, interactive: bool = True) -> Dict[str, Any]:
        """スマートコミットワークフロー - 対話的・段階的コミット"""
        workflow_results = {
            "timestamp": datetime.now().isoformat(),
            "phases": []
        }

        # 最初にGit状況とおすすめアクションを表示
        self._show_git_status_and_recommendations()

        # Phase 1: ファイル分析
        print("\n🔍 Phase 1: ファイル分析・カテゴリ分け")
        categories = self.analyze_files()

        self._show_analysis_results(categories)

        phase1 = {
            "name": "analysis",
            "categories": len(categories),
            "total_files": sum(len(cat.files) for cat in categories),
            "details": [{"name": cat.name, "count": len(cat.files), "priority": cat.priority} for cat in categories]
        }
        workflow_results["phases"].append(phase1)

        # Phase 2: ファイル整理提案（任意）
        cleanup_preview = None
        executed_result = None

        if interactive:
            print("\n🧹 Phase 2: ファイル整理提案")
            try:
                cleanup_preview = self.cleanup_files(dry_run=True)

                if cleanup_preview and cleanup_preview.get("total_actions", 0) > 0:
                    self._show_detailed_cleanup_preview(cleanup_preview)

                    print("\n💡 整理オプション:")
                    print("  y = 対話的整理実行（推奨）")
                    print("  a = 全て自動実行")
                    print("  n = 整理をスキップ")

                    choice = input("選択 [y/a/N]: ").lower()

                    if choice == 'y':
                        print("🧹 対話的ファイル整理開始...")
                        executed_result = self.cleanup_files(dry_run=False, interactive=True)
                        if executed_result and executed_result.get('total_actions', 0) > 0:
                            print(f"✅ 整理完了: {executed_result['total_actions']}件処理")
                    elif choice == 'a':
                        print("🧹 自動ファイル整理実行中...")
                        executed_result = self.cleanup_files(dry_run=False)
                        if executed_result:
                            print("✅ 自動整理完了")
                    else:
                        print("⏭️  整理をスキップします")
                else:
                    print("✨ 整理の必要なファイルはありません")

            except Exception as e:
                print(f"❌ 整理処理エラー: {e}")
                print(f"� エラー詳細: {type(e).__name__}")
                print("�💡 このエラーをスキップして続行します")
                print("🔧 問題が続く場合は 'help' でサポート情報を確認してください")

        phase2 = {
            "name": "cleanup_preview",
            "actions": cleanup_preview.get("total_actions", 0) if cleanup_preview else 0,
            "executed": executed_result is not None and executed_result.get("total_actions", 0) > 0
        }
        workflow_results["phases"].append(phase2)

        # Phase 3: 対話的コミット
        print("\n📝 Phase 3: 段階的コミット")
        commit_results = self._interactive_commit_process(categories, interactive)

        phase3 = {
            "name": "commits",
            "total": len(commit_results),
            "successful": len([r for r in commit_results if r["success"]]),
            "failed": len([r for r in commit_results if not r["success"]]),
            "details": commit_results
        }
        workflow_results["phases"].append(phase3)

        # Phase 4: プッシュは手動のみ（auto_pushは削除）
        if interactive and phase3["successful"] > 0:
            print(f"\n🌐 Phase 4: リモート状況確認")
            remote_status = self.check_remote_status()

            if remote_status["has_remote"] and remote_status.get("can_push"):
                print(f"📡 リモート設定済み: {len(remote_status['remotes'])}件")
                if input("\nプッシュしますか？ [y/N]: ").lower() == 'y':
                    print("📤 プッシュ実行中...")
                    push_result = self._execute_push()
                    if push_result["success"]:
                        print("✅ プッシュ完了")
                    else:
                        print(f"❌ プッシュ失敗: {push_result.get('error', '')}")
            else:
                print("⚠️  リモート未設定またはプッシュ対象なし")

        # 結果サマリー
        print(f"\n🎉 ワークフロー完了!")
        print(f"📊 コミット: {phase3['successful']}/{phase3['total']} 成功")

        return workflow_results

    def _show_git_status_and_recommendations(self):
        """Git状況とおすすめアクションを表示"""
        print("=" * 60)
        print("🚀 Git Smart Agent - インテリジェント Git 管理")
        print("=" * 60)

        # Git基本情報
        status = self.get_git_status()

        try:
            current_branch = subprocess.run(
                "git branch --show-current",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            ).stdout.strip() or "detached"

            remote_info = subprocess.run(
                "git remote get-url origin",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            ).stdout.strip() or "未設定"

        except:
            current_branch = "unknown"
            remote_info = "unknown"

        print(f"📍 ブランチ: {current_branch}")
        print(f"🌐 リモート: {remote_info}")
        print(f"📁 変更ファイル: {status.total_files}件")
        print(f"   - Staged: {len(status.staged)}件")
        print(f"   - Modified: {len(status.modified)}件")
        print(f"   - Untracked: {len(status.untracked)}件")
        if status.deleted:
            print(f"   - Deleted: {len(status.deleted)}件")

        print("\n💡 おすすめアクション:")
        if status.total_files == 0:
            print("   ✅ 変更なし - 作業お疲れさまでした！")
        elif status.total_files <= 5:
            print("   📝 ファイル数が少ないので、個別に丁寧なコミットがおすすめ")
        elif status.total_files <= 20:
            print("   🔄 適度なファイル数です。カテゴリ別にまとめてコミット")
        else:
            print("   🧹 ファイル数が多いです。整理してからのコミットを強く推奨")

        if len(status.untracked) > len(status.modified):
            print("   🆕 新規ファイルが多数あります。重要度順にコミットしましょう")

        print("\n🛠️  利用可能なコマンド:")
        print("   📊 analyze  - ファイル分析・カテゴリ分け")
        print("   🧹 cleanup  - ファイル整理・統合")
        print("   📝 workflow - 完全対話的コミット（推奨）")
        print("   🌐 remote   - リモート状況確認")
        print("   ❓ help     - 詳細ヘルプ")

    def _show_analysis_results(self, categories: List[FileCategory]):
        """ファイル分析結果表示"""
        print("\n📊 ファイル分析結果:")
        print("-" * 50)

        total_files = sum(len(cat.files) for cat in categories)

        for category in sorted(categories, key=lambda x: x.priority):
            if not category.files:
                continue

            percentage = (len(category.files) / total_files) * 100
            priority_icon = "🔥" if category.priority <= 2 else "⚡" if category.priority <= 4 else "📁"

            print(f"{priority_icon} {category.description}: {len(category.files)}件 ({percentage:.1f}%)")

            # 重要ファイルまたは削除対象は詳細表示
            if category.priority <= 2 or category.name == "cleanup":
                for file in category.files[:5]:
                    print(f"     - {file}")
                if len(category.files) > 5:
                    print(f"     ... 他 {len(category.files)-5}件")
            elif len(category.files) <= 3:
                for file in category.files:
                    print(f"     - {file}")
            else:
                print(f"     - {category.files[0]} ... 他 {len(category.files)-1}件")

        print("-" * 50)
        print(f"📈 合計: {total_files}件のファイルをカテゴリ分けしました")

    def _interactive_commit_process(self, categories: List[FileCategory], interactive: bool = True) -> List[Dict[str, Any]]:
        """対話的コミットプロセス"""
        commit_results = []

        if not interactive:
            # 非対話モードは従来通り
            return self._auto_commit_process(categories)

        print("\n" + "="*60)
        print("📝 対話的コミットプロセス開始")
        print("="*60)
        print("💡 各ファイルごとに確認しながらコミットします")
        print("💡 コミットメッセージは AI が生成し、確認・編集できます")
        print("💡 [Enter]=確定 / r=再生成 / e=編集 / s=スキップ / q=中止")

        # 優先度順にカテゴリ処理
        for category in sorted(categories, key=lambda x: x.priority):
            if not category.files:
                continue

            print(f"\n" + "="*40)
            print(f"📁 {category.description} ({len(category.files)}件)")
            print("="*40)

            # カテゴリ全体のスキップ確認
            if len(category.files) > 3:
                action = input(f"このカテゴリを処理しますか？ [y=処理/s=スキップ/q=中止]: ").lower()
                if action == 'q':
                    print("❌ ユーザーによる中止")
                    break
                elif action == 's':
                    print(f"⏭️  カテゴリ「{category.description}」をスキップ")
                    continue

            # ファイル個別処理
            for i, file_path in enumerate(category.files, 1):
                print(f"\n📄 [{i}/{len(category.files)}] {file_path}")

                # ファイル存在確認
                full_path = self.project_root / file_path
                if not full_path.exists():
                    print("   ⚠️  ファイルが存在しません（削除されたファイル）")
                    if self._handle_deleted_file(file_path):
                        commit_results.append({
                            "file": file_path,
                            "message": f":remove: {Path(file_path).name} 削除",
                            "success": True,
                            "category": category.name
                        })
                    continue

                # ステージング
                if not self.stage_file(file_path):
                    print("   ❌ ステージング失敗")
                    continue

                # 差分取得
                diff_content = self.get_file_diff(file_path, staged=True)
                if not diff_content:
                    print("   ⚠️  差分がありません - スキップ")
                    continue

                # 差分表示（簡潔版）
                self._show_diff_summary(diff_content)

                # コミットメッセージ生成・対話
                commit_result = self._interactive_commit_single_file(file_path, diff_content, category)
                if commit_result:
                    commit_results.append(commit_result)

                # 進行確認
                if i < len(category.files):
                    continue_action = input("\n次のファイルに進みますか？ [Enter=続行/q=中止]: ")
                    if continue_action.lower() == 'q':
                        print("❌ ユーザーによる中止")
                        return commit_results

        return commit_results

    def _auto_commit_process(self, categories: List[FileCategory]) -> List[Dict[str, Any]]:
        """自動コミットプロセス（非対話モード）"""
        commit_results = []

        for category in sorted(categories, key=lambda x: x.priority):
            if not category.files:
                continue

            print(f"\n📁 {category.description} ({len(category.files)}件)")

            for file_path in category.files:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    continue

                if self.stage_file(file_path):
                    diff_content = self.get_file_diff(file_path, staged=True)
                    if diff_content:
                        message = self.generate_commit_message(file_path, diff_content)

                        if self.commit_file(file_path, message):
                            commit_results.append({
                                "file": file_path,
                                "message": message,
                                "success": True,
                                "category": category.name
                            })
                            print(f"   ✅ {file_path} → {message}")
                        else:
                            commit_results.append({
                                "file": file_path,
                                "message": message,
                                "success": False,
                                "category": category.name
                            })
                            print(f"   ❌ {file_path} → コミット失敗")

        return commit_results

    def _execute_push(self) -> Dict[str, Any]:
        try:
            result = subprocess.run(
                "git push",
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root
            )

            return {
                "success": result.returncode == 0,
                "output": result.stdout,
                "error": result.stderr
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def interactive_smart_mode(self):
        """スマート対話モード"""
        import sys

        print("🚀 Git Smart Agent - 高機能モード")

        # 起動時にリモート変更確認
        self._check_remote_changes_on_startup()

        print("利用可能なコマンド:")
        print("  📊 analyze   - ファイル分析・カテゴリ分け")
        print("  🧹 cleanup   - ファイル整理提案表示（移動・削除は手動実行）")
        print("  📝 workflow  - 対話的コミットワークフロー（推奨）")
        print("  🔍 inspect   - ファイル/ディレクトリ詳細分析と質問対応")
        print("  🌿 git       - Git操作ヘルプとコマンド実行")
        print("  🤖 providers - 全AIプロバイダー状態確認")
        print("  🌐 remote    - リモート状況確認")
        print("  ❓ help      - 詳細ヘルプ")
        print("  🚪 quit      - 終了")

        loop_count = 0  # 無限ループ防止
        max_loops = 1000  # 最大ループ回数

        while loop_count < max_loops:
            loop_count += 1
            try:
                # 入力ストリーム確認
                if not sys.stdin.isatty() and sys.stdin.closed:
                    print("👋 入力ストリームが閉じられました")
                    break

                command = input("\n🤖 > ").strip().lower()

                if command == "quit" or command == "q" or command == "exit":
                    break

                elif command == "analyze":
                    categories = self.analyze_files()
                    self._show_analysis_results(categories)

                elif command == "cleanup":
                    print("\n🧹 ファイル整理提案（表示のみ）:")
                    print("  1. 基本整理提案表示")
                    print("  2. 詳細整理提案表示")
                    print("  3. カテゴリ別整理提案")
                    print("  q. 戻る")
                    print("  ⚠️ 注意: 実際の移動・削除は手動で実行してください")

                    choice = input("選択 [1-3/q]: ").strip()

                    if choice == "q" or choice == "quit":
                        continue
                    elif choice == "1":
                        cleanup_result = self.cleanup_files(dry_run=True)
                        self._show_detailed_cleanup_preview(cleanup_result)
                    elif choice == "2":
                        cleanup_result = self.cleanup_files(dry_run=True)
                        self._show_detailed_cleanup_preview(cleanup_result)
                        self._show_cleanup_commands(cleanup_result)
                    elif choice == "3":
                        self.show_categorized_cleanup_suggestions()
                    else:
                        print("❓ 1-3 の数字または q を入力してください")

                elif command == "inspect" or command == "i":
                    self.interactive_inspect_mode()

                elif command == "git" or command == "g":
                    self.interactive_git_mode()

                elif command == "providers" or command == "p":
                    self._show_all_provider_status()

                elif command == "workflow":
                    self.smart_commit_workflow(auto_push=False, interactive=True)

                elif command == "remote":
                    remote_status = self.check_remote_status()
                    if remote_status["has_remote"]:
                        print("📡 リモート設定:")
                        for remote in remote_status["remotes"]:
                            print(f"   {remote['name']}: {remote['url']}")
                        if remote_status.get("can_push"):
                            print("✅ プッシュ可能")
                        else:
                            print("⚠️  プッシュ対象なし")
                    else:
                        print("⚠️  リモート未設定")
                        print("💡 設定方法: git remote add origin <URL>")

                elif command == "help" or command == "h":
                    self._show_detailed_help()

                else:
                    print("❓ 未知のコマンド。'help' で詳細ヘルプを表示")

            except (KeyboardInterrupt, EOFError):
                print("\n👋 入力終了により終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")

        if loop_count >= max_loops:
            print("⚠️ 最大ループ回数に達しました。安全のため終了します。")

        print("👋 Git Smart Agent 終了")

    def interactive_inspect_mode(self):
        """ファイル/ディレクトリ詳細分析と質問対応モード"""
        print("\n🔍 ファイル/ディレクトリ インスペクター")
        print("指定したパスの詳細分析と質問対応を行います")
        print("コマンド例: analyze README.md, ask このファイルの目的は？, back")

        current_target = None
        current_analysis = None
        max_iterations = 50
        iteration_count = 0

        while iteration_count < max_iterations:
            iteration_count += 1
            try:
                if current_target:
                    prompt = f"\n🔍 [{current_target}] > "
                else:
                    prompt = "\n🔍 > "

                user_input = input(prompt).strip()

                if user_input.lower() in ["back", "quit", "q", "exit"]:
                    break

                elif user_input.startswith("analyze "):
                    path = user_input[8:].strip()
                    if path.startswith('"') and path.endswith('"'):
                        path = path[1:-1]

                    result = self._analyze_path(path)
                    if result:
                        current_target = path
                        current_analysis = result
                        self._show_path_analysis(result)
                    else:
                        print(f"❌ パス '{path}' の分析に失敗しました")

                elif user_input.startswith("ask "):
                    if not current_analysis:
                        print("❌ まず 'analyze <path>' でファイル/ディレクトリを分析してください")
                        continue

                    question = user_input[4:].strip()
                    if question:
                        answer = self._answer_about_path(current_analysis, question)
                        print(f"\n💬 回答:\n{answer}")
                    else:
                        print("❓ 質問を入力してください。例: ask このファイルの目的は？")

                elif user_input.lower() == "help":
                    self._show_inspect_help()

                elif user_input == "":
                    continue

                else:
                    print("❓ 無効なコマンド。使用可能:")
                    print("  analyze <path> - ファイル/ディレクトリ分析")
                    print("  ask <question> - 分析済みパスについて質問")
                    print("  help - ヘルプ表示")
                    print("  back - 戻る")

            except KeyboardInterrupt:
                print("\n👋 インスペクターを終了")
                break
            except EOFError:
                print("\n👋 入力終了により終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")

        if iteration_count >= max_iterations:
            print("⚠️  最大反復回数に達しました。")

    def _analyze_path(self, path: str):
        """指定されたパスの簡易分析"""
        try:
            from pathlib import Path

            target_path = Path(path)
            if not target_path.exists():
                target_path = self.project_root / path
                if not target_path.exists():
                    return None

            analysis = {
                "path": str(target_path),
                "name": target_path.name,
                "is_file": target_path.is_file(),
                "is_dir": target_path.is_dir(),
                "size": 0
            }

            if target_path.is_file() and target_path.stat().st_size < 100000:  # 100KB以下
                try:
                    with open(target_path, 'r', encoding='utf-8', errors='ignore') as f:
                        analysis["content"] = f.read(1000)  # 最初の1000文字
                except:
                    analysis["content"] = "[読み取り不可]"
                analysis["size"] = target_path.stat().st_size

            elif target_path.is_dir():
                files = list(target_path.glob("*"))[:20]  # 最大20ファイル
                analysis["file_count"] = len(files)
                analysis["files"] = [f.name for f in files if f.is_file()][:10]

            return analysis

        except Exception:
            return None

    def _show_path_analysis(self, analysis):
        """パス分析結果の簡易表示"""
        print(f"\n📋 分析結果: {analysis['name']}")
        print("=" * 40)

        if analysis["is_file"]:
            print(f"📄 ファイル: {analysis['path']}")
            if analysis.get("size"):
                print(f"📏 サイズ: {analysis['size']} bytes")
            if analysis.get("content"):
                print(f"\n📖 内容プレビュー:")
                lines = analysis["content"].split('\n')[:5]
                for line in lines:
                    print(f"  {line[:80]}")

        elif analysis["is_dir"]:
            print(f"📁 ディレクトリ: {analysis['path']}")
            if analysis.get("file_count"):
                print(f"📊 ファイル数: {analysis['file_count']}件")
            if analysis.get("files"):
                print(f"📄 主要ファイル: {', '.join(analysis['files'][:5])}")

        print("\n💡 'ask <質問>' で詳細を質問できます")

    def _answer_about_path(self, analysis, question: str) -> str:
        """パスについての簡易回答"""
        question_lower = question.lower()

        if analysis["is_file"]:
            if "目的" in question or "何" in question:
                ext = Path(analysis["name"]).suffix.lower()
                if ext == ".py":
                    return f"Pythonスクリプトファイルです。プログラムコードが含まれています。"
                elif ext == ".md":
                    return f"Markdownドキュメントです。説明書や仕様書として使用されています。"
                elif ext in [".yaml", ".yml", ".json"]:
                    return f"設定ファイルです。アプリケーションの動作設定が定義されています。"
                else:
                    return f"{ext}形式のファイルです。"

            elif "機能" in question and analysis.get("content"):
                if "def " in analysis["content"]:
                    return "このファイルには関数定義が含まれており、何らかの処理機能を提供しています。"
                elif "class " in analysis["content"]:
                    return "このファイルにはクラス定義が含まれており、オブジェクト指向の機能を提供しています。"

        elif analysis["is_dir"]:
            if "目的" in question or "何" in question:
                return f"ディレクトリで、{analysis.get('file_count', 0)}個のファイルが含まれています。プロジェクトの一部として機能分割されていると推測されます。"

        return "より具体的な質問をしていただけると、詳細な回答を提供できます。"

    def _show_inspect_help(self):
        """インスペクター機能の簡易ヘルプ"""
        print("""
🔍 インスペクター - ヘルプ

使い方:
  analyze <path> - ファイル/ディレクトリ分析
  ask <question> - 質問
  back - 戻る

例:
  analyze README.md
  ask このファイルの目的は？
""")

    def interactive_git_mode(self):
        """Git操作モード"""
        print("\n🌿 Git操作モード")
        print("Git情報確認、操作実行、ヘルプを提供します")
        print("コマンド例: status, branch, diff, reset, log, help, back")

        max_iterations = 50
        iteration_count = 0

        # 現在のGit状況を表示
        self._show_current_git_status()

        while iteration_count < max_iterations:
            iteration_count += 1
            try:
                user_input = input("\n🌿 git > ").strip()

                if user_input.lower() in ["back", "quit", "q", "exit"]:
                    break

                elif user_input == "status" or user_input == "st":
                    self._show_detailed_git_status()

                elif user_input == "branch" or user_input == "br":
                    self._show_branch_info()

                elif user_input.startswith("diff"):
                    parts = user_input.split()
                    if len(parts) == 1:
                        self._show_diff_summary()
                    elif len(parts) == 2:
                        self._show_diff_with_target(parts[1])
                    else:
                        self._show_diff_help()

                elif user_input.startswith("reset"):
                    parts = user_input.split()
                    if len(parts) == 1:
                        self._show_reset_options()
                    else:
                        self._handle_reset_request(parts[1:])

                elif user_input == "log" or user_input.startswith("log "):
                    parts = user_input.split()
                    count = 10
                    if len(parts) > 1 and parts[1].isdigit():
                        count = int(parts[1])
                    self._show_commit_log(count)

                elif user_input == "help" or user_input == "h":
                    self._show_git_help()

                elif user_input.startswith("search "):
                    query = user_input[7:].strip()
                    if query:
                        self._search_git_knowledge(query)
                    else:
                        print("使用例: search git reset の使い方")

                elif user_input == "":
                    continue

                else:
                    # 直接Gitコマンド実行を提案
                    self._suggest_git_command(user_input)

            except KeyboardInterrupt:
                print("\n👋 Git操作モード終了")
                break
            except EOFError:
                print("\n👋 入力終了により終了します")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")

        if iteration_count >= max_iterations:
            print("⚠️  最大反復回数に達しました。")

    def _show_current_git_status(self):
        """現在のGit状況表示"""
        try:
            # 現在のブランチ
            branch_result = subprocess.run(
                "git branch --show-current",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "不明"

            # 未コミット変更
            status_result = subprocess.run(
                "git status --porcelain",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )
            changes = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

            print(f"\n📍 現在の状況:")
            print(f"🌿 ブランチ: {current_branch}")
            print(f"📝 未コミット変更: {len([c for c in changes if c])}件")

            if changes and changes[0]:
                print("📋 変更ファイル:")
                for change in changes[:5]:
                    if change:
                        status_code = change[:2]
                        filename = change[3:]
                        status_desc = self._get_status_description(status_code)
                        print(f"   {status_desc} {filename}")
                if len(changes) > 5:
                    print(f"   ... 他 {len(changes)-5}件")

        except Exception as e:
            print(f"❌ Git状況取得エラー: {e}")

    def _get_status_description(self, status_code: str) -> str:
        """Git status コードの説明"""
        status_map = {
            "??": "🆕 新規",
            "A ": "➕ 追加",
            "M ": "📝 修正",
            "MM": "📝 修正",
            " M": "📝 修正",
            "D ": "🗑️ 削除",
            "R ": "🔄 移動",
            "C ": "📋 複製"
        }
        return status_map.get(status_code, f"❓ {status_code}")

    def _show_detailed_git_status(self):
        """詳細なGit status表示"""
        try:
            result = subprocess.run(
                "git status",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )
            if result.returncode == 0:
                print("\n📊 詳細ステータス:")
                print(result.stdout)
            else:
                print(f"❌ git statusエラー: {result.stderr}")
        except Exception as e:
            print(f"❌ エラー: {e}")

    def _show_branch_info(self):
        """ブランチ情報表示"""
        try:
            # ローカルブランチ
            local_result = subprocess.run(
                "git branch -v",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )

            # リモートブランチ
            remote_result = subprocess.run(
                "git branch -r",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )

            print("\n🌿 ブランチ情報:")
            if local_result.returncode == 0:
                print("📍 ローカルブランチ:")
                for line in local_result.stdout.strip().split('\n'):
                    if line.strip():
                        print(f"   {line}")

            if remote_result.returncode == 0 and remote_result.stdout.strip():
                print("\n🌐 リモートブランチ:")
                for line in remote_result.stdout.strip().split('\n')[:10]:
                    if line.strip():
                        print(f"   {line.strip()}")

        except Exception as e:
            print(f"❌ ブランチ情報取得エラー: {e}")

    def _show_diff_summary(self):
        """差分サマリー表示"""
        try:
            # 作業ディレクトリとステージの差分
            working_result = subprocess.run(
                "git diff --stat",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )

            # ステージとHEADの差分
            staged_result = subprocess.run(
                "git diff --cached --stat",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )

            print("\n📊 差分サマリー:")

            if working_result.stdout.strip():
                print("🔧 作業ディレクトリの変更:")
                print(working_result.stdout)
            else:
                print("🔧 作業ディレクトリ: 変更なし")

            if staged_result.stdout.strip():
                print("📋 ステージ済みの変更:")
                print(staged_result.stdout)
            else:
                print("📋 ステージ: 変更なし")

        except Exception as e:
            print(f"❌ 差分取得エラー: {e}")

    def _show_diff_with_target(self, target: str):
        """指定したターゲットとの差分表示"""
        try:
            result = subprocess.run(
                f"git diff --stat {target}",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )

            if result.returncode == 0:
                print(f"\n📊 {target}との差分:")
                if result.stdout.strip():
                    print(result.stdout)
                else:
                    print("差分なし")
            else:
                print(f"❌ 差分取得エラー: {result.stderr}")

        except Exception as e:
            print(f"❌ エラー: {e}")

    def _show_reset_options(self):
        """リセットオプション表示"""
        print("""
🔄 Git Reset オプション:

⚠️ 重要: 以下のコマンドは慎重に使用してください

💡 基本的なリセット:
  reset HEAD~1     - 最新コミットを取り消し（変更は保持）
  reset --soft     - コミットのみ取り消し（ステージも保持）
  reset --hard     - すべて取り消し（⚠️ 変更も削除）

📝 使用例:
  • 最新コミットをやり直したい → reset HEAD~1
  • コミットメッセージを修正したい → reset --soft HEAD~1
  • すべてを元に戻したい → reset --hard HEAD~1

⚠️ 注意: --hard は変更が完全に失われます！

🔍 詳細確認コマンド:
  • log 5 - 最新5件のコミット履歴表示
  • diff HEAD~1 - 前のコミットとの差分表示
""")

    def _handle_reset_request(self, args: list):
        """リセット要求の処理"""
        if not args:
            self._show_reset_options()
            return

        reset_arg = " ".join(args)

        print(f"⚠️ 実行しようとしているコマンド: git reset {reset_arg}")
        print("⚠️ このコマンドは変更を取り消します。本当に実行しますか？")

        if "--hard" in reset_arg:
            print("🚨 --hard オプションは作業ディレクトリの変更も削除します！")

        choice = input("\n実行しますか？ [yes/No]: ").lower()

        if choice in ["yes", "y"]:
            try:
                result = subprocess.run(
                    f"git reset {reset_arg}",
                    shell=True, capture_output=True, text=True, cwd=self.project_root
                )

                if result.returncode == 0:
                    print("✅ リセット完了")
                    if result.stdout:
                        print(result.stdout)
                    # 現在の状況を再表示
                    self._show_current_git_status()
                else:
                    print(f"❌ リセットエラー: {result.stderr}")

            except Exception as e:
                print(f"❌ エラー: {e}")
        else:
            print("❌ リセットをキャンセルしました")

    def _show_commit_log(self, count: int = 10):
        """コミットログ表示"""
        try:
            result = subprocess.run(
                f"git log --oneline -n {count}",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )

            if result.returncode == 0:
                print(f"\n📜 最新{count}件のコミット:")
                for i, line in enumerate(result.stdout.strip().split('\n'), 1):
                    if line.strip():
                        print(f"  {i:2}. {line}")
            else:
                print(f"❌ ログ取得エラー: {result.stderr}")

        except Exception as e:
            print(f"❌ エラー: {e}")

    def _search_git_knowledge(self, query: str):
        """Git知識検索（将来的にDB・Web検索対応予定）"""
        print(f"\n🔍 検索中: {query}")

        # 現在は基本的なローカル知識ベース
        knowledge_base = {
            "reset": """
🔄 Git Reset について:

基本的な使い方:
• git reset HEAD~1 - 最新コミットを取り消し
• git reset --soft HEAD~1 - コミットのみ取り消し
• git reset --hard HEAD~1 - 変更も含めて完全取り消し

モード説明:
• --soft: HEADのみ移動、ステージとワーキングディレクトリは保持
• --mixed (デフォルト): HEADとインデックスをリセット、ワーキングディレクトリは保持
• --hard: すべてリセット（⚠️ 変更が失われます）
""",
            "diff": """
📊 Git Diff について:

基本コマンド:
• git diff - ワーキングディレクトリとステージの差分
• git diff --cached - ステージとHEADの差分
• git diff HEAD - ワーキングディレクトリとHEADの差分
• git diff HEAD~1 - 前のコミットとの差分

オプション:
• --stat - 変更統計のみ表示
• --name-only - ファイル名のみ表示
""",
            "branch": """
🌿 Git Branch について:

基本操作:
• git branch - ローカルブランチ一覧
• git branch -r - リモートブランチ一覧
• git branch <name> - 新規ブランチ作成
• git checkout <name> - ブランチ切り替え
• git checkout -b <name> - 作成して切り替え
"""
        }

        # キーワードマッチング
        found = False
        for keyword, info in knowledge_base.items():
            if keyword.lower() in query.lower():
                print(info)
                found = True
                break

        if not found:
            print(f"""
❓ '{query}' について詳細な情報は現在のローカル知識ベースにありません。

💡 利用可能な検索キーワード:
• reset - git resetの使い方
• diff - git diffの使い方
• branch - git branchの使い方

🚀 将来的な機能拡張予定:
• データベース連携による詳細情報提供
• Web検索による最新情報取得
• AI による個別状況に応じた回答生成
""")

    def _suggest_git_command(self, user_input: str):
        """Gitコマンドの提案"""
        suggestions = {
            "今のブランチ": "git branch --show-current",
            "ブランチ一覧": "git branch -v",
            "コミット履歴": "git log --oneline -10",
            "前のコミット": "git reset HEAD~1",
            "差分確認": "git diff",
            "状況確認": "git status"
        }

        print(f"\n💡 '{user_input}' に対する提案:")

        # キーワードマッチング
        found_suggestions = []
        for keyword, command in suggestions.items():
            if any(word in user_input for word in keyword.split()):
                found_suggestions.append((keyword, command))

        if found_suggestions:
            for keyword, command in found_suggestions:
                print(f"• {keyword}: {command}")

            choice = input("\nコマンドを実行しますか？ [コマンド番号/n]: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(found_suggestions):
                    self._execute_safe_git_command(found_suggestions[idx][1])
        else:
            print("• 該当する提案が見つかりませんでした")
            print("• 'help' でGitコマンド一覧を確認してください")

    def _execute_safe_git_command(self, command: str):
        """安全なGitコマンド実行"""
        safe_commands = [
            "git status", "git branch", "git log", "git diff",
            "git show", "git branch --show-current"
        ]

        is_safe = any(command.startswith(safe_cmd) for safe_cmd in safe_commands)

        if is_safe:
            try:
                result = subprocess.run(
                    command, shell=True, capture_output=True, text=True, cwd=self.project_root
                )

                if result.returncode == 0:
                    print(f"\n💻 実行: {command}")
                    print(result.stdout)
                else:
                    print(f"❌ エラー: {result.stderr}")

            except Exception as e:
                print(f"❌ 実行エラー: {e}")
        else:
            print(f"⚠️ 安全性のため、コマンド '{command}' の自動実行は制限されています")
            print("手動で実行してください")

    def _show_git_help(self):
        """Gitヘルプ表示"""
        print("""
🌿 Git操作モード - ヘルプ

📍 状況確認:
  status, st     - 詳細な Git status
  branch, br     - ブランチ情報表示
  log [数]       - コミット履歴表示（デフォルト10件）

📊 差分確認:
  diff           - 現在の差分サマリー
  diff HEAD~1    - 前のコミットとの差分
  diff <commit>  - 指定コミットとの差分

🔄 操作:
  reset          - リセットオプション表示
  reset HEAD~1   - 最新コミットを取り消し（要確認）

🔍 検索・ヘルプ:
  search <query> - Git知識検索
  help, h        - このヘルプ表示

💬 自然言語:
  今のブランチは？      → ブランチ情報表示
  前のコミットとの差分   → 差分表示
  コミットを一つ戻りたい → リセット提案

🚀 将来予定機能:
  • データベース連携による詳細情報
  • Web検索による最新Git情報取得
  • AI による状況に応じたアドバイス

⚠️ 注意:
  変更を伴う操作は確認後に実行されます
  重要な操作前には必ずバックアップを取ってください
""")

    def _show_all_provider_status(self):
        """全AIプロバイダーの詳細状態表示"""
        print("\n🤖 AIプロバイダー状態確認")
        print("=" * 50)

        providers = ['gemini', 'huggingface', 'ollama']

        for provider in providers:
            print(f"\n🔍 {provider.title()} プロバイダー:")
            try:
                # プロバイダー接続テスト
                if provider == 'gemini':
                    status = self._test_gemini_connection()
                elif provider == 'huggingface':
                    status = self._test_huggingface_connection()
                elif provider == 'ollama':
                    status = self._test_ollama_connection()
                else:
                    status = {'connected': False, 'error': '未サポート'}

                if status['connected']:
                    print(f"   ✅ 接続OK - {status.get('model', 'N/A')}")
                    if 'details' in status:
                        print(f"      {status['details']}")
                else:
                    print(f"   × 接続失敗 - {status.get('error', '不明なエラー')}")
                    if 'token_status' in status:
                        print(f"      TOKEN: {status['token_status']}")

            except Exception as e:
                print(f"   × エラー - {str(e)}")

        print("\n💡 プロバイダー使用順序: Gemini → HuggingFace → Ollama")

    def _test_gemini_connection(self) -> Dict[str, Any]:
        """Gemini接続テスト"""
        try:
            from services.llm.provider_gemini import GeminiProvider
            provider = GeminiProvider()

            # 簡単なテストプロンプト
            result = provider.generate_text("Hello", max_tokens=10)

            return {
                'connected': True,
                'model': 'gemini-1.5-flash',
                'details': f'レスポンス長: {len(result)} chars'
            }
        except Exception as e:
            error_msg = str(e)
            if "API_KEY" in error_msg or "key" in error_msg.lower():
                return {'connected': False, 'error': 'API_KEY未設定またはTOKEN期限切れ', 'token_status': '期限切れ'}
            elif "quota" in error_msg.lower():
                return {'connected': False, 'error': 'クォータ超過', 'token_status': 'クォータ不足'}
            else:
                return {'connected': False, 'error': f'接続エラー: {error_msg}'}

    def _test_huggingface_connection(self) -> Dict[str, Any]:
        """HuggingFace接続テスト"""
        try:
            from services.llm.provider_huggingface import HuggingFaceProvider
            provider = HuggingFaceProvider()

            result = provider.generate_text("Hello", max_tokens=10)

            return {
                'connected': True,
                'model': 'meta-llama/Llama-2-7b-chat-hf',
                'details': f'レスポンス長: {len(result)} chars'
            }
        except Exception as e:
            error_msg = str(e)
            if "token" in error_msg.lower() or "unauthorized" in error_msg.lower():
                return {'connected': False, 'error': 'TOKEN無効または期限切れ', 'token_status': '期限切れ'}
            else:
                return {'connected': False, 'error': f'接続エラー: {error_msg}'}

    def _test_ollama_connection(self) -> Dict[str, Any]:
        """Ollama接続テスト"""
        try:
            try:
                import requests
            except ImportError:
                return {'connected': False, 'error': 'requests ライブラリが必要です'}

            # Ollamaサービス確認
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    models = response.json().get('models', [])
                    model_count = len(models)
                    return {
                        'connected': True,
                        'model': 'ollama-server',
                        'details': f'利用可能モデル: {model_count}個'
                    }
                else:
                    return {'connected': False, 'error': f'Ollamaサーバー応答エラー: {response.status_code}'}
            except requests.exceptions.RequestException:
                return {'connected': False, 'error': 'Ollamaサーバー未起動またはアクセス不可'}

        except Exception as e:
            return {'connected': False, 'error': f'Ollama接続エラー: {str(e)}'}

    def _show_detailed_help(self):
        """詳細ヘルプ表示"""
        print("""
🚀 Git Smart Agent - 詳細ヘルプ

📋 概要:
  このツールは、Gitの複雑な操作を自動化し、
  AIによるコミットメッセージ生成で効率的な開発をサポートします。

🔧 主要機能詳細:

  📊 analyze - ファイル分析・カテゴリ分け
     🎯 何ができる:
       • 変更ファイルを重要度・種類別に自動分類
       • ファイル数と変更規模の可視化
       • 優先的にコミットすべきファイルの特定

     📂 カテゴリ詳細:
       🔥 重要・緊急: __init__.py, main.py, setup.py, requirements.txt
       ⚡ 機能開発: .py/.js/.ts ファイル（コア機能）
       📝 ドキュメント: README.md, .md ファイル
       🧪 テスト: test_*, *_test.py, tests/ 内ファイル
       ⚙️  設定: .yaml, .json, .toml, .ini ファイル
       🗂️  整理対象: 古いファイル、一時ファイル、重複ファイル
       📁 その他: 上記以外のファイル

  🧹 cleanup - ファイル整理（表示のみ）
     🎯 何ができる:
       • ファイル整理の提案と詳細説明表示
       • 移動先ディレクトリと理由の明示
       • プロジェクト構造の最適化案提示
       • ⚠️ 注意: 実際の移動・削除は行いません（表示のみ）

     🗂️  整理パターン:
       • テストファイル → tests/ ディレクトリ
       • 設定ファイル → config/ ディレクトリ
       • ドキュメント → docs/ ディレクトリ
       • 古いファイル → archive/ ディレクトリ
       • 一時ファイル → 削除候補として表示

  📝 workflow - 対話的コミット（推奨）
     🎯 何ができる:
       • Git状況の詳細分析と表示
       • ファイル別の差分詳細表示
       • AIによる自動コミットメッセージ生成
       • メッセージの確認・編集・再生成
       • 1ファイルずつの段階的コミット実行

     💬 コミット対話オプション:
       Enter: メッセージを確定してコミット
       r: AIで新しいメッセージを再生成
       e: 手動でメッセージを編集
       d: より詳細なメッセージを再生成
       s: このファイルをスキップ
       q: コミットプロセスを中止

  🤖 providers - AIプロバイダー状態確認
     🎯 何ができる:
       • 全AIプロバイダーの接続状況確認
       • APIキーの有効性チェック
       • モデル利用可能性の検証
       • エラー詳細とトラブルシューティング情報

  🌿 git - Git操作ヘルプとコマンド実行
     🎯 何ができる:
       • 現在のブランチ・状況確認
       • コミット履歴の表示
       • 差分確認（前のコミットとの比較等）
       • 安全なリセット操作の実行
       • Git知識検索とコマンド提案
       • 自然言語でのGit操作質問対応

     💬 自然言語対応例:
       • "今のブランチは？" → ブランチ情報表示
       • "前のコミットとの差分は？" → 差分表示
       • "コミットを一つ戻りたい" → リセット提案・実行
       • "最新10件のコミット" → ログ表示

💡 使用シナリオ別ガイド:

  🆕 新規プロジェクト開始時:
     1. 'analyze' でファイル状況を把握
     2. 'cleanup' で整理提案を確認
     3. 'workflow' で初回コミット実行

  � 日常の開発作業:
     1. 'analyze' で変更ファイルを確認
     2. 'workflow' で段階的コミット
     3. 'push' でリモート同期

  🧹 プロジェクト整理時:
     1. 'cleanup' で整理案を確認
     2. 手動でファイル移動・削除実行
     3. 'workflow' で整理結果をコミット

🎪 コミットメッセージ形式:
  :add: 新機能・新ファイル追加
  :fix: バグ修正・問題解決
  :update: 既存機能の改善・更新
  :refactor: コードの構造改善
  :docs: ドキュメント更新・追加
  :test: テスト追加・修正
  :config: 設定ファイル変更
  :remove: ファイル削除・機能削除
  :move: ファイル移動・リネーム

❓ よくある質問とカテゴリ別活用法:

  📊 analyze機能について:
  Q: どのファイルを優先的にコミットすべき？
  A: 🔥重要・緊急カテゴリを最優先、次に⚡機能開発を処理

  Q: ファイルが多すぎて把握できない
  A: analyzeで自動分類後、カテゴリ別に段階的に処理

  🧹 cleanup機能について:
  Q: 本当に削除・移動しても大丈夫？
  A: このツールは提案表示のみ。実際の操作は手動で安全確認後に実行

  Q: プロジェクト構造を最適化したい
  A: cleanup結果を参考に、同種ファイルを適切なディレクトリに整理

  📝 workflow機能について:
  Q: コミットメッセージが気に入らない
  A: 'r'で再生成、'e'で手動編集、'd'でより詳細な生成が可能

  Q: 特定のファイルだけコミットしたい
  A: workflow中に不要ファイルを's'でスキップ

  🤖 providers機能について:
  Q: AIが応答しない
  A: providersでAPIキー設定や接続状況を確認

  🌿 git機能について:
  Q: 今のブランチを知りたい
  A: 'git' → 'branch' または 'git' → "今のブランチは？"

  Q: コミットを一つ戻したい
  A: 'git' → 'reset HEAD~1' または 'git' → "コミットを一つ戻りたい"

  Q: 前のコミットとの差分を見たい
  A: 'git' → 'diff HEAD~1' または 'git' → "前のコミットとの差分は？"

  Q: Gitコマンドがわからない
  A: 'git' → 'search <操作名>' で知識検索、'help'で一覧表示

  Q: 安全にGit操作をしたい
  A: git機能は危険な操作前に確認画面が表示されます

  ⚙️ 一般的な使い方:
  Q: 初めて使う時は何から始める？
  A: まず'analyze'で状況把握、次に'workflow'で対話的コミット

  Q: 他のプロジェクトでも使える？
  A: はい。Gitが使われていれば、どのプロジェクトでも利用可能

  🚀 将来の機能拡張予定:
  Q: もっと詳細なGit情報が欲しい
  A: データベース連携・Web検索機能を開発中です

  Q: AI によるGitアドバイスは？
  A: 状況に応じたカスタマイズ回答機能を計画中です
""")

    def add_helper_methods_here(self):
        # 以下にヘルパーメソッドを追加する場所を確保
        pass

    def _show_diff_summary(self, diff_content: str):
        """差分サマリー表示（正規表現使用）"""
        import re

        lines = diff_content.split('\n')
        # 正規表現でより正確にマッチング
        added_lines = len([l for l in lines if re.match(r'^\+[^+]', l)])
        removed_lines = len([l for l in lines if re.match(r'^-[^-]', l)])

        print(f"   📊 変更: +{added_lines} -{removed_lines} 行")

        # 重要な変更のプレビュー
        important_changes = []
        for line in lines[:20]:
            if re.match(r'^\+[^+]', line):
                clean_line = line[1:].strip()
                if clean_line and not clean_line.startswith('#'):
                    important_changes.append(f"   + {clean_line[:60]}")
            elif re.match(r'^-[^-]', line):
                clean_line = line[1:].strip()
                if clean_line and not clean_line.startswith('#'):
                    important_changes.append(f"   - {clean_line[:60]}")

        if important_changes:
            print("   🔍 主な変更:")
            for change in important_changes[:3]:
                print(change)
            if len(important_changes) > 3:
                print(f"   ... 他 {len(important_changes)-3}件の変更")

    def _interactive_commit_single_file(self, file_path: str, diff_content: str, category: FileCategory) -> Optional[Dict[str, Any]]:
        """単一ファイルの対話的コミット"""
        rejected_messages = []
        max_interactions = 10  # 最大対話回数制限
        interaction_count = 0

        # 初回コミットメッセージ生成
        message, generator = self._generate_better_commit_message(file_path, diff_content, rejected_messages)

        while interaction_count < max_interactions:
            interaction_count += 1

            print(f"\n💬 コミットメッセージ案:")
            print(f"   {message}")
            print(f"   🤖 生成者: {generator}")

            action = input("\n[Enter=確定 / r=再生成 / e=編集 / d=詳細再生成 / s=スキップ / h=ヘルプ / q=中止]: ").lower()

            if action == "" or action == "y":
                # コミット確定
                if self.commit_file(file_path, message):
                    print(f"   ✅ コミット完了: {file_path}")
                    return {
                        "file": file_path,
                        "message": message,
                        "success": True,
                        "category": category.name
                    }
                else:
                    print(f"   ❌ コミット失敗: {file_path}")
                    return {
                        "file": file_path,
                        "message": message,
                        "success": False,
                        "category": category.name
                    }

            elif action == "r":
                # 再生成制限チェック
                if len(rejected_messages) >= 5:
                    print("   ⚠️  再生成回数上限に達しました。現在のメッセージで確定するか編集してください。")
                    continue

                rejected_messages.append(message)
                new_message, new_generator = self._generate_better_commit_message(file_path, diff_content, rejected_messages)
                if new_message != message:
                    message = new_message
                    generator = new_generator
                else:
                    print("   ⚠️  新しいメッセージを生成できませんでした（フォールバック使用済み）")

            elif action == "e":
                # 編集
                new_message = input(f"新しいメッセージを入力: ")
                if new_message.strip():
                    message = new_message.strip()
                    generator = "ユーザー編集"

            elif action == "d":
                # 詳細再生成
                rejected_messages.append(message)
                message = self._generate_detailed_commit_message(file_path, diff_content, rejected_messages)

            elif action == "s":
                # スキップ
                print(f"   ⏭️  スキップ: {file_path}")
                # アンステージ
                subprocess.run(f"git restore --staged -- {file_path}", shell=True, cwd=self.project_root)
                return None

            elif action == "h":
                # ヘルプ
                self._show_commit_help()

            elif action == "q":
                # 中止
                print("❌ ユーザーによる中止")
                return None

            else:
                print("❓ 無効な入力です。h でヘルプを表示")

        # 最大対話回数に達した場合の強制終了
        if interaction_count >= max_interactions:
            print(f"   ⚠️  最大対話回数({max_interactions})に達しました。現在のメッセージでコミットします。")
            if self.commit_file(file_path, message):
                print(f"   ✅ 強制コミット完了: {file_path}")
                return {
                    "file": file_path,
                    "message": message,
                    "success": True,
                    "category": category.name
                }
            else:
                print(f"   ❌ 強制コミット失敗: {file_path}")
                return {
                    "file": file_path,
                    "message": message,
                    "success": False,
                    "category": category.name
                }

        return None

    def _generate_better_commit_message(self, file_path: str, diff_content: str, rejected_messages: List[str] = None) -> tuple:
        """改良されたコミットメッセージ生成 - チャンク処理対応"""
        if rejected_messages is None:
            rejected_messages = []

        # ファイル分析
        path_obj = Path(file_path)
        filename = path_obj.name

        # 差分が長い場合はチャンク処理を試行
        if len(diff_content) > 1000:
            print(f"   📝 差分が長いため、チャンク処理を実行...")

            # より確実なチャンク処理でコミットメッセージ生成
            instruction = f"次のGit差分の内容を分析し、{filename}ファイルで何が変更されたかを詳しく説明してください"

            try:
                # チャンク数を制限（プロバイダー負荷軽減）
                max_chunks = 5
                estimated_chunks = len(diff_content) // 500 + 1

                if estimated_chunks > max_chunks:
                    # チャンクが多すぎる場合は要約してから処理
                    chunk_size = len(diff_content) // max_chunks
                    print(f"   ⚠️ チャンク数制限: {estimated_chunks} → {max_chunks} (サイズ: {chunk_size})")
                else:
                    chunk_size = 500  # デフォルトサイズ
                    print(f"   ℹ️ チャンク処理: {estimated_chunks}個 (サイズ: {chunk_size})")

                response = self.llm_agent.generate_text_chunked(
                    text=diff_content,
                    chunk_size=chunk_size,
                    instruction=instruction,
                    combine_instruction=f"上記の{filename}の変更分析を基に、適切なGitコミットメッセージを日本語で30文字以内で作成してください。フォーマット例: ':update: 機能追加'"
                )

                if response.is_success and response.content:
                    # 日本語チェックとクリーニング
                    message = response.content.strip()
                    if any('\u3040' <= char <= '\u309F' or '\u30A0' <= char <= '\u30FF' or '\u4E00' <= char <= '\u9FAF' for char in message):
                        message = self._clean_commit_message(message)
                        if self._validate_commit_message(message):
                            return message, f"チャンク処理AI生成({response.provider})"
                        elif message.startswith(':'):
                            # 検証失敗でも:で始まっていれば使用
                            return message[:50] if len(message) > 50 else message, f"チャンク処理AI生成({response.provider})"

                print(f"   ⚠️  チャンク処理失敗、従来方式にフォールバック")
            except Exception as e:
                print(f"   ⚠️  チャンク処理エラー: {e}")

        # 従来の処理
        import re
        lines = diff_content.split('\n')
        added_lines = len([l for l in lines if re.match(r'^\+[^+]', l)])
        removed_lines = len([l for l in lines if re.match(r'^-[^-]', l)])

        # 変更内容キーワード分析
        content_keywords = self._analyze_diff_keywords(diff_content)

        # LLMプロンプト構築
        prompt = self._build_commit_prompt(file_path, diff_content, content_keywords, rejected_messages)

        # プロバイダー状態表示
        print(f"   🤖 AI生成中...")

        # 複数プロバイダーで生成試行
        providers_status = []
        message = None
        generator = "未知"
        max_retries = 3
        retry_count = 0

        # フォールバック用デフォルトメッセージ
        fallback_message = f":update: {filename} ファイル更新"

        while not message and retry_count < max_retries:
            retry_count += 1

            # 1. Gemini試行
            if retry_count == 1:
                try:
                    from agents.llm_agent import LLMRequest

                    request = LLMRequest(
                        prompt=prompt,
                        system_message="短く回答",
                        max_tokens=20,  # 最小に
                        temperature=0.0  # 決定的に
                    )

                    response = self.llm_agent.generate_text(request)

                    if response.is_success and response.content:
                        temp_message = response.content.strip()

                        # 警告メッセージかチェック
                        if temp_message.startswith('[警告]') or 'max_tokens' in temp_message:
                            print(f"   🔍 Gemini警告: '{temp_message[:50]}...'")
                            providers_status.append("⚠️  Gemini: max_tokens制限に達しました")
                        else:
                            temp_message = self._clean_commit_message(temp_message)

                            if self._validate_commit_message(temp_message):
                                message = temp_message
                                generator = "Gemini (gemini-2.5-flash)"
                                providers_status.append("✅ Gemini: 生成成功")
                            else:
                                print(f"   🔍 Gemini検証失敗: 長さ={len(temp_message)}, 内容='{temp_message}'")
                                providers_status.append("⚠️  Gemini: フォーマット不正")
                    else:
                        providers_status.append("❌ Gemini: 生成失敗")

                except Exception as e:
                    providers_status.append(f"❌ Gemini: エラー ({str(e)[:30]})")

            # 1. Ollama試行（最優先・安定性重視）
            if retry_count == 1 and not message:
                try:
                    ollama_message = self._try_ollama_generation(prompt)
                    if ollama_message:
                        message = ollama_message
                        generator = "Ollama (ローカルモデル)"
                        providers_status.append("✅ Ollama: 生成成功")
                        break  # 成功したら他のプロバイダーを試さない（安定性優先）
                    else:
                        providers_status.append("❌ Ollama: 生成失敗")
                except Exception as e:
                    providers_status.append(f"❌ Ollama: エラー ({str(e)[:30]})")

            # 2. HuggingFace試行（制限チェック付き）
            elif retry_count == 2 and not message:
                try:
                    hf_message = self._try_huggingface_generation(prompt)
                    if hf_message:
                        message = hf_message
                        generator = "HuggingFace (openai/gpt-oss-20b)"
                        providers_status.append("✅ HuggingFace: 生成成功")
                        break  # 成功したら即座に終了
                    else:
                        providers_status.append("❌ HuggingFace: 生成失敗")
                except Exception as e:
                    providers_status.append(f"❌ HuggingFace: エラー ({str(e)[:30]})")

            # 3. Gemini試行
            elif retry_count == 3 and not message:
                try:
                    # Gemini API (通常リクエスト)
                    request = LLMRequest(
                        prompt=prompt,
                        system_message="短く回答",
                        max_tokens=20,  # 最小に
                        temperature=0.0  # 決定的に
                    )

                    response = self.llm_agent.generate_text(request)

                    if response.is_success and response.content:
                        temp_message = response.content.strip()

                        # 警告メッセージかチェック
                        if temp_message.startswith('[警告]') or 'max_tokens' in temp_message:
                            print(f"   🔍 Gemini警告: '{temp_message[:50]}...'")
                            providers_status.append("⚠️  Gemini: max_tokens制限に達しました")
                        else:
                            temp_message = self._clean_commit_message(temp_message)

                            if self._validate_commit_message(temp_message):
                                message = temp_message
                                generator = "Gemini (gemini-2.5-flash)"
                                providers_status.append("✅ Gemini: 生成成功")
                            else:
                                print(f"   🔍 Gemini検証失敗: 長さ={len(temp_message)}, 内容='{temp_message}'")
                                providers_status.append("⚠️  Gemini: フォーマット不正")
                    else:
                        providers_status.append("❌ Gemini: 生成失敗")

                except Exception as e:
                    providers_status.append(f"❌ Gemini: エラー ({str(e)[:30]})")

        # 最終的にメッセージがない場合の安全策（改良版）
        if not message:
            # ファイル分析に基づくスマートフォールバック
            filename = Path(file_path).name
            if 'test' in filename.lower():
                message = f":test: {filename}テスト更新"
            elif filename.endswith('.md'):
                message = f":docs: {filename}ドキュメント更新"
            elif 'config' in filename.lower() or filename.endswith('.yaml') or filename.endswith('.json'):
                message = f":config: {filename}設定更新"
            elif any(keyword in content_keywords for keyword in ['関数追加', 'クラス追加']):
                message = f":add: {filename}機能追加"
            elif any(keyword in content_keywords for keyword in ['バグ修正', '修正']):
                message = f":fix: {filename}修正"
            else:
                message = f":update: {filename}更新"
            generator = "スマートフォールバック（ファイル分析）"
            providers_status.append("🔄 スマートフォールバック: ファイル分析ベース")

        # プロバイダー状況表示
        for status in providers_status:
            print(f"   {status}")

        return message, generator

    def _try_huggingface_generation(self, prompt: str) -> str:
        """HuggingFace API でコミットメッセージ生成"""
        try:
            from agents.llm_agent import LLMRequest

            # シンプルで短いプロンプト
            simple_prompt = f"Git diff: {prompt[:200]}\nCommit message (format ':prefix: description', max 20 chars):"

            request = LLMRequest(
                prompt=simple_prompt,
                system_message="Generate short Git commit message. Format: ':prefix: description'. Max 20 characters.",
                max_tokens=15,  # 短く制限
                temperature=0.0,
                preferred_provider="huggingface"
            )

            # デバッグ: プロンプト内容を表示
            print(f"   🔍 HF送信プロンプト: '{simple_prompt[:50]}...'")

            response = self.llm_agent.generate_text(request)

            if response.is_success and response.content:
                message = response.content.strip()

                # コミットメッセージを抽出（複数行や説明から）
                message = self._extract_commit_message(message)
                message = self._clean_commit_message(message)

                if self._validate_commit_message(message):
                    return message
                else:
                    print(f"   🔍 HF検証失敗: '{message}'")
            else:
                print(f"   🔍 HF失敗理由: success={response.is_success}, content='{response.content if response.content else 'None'}'")
            return None
        except Exception:
            return None

    def _try_ollama_generation(self, prompt: str) -> str:
        """Ollama API でコミットメッセージ生成（安定性重視）"""
        try:
            from agents.llm_agent import LLMRequest

            # シンプルで短いプロンプト
            simple_prompt = f"Git diff: {prompt[:200]}\nCommit message (format ':prefix: description', max 20 chars):"

            request = LLMRequest(
                prompt=simple_prompt,
                system_message="Generate short Git commit message. Format: ':prefix: description'. Max 20 characters.",
                max_tokens=15,  # 短く制限
                temperature=0.0,
                preferred_provider="ollama"
            )

            # デバッグ: プロンプト内容を表示
            print(f"   🔍 Ollama送信プロンプト: '{simple_prompt[:50]}...'")

            response = self.llm_agent.generate_text(request)

            if response.is_success and response.content:
                message = response.content.strip()

                # コミットメッセージを抽出（複数行や説明から）
                message = self._extract_commit_message(message)
                message = self._clean_commit_message(message)

                if self._validate_commit_message(message):
                    return message
                else:
                    print(f"   🔍 Ollama検証失敗: '{message}'")
                    # 検証失敗でも:で始まっていれば使用（安定性優先）
                    if message.startswith(':'):
                        return message
            else:
                print(f"   🔍 Ollama失敗理由: success={response.is_success}, content='{response.content if response.content else 'None'}'")
            return None
        except Exception as e:
            print(f"   🔍 Ollama例外エラー: {str(e)[:100]}")
            return None

    def _check_ollama_connection(self) -> Dict[str, Any]:
        """Ollama接続確認"""
        try:
            import subprocess
            result = subprocess.run(
                "ollama list",
                shell=True, capture_output=True, text=True, timeout=5
            )

            if result.returncode == 0:
                models = [line.split()[0] for line in result.stdout.split('\n')[1:] if line.strip()]
                model_count = len([m for m in models if m and not m.startswith('NAME')])
                return {
                    "available": True,
                    "info": f"接続成功 (モデル数: {model_count})",
                    "models": models
                }
            else:
                return {
                    "available": False,
                    "error": "サーバー未起動"
                }
        except subprocess.TimeoutExpired:
            return {
                "available": False,
                "error": "接続タイムアウト"
            }
        except Exception as e:
            return {
                "available": False,
                "error": f"接続エラー ({str(e)[:20]})"
            }

    def _generate_with_ollama(self, prompt: str) -> str:
        """Ollama生成"""
        try:
            import subprocess
            result = subprocess.run(
                f'ollama run qwen2.5:1.5b-instruct "{prompt[:500]}"',
                shell=True, capture_output=True, text=True, timeout=30
            )

            if result.returncode == 0:
                message = result.stdout.strip().split('\n')[0]
                return self._clean_commit_message(message)
        except:
            pass
        return ""

    def _analyze_diff_keywords(self, diff_content: str) -> List[str]:
        """差分からキーワード抽出"""
        keywords = []
        lines = diff_content.split('\n')

        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                content = line[1:].strip()

                if 'def ' in content:
                    keywords.append('関数追加')
                elif 'class ' in content:
                    keywords.append('クラス追加')
                elif 'import ' in content:
                    keywords.append('インポート追加')
                elif any(word in content.lower() for word in ['config', '設定', 'setting']):
                    keywords.append('設定変更')
                elif any(word in content.lower() for word in ['test', 'テスト']):
                    keywords.append('テスト')
                elif any(word in content.lower() for word in ['fix', '修正', 'bug']):
                    keywords.append('バグ修正')
                elif any(word in content.lower() for word in ['add', '追加', 'new']):
                    keywords.append('機能追加')
                elif any(word in content.lower() for word in ['readme', 'doc', 'ドキュメント']):
                    keywords.append('ドキュメント')

        return list(set(keywords))

    def _build_commit_prompt(self, file_path: str, diff_content: str, keywords: List[str], rejected_messages: List[str]) -> str:
        """コミットメッセージ生成プロンプト構築（最小版）"""
        filename = Path(file_path).name

        # 最小プロンプト
        prompt = f":update: {filename}"

        return prompt

    def _clean_commit_message(self, message: str) -> str:
        """コミットメッセージのクリーニング"""
        import re

        # 絵文字削除
        emoji_pattern = re.compile("[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\U00002702-\U000027B0\U000024C2-\U0001F251]+")
        message = emoji_pattern.sub('', message)

        # 余分な文字削除
        message = re.sub(r'[*`]', '', message)
        message = re.sub(r'\s+', ' ', message)
        message = message.strip('- ')

        return message.strip()

    def _extract_commit_message(self, text: str) -> str:
        """AIが生成したテキストからコミットメッセージを抽出"""
        import re

        # デバッグ: 受信したテキストを表示
        if hasattr(self, 'debug') and self.debug:
            print(f"   🔍 抽出前テキスト: '{text[:100]}...'")

        # 一重引用符・バッククォートを除去（Ollamaの出力によくある）
        clean_text = text.strip().replace("'", "").replace('"', '').replace('`', '')

        # 複数行の場合、最初の行を取得
        lines = clean_text.split('\n')
        for line in lines:
            line = line.strip()
            if line and ':' in line:
                # :prefix: 形式の行を探す
                match = re.match(r'^:([a-zA-Z]+):\s*(.*)', line)
                if match:
                    prefix, description = match.groups()

                    # 重複したprefixを除去
                    if description.startswith(':' + prefix + ':'):
                        description = description[len(':' + prefix + ':'):].strip()

                    # 空の説明部分を補完
                    if not description.strip():
                        if 'test' in prefix.lower() or 'test' in line.lower():
                            description = "テスト関数を改善"
                        else:
                            description = "ファイルを更新"

                    result = f":{prefix}: {description}".strip()
                    return result[:50]  # 50文字で制限

        # コロン形式が見つからない場合、最初の意味のある行
        for line in lines:
            line = line.strip()
            if line and len(line) > 5 and not line.startswith('以下'):
                # :update: を先頭に追加
                if not line.startswith(':'):
                    line = ':update: ' + line
                return line[:50]

        # 最後の手段として
        return ":update: ファイル更新"

    def _validate_commit_message(self, message: str) -> bool:
        """コミットメッセージ検証（緩和版）"""
        if not message or len(message) < 8 or len(message) > 120:  # 最小文字数を8に緩和
            return False

        if not message.startswith(':'):
            return False

        valid_prefixes = [':add:', ':fix:', ':update:', ':refactor:', ':docs:', ':test:', ':config:', ':remove:']
        return any(message.startswith(prefix) for prefix in valid_prefixes)

    def _generate_rule_based_message(self, file_path: str, added_lines: int, removed_lines: int, keywords: List[str]) -> str:
        """ルールベースコミットメッセージ生成"""
        filename = Path(file_path).name

        # prefix決定
        if added_lines > removed_lines * 2:
            prefix = ":add:"
        elif removed_lines > added_lines * 2:
            prefix = ":fix:"
        elif 'テスト' in keywords:
            prefix = ":test:"
        elif 'ドキュメント' in keywords or filename.endswith('.md'):
            prefix = ":docs:"
        elif '設定変更' in keywords or filename.endswith(('.yaml', '.yml', '.json')):
            prefix = ":config:"
        else:
            prefix = ":update:"

        # 説明生成
        if keywords:
            description = f"{filename} {keywords[0]}対応"
        else:
            description = f"{filename} 機能更新"

        return f"{prefix} {description}"

    def _generate_detailed_commit_message(self, file_path: str, diff_content: str, rejected_messages: List[str]) -> str:
        """詳細コミットメッセージ生成"""
        prompt = f"""以下のファイル変更について、開発者が理解しやすい詳細なコミットメッセージを生成してください。

ファイル: {file_path}

要件:
1. 形式: ":prefix: 詳細な変更内容と目的"
2. どの機能・メソッド・クラスを変更したか具体的に
3. なぜその変更が必要だったか
4. 80-120文字程度で詳細に
5. 技術的に正確で具体的な表現
6. 絵文字は使用しない

却下された案: {', '.join(rejected_messages[-3:]) if rejected_messages else 'なし'}

差分:
{diff_content[:1500]}
"""

        try:
            from agents.llm_agent import LLMRequest

            request = LLMRequest(
                prompt=prompt,
                system_message="詳細で技術的なコミットメッセージを生成する専門家として、開発者が理解しやすい具体的な説明を日本語で作成してください。",
                max_tokens=200,
                temperature=0.2
            )

            response = self.llm_agent.generate_text(request)

            if response.is_success and response.content:
                message = self._clean_commit_message(response.content.strip())
                if self._validate_commit_message(message):
                    return message
        except Exception:
            pass

        return self._generate_better_commit_message(file_path, diff_content, rejected_messages)

    def _handle_deleted_file(self, file_path: str) -> bool:
        """削除ファイルの処理"""
        try:
            result = subprocess.run(
                f"git rm -- {file_path}",
                shell=True, capture_output=True, text=True, cwd=self.project_root
            )
            return result.returncode == 0
        except:
            return False

    def _show_commit_help(self):
        """コミットヘルプ表示"""
        print("""
🚀 Git Smart Agent - コミットコマンド詳細ヘルプ

📝 利用可能なアクション:
  [Enter] / y  - 現在のメッセージでコミット確定
  r           - AIで新しいメッセージを再生成
  e           - 手動でメッセージを編集
  d           - より詳細なメッセージをAI生成
  s           - このファイルをスキップ（アンステージ）
  h           - このヘルプを表示
  q           - 全体を中止

💡 コミットメッセージ形式:
  :add:      - 新機能・新ファイル追加
  :fix:      - バグ修正・問題解決
  :update:   - 既存機能の改善・更新
  :refactor: - コードの構造改善
  :docs:     - ドキュメント更新
  :test:     - テスト追加・修正
  :config:   - 設定ファイル変更

🎯 良いコミットメッセージの例:
  ✅ :add: LLM Agent にGemini API連携機能を追加
  ✅ :fix: Git Agent のファイル検索で空文字エラーを修正
  ✅ :update: MCP設定でタイムアウト値を30秒に変更
  ❌ :update: 更新  (具体性不足)
  ❌ 🎉 :add: 新機能追加  (絵文字使用)
""")


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Git Smart Agent - 高機能Git管理")
    parser.add_argument("--workflow", action="store_true", help="対話的ワークフロー実行")
    parser.add_argument("--auto", action="store_true", help="非対話モード（自動コミット）")
    parser.add_argument("--cleanup", action="store_true", help="ファイル整理のみ")
    parser.add_argument("--analyze", action="store_true", help="ファイル分析のみ")
    parser.add_argument("--interactive", action="store_true", help="対話モード")

    args = parser.parse_args()

    agent = GitSmartAgent()

    if args.analyze:
        categories = agent.analyze_files()
        agent._show_analysis_results(categories)

    elif args.cleanup:
        result = agent.cleanup_files(dry_run=False)
        print(f"🧹 整理完了: {result['total_actions']}件のアクション")

    elif args.workflow:
        # デフォルトは対話モード、--autoで非対話
        interactive_mode = not args.auto
        agent.smart_commit_workflow(auto_push=False, interactive=interactive_mode)

    elif args.interactive:
        agent.interactive_smart_mode()

    else:
        # デフォルト: 対話モード
        agent.interactive_smart_mode()


if __name__ == "__main__":
    main()
