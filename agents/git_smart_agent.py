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

    def cleanup_files(self, dry_run: bool = True) -> Dict[str, Any]:
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
                            "source": str(source),
                            "target": str(target),
                            "category": category.name
                        }
                        actions.append(action)
                        
                        if not dry_run:
                            target_dir.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(source), str(target))
        
        # 削除対象
        for pattern in self.cleanup_rules["delete_patterns"]:
            for file_path in self.project_root.glob(pattern):
                if file_path.exists():
                    action = {
                        "type": "delete",
                        "target": str(file_path)
                    }
                    actions.append(action)
                    
                    if not dry_run:
                        if file_path.is_file():
                            file_path.unlink()
                        elif file_path.is_dir():
                            shutil.rmtree(file_path)
        
        return {
            "dry_run": dry_run,
            "actions": actions,
            "total_actions": len(actions)
        }

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

    def smart_commit_workflow(self, auto_push: bool = False) -> Dict[str, Any]:
        """スマートコミットワークフロー"""
        workflow_results = {
            "timestamp": datetime.now().isoformat(),
            "phases": []
        }
        
        # Phase 1: ファイル分析
        print("🔍 Phase 1: ファイル分析中...")
        categories = self.analyze_files()
        
        phase1 = {
            "name": "analysis",
            "categories": len(categories),
            "total_files": sum(len(cat.files) for cat in categories),
            "details": [{"name": cat.name, "count": len(cat.files), "priority": cat.priority} for cat in categories]
        }
        workflow_results["phases"].append(phase1)
        
        # Phase 2: ファイル整理（ドライラン）
        print("🧹 Phase 2: ファイル整理提案...")
        cleanup_preview = self.cleanup_files(dry_run=True)
        
        phase2 = {
            "name": "cleanup_preview",
            "actions": cleanup_preview["total_actions"],
            "suggestions": cleanup_preview["actions"][:5]  # 上位5件表示
        }
        workflow_results["phases"].append(phase2)
        
        # ユーザー確認
        if cleanup_preview["total_actions"] > 0:
            print(f"📋 整理提案: {cleanup_preview['total_actions']}件のアクション")
            for action in cleanup_preview["actions"][:3]:
                print(f"   {action['type']}: {Path(action.get('source', action.get('target', ''))).name}")
            
            if input("\n整理を実行しますか？ [y/N]: ").lower() == 'y':
                print("🧹 ファイル整理実行中...")
                self.cleanup_files(dry_run=False)
                phase2["executed"] = True
        
        # Phase 3: 段階的コミット
        print("📝 Phase 3: 段階的コミット...")
        commit_results = []
        
        # 優先度順にコミット
        for category in sorted(categories, key=lambda x: x.priority):
            if not category.files:
                continue
                
            print(f"\n📁 {category.description} ({len(category.files)}件)")
            
            for file_path in category.files:
                # ファイル存在確認
                full_path = self.project_root / file_path
                if not full_path.exists():
                    continue
                
                # ステージング
                if self.stage_file(file_path):
                    # コミットメッセージ生成
                    diff_content = self.get_file_diff(file_path, staged=True)
                    if diff_content:
                        message = self.generate_commit_message(file_path, diff_content)
                        
                        print(f"   📄 {file_path}")
                        print(f"   💬 {message}")
                        
                        # コミット実行
                        if self.commit_file(file_path, message):
                            commit_results.append({
                                "file": file_path,
                                "message": message,
                                "success": True,
                                "category": category.name
                            })
                            print("   ✅ コミット完了")
                        else:
                            commit_results.append({
                                "file": file_path,
                                "message": message,
                                "success": False,
                                "category": category.name
                            })
                            print("   ❌ コミット失敗")
        
        phase3 = {
            "name": "commits",
            "total": len(commit_results),
            "successful": len([r for r in commit_results if r["success"]]),
            "failed": len([r for r in commit_results if not r["success"]]),
            "details": commit_results
        }
        workflow_results["phases"].append(phase3)
        
        # Phase 4: リモート確認・プッシュ
        print("\n🌐 Phase 4: リモート状況確認...")
        remote_status = self.check_remote_status()
        
        phase4 = {
            "name": "remote_check",
            "has_remote": remote_status["has_remote"],
            "can_push": remote_status.get("can_push", False)
        }
        
        if remote_status["has_remote"]:
            remotes = remote_status["remotes"]
            print(f"📡 リモート: {len(remotes)}件設定済み")
            for remote in remotes[:2]:
                print(f"   {remote['name']}: {remote['url']}")
            
            if remote_status.get("can_push") and auto_push:
                print("📤 自動プッシュ実行中...")
                push_result = self._execute_push()
                phase4["push_result"] = push_result
            elif remote_status.get("can_push"):
                if input("\nプッシュしますか？ [y/N]: ").lower() == 'y':
                    print("📤 プッシュ実行中...")
                    push_result = self._execute_push()
                    phase4["push_result"] = push_result
        else:
            print("⚠️  リモートリポジトリ未設定")
            print("💡 GitHub等にリポジトリを作成して以下コマンドで設定:")
            print("   git remote add origin <URL>")
            print("   git push -u origin main")
            phase4["suggestion"] = "リモートリポジトリ設定が必要"
        
        workflow_results["phases"].append(phase4)
        
        # 結果サマリー
        print(f"\n🎉 ワークフロー完了!")
        print(f"📊 コミット: {phase3['successful']}/{phase3['total']} 成功")
        if phase4.get("push_result"):
            print(f"📤 プッシュ: {'成功' if phase4['push_result']['success'] else '失敗'}")
        
        return workflow_results

    def _execute_push(self) -> Dict[str, Any]:
        """プッシュ実行"""
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
        print("コマンド: analyze, cleanup, workflow, push, remote, quit")
        
        while True:
            try:
                command = input("\n🤖 > ").strip()
                
                if command == "quit":
                    break
                    
                elif command == "analyze":
                    categories = self.analyze_files()
                    print(f"\n📊 ファイル分析結果:")
                    for cat in categories:
                        print(f"   {cat.description}: {len(cat.files)}件")
                        for file in cat.files[:3]:
                            print(f"     - {file}")
                        if len(cat.files) > 3:
                            print(f"     ... 他 {len(cat.files)-3}件")
                
                elif command == "cleanup":
                    cleanup_result = self.cleanup_files(dry_run=True)
                    print(f"\n🧹 整理提案: {cleanup_result['total_actions']}件")
                    for action in cleanup_result["actions"][:5]:
                        print(f"   {action['type']}: {Path(action.get('source', action.get('target', ''))).name}")
                    
                    if input("\n実行しますか？ [y/N]: ").lower() == 'y':
                        self.cleanup_files(dry_run=False)
                        print("✅ 整理完了")
                
                elif command == "workflow":
                    auto_push = input("自動プッシュしますか？ [y/N]: ").lower() == 'y'
                    self.smart_commit_workflow(auto_push=auto_push)
                
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
                    else:
                        print("⚠️  リモート未設定")
                        print("💡 設定方法: git remote add origin <URL>")
                
                else:
                    print("未知のコマンド。使用可能: analyze, cleanup, workflow, push, remote, quit")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"エラー: {e}")
        
        print("👋 Git Smart Agent 終了")


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Git Smart Agent - 高機能Git管理")
    parser.add_argument("--workflow", action="store_true", help="スマートワークフロー実行")
    parser.add_argument("--auto-push", action="store_true", help="自動プッシュ有効")
    parser.add_argument("--cleanup", action="store_true", help="ファイル整理のみ")
    parser.add_argument("--analyze", action="store_true", help="ファイル分析のみ")
    parser.add_argument("--interactive", action="store_true", help="対話モード")
    
    args = parser.parse_args()
    
    agent = GitSmartAgent()
    
    if args.analyze:
        categories = agent.analyze_files()
        print("📊 ファイル分析結果:")
        for cat in categories:
            print(f"   {cat.description}: {len(cat.files)}件")
    
    elif args.cleanup:
        result = agent.cleanup_files(dry_run=False)
        print(f"🧹 整理完了: {result['total_actions']}件のアクション")
    
    elif args.workflow:
        agent.smart_commit_workflow(auto_push=args.auto_push)
    
    elif args.interactive:
        agent.interactive_smart_mode()
    
    else:
        # デフォルト: 対話モード
        agent.interactive_smart_mode()


if __name__ == "__main__":
    main()