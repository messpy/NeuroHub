# MCPエージェント 概要

## 🎯 役割と責任

MCPエージェント（Model Context Protocol Agent）は、ユーザーのプロンプトから自動的にプロジェクトを生成するシステムです。

---

## 📋 主要機能

### 1. 仕様正規化（spec_normalizer.py）
- ユーザープロンプト→JSON Schema変換
- プロジェクトタイプ自動検出
- バリデーション

### 2. 禁止コマンド検知（command_validator.py）
- 危険コマンドの検出（rm -rf, chmod 777等）
- 代替案自動提示
- コードスニペット内検証

### 3. プロジェクト設計（project_designer.py）
- プロジェクト構造生成
- 依存関係自動検出
- タスクリスト生成
- テスト戦略生成

---

## 🏗️ MCP新フロー

```
ユーザープロンプト
    ↓
仕様正規化（JSON Schema）
    ↓
プロジェクト設計・計画生成
    ↓
スキャフォールド生成（Jinja2）
    ↓
テスト生成
    ↓
静的検証（ruff/mypy/bandit）
    ↓
ユニットテスト実行
    ↓
修正ループ
    ↓
README生成・成果物固定化
```

---

## 🔧 使用方法

### 仕様正規化

```python
from services.mcp.spec_normalizer import SpecNormalizer

normalizer = SpecNormalizer()

# プロンプト正規化
spec = normalizer.normalize_prompt(
    "シンプルなTODOリストCLIアプリを作りたい"
)

# バリデーション
is_valid, error = normalizer.validate_spec(spec)
```

### コマンド検証

```python
from services.mcp.command_validator import CommandValidator

validator = CommandValidator()

# コマンド検証
is_safe, violation = validator.validate_command("rm -rf /")

if not is_safe:
    print(f"危険: {violation['reason']}")
    print("代替案:")
    for alt in violation['alternatives']:
        print(f"  - {alt}")
```

### プロジェクト設計

```python
from services.mcp.project_designer import ProjectDesigner

designer = ProjectDesigner()

# 計画生成
plan = designer.create_plan(spec)

# 構造確認
print(designer.get_file_structure_tree())
```

---

## 🧪 テスト

### テストファイル
- `tests/test_mcp_workflow.py`: 統合テスト（6/6 PASSED）

### 実行コマンド
```bash
pytest tests/test_mcp_workflow.py -v -s
```

---

## 📖 関連ドキュメント

- [詳細設計](./DETAILED_DESIGN.md)
- [コーディングルール](./CODING_RULES.md)
- [その他設計](./OTHER_DESIGNS.md)

---

*最終更新: 2025年11月2日*
