#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Organizer - プロジェクト全体整理ツール
- 重複ファイル検出・統合
- MCPコンポーネント整理
- テストファイル統合
- DBファイル統合
"""

import os
import json
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
import hashlib


class ProjectOrganizer:
    """プロジェクト整理クラス"""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root)
        self.rules = self._load_organization_rules()
        
    def _load_organization_rules(self) -> Dict[str, Any]:
        """整理ルール定義"""
        return {
            "merge_directories": {
                "tests/": [
                    "test/",
                    "testing/",
                    "test_*/"
                ],
                "docs/": [
                    "documentation/",
                    "doc/",
                    "docs_*/"
                ],
                "_archive/old_tests/": [
                    "simple_*",
                    "debug_*",
                    "validate_*",
                    "fix_*",
                    "*_test_*"
                ]
            },
            "file_consolidation": {
                "services/db/database.db": [
                    "neurohub_llm.db",
                    "*.db",
                    "database/*"
                ],
                "docs/README.md": [
                    "README*.md",
                    "readme*.md"
                ],
                "docs/TESTING.md": [
                    "TEST_*.md",
                    "LINUX_TEST_*.md",
                    "*_TEST_*.md"
                ],
                "docs/SETUP.md": [
                    "LINUX_*.md",
                    "SETUP*.md",
                    "*_SETUP*.md"
                ]
            },
            "mcp_consolidation": {
                "services/mcp/": [
                    "mcp_*.py",
                    "*_mcp.py",
                    "simple_mcp_*"
                ]
            },
            "delete_patterns": [
                "*.tmp",
                "*.backup",
                "*.bak",
                "__pycache__/",
                "*.pyc",
                ".DS_Store",
                "*_backup*",
                "git_status_helper.py"  # 一時ツール
            ]
        }

    def analyze_duplicates(self) -> Dict[str, List[str]]:
        """重複ファイル検出"""
        file_hashes = defaultdict(list)
        duplicates = {}
        
        # ハッシュ計算
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not self._should_ignore(file_path):
                try:
                    with open(file_path, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()
                        file_hashes[file_hash].append(str(file_path.relative_to(self.project_root)))
                except:
                    continue
        
        # 重複抽出
        for file_hash, files in file_hashes.items():
            if len(files) > 1:
                duplicates[f"hash_{file_hash[:8]}"] = files
        
        return duplicates

    def analyze_similar_files(self) -> Dict[str, List[str]]:
        """類似ファイル検出（名前ベース）"""
        similar_groups = defaultdict(list)
        
        # ファイル名パターン分析
        for file_path in self.project_root.rglob("*.py"):
            if file_path.is_file():
                name = file_path.stem
                
                # パターン抽出
                base_patterns = [
                    name.replace("_test", "").replace("test_", ""),
                    name.replace("debug_", "").replace("_debug", ""),
                    name.replace("simple_", "").replace("_simple", ""),
                    name.replace("fix_", "").replace("_fix", ""),
                ]
                
                for pattern in base_patterns:
                    if pattern and len(pattern) > 3:
                        key = f"pattern_{pattern}"
                        similar_groups[key].append(str(file_path.relative_to(self.project_root)))
        
        # 2個以上のグループのみ返す
        return {k: v for k, v in similar_groups.items() if len(v) > 1}

    def _should_ignore(self, file_path: Path) -> bool:
        """無視すべきファイル判定"""
        ignore_patterns = [
            ".git/", "__pycache__/", ".vscode/",
            "venv/", "venv_linux/", ".env",
            "node_modules/", ".pytest_cache/"
        ]
        
        path_str = str(file_path)
        return any(pattern in path_str for pattern in ignore_patterns)

    def create_organization_plan(self) -> Dict[str, Any]:
        """整理計画作成"""
        plan = {
            "timestamp": str(Path().cwd()),
            "actions": [],
            "summary": {}
        }
        
        # 1. 重複ファイル処理
        duplicates = self.analyze_duplicates()
        for group, files in duplicates.items():
            if len(files) > 1:
                # 最新ファイルを残す
                newest_file = max(files, key=lambda f: (self.project_root / f).stat().st_mtime)
                for file in files:
                    if file != newest_file:
                        plan["actions"].append({
                            "type": "delete_duplicate",
                            "file": file,
                            "keep": newest_file,
                            "reason": f"重複ファイル（{group}）"
                        })
        
        # 2. ディレクトリ統合
        for target_dir, source_patterns in self.rules["merge_directories"].items():
            target_path = self.project_root / target_dir
            
            for pattern in source_patterns:
                for source_path in self.project_root.glob(pattern):
                    if source_path.is_dir() and source_path != target_path:
                        plan["actions"].append({
                            "type": "merge_directory",
                            "source": str(source_path.relative_to(self.project_root)),
                            "target": target_dir,
                            "reason": f"ディレクトリ統合: {pattern}"
                        })
        
        # 3. ファイル統合
        for target_file, source_patterns in self.rules["file_consolidation"].items():
            target_path = self.project_root / target_file
            matching_files = []
            
            for pattern in source_patterns:
                matching_files.extend(self.project_root.glob(pattern))
            
            if len(matching_files) > 1:
                # 統合対象ファイルを選択
                for source_path in matching_files:
                    if source_path.is_file() and source_path != target_path:
                        plan["actions"].append({
                            "type": "consolidate_file",
                            "source": str(source_path.relative_to(self.project_root)),
                            "target": target_file,
                            "reason": f"ファイル統合: {pattern}"
                        })
        
        # 4. MCP統合
        mcp_files = []
        for pattern in self.rules["mcp_consolidation"]["services/mcp/"]:
            mcp_files.extend(self.project_root.glob(pattern))
        
        for mcp_file in mcp_files:
            if mcp_file.is_file() and "services/mcp/" not in str(mcp_file):
                plan["actions"].append({
                    "type": "move_to_mcp",
                    "source": str(mcp_file.relative_to(self.project_root)),
                    "target": f"services/mcp/{mcp_file.name}",
                    "reason": "MCP関連ファイル統合"
                })
        
        # 5. 削除対象
        for pattern in self.rules["delete_patterns"]:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    plan["actions"].append({
                        "type": "delete",
                        "file": str(file_path.relative_to(self.project_root)),
                        "reason": f"不要ファイル: {pattern}"
                    })
        
        # サマリー作成
        action_types = defaultdict(int)
        for action in plan["actions"]:
            action_types[action["type"]] += 1
        
        plan["summary"] = {
            "total_actions": len(plan["actions"]),
            "by_type": dict(action_types),
            "affected_files": len(set(action.get("file", action.get("source", "")) for action in plan["actions"]))
        }
        
        return plan

    def execute_plan(self, plan: Dict[str, Any], dry_run: bool = True) -> Dict[str, Any]:
        """整理計画実行"""
        results = {
            "dry_run": dry_run,
            "executed": [],
            "failed": [],
            "skipped": []
        }
        
        for action in plan["actions"]:
            try:
                if action["type"] == "delete_duplicate":
                    file_path = self.project_root / action["file"]
                    if file_path.exists():
                        if not dry_run:
                            file_path.unlink()
                        results["executed"].append(action)
                    else:
                        results["skipped"].append({**action, "reason": "ファイルが存在しない"})
                
                elif action["type"] == "merge_directory":
                    source_path = self.project_root / action["source"]
                    target_path = self.project_root / action["target"]
                    
                    if source_path.exists():
                        if not dry_run:
                            target_path.mkdir(parents=True, exist_ok=True)
                            # ファイルを移動
                            for item in source_path.rglob("*"):
                                if item.is_file():
                                    rel_path = item.relative_to(source_path)
                                    new_path = target_path / rel_path
                                    new_path.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.move(str(item), str(new_path))
                            # 空ディレクトリ削除
                            if source_path.exists():
                                shutil.rmtree(source_path)
                        results["executed"].append(action)
                    else:
                        results["skipped"].append({**action, "reason": "ディレクトリが存在しない"})
                
                elif action["type"] == "consolidate_file":
                    source_path = self.project_root / action["source"]
                    target_path = self.project_root / action["target"]
                    
                    if source_path.exists():
                        if not dry_run:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            if target_path.exists():
                                # 内容をマージ
                                with open(target_path, 'a', encoding='utf-8') as target_file:
                                    target_file.write(f"\n\n# --- Merged from {action['source']} ---\n\n")
                                    with open(source_path, 'r', encoding='utf-8') as source_file:
                                        target_file.write(source_file.read())
                            else:
                                shutil.move(str(source_path), str(target_path))
                        results["executed"].append(action)
                    else:
                        results["skipped"].append({**action, "reason": "ファイルが存在しない"})
                
                elif action["type"] == "move_to_mcp":
                    source_path = self.project_root / action["source"]
                    target_path = self.project_root / action["target"]
                    
                    if source_path.exists():
                        if not dry_run:
                            target_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(source_path), str(target_path))
                        results["executed"].append(action)
                    else:
                        results["skipped"].append({**action, "reason": "ファイルが存在しない"})
                
                elif action["type"] == "delete":
                    file_path = self.project_root / action["file"]
                    if file_path.exists():
                        if not dry_run:
                            if file_path.is_file():
                                file_path.unlink()
                            elif file_path.is_dir():
                                shutil.rmtree(file_path)
                        results["executed"].append(action)
                    else:
                        results["skipped"].append({**action, "reason": "ファイルが存在しない"})
                
            except Exception as e:
                results["failed"].append({**action, "error": str(e)})
        
        return results

    def generate_report(self, plan: Dict[str, Any]) -> str:
        """整理レポート生成"""
        report = f"""# プロジェクト整理計画

## 概要
- 総アクション数: {plan['summary']['total_actions']}
- 影響ファイル数: {plan['summary']['affected_files']}

## アクション種別
"""
        
        for action_type, count in plan['summary']['by_type'].items():
            report += f"- {action_type}: {count}件\n"
        
        report += "\n## 詳細アクション\n\n"
        
        for i, action in enumerate(plan['actions'][:20], 1):  # 上位20件
            report += f"{i}. **{action['type']}**: "
            if 'source' in action:
                report += f"`{action['source']}` → `{action.get('target', 'DELETE')}`"
            else:
                report += f"`{action.get('file', 'N/A')}`"
            report += f" ({action['reason']})\n"
        
        if len(plan['actions']) > 20:
            report += f"\n... 他 {len(plan['actions']) - 20}件\n"
        
        return report


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project Organizer - プロジェクト整理ツール")
    parser.add_argument("--analyze", action="store_true", help="分析のみ実行")
    parser.add_argument("--execute", action="store_true", help="整理実行")
    parser.add_argument("--dry-run", action="store_true", help="ドライラン（実際の変更なし）")
    parser.add_argument("--report", type=str, help="レポート出力ファイル")
    
    args = parser.parse_args()
    
    project_root = Path(__file__).parent.parent
    organizer = ProjectOrganizer(project_root)
    
    if args.analyze or not args.execute:
        print("🔍 プロジェクト分析中...")
        plan = organizer.create_organization_plan()
        
        print(f"📊 整理計画:")
        print(f"   総アクション数: {plan['summary']['total_actions']}")
        print(f"   影響ファイル数: {plan['summary']['affected_files']}")
        
        for action_type, count in plan['summary']['by_type'].items():
            print(f"   {action_type}: {count}件")
        
        # レポート生成
        if args.report:
            report = organizer.generate_report(plan)
            with open(args.report, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 レポート出力: {args.report}")
        
        # 詳細表示（上位10件）
        print("\n📋 主要アクション（上位10件）:")
        for i, action in enumerate(plan['actions'][:10], 1):
            print(f"   {i}. {action['type']}: ", end="")
            if 'source' in action:
                print(f"{action['source']} → {action.get('target', 'DELETE')}")
            else:
                print(f"{action.get('file', 'N/A')}")
    
    if args.execute:
        print("\n🚀 整理実行中...")
        plan = organizer.create_organization_plan()
        results = organizer.execute_plan(plan, dry_run=args.dry_run)
        
        print(f"✅ 実行完了:")
        print(f"   実行: {len(results['executed'])}件")
        print(f"   スキップ: {len(results['skipped'])}件")
        print(f"   失敗: {len(results['failed'])}件")
        
        if results['failed']:
            print("\n❌ 失敗項目:")
            for failed in results['failed'][:5]:
                print(f"   {failed.get('source', failed.get('file', 'N/A'))}: {failed['error']}")


if __name__ == "__main__":
    main()