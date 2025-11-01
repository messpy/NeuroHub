# NeuroHub Testing Guide

## テスト環境セットアップ

### 前提条件
- Python 3.8以上
- Git
- 仮想環境（推奨）

### 依存関係のインストール

```bash
# 開発依存関係をインストール
pip install -r requirements-dev.txt

# または個別にインストール
pip install pytest pytest-cov pytest-mock requests-mock flake8 black isort
```

### テスト実行方法

#### 1. 基本的なテスト実行
```bash
# すべてのテストを実行
pytest tests/ -v

# 特定のテストファイルを実行
pytest tests/agents/test_git_agent.py -v

# 特定のテスト関数を実行
pytest tests/agents/test_git_agent.py::test_git_agent_initialization -v
```

#### 2. カバレッジ付きテスト実行
```bash
# カバレッジレポート生成
pytest tests/ --cov=agents --cov=services --cov-report=html --cov-report=term

# HTMLレポートの確認
# htmlcov/index.html をブラウザで開く
```

#### 3. 統合テストランナーの使用

**Linux/Mac:**
```bash
python run_tests.py --all
python run_tests.py --python --coverage
python run_tests.py --shell
```

**Windows:**
```cmd
run_tests.bat --all
run_tests.bat --python --coverage
run_tests.bat --shell
```

#### 4. コード品質チェック
```bash
# 構文チェック
flake8 .

# コードフォーマットチェック
black --check .

# インポート並び順チェック
isort --check-only .

# すべて自動修正
black .
isort .
```

## テスト構造

### ディレクトリ構成
```
tests/
├── agents/
│   ├── test_git_agent.py      # GitAgent単体テスト
│   ├── test_llm_agent.py      # LLMAgent単体テスト
│   ├── test_config_agent.py   # ConfigAgent単体テスト
│   └── test_command_agent.py  # CommandAgent単体テスト
├── services/
│   ├── test_llm_providers.py  # LLMプロバイダーテスト
│   └── test_db_services.py    # データベースサービステスト
└── tools/
    └── test_git_commit_ai.sh   # シェルツールテスト
```

### テストカバレッジ

#### Agents (agents/)
- **GitAgent**: Git操作、コミットメッセージ生成、ファイル処理
- **LLMAgent**: プロバイダー管理、テキスト生成、フォールバック機能
- **ConfigAgent**: 設定読み込み、検証、環境変数処理
- **CommandAgent**: コマンド実行、パイプライン処理、エラーハンドリング

#### Services (services/)
- **LLMProviders**: Gemini、HuggingFace、Ollama API統合
- **DatabaseServices**: SQLite操作、履歴管理、検索機能

#### Tools (tools/)
- **git_commit_ai**: シェルスクリプトとしての独立動作テスト

## モッキング戦略

### LLMプロバイダーのモック
```python
@pytest.fixture
def mock_gemini_provider():
    with patch('services.llm.provider_gemini.GeminiProvider') as mock:
        instance = mock.return_value
        instance.is_configured.return_value = True
        instance.generate_text.return_value = "Mocked response"
        yield instance
```

### Git操作のモック
```python
@pytest.fixture
def mock_git_operations():
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Success"
        yield mock_run
```

### データベース操作のモック
```python
@pytest.fixture
def temp_database():
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    os.unlink(db_path)
```

## CI/CD統合

### GitHub Actions
`.github/workflows/test.yml` でCI/CDパイプラインが設定されています。

**実行内容:**
1. Python 3.8-3.11での多バージョンテスト
2. 依存関係のインストール
3. Linting (flake8)
4. フォーマットチェック (black)
5. インポート並び順チェック (isort)
6. 単体テスト実行
7. カバレッジレポート生成
8. シェルツールテスト

### ローカル検証
```bash
# テスト環境の検証
python validate_tests.py

# 手動でCI相当のチェック実行
flake8 .
black --check .
isort --check-only .
pytest tests/ --cov=agents --cov=services -v
```

## トラブルシューティング

### よくある問題

1. **ImportError: No module named 'agents'**
   ```bash
   # プロジェクトルートディレクトリで実行
   export PYTHONPATH="${PYTHONPATH}:$(pwd)"
   pytest tests/
   ```

2. **FileNotFoundError in database tests**
   ```bash
   # テンポラリデータベースの権限確認
   chmod 755 /tmp
   ```

3. **Mock not working properly**
   ```python
   # patch decoratorの順序確認
   @patch('module.function')
   def test_function(self, mock_func):
       pass
   ```

4. **Windows PowerShell実行エラー**
   ```cmd
   # 実行ポリシー変更
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

   # またはバッチファイル使用
   run_tests.bat --all
   ```

### デバッグ方法

1. **詳細ログ出力**
   ```bash
   pytest tests/ -v -s --tb=long
   ```

2. **特定テストのデバッグ**
   ```bash
   pytest tests/agents/test_git_agent.py::test_specific_function -v -s
   ```

3. **カバレッジ詳細確認**
   ```bash
   pytest tests/ --cov=agents --cov-report=term-missing
   ```

## ベストプラクティス

### テスト作成ガイドライン

1. **AAA パターン**
   - Arrange: テストデータ準備
   - Act: 実際の処理実行
   - Assert: 結果検証

2. **独立性の確保**
   - 各テストは他に依存しない
   - fixtureで環境初期化

3. **エッジケース考慮**
   - 正常系、異常系両方をテスト
   - 境界値テストの実装

4. **意味のあるテスト名**
   ```python
   def test_git_agent_commits_staged_files_successfully():
       pass
   ```

### メンテナンス

- 定期的なテスト見直し（月次）
- カバレッジ目標: 80%以上
- 新機能追加時は必ずテスト追加
- 失敗したテストは優先的に修正
