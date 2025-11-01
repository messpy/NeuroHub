#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroHub プロジェクト整理ツール

功能:
- rootにある`test_*.py`ファイルをtests/に移動
- 重複・古いファイルを_archive/に移動
- 一時ファイルを削除
- ファイル整理のレポート生成
"""

import os
import sys
import shutil
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

# プロジェクトルート
ROOT = Path(__file__).parent.parent
os.chdir(ROOT)

class ProjectCleaner:
    """プロジェクト整理クラス"""
    
    def __init__(self):
        self.root = ROOT
        self.report = {
            'moved_files': [],
            'archived_files': [],
            'deleted_files': [],
            'errors': []
        }
        
        # 移動ルール
        self.move_rules = {
            'tests/': [
                # rootのtest_*.pyファイルをtests/に移動
                'test_quick.py',
                'test_provider_limits.py', 
                'test_mcp_integration.py',
                'test_knowledge_manager.py',
                'test_db_simple.py',
                'test_db_manager.py',
                'test_db_integration.py',
                'test_db_init.py'
            ]
        }
        
        # アーカイブ対象（古い・重複ファイル）
        self.archive_targets = [
            # 統合済み重複ファイル（debug系）
            'debug_*.py',
            'simple_*.py',
            'fix_*.py',
            'validate_*.py',
            # バックアップファイル
            '*.bak',
            '*_backup*',
            '*.old',
            # 一時ファイル
            '*.tmp',
        ]
        
        # 削除対象（完全不要）
        self.delete_targets = [
            '__pycache__',
            '*.pyc',
            '*.pyo', 
            '.DS_Store',
            'Thumbs.db'
        ]

    def analyze_files(self) -> Dict[str, List[str]]:
        """ファイル分析"""
        analysis = {
            'test_files_in_root': [],
            'archive_candidates': [],
            'delete_candidates': [],
            'already_organized': []
        }
        
        # rootの test_*.py ファイル
        for pattern in self.move_rules['tests/']:
            files = list(self.root.glob(pattern))
            analysis['test_files_in_root'].extend([str(f.relative_to(self.root)) for f in files])
        
        # アーカイブ候補
        for pattern in self.archive_targets:
            files = list(self.root.rglob(pattern))
            # 既に_archiveにあるものは除外
            files = [f for f in files if '_archive' not in str(f)]
            analysis['archive_candidates'].extend([str(f.relative_to(self.root)) for f in files])
        
        # 削除候補
        for pattern in self.delete_targets:
            files = list(self.root.rglob(pattern))
            analysis['delete_candidates'].extend([str(f.relative_to(self.root)) for f in files])
        
        return analysis

    def move_test_files(self, dry_run: bool = True) -> List[str]:
        """rootのtest_*.pyファイルをtests/に移動"""
        moved = []
        tests_dir = self.root / 'tests'
        tests_dir.mkdir(exist_ok=True)
        
        for pattern in self.move_rules['tests/']:
            files = list(self.root.glob(pattern))
            for file in files:
                target = tests_dir / file.name
                
                try:
                    if not dry_run:
                        if target.exists():
                            # 既存ファイルがある場合はバックアップ
                            backup_name = f"{file.stem}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}{file.suffix}"
                            backup_target = tests_dir / backup_name
                            shutil.move(str(target), str(backup_target))
                            print(f"  🔄 既存ファイルをバックアップ: {target.relative_to(self.root)} → {backup_target.relative_to(self.root)}")
                        
                        shutil.move(str(file), str(target))
                        print(f"  ✅ 移動: {file.relative_to(self.root)} → {target.relative_to(self.root)}")
                    else:
                        print(f"  📝 移動予定: {file.relative_to(self.root)} → {target.relative_to(self.root)}")
                    
                    moved.append(str(file.relative_to(self.root)))
                    self.report['moved_files'].append({
                        'source': str(file.relative_to(self.root)),
                        'target': str(target.relative_to(self.root)),
                        'type': 'test_file'
                    })
                    
                except Exception as e:
                    error_msg = f"移動エラー {file.relative_to(self.root)}: {e}"
                    print(f"  ❌ {error_msg}")
                    self.report['errors'].append(error_msg)
        
        return moved

    def archive_old_files(self, dry_run: bool = True) -> List[str]:
        """古い・重複ファイルを_archive/に移動"""
        archived = []
        archive_dir = self.root / '_archive'
        archive_dir.mkdir(exist_ok=True)
        
        # カテゴリ別のサブディレクトリ
        subdirs = {
            'debug': archive_dir / 'debug',
            'legacy': archive_dir / 'legacy', 
            'backup': archive_dir / 'backup',
            'temp': archive_dir / 'temp'
        }
        
        for subdir in subdirs.values():
            subdir.mkdir(exist_ok=True)
        
        for pattern in self.archive_targets:
            files = list(self.root.rglob(pattern))
            # 既に_archiveにあるものは除外
            files = [f for f in files if '_archive' not in str(f) and 'old' not in str(f)]
            
            for file in files:
                # カテゴリ判定
                if 'debug' in file.name:
                    target_dir = subdirs['debug']
                elif any(x in file.name for x in ['bak', 'backup', 'old']):
                    target_dir = subdirs['backup']
                elif 'tmp' in file.name:
                    target_dir = subdirs['temp']
                else:
                    target_dir = subdirs['legacy']
                
                target = target_dir / file.name
                
                try:
                    if not dry_run:
                        if target.exists():
                            # 重複回避
                            base_name = file.stem
                            suffix = file.suffix
                            counter = 1
                            while target.exists():
                                target = target_dir / f"{base_name}_{counter}{suffix}"
                                counter += 1
                        
                        shutil.move(str(file), str(target))
                        print(f"  ✅ アーカイブ: {file.relative_to(self.root)} → {target.relative_to(self.root)}")
                    else:
                        print(f"  📝 アーカイブ予定: {file.relative_to(self.root)} → {target.relative_to(self.root)}")
                    
                    archived.append(str(file.relative_to(self.root)))
                    self.report['archived_files'].append({
                        'source': str(file.relative_to(self.root)),
                        'target': str(target.relative_to(self.root)),
                        'category': target_dir.name
                    })
                    
                except Exception as e:
                    error_msg = f"アーカイブエラー {file.relative_to(self.root)}: {e}"
                    print(f"  ❌ {error_msg}")
                    self.report['errors'].append(error_msg)
        
        return archived

    def delete_temp_files(self, dry_run: bool = True) -> List[str]:
        """一時ファイル削除"""
        deleted = []
        
        for pattern in self.delete_targets:
            files = list(self.root.rglob(pattern))
            
            for file in files:
                try:
                    if not dry_run:
                        if file.is_dir():
                            shutil.rmtree(file)
                            print(f"  ✅ ディレクトリ削除: {file.relative_to(self.root)}")
                        else:
                            file.unlink()
                            print(f"  ✅ ファイル削除: {file.relative_to(self.root)}")
                    else:
                        print(f"  📝 削除予定: {file.relative_to(self.root)}")
                    
                    deleted.append(str(file.relative_to(self.root)))
                    self.report['deleted_files'].append({
                        'path': str(file.relative_to(self.root)),
                        'type': 'directory' if file.is_dir() else 'file'
                    })
                    
                except Exception as e:
                    error_msg = f"削除エラー {file.relative_to(self.root)}: {e}"
                    print(f"  ❌ {error_msg}")
                    self.report['errors'].append(error_msg)
        
        return deleted

    def generate_report(self) -> str:
        """整理レポート生成"""
        report = f"""# NeuroHub プロジェクト整理レポート

実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📊 整理サマリー
- 移動したファイル: {len(self.report['moved_files'])}件
- アーカイブしたファイル: {len(self.report['archived_files'])}件  
- 削除したファイル: {len(self.report['deleted_files'])}件
- エラー: {len(self.report['errors'])}件

## 📁 移動されたファイル
"""
        
        if self.report['moved_files']:
            for item in self.report['moved_files']:
                report += f"- `{item['source']}` → `{item['target']}`\n"
        else:
            report += "移動されたファイルはありません。\n"
        
        report += "\n## 📦 アーカイブされたファイル\n"
        
        if self.report['archived_files']:
            for item in self.report['archived_files']:
                report += f"- `{item['source']}` → `{item['target']}` ({item['category']})\n"
        else:
            report += "アーカイブされたファイルはありません。\n"
        
        report += "\n## 🗑️ 削除されたファイル\n"
        
        if self.report['deleted_files']:
            for item in self.report['deleted_files']:
                report += f"- `{item['path']}` ({item['type']})\n"
        else:
            report += "削除されたファイルはありません。\n"
        
        if self.report['errors']:
            report += "\n## ❌ エラー\n"
            for error in self.report['errors']:
                report += f"- {error}\n"
        
        report += f"""
## 📋 整理後の推奨プロジェクト構造

```
NeuroHub/
├── agents/          # エージェントモジュール
├── services/        # サービスレイヤー  
├── config/          # 設定ファイル
├── tests/           # 全テストファイル ← 移動完了
├── tools/           # ユーティリティツール
├── docs/            # ドキュメント
├── data/            # データファイル
├── logs/            # ログファイル
├── _archive/        # アーカイブファイル ← 整理完了
│   ├── debug/       # デバッグファイル
│   ├── legacy/      # レガシーファイル  
│   ├── backup/      # バックアップファイル
│   └── temp/        # 一時ファイル
└── old/             # 既存アーカイブ (保持)
```

## 🚀 次のステップ
1. アーカイブされたファイルの最終確認
2. 単体テストの実行と検証  
3. CI/CDパイプラインのセットアップ
4. ドキュメントの更新
"""
        
        return report

    def cleanup(self, dry_run: bool = True) -> str:
        """プロジェクト整理実行"""
        print("🧹 NeuroHub プロジェクト整理開始")
        print("=" * 50)
        
        if dry_run:
            print("💡 ドライランモード: 実際の変更は行いません")
        
        print("\n📊 整理前の分析:")
        analysis = self.analyze_files()
        
        for category, files in analysis.items():
            if files:
                print(f"  {category}: {len(files)}件")
                for file in files[:3]:  # 最初の3件のみ表示
                    print(f"    - {file}")
                if len(files) > 3:
                    print(f"    ... 他 {len(files)-3}件")
        
        # 1. テストファイル移動
        print("\n📝 Phase 1: テストファイル移動")
        self.move_test_files(dry_run)
        
        # 2. 古いファイルアーカイブ
        print("\n📦 Phase 2: 古いファイルアーカイブ")
        self.archive_old_files(dry_run)
        
        # 3. 一時ファイル削除
        print("\n🗑️ Phase 3: 一時ファイル削除")
        self.delete_temp_files(dry_run)
        
        print("\n📋 整理完了!")
        print("=" * 50)
        
        # レポート生成・保存
        report = self.generate_report()
        report_path = self.root / f"docs/PROJECT_CLEANUP_REPORT_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        if not dry_run:
            with open(report_path, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 詳細レポート: {report_path.relative_to(self.root)}")
        
        return report


def main():
    """メイン実行"""
    import argparse
    
    parser = argparse.ArgumentParser(description="NeuroHub プロジェクト整理ツール")
    parser.add_argument('--dry-run', action='store_true', help='ドライランモード（実際の変更なし）')
    parser.add_argument('--analyze-only', action='store_true', help='分析のみ実行')
    
    args = parser.parse_args()
    
    cleaner = ProjectCleaner()
    
    if args.analyze_only:
        print("🔍 プロジェクト分析のみ実行")
        analysis = cleaner.analyze_files()
        
        for category, files in analysis.items():
            print(f"\n{category}: {len(files)}件")
            for file in files:
                print(f"  - {file}")
    else:
        report = cleaner.cleanup(dry_run=args.dry_run)
        
        if args.dry_run:
            print("\n" + "="*50)
            print("💡 実際に整理を実行するには: python tools/cleanup_project.py")


if __name__ == "__main__":
    main()