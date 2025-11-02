#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/mcp/project_designer.py

プロジェクト設計・計画生成モジュール
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime


class ProjectDesigner:
    """プロジェクト設計クラス - 正規化された仕様から実装計画を生成"""
    
    # プロジェクトタイプ別のテンプレート構造
    PROJECT_TEMPLATES = {
        "cli": {
            "structure": [
                "main.py",
                "cli/",
                "cli/__init__.py",
                "cli/commands.py",
                "utils/",
                "utils/__init__.py",
                "utils/helpers.py",
                "tests/",
                "tests/test_cli.py",
                "README.md",
                "requirements.txt"
            ],
            "dependencies": ["click", "pytest"]
        },
        "web_app": {
            "structure": [
                "app.py",
                "templates/",
                "templates/index.html",
                "static/",
                "static/css/",
                "static/js/",
                "models/",
                "routes/",
                "tests/",
                "README.md",
                "requirements.txt"
            ],
            "dependencies": ["flask", "pytest"]
        },
        "db_app": {
            "structure": [
                "main.py",
                "models/",
                "models/__init__.py",
                "models/database.py",
                "migrations/",
                "config/",
                "config/db_config.py",
                "tests/",
                "tests/test_db.py",
                "README.md",
                "requirements.txt"
            ],
            "dependencies": ["sqlalchemy", "pytest"]
        },
        "scraper": {
            "structure": [
                "scraper.py",
                "parsers/",
                "parsers/__init__.py",
                "storage/",
                "tests/",
                "tests/test_scraper.py",
                "README.md",
                "requirements.txt"
            ],
            "dependencies": ["requests", "beautifulsoup4", "pytest"]
        }
    }
    
    def __init__(self):
        """初期化"""
        self.current_plan = None
    
    def create_plan(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        仕様から実装計画を生成
        
        Args:
            spec: 正規化された仕様（spec_normalizer.pyの出力）
            
        Returns:
            実装計画（ファイル構造、依存関係、タスク等）
        """
        project_type = spec.get("project_type", "cli")
        template = self.PROJECT_TEMPLATES.get(project_type, self.PROJECT_TEMPLATES["cli"])
        
        # 基本計画
        plan = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "project_type": project_type,
                "description": spec.get("description", ""),
                "version": "1.0.0"
            },
            "structure": template["structure"].copy(),
            "dependencies": template["dependencies"].copy(),
            "features": spec.get("features", []),
            "tasks": self._generate_tasks(spec),
            "testing_strategy": self._generate_testing_strategy(spec),
            "validation_steps": [
                "ruff check .",
                "mypy .",
                "bandit -r .",
                "pytest tests/"
            ]
        }
        
        # データベース使用時の追加設定
        if spec.get("database", False):
            plan["dependencies"].extend(["sqlalchemy", "alembic"])
            plan["structure"].extend([
                "migrations/",
                "models/database.py"
            ])
        
        # API連携の追加
        if spec.get("api_integration"):
            plan["dependencies"].append("requests")
            for api in spec["api_integration"]:
                plan["structure"].append(f"integrations/{api}.py")
        
        self.current_plan = plan
        return plan
    
    def _generate_tasks(self, spec: Dict[str, Any]) -> List[Dict[str, str]]:
        """タスクリスト生成"""
        tasks = [
            {
                "id": "1",
                "title": "プロジェクト構造作成",
                "description": "ディレクトリとファイルの初期セットアップ",
                "status": "pending"
            },
            {
                "id": "2",
                "title": "依存関係インストール",
                "description": "requirements.txtから必要パッケージをインストール",
                "status": "pending"
            }
        ]
        
        # 機能ごとのタスク追加
        for i, feature in enumerate(spec.get("features", []), start=3):
            tasks.append({
                "id": str(i),
                "title": f"{feature}機能実装",
                "description": f"{feature}の実装とテスト作成",
                "status": "pending"
            })
        
        # 最終タスク
        tasks.extend([
            {
                "id": str(len(tasks) + 1),
                "title": "静的解析実行",
                "description": "ruff, mypy, banditによるコード検証",
                "status": "pending"
            },
            {
                "id": str(len(tasks) + 2),
                "title": "ユニットテスト実行",
                "description": "pytest実行と結果確認",
                "status": "pending"
            },
            {
                "id": str(len(tasks) + 3),
                "title": "README作成",
                "description": "使用方法とドキュメント作成",
                "status": "pending"
            }
        ])
        
        return tasks
    
    def _generate_testing_strategy(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """テスト戦略生成"""
        testing_level = spec.get("testing_level", "basic")
        
        strategy = {
            "level": testing_level,
            "unit_tests": True,
            "integration_tests": testing_level == "comprehensive",
            "coverage_target": 80 if testing_level == "comprehensive" else 60,
            "test_files": []
        }
        
        # 機能ごとのテストファイル
        for feature in spec.get("features", []):
            strategy["test_files"].append(f"tests/test_{feature}.py")
        
        return strategy
    
    def save_plan(self, output_path: Path) -> None:
        """計画をJSONファイルに保存"""
        if not self.current_plan:
            raise ValueError("計画が生成されていません")
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.current_plan, f, ensure_ascii=False, indent=2)
    
    def load_plan(self, input_path: Path) -> Dict[str, Any]:
        """計画をJSONファイルから読み込み"""
        with open(input_path, 'r', encoding='utf-8') as f:
            self.current_plan = json.load(f)
        
        return self.current_plan
    
    def get_file_structure_tree(self) -> str:
        """ファイル構造をツリー形式で表示"""
        if not self.current_plan:
            return "計画が生成されていません"
        
        tree = "プロジェクト構造:\n"
        tree += "project_root/\n"
        
        for item in self.current_plan["structure"]:
            if item.endswith("/"):
                tree += f"├── {item}\n"
            else:
                tree += f"├── {item}\n"
        
        return tree


# 使用例とテスト
if __name__ == "__main__":
    from spec_normalizer import SpecNormalizer
    
    # 仕様正規化
    normalizer = SpecNormalizer()
    prompt = "シンプルな計算機CLIアプリを作りたい。加算、減算、乗算、除算機能が必要。結果をデータベースに保存したい。"
    spec = normalizer.normalize_prompt(prompt)
    
    print("=== プロジェクト設計テスト ===\n")
    print("仕様:")
    print(json.dumps(spec, ensure_ascii=False, indent=2))
    print("\n" + "=" * 60 + "\n")
    
    # プロジェクト設計
    designer = ProjectDesigner()
    plan = designer.create_plan(spec)
    
    print("生成された計画:")
    print(json.dumps(plan, ensure_ascii=False, indent=2))
    print("\n" + "=" * 60 + "\n")
    
    # ファイル構造表示
    print(designer.get_file_structure_tree())
    
    # 計画保存
    output_path = Path("data/project_plans/test_plan.json")
    designer.save_plan(output_path)
    print(f"\n✅ 計画を {output_path} に保存しました")
