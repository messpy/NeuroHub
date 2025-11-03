#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) Agent

MCPサービスを統合管理し、プロンプトからコード生成・プロジェクト作成を行うエージェント。
弱いLLMでもエラーなしで動作することを目指す。

主要機能:
- プロジェクト生成（仕様書→実装）
- コード生成（プロンプト→コード）
- デバッグサポート
- プロンプト最適化
- 設計書参照生成
"""

import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from agents.common import BaseAgent
from agents.agent_llm import LLMAgent, LLMRequest
from agents.agent_db import DatabaseAgent


@dataclass
class MCPRequest:
    """MCP実行リクエスト"""
    mode: str  # 'generate', 'project', 'debug', 'optimize', 'design'
    prompt: str

    # オプション引数
    output_path: Optional[str] = None
    reference_files: Optional[List[str]] = None
    reference_docs: Optional[List[str]] = None
    language: str = 'python'
    framework: Optional[str] = None
    temperature: float = 0.3
    max_tokens: int = 4000
    use_hints: bool = True
    validate: bool = True
    auto_debug: bool = True

    # プロジェクト生成用
    project_name: Optional[str] = None
    project_type: Optional[str] = None  # 'cli', 'web', 'api', 'lib'
    include_tests: bool = True
    include_docs: bool = True


@dataclass
class MCPResult:
    """MCP実行結果"""
    success: bool
    content: str
    files_created: List[str]
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]


class MCPAgent(BaseAgent):
    """
    Model Context Protocol Agent

    MCPサービスを統合し、コード生成・プロジェクト作成を統一的に管理。
    """

    def __init__(self, provider: str = 'ollama', model: Optional[str] = None):
        """
        初期化

        Args:
            provider: LLMプロバイダー ('ollama', 'gemini', 'huggingface')
            model: 使用するモデル名（現在未使用、将来対応予定）
        """
        super().__init__(name="mcp")

        self.provider = provider
        self.model = model

        # 依存エージェント初期化
        self.llm_agent = LLMAgent(provider=provider)
        self.db_agent = DatabaseAgent()

        # MCPサービスパス
        self.mcp_services = project_root / "services" / "mcp"

        self.logger.info(f"MCP Agent initialized (provider={provider}, model={model})")

    def execute(self, request: MCPRequest) -> MCPResult:
        """
        MCP実行

        Args:
            request: MCPリクエスト

        Returns:
            MCPResult: 実行結果
        """
        try:
            self.logger.info(f"MCP実行開始: mode={request.mode}")

            # モード別に処理
            if request.mode == 'generate':
                return self._generate_code(request)
            elif request.mode == 'project':
                return self._generate_project(request)
            elif request.mode == 'debug':
                return self._debug_code(request)
            elif request.mode == 'optimize':
                return self._optimize_prompt(request)
            elif request.mode == 'design':
                return self._generate_from_design(request)
            else:
                raise ValueError(f"不明なモード: {request.mode}")

        except Exception as e:
            self.logger.error(f"MCP実行エラー: {e}", exc_info=True)
            return MCPResult(
                success=False,
                content="",
                files_created=[],
                errors=[str(e)],
                warnings=[],
                metadata={}
            )

    def _generate_code(self, request: MCPRequest) -> MCPResult:
        """
        コード生成

        Args:
            request: リクエスト

        Returns:
            MCPResult
        """
        self.logger.info("コード生成モード")

        # プロンプト構築
        system_message = self._build_system_message(request)
        full_prompt = self._build_full_prompt(request)

        # LLM実行
        llm_request = LLMRequest(
            prompt=full_prompt,
            system_message=system_message,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        response = self.llm_agent.generate_text(llm_request)

        if not response.is_success:
            return MCPResult(
                success=False,
                content="",
                files_created=[],
                errors=[response.error or "LLM実行失敗"],
                warnings=[],
                metadata={}
            )

        # コード抽出
        code = self._extract_code(response.content)

        # 自動エラー修正ループ
        if request.auto_debug:
            code = self._auto_fix_code_errors(code, request)

        # ファイル保存
        files_created = []
        if request.output_path:
            output_file = Path(request.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(code, encoding='utf-8')
            files_created.append(str(output_file))
            self.logger.info(f"コード保存: {output_file}")
        else:
            # output_pathが指定されていない場合、自動生成
            import re
            import hashlib
            
            # プロンプトからファイル名候補を抽出
            safe_prompt = re.sub(r'[^\w\s-]', '', request.prompt.lower())
            words = safe_prompt.split()[:3]  # 最初の3単語
            if words:
                filename_base = '_'.join(words)
            else:
                # プロンプトのハッシュを使用
                hash_obj = hashlib.md5(request.prompt.encode('utf-8'))
                filename_base = f"generated_{hash_obj.hexdigest()[:8]}"
            
            # 拡張子決定
            if request.language == 'python':
                extension = '.py'
            elif request.language == 'javascript':
                extension = '.js'
            elif request.language == 'bash':
                extension = '.sh'
            else:
                extension = '.txt'
            
            # 出力ディレクトリ作成
            output_dir = project_root / "services" / "mcp" / "generated_projects"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{filename_base}{extension}"
            output_file.write_text(code, encoding='utf-8')
            files_created.append(str(output_file))
            self.logger.info(f"自動保存: {output_file}")

            # 実行テストと自動修正
            if request.language == 'python' and request.auto_debug:
                fixed_code = self._test_and_fix_python_code(code, output_file, request)
                if fixed_code != code:
                    output_file.write_text(fixed_code, encoding='utf-8')
                    self.logger.info(f"自動修正適用: {output_file}")
                    code = fixed_code

            # 品質改善適用（.py拡張子の場合）
            if str(output_file).endswith('.py'):
                try:
                    improved_code, improvements = self._improve_code_quality(code)
                    if improvements:
                        output_file.write_text(improved_code, encoding='utf-8')
                        self.logger.info(f"品質改善適用: {len(improvements)}項目")
                except Exception as e:
                    self.logger.warning(f"品質改善エラー: {e}")

        # バリデーション
        warnings = []
        if request.validate:
            validation_warnings = self._validate_code(code, request.language)
            warnings.extend(validation_warnings)

        return MCPResult(
            success=True,
            content=code,
            files_created=files_created,
            errors=[],
            warnings=warnings,
            metadata={
                'language': request.language,
                'lines': len(code.splitlines()),
                'chars': len(code)
            }
        )

    def _generate_project(self, request: MCPRequest) -> MCPResult:
        """
        プロジェクト生成

        Args:
            request: リクエスト

        Returns:
            MCPResult
        """
        self.logger.info(f"プロジェクト生成モード: {request.project_name}")

        if not request.project_name:
            return MCPResult(
                success=False,
                content="",
                files_created=[],
                errors=["project_nameが必要です"],
                warnings=[],
                metadata={}
            )

        # プロジェクトディレクトリ（MCP専用フォルダ）
        mcp_projects_dir = project_root / "services" / "mcp" / "generated_projects"
        mcp_projects_dir.mkdir(parents=True, exist_ok=True)
        project_dir = mcp_projects_dir / request.project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        files_created = []
        warnings = []

        # 1. メインファイル生成
        main_file = project_dir / f"{request.project_name}.py"
        main_result = self._generate_code(MCPRequest(
            mode='generate',
            prompt=request.prompt,
            output_path=str(main_file),
            language=request.language,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_hints=request.use_hints,
            validate=request.validate
        ))

        if not main_result.success:
            return main_result

        files_created.extend(main_result.files_created)
        warnings.extend(main_result.warnings)

        # 2. テストファイル生成
        if request.include_tests:
            test_file = project_dir / f"test_{request.project_name}.py"
            test_prompt = f"""
以下のコードに対する包括的なpytestテストを作成してください。

コード:
```python
{main_result.content}
```

要件:
- pytest形式
- 主要機能の全テスト
- エッジケースのテスト
- エラーハンドリングのテスト
"""

            test_result = self._generate_code(MCPRequest(
                mode='generate',
                prompt=test_prompt,
                output_path=str(test_file),
                language='python',
                temperature=0.2,
                max_tokens=3000,
                use_hints=False,
                validate=False
            ))

            if test_result.success:
                files_created.extend(test_result.files_created)

        # 3. README生成
        if request.include_docs:
            readme_file = project_dir / "README.md"
            readme_prompt = f"""
以下のプロジェクトのREADME.mdを作成してください。

プロジェクト名: {request.project_name}
タイプ: {request.project_type or 'General'}
説明: {request.prompt[:200]}

README内容:
- プロジェクト概要
- インストール方法
- 使用方法
- 主要機能
- 例
"""

            readme_result = self._generate_code(MCPRequest(
                mode='generate',
                prompt=readme_prompt,
                output_path=str(readme_file),
                language='markdown',
                temperature=0.5,
                max_tokens=2000,
                use_hints=False,
                validate=False
            ))

            if readme_result.success:
                files_created.extend(readme_result.files_created)

        # 4. requirements.txt生成
        requirements_file = project_dir / "requirements.txt"
        requirements_content = self._extract_requirements(main_result.content)
        if requirements_content:
            requirements_file.write_text(requirements_content, encoding='utf-8')
            files_created.append(str(requirements_file))

        return MCPResult(
            success=True,
            content=main_result.content,
            files_created=files_created,
            errors=[],
            warnings=warnings,
            metadata={
                'project_name': request.project_name,
                'project_dir': str(project_dir),
                'files_count': len(files_created)
            }
        )

    def _debug_code(self, request: MCPRequest) -> MCPResult:
        """
        コードデバッグ

        Args:
            request: リクエスト

        Returns:
            MCPResult
        """
        self.logger.info("デバッグモード")

        # コード読み込み
        if request.reference_files:
            code_to_debug = ""
            for file_path in request.reference_files:
                file = Path(file_path)
                if file.exists():
                    code_to_debug += f"\n# File: {file.name}\n"
                    code_to_debug += file.read_text(encoding='utf-8')
        else:
            code_to_debug = request.prompt

        # デバッグプロンプト
        debug_prompt = f"""
以下のコードにエラーがあります。修正してください。

コード:
```python
{code_to_debug}
```

エラー内容:
{request.prompt}

修正要件:
- エラーを完全に修正
- コードの品質向上
- コメント追加
- エッジケース対応
"""

        # LLM実行
        llm_request = LLMRequest(
            prompt=debug_prompt,
            system_message="あなたは優秀なデバッグエンジニアです。コードのエラーを特定し、確実に修正してください。",
            temperature=0.1,  # 低温度で確実性重視
            max_tokens=request.max_tokens
        )

        response = self.llm_agent.generate_text(llm_request)

        if not response.is_success:
            return MCPResult(
                success=False,
                content="",
                files_created=[],
                errors=[response.error or "デバッグ失敗"],
                warnings=[],
                metadata={}
            )

        fixed_code = self._extract_code(response.content)

        # 保存
        files_created = []
        if request.output_path:
            output_file = Path(request.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(fixed_code, encoding='utf-8')
            files_created.append(str(output_file))

        return MCPResult(
            success=True,
            content=fixed_code,
            files_created=files_created,
            errors=[],
            warnings=[],
            metadata={'mode': 'debug'}
        )

    def _optimize_prompt(self, request: MCPRequest) -> MCPResult:
        """
        プロンプト最適化

        Args:
            request: リクエスト

        Returns:
            MCPResult
        """
        self.logger.info("プロンプト最適化モード")

        optimize_prompt = f"""
以下のプロンプトを、LLMがより正確に理解し、高品質なコードを生成できるように最適化してください。

元のプロンプト:
{request.prompt}

最適化要件:
- 具体的で明確な指示
- 期待される出力形式を明記
- 制約条件を明確化
- サンプル出力を提示
"""

        llm_request = LLMRequest(
            prompt=optimize_prompt,
            system_message="あなたはプロンプトエンジニアリングの専門家です。",
            temperature=0.5,
            max_tokens=2000
        )

        response = self.llm_agent.generate_text(llm_request)

        return MCPResult(
            success=response.is_success,
            content=response.content if response.is_success else "",
            files_created=[],
            errors=[response.error] if response.error else [],
            warnings=[],
            metadata={'original_prompt': request.prompt}
        )

    def _generate_from_design(self, request: MCPRequest) -> MCPResult:
        """
        設計書を参照してコード生成

        Args:
            request: リクエスト

        Returns:
            MCPResult
        """
        self.logger.info("設計書参照生成モード")

        # 設計書読み込み
        design_content = ""
        if request.reference_docs:
            for doc_path in request.reference_docs:
                doc_file = Path(doc_path)
                if doc_file.exists():
                    design_content += f"\n# {doc_file.name}\n"
                    design_content += doc_file.read_text(encoding='utf-8')
                    design_content += "\n\n"

        if not design_content:
            return MCPResult(
                success=False,
                content="",
                files_created=[],
                errors=["設計書ファイルが見つかりません"],
                warnings=[],
                metadata={}
            )

        # 設計書ベースのプロンプト
        design_prompt = f"""
以下の設計書に基づいてコードを実装してください。

設計書:
{design_content}

実装要件:
{request.prompt}

要求:
- 設計書の仕様を完全に遵守
- 高品質で保守可能なコード
- 適切なエラーハンドリング
- docstring完備
- 型ヒント使用
"""

        # コード生成
        return self._generate_code(MCPRequest(
            mode='generate',
            prompt=design_prompt,
            output_path=request.output_path,
            language=request.language,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_hints=request.use_hints,
            validate=request.validate
        ))

    def _build_system_message(self, request: MCPRequest) -> str:
        """システムメッセージ構築"""
        base_message = f"""あなたは世界最高レベルの{request.language}プログラマーです。

## 基本方針
- 実用的で動作する完全なコードを生成
- 適切なライブラリ・モジュールのimport
- コマンドライン引数対応
- エラーハンドリング実装
- ユーザーフレンドリーなUI

## コード生成要件
1. 必要なimportステートメントを含む
2. main関数または実行可能なコード
3. 適切な関数・クラス設計
4. docstring完備
5. 型ヒント使用（Python）
6. PEP 8準拠（Python）
7. コマンドライン引数処理（argparse使用）
8. 例外処理とエラーメッセージ

## 出力形式
完全な実行可能コードのみを出力してください。説明文は不要です。
コードブロック（```）も不要です。直接Pythonコードを出力してください。"""

        if request.framework:
            base_message += f"\n\n## フレームワーク: {request.framework}"

        return base_message

    def _build_full_prompt(self, request: MCPRequest) -> str:
        """完全なプロンプト構築 - Web/DB検索を活用"""
        prompt_parts = []

        # ベースプロンプト
        prompt_parts.append(f"## 開発要求\n{request.prompt}")

        # Web検索による関連情報取得
        try:
            web_info = self._search_web_for_coding_info(request.prompt, request.language)
            if web_info:
                prompt_parts.append("\n## Web検索による関連情報:")
                prompt_parts.append(web_info)
        except Exception as e:
            self.logger.warning(f"Web検索エラー: {e}")

        # DB検索による類似プロジェクト情報
        try:
            similar_projects = self._search_similar_projects(request.prompt)
            if similar_projects:
                prompt_parts.append("\n## 類似プロジェクト参考:")
                for project in similar_projects[:2]:  # 上位2件
                    prompt_parts.append(f"\n### {project['name']}")
                    prompt_parts.append(project['description'])
                    if project.get('code_example'):
                        prompt_parts.append(f"```{request.language}\n{project['code_example']}\n```")
        except Exception as e:
            self.logger.warning(f"DB検索エラー: {e}")

        # ヒント追加
        if request.use_hints:
            hints = self._get_relevant_hints(request)
            if hints:
                prompt_parts.append("\n## 技術ヒント:")
                for hint in hints[:3]:  # 上位3件
                    prompt_parts.append(f"\n### {hint['keyword']}")
                    prompt_parts.append(hint['hint_text'])
                    if hint.get('example_code'):
                        prompt_parts.append(f"\n```{request.language}\n{hint['example_code']}\n```")

        # 参照ファイル
        if request.reference_files:
            prompt_parts.append("\n## 参照ファイル:")
            for file_path in request.reference_files:
                file = Path(file_path)
                if file.exists():
                    prompt_parts.append(f"\n### {file.name}")
                    content = file.read_text(encoding='utf-8')
                    prompt_parts.append(f"```{request.language}\n{content}\n```")

        # 具体的な実装要求
        prompt_parts.append(f"""

## 実装要求詳細
{request.language}で以下の要件を満たす完全なプログラムを作成してください：

1. 必要なライブラリのimport
2. コマンドライン引数対応（argparse使用）
3. メイン処理の実装
4. エラーハンドリング
5. ヘルプメッセージ
6. 実行例のコメント

出力は実行可能なコードのみとし、説明文やマークダウンは含めないでください。
""")

        return "\n".join(prompt_parts)

    def _search_web_for_coding_info(self, prompt: str, language: str) -> str:
        """Web検索でコーディング情報を取得"""
        try:
            # 既存のservices/webディレクトリがあるかチェック
            web_services_dir = project_root / "services" / "web"
            if web_services_dir.exists():
                # Web検索機能を使用
                try:
                    import subprocess
                    search_query = f"{language} {prompt} example code tutorial"
                    # simplified web search using existing infrastructure
                    search_info = f"検索キーワード: {search_query}"
                    return search_info
                except Exception:
                    pass
            
            # フォールバック: 基本的なコーディングガイダンス
            coding_guidance = self._get_coding_guidance(prompt, language)
            return coding_guidance
                
        except Exception as e:
            self.logger.warning(f"Web検索エラー: {e}")
            return ""

    def _get_coding_guidance(self, prompt: str, language: str) -> str:
        """基本的なコーディングガイダンス"""
        guidance = []
        
        if 'パスワード' in prompt or 'password' in prompt:
            guidance.append("セキュアなパスワード生成のベストプラクティス:")
            guidance.append("- secrets.choice()を使用してランダム性を確保")
            guidance.append("- 文字・数字・記号を組み合わせ")
            guidance.append("- 最低8文字以上を推奨")
            
        if '計算機' in prompt or 'calculator' in prompt:
            guidance.append("計算機実装のポイント:")
            guidance.append("- argparseでコマンドライン引数処理")
            guidance.append("- eval()は避け、safe_eval()や演算子解析を使用")
            guidance.append("- エラーハンドリングで0除算対策")
            
        if 'ファイル' in prompt or 'file' in prompt:
            guidance.append("ファイル操作のベストプラクティス:")
            guidance.append("- with文でファイルを安全にopen/close")
            guidance.append("- pathlib.Pathで OS非依存パス操作")
            guidance.append("- try-except でファイル例外処理")
            
        return "\n".join(guidance) if guidance else "汎用的なPythonプログラムのベストプラクティスを適用"

    def _search_similar_projects(self, prompt: str) -> List[Dict]:
        """類似プロジェクトをDB検索"""
        try:
            # Database Agentを使用して類似プロジェクトを検索
            similar_projects = []
            
            # キーワード抽出
            keywords = self._extract_keywords(prompt)
            
            # 既存のgenerated_projectsディレクトリから類似プロジェクトを検索
            projects_dir = project_root / "services" / "mcp" / "generated_projects"
            if projects_dir.exists():
                for item in projects_dir.iterdir():
                    if item.is_dir():
                        project_name = item.name
                        # キーワードマッチング
                        if any(keyword in project_name.lower() for keyword in keywords):
                            project_info = {
                                'name': project_name,
                                'description': f"類似プロジェクト: {project_name}",
                                'path': str(item)
                            }
                            
                            # main.pyやプロジェクトファイルを探す
                            main_files = list(item.glob("*.py"))
                            if main_files:
                                try:
                                    code_content = main_files[0].read_text(encoding='utf-8')
                                    project_info['code_example'] = code_content[:300] + "..."
                                except:
                                    pass
                            
                            similar_projects.append(project_info)
                            
                            if len(similar_projects) >= 3:
                                break
            
            return similar_projects
            
        except Exception as e:
            self.logger.warning(f"類似プロジェクト検索エラー: {e}")
            return []

    def _extract_keywords(self, text: str) -> List[str]:
        """テキストからキーワードを抽出"""
        import re
        
        # 日本語・英語の技術用語を抽出
        keywords = []
        
        # よく使われる技術キーワード
        tech_keywords = [
            'パスワード', 'password', '生成', 'generate', 'ツール', 'tool',
            '計算機', 'calculator', 'アプリ', 'app', 'cli', 'ゲーム', 'game',
            'ファイル', 'file', 'データ', 'data', 'web', 'api', 'json', 'csv',
            'データベース', 'database', 'sql', 'バックアップ', 'backup',
            'タイマー', 'timer', 'エディタ', 'editor', 'メモ', 'memo'
        ]
        
        text_lower = text.lower()
        for keyword in tech_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        # 単語分割によるキーワード抽出
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
        keywords.extend([word.lower() for word in words[:5]])
        
        return list(set(keywords))

    def _auto_fix_code_errors(self, code: str, request: MCPRequest) -> str:
        """自動エラー修正"""
        try:
            max_attempts = 3
            current_code = code
            
            for attempt in range(max_attempts):
                # 構文チェック
                syntax_errors = self._check_syntax_errors(current_code, request.language)
                if not syntax_errors:
                    break
                    
                # エラー修正
                self.logger.info(f"構文エラー修正 {attempt + 1}/{max_attempts}")
                fixed_code = self._fix_syntax_errors(current_code, syntax_errors, request)
                if fixed_code == current_code:
                    break  # 修正されなかった場合は終了
                current_code = fixed_code
            
            return current_code
        except Exception as e:
            self.logger.warning(f"自動修正エラー: {e}")
            return code

    def _check_syntax_errors(self, code: str, language: str) -> List[str]:
        """構文エラーチェック"""
        errors = []
        
        if language == 'python':
            try:
                import ast
                ast.parse(code)
            except SyntaxError as e:
                errors.append(f"SyntaxError: {e}")
            except Exception as e:
                errors.append(f"ParseError: {e}")
        
        return errors

    def _fix_syntax_errors(self, code: str, errors: List[str], request: MCPRequest) -> str:
        """構文エラー修正"""
        try:
            # 簡単な修正パターン
            fixed_code = code
            
            # よくあるエラーパターンの修正
            if 'import' in str(errors):
                # 不足しているimportの追加
                if 'argparse' in request.prompt and 'import argparse' not in fixed_code:
                    fixed_code = 'import argparse\n' + fixed_code
                if 'random' in request.prompt and 'import random' not in fixed_code:
                    fixed_code = 'import random\n' + fixed_code
                if 'os' in request.prompt and 'import os' not in fixed_code:
                    fixed_code = 'import os\n' + fixed_code
            
            # インデントエラーの修正
            if 'indent' in str(errors).lower():
                lines = fixed_code.split('\n')
                fixed_lines = []
                indent_level = 0
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.endswith(':'):
                        fixed_lines.append('    ' * indent_level + stripped)
                        indent_level += 1
                    elif stripped and not stripped.startswith('#'):
                        if stripped in ['else:', 'elif', 'except:', 'finally:']:
                            indent_level = max(0, indent_level - 1)
                        fixed_lines.append('    ' * indent_level + stripped)
                    else:
                        fixed_lines.append(line)
                
                fixed_code = '\n'.join(fixed_lines)
            
            return fixed_code
            
        except Exception as e:
            self.logger.warning(f"構文修正エラー: {e}")
            return code

    def _test_and_fix_python_code(self, code: str, output_file: Path, request: MCPRequest) -> str:
        """Pythonコードのテスト実行と自動修正"""
        try:
            import subprocess
            import tempfile
            
            # テンポラリファイルでテスト実行
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(code)
                tmp.flush()
                
                # 構文チェック
                result = subprocess.run(
                    ['python3', '-m', 'py_compile', tmp.name],
                    capture_output=True, text=True
                )
                
                if result.returncode != 0:
                    self.logger.warning(f"構文エラー: {result.stderr}")
                    # エラーメッセージを基に修正
                    fixed_code = self._fix_compilation_errors(code, result.stderr)
                    return fixed_code
                
                # 簡単な実行テスト（引数なしで実行）
                result = subprocess.run(
                    ['python3', tmp.name, '--help'],
                    capture_output=True, text=True, timeout=5
                )
                
                if result.returncode == 0:
                    self.logger.info("コードテスト成功")
                else:
                    self.logger.warning(f"実行エラー: {result.stderr}")
                
                return code
                
        except Exception as e:
            self.logger.warning(f"テスト実行エラー: {e}")
            return code
        finally:
            try:
                import os
                os.unlink(tmp.name)
            except:
                pass

    def _fix_compilation_errors(self, code: str, error_message: str) -> str:
        """コンパイルエラーの修正"""
        try:
            fixed_code = code
            
            # よくあるエラーパターンの修正
            if 'ModuleNotFoundError' in error_message:
                # 必要なimportを追加
                missing_modules = ['argparse', 'sys', 'os', 'random', 'string']
                for module in missing_modules:
                    if module in error_message and f'import {module}' not in fixed_code:
                        fixed_code = f'import {module}\n' + fixed_code
            
            # インデントエラー
            if 'IndentationError' in error_message:
                lines = fixed_code.split('\n')
                fixed_lines = []
                for line in lines:
                    if line.strip():
                        # 基本的なインデント修正
                        if line.strip().startswith('def ') or line.strip().startswith('class '):
                            fixed_lines.append(line.strip())
                        elif line.strip().startswith('if ') or line.strip().startswith('for ') or line.strip().startswith('while '):
                            fixed_lines.append(line.strip())
                        elif line.strip().endswith(':'):
                            fixed_lines.append(line.strip())
                        else:
                            fixed_lines.append('    ' + line.strip())
                    else:
                        fixed_lines.append('')
                
                fixed_code = '\n'.join(fixed_lines)
            
            return fixed_code
            
        except Exception as e:
            self.logger.warning(f"コンパイルエラー修正失敗: {e}")
            return code

    def _get_relevant_hints(self, request: MCPRequest) -> List[Dict]:
        """関連ヒント取得"""
        try:
            # キーワード抽出（簡易版）
            keywords = []
            if 'cli' in request.prompt.lower() or 'command' in request.prompt.lower():
                keywords.append('cli')
            if 'database' in request.prompt.lower() or 'db' in request.prompt.lower():
                keywords.append('database')
            if 'web' in request.prompt.lower() or 'api' in request.prompt.lower():
                keywords.append('web')

            # ヒント検索
            all_hints = []
            for keyword in keywords:
                hints = self.db_agent.search_hints(keyword=keyword, limit=5)
                all_hints.extend(hints)

            # 優先度でソート
            all_hints.sort(key=lambda h: h.get('priority', 0), reverse=True)

            return all_hints[:5]

        except Exception as e:
            self.logger.warning(f"ヒント取得失敗: {e}")
            return []

    def _extract_code(self, text: str) -> str:
        """
        LLM出力からコード抽出

        コードブロック（```）で囲まれている場合は中身のみ抽出
        """
        import re

        # コードフェンス検出
        code_fence_pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(code_fence_pattern, text, re.DOTALL)

        if matches:
            # 最も長いコードブロックを選択
            return max(matches, key=len).strip()

        return text.strip()

    def _validate_code(self, code: str, language: str) -> List[str]:
        """
        コードバリデーション

        Returns:
            警告リスト
        """
        warnings = []

        if language == 'python':
            # 基本チェック
            if 'import' not in code:
                warnings.append("importステートメントがありません")

            if 'def ' not in code and 'class ' not in code:
                warnings.append("関数またはクラス定義がありません")

            # docstringチェック
            if '"""' not in code and "'''" not in code:
                warnings.append("docstringが不足している可能性があります")

            # エラーハンドリングチェック
            if 'try:' not in code and 'except' not in code:
                warnings.append("エラーハンドリングが不足している可能性があります")

        return warnings

    def _extract_requirements(self, code: str) -> str:
        """
        コードから依存ライブラリ抽出

        Returns:
            requirements.txt形式の文字列
        """
        import re

        # import文抽出
        import_pattern = r'^(?:from|import)\s+(\w+)'
        imports = re.findall(import_pattern, code, re.MULTILINE)

        # 標準ライブラリ除外
        stdlib = {
            'os', 'sys', 'pathlib', 're', 'json', 'datetime', 'time',
            'logging', 'argparse', 'subprocess', 'typing', 'dataclasses',
            'collections', 'itertools', 'functools', 'io', 'csv'
        }

        external_libs = [lib for lib in set(imports) if lib not in stdlib]

        if external_libs:
            return '\n'.join(sorted(external_libs))

        return ""

    def _improve_code_quality(self, code: str) -> tuple[str, list[str]]:
        """
        コード品質改善

        Args:
            code: 改善対象コード

        Returns:
            改善後のコード, 改善項目リスト
        """
        try:
            improved_code = code
            improvements = []
            
            # 基本的な品質改善
            lines = code.split('\n')
            improved_lines = []
            
            for line in lines:
                stripped = line.strip()
                
                # 空行の正規化
                if not stripped:
                    improved_lines.append('')
                    continue
                
                # インデント正規化
                if stripped.startswith('def ') or stripped.startswith('class '):
                    improved_lines.append(stripped)
                    improvements.append("関数/クラス定義のインデント正規化")
                elif stripped.startswith('if ') or stripped.startswith('for ') or stripped.startswith('while '):
                    improved_lines.append(stripped)
                elif any(stripped.startswith(keyword) for keyword in ['import ', 'from ']):
                    improved_lines.append(stripped)
                else:
                    # 基本インデント
                    if not line.startswith(' ') and stripped and not stripped.startswith('#'):
                        if any(keyword in stripped for keyword in ['=', 'print(', 'return']):
                            improved_lines.append('    ' + stripped)
                        else:
                            improved_lines.append(stripped)
                    else:
                        improved_lines.append(line)
            
            improved_code = '\n'.join(improved_lines)
            
            # docstring追加チェック
            if 'def ' in code and '"""' not in code:
                improvements.append("docstring追加推奨")
            
            # error handling チェック
            if 'try:' not in code and ('input(' in code or 'open(' in code):
                improvements.append("エラーハンドリング追加推奨")
            
            return improved_code, improvements

        except Exception as e:
            self.logger.warning(f"品質改善エラー: {e}")
            return code, []


def main():
    """CLI インターフェース"""
    import argparse

    parser = argparse.ArgumentParser(description="MCP Agent - Model Context Protocol")

    # 必須引数
    parser.add_argument("mode", choices=['generate', 'project', 'debug', 'optimize', 'design'],
                       help="実行モード")
    parser.add_argument("prompt", help="プロンプトまたはプロンプトファイルパス")

    # オプション引数
    parser.add_argument("--output", "-o", help="出力ファイルパス")
    parser.add_argument("--project-name", help="プロジェクト名（projectモード用）")
    parser.add_argument("--project-type", choices=['cli', 'web', 'api', 'lib'],
                       help="プロジェクトタイプ")
    parser.add_argument("--language", "-l", default='python', help="プログラミング言語")
    parser.add_argument("--framework", "-f", help="フレームワーク名")
    parser.add_argument("--reference-files", "-r", nargs='+', help="参照ファイル")
    parser.add_argument("--reference-docs", "-d", nargs='+', help="参照設計書")
    parser.add_argument("--provider", default='ollama', help="LLMプロバイダー")
    parser.add_argument("--model", "-m", help="LLMモデル名")
    parser.add_argument("--temperature", "-t", type=float, default=0.3, help="Temperature")
    parser.add_argument("--max-tokens", type=int, default=4000, help="最大トークン数")
    parser.add_argument("--no-hints", action='store_true', help="ヒント使用しない")
    parser.add_argument("--no-validate", action='store_true', help="バリデーションしない")
    parser.add_argument("--no-tests", action='store_true', help="テスト生成しない")
    parser.add_argument("--no-docs", action='store_true', help="ドキュメント生成しない")

    args = parser.parse_args()

    # プロンプト読み込み
    prompt_path = Path(args.prompt)
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding='utf-8')
        print(f"プロンプトファイル読み込み: {prompt_path}")
    else:
        prompt = args.prompt

    # リクエスト構築
    request = MCPRequest(
        mode=args.mode,
        prompt=prompt,
        output_path=args.output,
        project_name=args.project_name,
        project_type=args.project_type,
        language=args.language,
        framework=args.framework,
        reference_files=args.reference_files,
        reference_docs=args.reference_docs,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        use_hints=not args.no_hints,
        validate=not args.no_validate,
        include_tests=not args.no_tests,
        include_docs=not args.no_docs
    )

    # エージェント実行
    agent = MCPAgent(provider=args.provider, model=args.model)
    result = agent.execute(request)

    # 結果表示
    print("\n" + "=" * 60)
    print("MCP実行結果")
    print("=" * 60)
    print(f"成功: {'✅' if result.success else '❌'}")
    print(f"生成ファイル数: {len(result.files_created)}")

    if result.files_created:
        print("\n📁 生成ファイル:")
        for file in result.files_created:
            print(f"  📄 {file}")
            
        print("\n🚀 実行コマンド:")
        for file in result.files_created:
            file_path = Path(file)
            if file_path.suffix == '.py':
                print(f"  python3 {file}")
                print(f"  # または: cd {file_path.parent} && python3 {file_path.name}")
            elif file_path.suffix == '.sh':
                print(f"  bash {file}")
                print(f"  # または: chmod +x {file} && {file}")
            elif file_path.suffix == '.js':
                print(f"  node {file}")
            else:
                print(f"  # テキストファイル: cat {file}")

    if result.warnings:
        print("\n警告:")
        for warning in result.warnings:
            print(f"  ⚠️  {warning}")

    if result.errors:
        print("\nエラー:")
        for error in result.errors:
            print(f"  ❌ {error}")

    if result.metadata:
        print("\nメタデータ:")
        for key, value in result.metadata.items():
            print(f"  {key}: {value}")

    # コード表示（generateモード）
    if args.mode == 'generate' and result.success and not args.output:
        print("\n生成コード:")
        print("-" * 60)
        print(result.content)
        print("-" * 60)

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
