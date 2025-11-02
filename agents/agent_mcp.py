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
    auto_debug: bool = False

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

        # ファイル保存
        files_created = []
        if request.output_path:
            output_file = Path(request.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(code, encoding='utf-8')
            files_created.append(str(output_file))
            self.logger.info(f"コード保存: {output_file}")

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
        base_message = f"あなたは優秀な{request.language}プログラマーです。"

        if request.framework:
            base_message += f"\n{request.framework}フレームワークの専門家です。"

        base_message += """

コード生成時の要件:
- 高品質で保守可能なコード
- 適切なエラーハンドリング
- 型ヒント使用（Python）
- docstring完備
- PEP 8準拠（Python）
- テスト可能な設計
"""

        return base_message

    def _build_full_prompt(self, request: MCPRequest) -> str:
        """完全なプロンプト構築"""
        prompt_parts = []

        # ベースプロンプト
        prompt_parts.append(request.prompt)

        # ヒント追加
        if request.use_hints:
            hints = self._get_relevant_hints(request)
            if hints:
                prompt_parts.append("\n## 参考ヒント:")
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

        return "\n".join(prompt_parts)

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
        print("\n生成ファイル:")
        for file in result.files_created:
            print(f"  - {file}")

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
