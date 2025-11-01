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
        """整理対象ファイル判定"""
        cleanup_patterns = [
            "LINUX_", "TEST_", "COMPLETION_",
            ".backup", "_backup", 
            "git_status_helper.py",
            "fix_", "debug_"
        ]
        return any(pattern in file_path for pattern in cleanup_patterns)
        
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
                        target = target_dir / Path(file_path).name
                        
                        action = {
                            "type": "move",
                            "source": str(source.relative_to(self.project_root)),
                            "target": str(target.relative_to(self.project_root)),
                            "category": category.name,
                            "reason": f"{category.description}ファイルを適切なディレクトリに整理"
                        }
                        actions.append(action)
        
        # 削除対象
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
  
  🤖 MCP関連 → services/mcp/
     - mcp_*.py, *_mcp.py
     理由: MCPコンポーネントの統一配置
  
  📂 古いファイル → _archive/
     - LINUX_*, TEST_*, COMPLETION_*
     - *.backup, *_backup
     理由: 履歴保持しつつメイン領域を整理

🗑️  削除対象:
  - *.tmp, *.bak（一時ファイル）
  - __pycache__/（Python キャッシュ）
  - *.pyc（コンパイル済みPython）
  - .DS_Store（macOS システムファイル）

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
        
        while True:
            command = input("\n🧹 > ").strip().lower()
            
            if command == "back" or command == "quit":
                break
            elif command == "preview":
                cleanup_result = self.cleanup_files(dry_run=True)
                self._show_detailed_cleanup_preview(cleanup_result)
            elif command == "interactive":
                cleanup_result = self.cleanup_files(dry_run=False, interactive=True)
                if cleanup_result['total_actions'] > 0:
                    print(f"✅ 整理完了: {cleanup_result['total_actions']}件処理")
                else:
                    print("✨ 整理の必要なファイルはありませんでした")
            elif command == "help":
                self.show_cleanup_help()
            else:
                print("利用可能: preview, interactive, help, back")

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
            
            # 重要ファイルは詳細表示
            if category.priority <= 2:
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
        print("🚀 Git Smart Agent - 高機能モード")
        print("利用可能なコマンド:")
        print("  📊 analyze   - ファイル分析・カテゴリ分け")
        print("  🧹 cleanup   - ファイル整理・統合（Git追跡ファイルとUntracked両方）") 
        print("  📝 workflow  - 対話的コミットワークフロー（推奨）")
        print("  🌐 remote    - リモート状況確認")
        print("  📤 push      - プッシュ実行")
        print("  ❓ help      - 詳細ヘルプ")
        print("  🚪 quit      - 終了")
        
        while True:
            try:
                command = input("\n🤖 > ").strip().lower()
                
                if command == "quit" or command == "q":
                    break
                    
                elif command == "analyze":
                    categories = self.analyze_files()
                    self._show_analysis_results(categories)
                
                elif command == "cleanup":
                    print("\n🧹 ファイル整理オプション:")
                    print("  1. プレビューのみ表示")
                    print("  2. 対話的整理実行")
                    print("  3. 詳細整理モード")
                    
                    choice = input("選択 [1-3]: ").strip()
                    
                    if choice == "1":
                        cleanup_result = self.cleanup_files(dry_run=True)
                        self._show_detailed_cleanup_preview(cleanup_result)
                    elif choice == "2":
                        cleanup_result = self.cleanup_files(dry_run=False, interactive=True)
                        if cleanup_result['total_actions'] > 0:
                            print(f"✅ 整理完了: {cleanup_result['total_actions']}件処理")
                    elif choice == "3":
                        self.interactive_cleanup_mode()
                    else:
                        print("❓ 1-3 の数字を入力してください")
                
                elif command == "workflow":
                    self.smart_commit_workflow(auto_push=False, interactive=True)
                
                elif command == "push":
                    remote_status = self.check_remote_status()
                    if remote_status["has_remote"] and remote_status.get("can_push"):
                        result = self._execute_push()
                        if result["success"]:
                            print("✅ プッシュ完了")
                        else:
                            print(f"❌ プッシュ失敗: {result.get('error', '')}")
                    else:
                        print("⚠️  プッシュ不可: リモート未設定またはコミットなし")
                
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
                    
            except KeyboardInterrupt:
                print("\n👋 中断されました")
                break
            except Exception as e:
                print(f"❌ エラー: {e}")
        
        print("👋 Git Smart Agent 終了")

    def _show_detailed_help(self):
        """詳細ヘルプ表示"""
        print("""
🚀 Git Smart Agent - 詳細ヘルプ

📋 概要:
  このツールは、Gitの複雑な操作を自動化し、
  AIによるコミットメッセージ生成で効率的な開発をサポートします。

🔧 主要機能:
  
  📊 analyze - ファイル分析
     - 変更ファイルを重要度別にカテゴリ分け
     - 重要: __init__.py, config.yaml, 主要スクリプト
     - 機能: agents/, services/, tools/ の Python ファイル
     - ドキュメント: .md ファイル
     - テスト: test_ で始まるファイル
     - 設定: .yaml, .json ファイル
     - その他: 上記以外のファイル

  🧹 cleanup - ファイル整理
     - Git追跡中およびUntracked両方のファイルを分析
     - テストファイル → tests/ ディレクトリ
     - MCPファイル → services/mcp/ ディレクトリ
     - 古いファイル → _archive/ ディレクトリ
     - 一時ファイル・キャッシュの削除
     - 各ファイルの移動先・理由を詳細表示
     - 対話的確認で安全な整理

  📝 workflow - 対話的コミット（推奨）
     - Git状況の詳細表示
     - ファイル分析とカテゴリ分け
     - 各ファイルの差分表示
     - AIによるコミットメッセージ自動生成
     - メッセージの確認・編集・再生成
     - 段階的な1ファイルずつコミット

  🌐 remote - リモート状況確認
     - 設定済みリモートリポジトリの表示
     - プッシュ可能性の確認
     - 未設定時の設定方法案内

  📤 push - プッシュ実行
     - リモートリポジトリへの変更送信
     - エラー時の詳細表示

💡 使用シナリオ:
  
  🎯 初回使用: 'workflow' で全自動対話的コミット
  📊 状況確認: 'analyze' でファイル状況把握
  🧹 整理: 'cleanup' でプロジェクト整理
  🚀 継続使用: 'workflow' で段階的コミット

🎪 コミットメッセージ形式:
  :add: 新機能・新ファイル追加
  :fix: バグ修正・問題解決  
  :update: 既存機能の改善・更新
  :refactor: コードの構造改善
  :docs: ドキュメント更新
  :test: テスト追加・修正
  :config: 設定ファイル変更

❓ よくある質問:
  Q: プッシュまで自動化したい
  A: workflow 完了後に 'push' コマンド実行

  Q: コミットメッセージが気に入らない
  A: workflow 中に 'r' で再生成、'e' で編集可能

  Q: ファイルが多すぎる
  A: まず 'cleanup' で整理、その後 'workflow'

  Q: 特定ファイルだけコミットしたい
  A: workflow 中に不要ファイルを 's' でスキップ
""")

    def add_helper_methods_here(self):
        # 以下にヘルパーメソッドを追加する場所を確保
        pass

    def _show_diff_summary(self, diff_content: str):
        """差分サマリー表示"""
        lines = diff_content.split('\n')
        added_lines = len([l for l in lines if l.startswith('+')])
        removed_lines = len([l for l in lines if l.startswith('-')])
        
        print(f"   📊 変更: +{added_lines} -{removed_lines} 行")
        
        # 重要な変更のプレビュー
        important_changes = []
        for line in lines[:20]:
            if line.startswith('+') and not line.startswith('+++'):
                clean_line = line[1:].strip()
                if clean_line and not clean_line.startswith('#'):
                    important_changes.append(f"   + {clean_line[:60]}")
            elif line.startswith('-') and not line.startswith('---'):
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
        
        # 初回コミットメッセージ生成
        message = self._generate_better_commit_message(file_path, diff_content, rejected_messages)
        
        while True:
            print(f"\n💬 コミットメッセージ案:")
            print(f"   {message}")
            
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
                # 再生成
                rejected_messages.append(message)
                new_message = self._generate_better_commit_message(file_path, diff_content, rejected_messages)
                if new_message != message:
                    message = new_message
                else:
                    print("   ⚠️  新しいメッセージを生成できませんでした")
            
            elif action == "e":
                # 編集
                new_message = input(f"新しいメッセージを入力: ")
                if new_message.strip():
                    message = new_message.strip()
            
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

    def _generate_better_commit_message(self, file_path: str, diff_content: str, rejected_messages: List[str] = None) -> str:
        """改良されたコミットメッセージ生成"""
        if rejected_messages is None:
            rejected_messages = []
        
        # ファイル分析
        path_obj = Path(file_path)
        filename = path_obj.name
        
        # 変更量分析
        lines = diff_content.split('\n')
        added_lines = len([l for l in lines if l.startswith('+') and not l.startswith('+++')])
        removed_lines = len([l for l in lines if l.startswith('-') and not l.startswith('---')])
        
        # 変更内容キーワード分析
        content_keywords = self._analyze_diff_keywords(diff_content)
        
        # LLMプロンプト構築
        prompt = self._build_commit_prompt(file_path, diff_content, content_keywords, rejected_messages)
        
        try:
            # LLMで生成
            from agents.llm_agent import LLMRequest
            
            request = LLMRequest(
                prompt=prompt,
                system_message="あなたはGitコミットメッセージの専門家です。具体的で技術的に正確なコミットメッセージを日本語で生成してください。絵文字は使用せず、:prefix: 形式で始めてください。",
                max_tokens=150,
                temperature=0.3
            )
            
            response = self.llm_agent.generate_text(request)
            
            if response.is_success and response.content:
                message = response.content.strip()
                # 絵文字を削除
                message = self._clean_commit_message(message)
                
                if self._validate_commit_message(message):
                    return message
                    
        except Exception as e:
            print(f"   ⚠️  LLM生成エラー: {e}")
        
        # フォールバック: ルールベース生成
        return self._generate_rule_based_message(file_path, added_lines, removed_lines, content_keywords)

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
        """コミットメッセージ生成プロンプト構築"""
        lines = diff_content.split('\n')
        added_lines = len([l for l in lines if l.startswith('+') and not l.startswith('+++')])
        removed_lines = len([l for l in lines if l.startswith('-') and not l.startswith('---')])
        
        prompt = f"""以下のファイル変更から具体的なコミットメッセージを生成してください。

ファイルパス: {file_path}
変更量: +{added_lines} -{removed_lines} 行
検出キーワード: {', '.join(keywords) if keywords else 'なし'}

必須要件:
1. 形式: ":prefix: 具体的な変更内容の説明"
2. prefix選択: :add:(新機能), :fix:(修正), :update:(改善), :refactor:(リファクタ), :docs:(文書), :test:(テスト), :config:(設定)
3. 説明は日本語で具体的に（50-100文字程度）
4. ファイル名や機能名を含める
5. 絵文字は使用しない
6. 技術的に正確で開発者が理解しやすい表現

差分内容（抜粋）:
{diff_content[:1000]}
"""
        
        if rejected_messages:
            prompt += f"\n却下された案: {', '.join(rejected_messages[-3:])}\n上記とは異なる表現で生成してください。"
        
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

    def _validate_commit_message(self, message: str) -> bool:
        """コミットメッセージ検証"""
        if not message or len(message) < 10 or len(message) > 120:
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