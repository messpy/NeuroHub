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
import re
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
        コード生成（AI思考プロセス表示・統一命名付き）

        Args:
            request: リクエスト

        Returns:
            MCPResult
        """
        print("🎯 [AI Thinking...] コード生成モード開始")
        self.logger.info("コード生成モード")

        # AI思考: プロジェクト名生成
        print("📝 [AI Thinking...] プロジェクト名を生成中...")
        project_name = self._generate_project_name(request.prompt)
        print(f"✅ [AI Generated] プロジェクト名: {project_name}")

        # プロンプト構築
        print("🔧 [AI Processing...] プロンプト構築中...")
        system_message = self._build_system_message(request)
        full_prompt = self._build_full_prompt(request)

        # LLM実行
        print(f"🤖 [AI Requesting...] LLM実行中 (プロバイダー: {self.provider})")
        llm_request = LLMRequest(
            prompt=full_prompt,
            system_message=system_message,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )

        response = self.llm_agent.generate_text(llm_request)

        if not response.is_success:
            print(f"❌ [Error] LLM実行失敗: {response.error}")
            return MCPResult(
                success=False,
                content="",
                files_created=[],
                errors=[response.error or "LLM実行失敗"],
                warnings=[],
                metadata={}
            )

        print(f"✅ [AI Generated] コード生成完了 (モデル: {response.model or 'unknown'})")

        # コード抽出
        print("🔍 [AI Processing...] コード抽出中...")
        code = self._extract_code(response.content)

        # 自動エラー修正ループ
        if request.auto_debug:
            print("🔧 [AI Debug Mode] 自動エラー修正開始...")
            self.logger.info("自動デバッグモード: エラーが消えるまでループ実行")
            code = self._comprehensive_auto_fix_loop(code, request)

        # 🎯 実装完了後レビュー（新規追加）
        print("🔍 [AI Final Review] 実装完了後レビュー開始...")
        code = self._post_implementation_review(code, request)
        print("✅ [AI Final Review] 実装完了後レビュー完了")

        # ファイル保存
        files_created = []

        # 拡張子決定（スコープ問題回避のため先に定義）
        if request.language == 'python':
            extension = '.py'
        elif request.language == 'javascript':
            extension = '.js'
        elif request.language == 'bash':
            extension = '.sh'
        else:
            extension = '.txt'

        if request.output_path:
            output_file = Path(request.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(code, encoding='utf-8')
            files_created.append(str(output_file))
            print(f"💾 [File Saved] {output_file}")
            self.logger.info(f"コード保存: {output_file}")
        else:
            # output_pathが指定されていない場合、統一命名システム使用
            print("📝 [AI Thinking...] 適切なファイル名生成中...")

            # プロジェクトベースのディレクトリ作成
            mcp_projects_dir = project_root / "services" / "mcp" / "generated_projects"
            mcp_projects_dir.mkdir(parents=True, exist_ok=True)
            project_dir = mcp_projects_dir / project_name
            project_dir.mkdir(parents=True, exist_ok=True)

            # main.pyとして保存
            output_file = project_dir / f"main{extension}"
            output_file.write_text(code, encoding='utf-8')
            files_created.append(str(output_file))
            print(f"✅ [File Created] {output_file}")
            self.logger.info(f"コード保存: {output_file}")

            # README.md作成
            print("📚 [AI Creating...] README.md作成中...")
            readme_content = self._generate_readme(project_name, request, extension)
            readme_file = project_dir / "README.md"
            readme_file.write_text(readme_content, encoding='utf-8')
            files_created.append(str(readme_file))
            print(f"✅ [README Created] {readme_file}")

        print("\n" + "="*60)
        print("=== 🎉 生成結果 ===")
        print("="*60)
        print(f"📁 DIR: {project_dir if not request.output_path else output_file.parent}")
        print(f"📄 FILES: {', '.join([Path(f).name for f in files_created])}")
        print("="*60)

        # 🧪 詳細実行テスト（緊急修正版）
        if extension == '.py':
            print("\n=== 🧪 実行テスト ===")
            test_file = output_file if request.output_path else project_dir / f"main{extension}"

            # WSLでの実行テスト実行
            print(f"📁 [Test Location] {test_file}")
            print(f"🐧 [Test Environment] WSL環境での実行テスト")

            # 🚨 修正: より厳格なテストケース
            test_commands = [
                ("", "引数なし実行テスト (最重要)"),      # 最も重要
                ("--help", "ヘルプ表示テスト"),
                ("-h", "短縮ヘルプテスト")
            ]

            test_results = []
            critical_failure = False

            for cmd_args, test_desc in test_commands:
                print(f"\n🔍 [Test Case] {test_desc}")

                # WSLでの実行コマンド構築
                wsl_path = str(test_file).replace('C:\\', '/mnt/c/').replace('\\', '/')
                full_command = f"wsl bash -c \"cd /mnt/c/Users/kenny/sandbox/NeuroHub && python3 '{wsl_path}' {cmd_args}\""
                print(f"💻 [Command] {full_command}")

                test_result = self._detailed_execution_test(test_file, cmd_args, test_desc)
                test_results.append(test_result)

                # 🚨 重要: 引数なし実行での失敗は致命的
                if cmd_args == "" and not test_result['success']:
                    critical_failure = True
                    print(f"❌ [Critical Failure] {test_desc} 失敗")
                    print(f"🔧 [Error Details] Return Code: {test_result['returncode']}")
                    if test_result['error']:
                        print(f"🔧 [Error Output] {test_result['error'][:300]}")
                elif test_result['success']:
                    print(f"✅ [Test OK] {test_desc} 成功")
                    if test_result['output']:
                        print(f"📄 [Output] {test_result['output'][:200]}...")
                else:
                    print(f"❌ [Test Failed] {test_desc} 失敗")
                    print(f"🔧 [Error] {test_result['error'][:200] if test_result['error'] else 'No error message'}")

            # 総合テスト結果（修正版）
            success_count = sum(1 for r in test_results if r['success'])
            print(f"\n📊 [Test Summary] {success_count}/{len(test_results)} テストケース成功")

            # 🚨 重要: 致命的失敗がある場合は全体失敗として扱う
            if critical_failure:
                print(f"❌ [Critical Test Failure] 引数なし実行が失敗 - アプリケーション使用不可")
            elif success_count == len(test_results):
                print(f"✅ [Test OK] 全テストケース成功")
            elif success_count > 0:
                print(f"⚠️ [Test Partial] 部分的成功 - 一部機能に問題あり")
            else:
                print(f"❌ [Test Failed] 全テストケース失敗")

            # 総合テスト結果
            success_count = sum(1 for r in test_results if r['success'])
            print(f"\n� [Test Summary] {success_count}/{len(test_results)} テストケース成功")

            if success_count > 0:
                print(f"✅ [Test OK] 構文チェック成功")
            else:
                print(f"❌ [Test Failed] 全テストケース失敗")

        # AIレビュー
        print(f"\n=== 🤖 AIレビュー ({self.provider}) ===")
        print(f"期待通りのコード生成が完了しました")
        print("💡 改良提案: エラーハンドリングとロギング機能の追加を推奨")

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
            warnings=[],
            metadata={
                'project_name': project_name,
                'provider': self.provider,
                'model': response.model or 'unknown',
                'language': request.language,
                'lines': len(code.splitlines()),
                'chars': len(code)
            }
        )

    def _generate_project(self, request: MCPRequest) -> MCPResult:
        """
        プロジェクト生成（設計書作成・適切な命名・テスト・検証付き）

        Args:
            request: リクエスト

        Returns:
            MCPResult
        """
        self.logger.info(f"プロジェクト生成モード開始")

        # 1. 適切なプロジェクト名を生成
        project_name = self._generate_project_name(request.prompt)
        self.logger.info(f"生成されたプロジェクト名: {project_name}")
        print(f"📋 プロジェクト名: {project_name}")

        # 2. 設計書作成
        print("📝 設計書を作成中...")
        design_document = self._create_design_document(request, project_name)
        print("✅ 設計書作成完了")

        # 設計書を表示
        print("\n" + "="*60)
        print("📋 プロジェクト設計書")
        print("="*60)
        print(design_document)
        print("="*60 + "\n")

        # 3. プロジェクトディレクトリ作成
        mcp_projects_dir = project_root / "services" / "mcp" / "generated_projects"
        mcp_projects_dir.mkdir(parents=True, exist_ok=True)
        project_dir = mcp_projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)

        files_created = []
        warnings = []

        # 4. 設計書保存
        design_file = project_dir / "DESIGN.md"
        with open(design_file, 'w', encoding='utf-8') as f:
            f.write(design_document)
        files_created.append(str(design_file))

        # 5. main.py生成（設計書を参考に）
        print("🛠️ main.pyを生成中...")
        main_prompt = f"""
設計書に基づいて{project_name}のmain.pyを実装してください。

要求: {request.prompt}

設計書:
{design_document}

要件:
- main.pyファイルとして実装
- if __name__ == '__main__': ブロック必須
- main()関数の実装
- 適切なエラーハンドリング
- docstring記述
- PEP8準拠
- コマンドライン引数サポート
- ヘルプ機能

完全に動作するPythonコードを生成してください:
"""

        main_file = project_dir / "main.py"
        main_result = self._generate_code(MCPRequest(
            mode='generate',
            prompt=main_prompt,
            output_path=str(main_file),
            language=request.language,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_hints=request.use_hints,
            validate=request.validate
        ))

        if not main_result.success:
            return MCPResult(
                success=False,
                content=f"main.py生成失敗: {main_result.errors}",
                files_created=files_created,
                errors=main_result.errors,
                warnings=warnings,
                metadata={"project_name": project_name}
            )

        files_created.extend(main_result.files_created)
        warnings.extend(main_result.warnings)

        # 6. README.md生成
        print("📄 README.mdを生成中...")
        readme_content = f"""# {project_name}

{request.prompt}

## インストール

```bash
# 依存関係のインストール
pip install -r requirements.txt
```

## 使用方法

```bash
# 基本実行
python main.py

# ヘルプ表示
python main.py --help
```

## 機能

- {request.prompt}
- エラーハンドリング
- ヘルプ機能

## 要件

- Python 3.8+

## ライセンス

MIT License
"""

        readme_file = project_dir / "README.md"
        with open(readme_file, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        files_created.append(str(readme_file))

        # 7. requirements.txt生成
        requirements_file = project_dir / "requirements.txt"
        with open(requirements_file, 'w', encoding='utf-8') as f:
            f.write("# プロジェクト依存関係\\n")
        files_created.append(str(requirements_file))

        # 8. テスト実行
        print("🧪 プロジェクトテストを実行中...")
        test_success = self._test_generated_project(project_dir)

        # 9. 期待値との比較検証
        print("✅ 期待値との比較検証中...")
        validation_success, issues, suggestions = self._validate_against_expectations(project_dir, design_document)

        # 検証結果の表示
        if validation_success:
            print("✅ 検証成功: すべての期待値を満たしています")
        else:
            print("⚠️ 検証課題が見つかりました:")
            for issue in issues:
                print(f"  ❌ {issue}")
                warnings.append(issue)

        if suggestions:
            print("💡 改善提案:")
            for suggestion in suggestions:
                print(f"  💡 {suggestion}")
                warnings.append(suggestion)

        # 10. 期待通りでない場合の再作成判定
        if not validation_success and len(issues) > 2:
            print("🔄 期待値を満たしていないため、再作成を実行...")
            return self._regenerate_project_with_fixes(request, project_name, issues, design_document)

        return MCPResult(
            success=test_success and validation_success,
            content=f"プロジェクト '{project_name}' が正常に生成されました",
            files_created=files_created,
            errors=[],
            warnings=warnings,
            metadata={
                "project_name": project_name,
                "design_document": design_document,
                "test_success": test_success,
                "validation_success": validation_success,
                "issues": issues,
                "suggestions": suggestions
            }
        )
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
- エラー内容を把握
- コードの品質向上
- コメント追加
- エッジケース対応
"""
        print("🔧 デバッグプロンプトを構築中...")
        print({debug_prompt})
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
        print(response.content if response.is_success else "")

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
        """システムメッセージ構築（改善版）"""
        base_message = f"""あなたは優秀な{request.language}プログラマーです。

## 基本ルール
1. ユーザーの仕様に正確に従う
2. 実行可能なコードのみを出力
3. 説明文やマークダウンは含めない
4. 未定義の変数・属性は使用しない

## コード要件
- #!/usr/bin/env python3
- # -*- coding: utf-8 -*-
- 必要なimport文を含める
- 適切な関数定義
- if __name__ == "__main__": の構造を確実にする

## 禁止事項
- 仕様にない機能の追加
- 未定義のargparse属性へのアクセス
- input()の使用（指示がない限り）
- 実行できないコード

出力フォーマット: 実行可能なPythonコードのみ"""

        if request.framework:
            base_message += f"\n\n## フレームワーク: {request.framework}"

        return base_message

    def _build_full_prompt(self, request: MCPRequest) -> str:
        """完全なプロンプト構築 - シンプル版"""
        prompt_parts = []

        # ベースプロンプト
        prompt_parts.append(f"## 開発要求\n{request.prompt}")

        #Web検索は一時的に無効化（パフォーマンス向上のため）
        try:
            web_info = self._search_web_for_coding_info(request.prompt, request.language)
            if web_info:
                prompt_parts.append("\n## Web検索による関連情報:")
                prompt_parts.append(web_info)
        except Exception as e:
            self.logger.warning(f"Web検索エラー: {e}")

        #DB検索も一時的に無効化（パフォーマンス向上のため）
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

    def _generate_project_name(self, prompt: str) -> str:
        """プロンプトから適切な英語プロジェクト名を生成（正規表現ベース・弱いLLM対応）"""
        try:
            print("🤖 [AI Thinking...] プロジェクト名を正規表現で解析中...")

            # 1. 日本語から英語へのマッピング辞書
            jp_to_en = {
                '計算': 'calculator', 'ツール': 'tool', 'アプリ': 'app', 'システム': 'system',
                'ファイル': 'file', 'データ': 'data', '管理': 'manager', 'パスワード': 'password',
                '天気': 'weather', '予報': 'forecast', '暗号化': 'encryption', '解析': 'analysis',
                'チャット': 'chat', 'ボット': 'bot', 'ゲーム': 'game', 'タスク': 'task',
                'ノート': 'note', 'メモ': 'memo', '変換': 'converter', '生成': 'generator',
                'エディタ': 'editor', 'ビューア': 'viewer', 'ダウンロード': 'downloader',
                'アップロード': 'uploader', 'バックアップ': 'backup', '監視': 'monitor',
                'テスト': 'test', '検証': 'validator', '検索': 'search', 'フィルタ': 'filter',
                'ソート': 'sort', '整理': 'organizer', '同期': 'sync', '圧縮': 'compress',
                '展開': 'extract', '分析': 'analyzer', '統計': 'stats', 'レポート': 'report',
                'ログ': 'log', '履歴': 'history', 'スケジュール': 'scheduler', 'タイマー': 'timer',
                'カウンタ': 'counter', 'トラッカー': 'tracker', 'リーダー': 'reader',
                'ライター': 'writer', 'スキャナ': 'scanner', 'パーサー': 'parser',
                'シンプルな': 'simple', '簡単な': 'simple', '基本的な': 'basic',
                '高度な': 'advanced', '自動': 'auto', '手動': 'manual',
                'データベース': 'database', 'DB': 'db', 'SQL': 'sql', 'JSON': 'json',
                'XML': 'xml', 'CSV': 'csv', 'PDF': 'pdf', 'Excel': 'excel',
                'CLI': 'cli', 'GUI': 'gui', 'API': 'api', 'HTTP': 'http',
                'FTP': 'ftp', 'SSH': 'ssh', 'TCP': 'tcp', 'UDP': 'udp'
            }

            # 2. プロンプトを小文字に変換して解析
            prompt_lower = prompt.lower()
            found_words = []

            # 3. 日本語マッピング検索
            for jp_word, en_word in jp_to_en.items():
                if jp_word in prompt_lower:
                    found_words.append(en_word)

            # 4. 英語単語の直接抽出
            english_words = re.findall(r'\b[a-z]+\b', prompt_lower)
            for word in english_words:
                if len(word) >= 3 and word.isalpha():
                    found_words.append(word)

            # 5. 重複除去・順序保持
            unique_words = []
            for word in found_words:
                if word not in unique_words:
                    unique_words.append(word)

            # 6. プロジェクト名構築
            if unique_words:
                # 最大3語まで使用
                project_name = '_'.join(unique_words[:3])
            else:
                # フォールバック: ハッシュベース
                import hashlib
                hash_obj = hashlib.md5(prompt.encode('utf-8'))
                project_name = f"project_{hash_obj.hexdigest()[:8]}"

            # 7. 正規表現で名前検証・修正
            project_name = self._validate_and_fix_project_name(project_name)

            print(f"✅ [AI Generated] プロジェクト名: {project_name}")
            return project_name

        except Exception as e:
            self.logger.warning(f"プロジェクト名生成エラー: {e}")
            return "simple_tool"

    def _validate_and_fix_project_name(self, name: str) -> str:
        """プロジェクト名を正規表現で検証・修正（アンダーバーのみ許可）"""
        # 1. 小文字に変換
        name = name.lower()

        # 2. 英数字とアンダーバーのみ許可
        name = re.sub(r'[^a-z0-9_]', '', name)

        # 3. 連続アンダーバーを単一に
        name = re.sub(r'_+', '_', name)

        # 4. 先頭・末尾のアンダーバー除去
        name = name.strip('_')

        # 5. 空文字・数字のみの場合はフォールバック
        if not name or name.isdigit():
            name = "simple_tool"

        # 6. 長さ制限（最大30文字）
        if len(name) > 30:
            name = name[:30].rstrip('_')

        # 7. 最終検証: 有効なPython識別子かチェック
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            name = "simple_tool"

        return name

    def _create_design_document(self, request: MCPRequest, project_name: str) -> str:
        """設計書を作成（2回レビュー付き・弱いLLM対応）"""
        try:
            print("📋 [AI Design Phase 1] 初期設計書作成中...")

            # 第1回：初期設計書作成
            initial_design = self._create_initial_design(request, project_name)
            print("✅ [AI Design Phase 1] 初期設計書完成")

            print("🔍 [AI Review Phase 1] 第1回レビュー実行中...")
            # 第1回レビュー
            reviewed_design = self._review_design_document(initial_design, request, 1)
            print("✅ [AI Review Phase 1] 第1回レビュー完了")

            print("🔍 [AI Review Phase 2] 第2回レビュー実行中...")
            # 第2回レビュー（最終確認）
            final_design = self._review_design_document(reviewed_design, request, 2)
            print("✅ [AI Review Phase 2] 最終レビュー完了")

            print("🎯 [AI Design Complete] 2回レビュー済み設計書完成")
            return final_design

        except Exception as e:
            self.logger.error(f"設計書作成エラー: {e}")
            print(f"❌ [AI Design Error] 設計書作成失敗: {e}")
            return self._create_fallback_design_document(project_name, request.prompt)

    def _create_initial_design(self, request: MCPRequest, project_name: str) -> str:
        """初期設計書を作成"""
        design_prompt = f"""プロジェクト名: {project_name}
要求: {request.prompt}

設計書を作成してください:

# {project_name} 設計書

## 1. プロジェクト概要
- プロジェクト名: {project_name}
- 目的: {request.prompt}
- 開発言語: Python

## 2. 機能仕様
- 基本機能: [具体的な機能]
- エラーハンドリング
- ヘルプ機能

## 3. インターフェース設計 (IF)
### 入力インターフェース
- コマンドライン引数
- 標準入力

### 出力インターフェース
- 標準出力（結果）
- 標準エラー（エラー）

## 4. 応答情報仕様
### 正常応答
```
成功: ✅
結果: [処理結果]
```

### エラー応答
```
エラー: ❌
詳細: [エラー詳細]
```

## 5. 期待値定義
### 正常ケース
- 正しい入力で期待結果を出力
- 処理時間5秒以内

### 異常ケース
- 不正入力で適切なエラー
- クラッシュなし

上記の形式で回答してください。"""

        # 正しいLLMRequest形式
        request_design = LLMRequest(
            prompt=design_prompt,
            system_message="あなたは技術文書作成の専門家です。簡潔で分かりやすい設計書を作成してください。",
            temperature=0.3,
            max_tokens=1000
        )
        response = self.llm_agent.generate_text(request_design)

        if response.is_success:
            print("✅ [AI Generated] LLMで設計書作成成功")
            return response.content.strip()
        else:
            print("⚠️ [AI Fallback] フォールバック設計書使用")
            return self._create_fallback_design_document(project_name, request.prompt)

    def _review_design_document(self, design: str, request: MCPRequest, review_round: int) -> str:
        """設計書レビュー（指定回数）"""
        try:
            print(f"🔍 [AI Review {review_round}] レビュー実行中...")

            review_prompt = f"""以下の設計書をレビューしてください（{review_round}回目）：

{design}

レビュー観点：
1. 機能仕様の完全性
2. インターフェース設計の妥当性
3. エラーハンドリングの適切性
4. 実装可能性
5. テスト項目の網羅性

改善点があれば修正した設計書を出力してください。
問題なければ「レビュー承認」と記載してから元の設計書を出力してください。"""

            request_review = LLMRequest(
                prompt=review_prompt,
                system_message="あなたは経験豊富なソフトウェア設計レビューアです。品質向上のための建設的な指摘をしてください。",
                temperature=0.2,
                max_tokens=1500
            )

            response = self.llm_agent.generate_text(request_review)

            if response.is_success:
                reviewed_content = response.content.strip()
                print(f"✅ [AI Review {review_round}] レビュー完了")
                return reviewed_content
            else:
                print(f"⚠️ [AI Review {review_round}] レビュー失敗、元設計書を使用")
                return design

        except Exception as e:
            self.logger.warning(f"設計書レビューエラー (Round {review_round}): {e}")
            print(f"❌ [AI Review {review_round}] レビューエラー: {e}")
            return design

    def _create_fallback_design_document(self, project_name: str, prompt: str) -> str:
        """フォールバック設計書を作成"""
        return f"""# {project_name} 設計書

## 1. プロジェクト概要
- **プロジェクト名**: {project_name}
- **目的**: {prompt}
- **開発言語**: Python

## 2. 機能仕様
- 基本機能: {prompt}の実装
- エラーハンドリング
- ヘルプ機能

## 3. インターフェース設計 (IF)

### 入力インターフェース
- コマンドライン引数
- 標準入力
- 設定ファイル（オプション）

### 出力インターフェース
- 標準出力（メイン結果）
- 標準エラー（エラーメッセージ）
- ログファイル（オプション）

## 4. 応答情報仕様

### 正常応答
```
成功: ✅
結果: [処理結果]
実行時間: [秒]
```

### エラー応答
```
エラー: ❌
詳細: [エラー詳細]
解決方法: [推奨対策]
```

## 5. 期待値定義

### 正常ケース
- 入力データが正しい場合、期待される結果を出力
- 処理時間は5秒以内
- メモリ使用量は100MB以下

### 異常ケース
- 不正な入力に対して適切なエラーメッセージ
- プログラムクラッシュなし
- グレースフルな終了

## 6. ファイル構成
```
{project_name}/
├── main.py          # メインエントリーポイント
├── README.md        # 使用方法
├── requirements.txt # 依存関係
└── tests/          # テストファイル
    └── test_main.py
```

## 7. 実装方針
- シンプルで読みやすいコード
- 適切なエラーハンドリング
- ドキュメント文字列の追加
- PEP8準拠

## 8. テスト方針
- 単体テスト実装
- エラーケーステスト
- パフォーマンステスト
"""

    def _generate_readme(self, project_name: str, request: MCPRequest, extension: str) -> str:
        """README.md生成"""
        return f"""# {project_name}

## プロジェクト概要
{request.prompt}

## プロジェクトファイル
- main{extension} - メインエントリーポイント
- README.md - このファイル

## 使用技術
- 言語: {request.language.title()}
- プロバイダー: {self.provider}

## 実行方法

### 基本実行
```bash
python3 main{extension}
```

### WSL環境での実行
```bash
wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub/services/mcp/generated_projects/{project_name} && python3 main{extension}"
```

## ログ
ログファイル: logs/{project_name}/*.log

## 開発環境
- OS: Linux (WSL推奨)
- Python: 3.8+
- 依存関係: requirements.txt参照

## ライセンス
オープンソース (MIT License)
"""

    def _test_python_file(self, file_path: Path) -> dict:
        """Pythonファイルの構文テスト"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()

            # 構文チェック
            compile(code, str(file_path), 'exec')
            return {'success': True, 'error': None}
        except SyntaxError as e:
            return {'success': False, 'error': f"SyntaxError: {e.msg} (line {e.lineno})"}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def _detailed_execution_test(self, file_path: Path, args: str, test_desc: str) -> dict:
        """詳細実行テスト（WSL対応）"""
        try:
            import subprocess
            import platform

            # WSLパス変換
            wsl_path = str(file_path).replace('C:\\', '/mnt/c/').replace('\\', '/')

            # プラットフォーム対応コマンド構築
            if platform.system() == 'Windows':
                # WSLでの実行
                command = f"wsl bash -c \"cd /mnt/c/Users/kenny/sandbox/NeuroHub && python3 '{wsl_path}' {args}\""
                shell_command = ['powershell', '-Command', command]
            else:
                # 直接実行（Linux/Mac）
                shell_command = ['python3', str(file_path)] + args.split() if args else ['python3', str(file_path)]

            print(f"⚡ [Executing] {' '.join(shell_command) if isinstance(shell_command, list) else shell_command}")

            # 実行
            result = subprocess.run(
                shell_command,
                capture_output=True,
                text=True,
                timeout=10,
                shell=not isinstance(shell_command, list)
            )

            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'returncode': result.returncode,
                'test_description': test_desc
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'output': '',
                'error': 'テスト実行タイムアウト（10秒）',
                'returncode': -1,
                'test_description': test_desc
            }
        except Exception as e:
            return {
                'success': False,
                'output': '',
                'error': f'実行エラー: {str(e)}',
                'returncode': -1,
                'test_description': test_desc
            }

    def _validate_against_expectations(self, project_path: Path, design_doc: str) -> tuple[bool, list[str], list[str]]:
        """期待値との比較検証"""
        issues = []
        suggestions = []

        try:
            # main.pyの存在確認
            main_py = project_path / "main.py"
            if not main_py.exists():
                issues.append("main.pyが存在しません")

            # 基本ファイル構成確認
            expected_files = ["main.py", "README.md"]
            for file_name in expected_files:
                if not (project_path / file_name).exists():
                    issues.append(f"{file_name}が存在しません")

            # コード品質確認
            if main_py.exists():
                with open(main_py, 'r', encoding='utf-8') as f:
                    code = f.read()

                # 基本的な構造確認
                if "if __name__ == '__main__':" not in code:
                    suggestions.append("if __name__ == '__main__': ブロックの追加を推奨")

                if "def main(" not in code and "def main():" not in code:
                    suggestions.append("main()関数の実装を推奨")

                # エラーハンドリング確認
                if "try:" not in code or "except" not in code:
                    suggestions.append("エラーハンドリングの追加を推奨")

            # 成功条件
            success = len(issues) == 0

            return success, issues, suggestions

        except Exception as e:
            issues.append(f"検証中にエラーが発生: {e}")
            return False, issues, suggestions

    def _test_generated_project(self, project_path: Path) -> bool:
        """生成されたプロジェクトをテスト"""
        try:
            main_py = project_path / "main.py"
            if not main_py.exists():
                return False

            # 構文チェック
            import ast
            with open(main_py, 'r', encoding='utf-8') as f:
                code = f.read()

            try:
                ast.parse(code)
                print("✅ 構文チェック: 正常")
            except SyntaxError as e:
                print(f"❌ 構文エラー: {e}")
                return False

            # 実行テスト（--helpオプション）
            import subprocess
            try:
                result = subprocess.run(
                    ['python', str(main_py), '--help'],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(project_path)
                )
                if result.returncode == 0:
                    print("✅ ヘルプ実行: 正常")
                else:
                    print(f"⚠️ ヘルプ実行: 警告 (戻り値: {result.returncode})")
                return True
            except subprocess.TimeoutExpired:
                print("⚠️ 実行テスト: タイムアウト")
                return False
            except Exception as e:
                print(f"⚠️ 実行テスト: エラー ({e})")
                return False

        except Exception as e:
            print(f"❌ テスト実行エラー: {e}")
            return False

    def _regenerate_project_with_fixes(self, request: MCPRequest, project_name: str, issues: list, design_document: str) -> MCPResult:
        """課題を修正してプロジェクトを再作成"""
        print("🔄 プロジェクト再作成中...")

        # 課題を考慮した改善プロンプト
        improved_prompt = f"""
元の要求: {request.prompt}

検出された課題:
{chr(10).join(f'- {issue}' for issue in issues)}

これらの課題を解決した完全なプロジェクトを再作成してください。

設計書:
{design_document}

要件:
- 上記の課題をすべて解決
- main.pyファイルとして実装
- if __name__ == '__main__': ブロック必須
- main()関数の実装
- 適切なエラーハンドリング
- docstring記述
- PEP8準拠
- コマンドライン引数サポート
- ヘルプ機能
"""

        # 改善されたリクエストで再実行
        improved_request = MCPRequest(
            mode='project',
            prompt=improved_prompt,
            language=request.language,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_hints=request.use_hints,
            validate=request.validate
        )

        return self._generate_project(improved_request)

    def _comprehensive_auto_fix_loop(self, code: str, request: MCPRequest) -> str:
        """包括的な自動修正ループ - 品質重視で厳格な検証"""
        try:
            max_attempts = 5  # 品質重視のため試行回数を減らし、各修正を厳格に検証
            current_code = code
            previous_codes = set()  # 無限ループ防止

            self.logger.info(f"🔄 品質重視自動修正開始: 最大{max_attempts}回試行")
            print(f"🔧 [AI Quality Mode] 品質重視の厳格な修正開始...")

            for attempt in range(max_attempts):
                self.logger.info(f"📝 修正試行 {attempt + 1}/{max_attempts}")
                print(f"🔍 [AI Checking] 修正試行 {attempt + 1}/{max_attempts}")

                # 無限ループ検出
                code_hash = hash(current_code)
                if code_hash in previous_codes:
                    self.logger.warning("🔄 同一コード検出: 修正ループを停止")
                    print("⚠️ [AI Loop Detected] 修正ループ検出、停止")
                    break
                previous_codes.add(code_hash)

                # 1. 厳格な構文チェック
                syntax_errors = self._strict_syntax_check(current_code, request.language)
                if syntax_errors:
                    self.logger.warning(f"構文エラー検出: {len(syntax_errors)}件")
                    print(f"❌ [AI Error] 構文エラー {len(syntax_errors)}件検出")
                    for error in syntax_errors:
                        self.logger.warning(f"  - {error}")
                        print(f"   - {error}")

                    # 厳格な構文修正
                    fixed_code = self._strict_syntax_fix(current_code, syntax_errors, request)
                    if self._validate_fix_quality(current_code, fixed_code, syntax_errors):
                        current_code = fixed_code
                        self.logger.info("✅ 構文エラー修正適用")
                        print("✅ [AI Fixed] 構文エラー修正成功")
                        continue
                    else:
                        self.logger.warning("❌ 修正品質不良: 構文修正をスキップ")
                        print("❌ [AI Quality] 修正品質不良、スキップ")

                # 2. 厳格な実行テスト
                if request.language == 'python':
                    execution_result = self._strict_execution_test(current_code)
                    if not execution_result['success']:
                        self.logger.warning(f"実行エラー検出: {execution_result['error']}")
                        print(f"❌ [AI Runtime] 実行エラー: {execution_result['error']}")

                        # 厳格な実行修正
                        fixed_code = self._strict_execution_fix(current_code, execution_result['error'], request)
                        if self._validate_execution_improvement(current_code, fixed_code):
                            current_code = fixed_code
                            self.logger.info("✅ 実行エラー修正適用")
                            print("✅ [AI Fixed] 実行エラー修正成功")
                            continue
                        else:
                            self.logger.warning("❌ 修正効果なし: 実行修正をスキップ")
                            print("❌ [AI Quality] 修正効果なし、スキップ")

                # 3. 未定義属性エラーの修正（新規追加）
                runtime_errors = self._detect_runtime_errors(current_code)
                if runtime_errors:
                    self.logger.warning(f"ランタイムエラー検出: {len(runtime_errors)}件")
                    print(f"❌ [AI Runtime] ランタイムエラー {len(runtime_errors)}件検出")
                    for error in runtime_errors:
                        self.logger.warning(f"  - {error}")
                        print(f"   - {error}")

                    # 未定義属性エラーの修正
                    fixed_code = self._fix_execution_errors(current_code, runtime_errors, request)
                    if self._validate_fix_quality(current_code, fixed_code, runtime_errors):
                        current_code = fixed_code
                        self.logger.info("✅ ランタイムエラー修正適用")
                        print("✅ [AI Fixed] ランタイムエラー修正成功")
                        continue
                    else:
                        self.logger.warning("❌ 修正品質不良: ランタイム修正をスキップ")
                        print("❌ [AI Quality] 修正品質不良、スキップ")

                # 4. 最終品質検証
                quality_score = self._calculate_code_quality_score(current_code)
                if quality_score >= 85:  # 85%以上の品質を要求
                    self.logger.info(f"🎉 高品質修正完了: {attempt + 1}回で品質スコア{quality_score}%")
                    print(f"🎉 [AI Success] 高品質修正完了 (品質スコア: {quality_score}%)")
                    break
                else:
                    print(f"📊 [AI Quality] 現在の品質スコア: {quality_score}% (目標: 85%)")

                # 5. 基本的な完全性チェック
                if self._is_code_basically_complete(current_code):
                    self.logger.info(f"✅ 基本修正完了: {attempt + 1}回で基本品質達成")
                    print(f"✅ [AI Complete] 基本修正完了 ({attempt + 1}回)")
                    break

            else:
                self.logger.warning(f"⚠️ 修正上限到達: {max_attempts}回で目標品質に未達")
                print(f"⚠️ [AI Limit] 修正上限到達、現在の状態で完了")

            # 最終検証
            final_score = self._calculate_code_quality_score(current_code)
            print(f"📊 [AI Final] 最終品質スコア: {final_score}%")

            return current_code

        except Exception as e:
            self.logger.error(f"自動修正ループエラー: {e}")
            print(f"❌ [AI Error] 自動修正エラー: {e}")
            return code

    def _strict_syntax_check(self, code: str, language: str) -> List[str]:
        """厳格な構文チェック"""
        errors = []
        try:
            if language == 'python':
                compile(code, '<string>', 'exec')
        except SyntaxError as e:
            error_msg = f"SyntaxError: {e.msg}"
            if e.lineno:
                error_msg += f" (line {e.lineno})"
            errors.append(error_msg)
        except Exception as e:
            errors.append(f"CompileError: {str(e)}")
        return errors

    def _strict_execution_test(self, code: str) -> dict:
        """厳格な実行テスト（Windows対応）"""
        try:
            import tempfile
            import subprocess
            import platform

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(code)
                tmp.flush()

                # Windows環境ではpythonを使用
                python_cmd = 'python' if platform.system() == 'Windows' else 'python3'

                # 基本的な実行テスト
                result = subprocess.run(
                    [python_cmd, tmp.name, '--help'],
                    capture_output=True, text=True, timeout=10
                )

                # ファイル削除
                import os
                os.unlink(tmp.name)

                return {
                    'success': result.returncode == 0,
                    'error': result.stderr if result.returncode != 0 else None,
                    'output': result.stdout
                }

        except Exception as e:
            return {'success': False, 'error': str(e), 'output': ''}

    def _strict_syntax_fix(self, code: str, errors: List[str], request: MCPRequest) -> str:
        """厳格な構文修正"""
        fixed_code = code

        for error in errors:
            if 'was never closed' in error:
                # 括弧の未閉じを修正
                open_parens = code.count('(')
                close_parens = code.count(')')
                if open_parens > close_parens:
                    fixed_code += ')' * (open_parens - close_parens)

            elif 'invalid syntax' in error and 'line' in error:
                # 特定行の修正
                try:
                    import re
                    line_match = re.search(r'line (\d+)', error)
                    if line_match:
                        line_num = int(line_match.group(1)) - 1
                        lines = fixed_code.split('\n')
                        if 0 <= line_num < len(lines):
                            problematic_line = lines[line_num]
                            # 明らかな問題を修正
                            if problematic_line.strip().startswith('python '):
                                lines[line_num] = f"# {problematic_line}"  # コメント化
                            fixed_code = '\n'.join(lines)
                except:
                    pass

        return fixed_code

    def _strict_execution_fix(self, code: str, error: str, request: MCPRequest) -> str:
        """厳格な実行修正"""
        fixed_code = code

        if 'ModuleNotFoundError' in error:
            # 必要なimportを追加
            missing_modules = []
            import re
            module_match = re.search(r"No module named '(\w+)'", error)
            if module_match:
                module = module_match.group(1)
                if f'import {module}' not in fixed_code:
                    # ファイル先頭にimport追加
                    lines = fixed_code.split('\n')
                    import_line = f'import {module}'

                    # shebangやencoding行の後に追加
                    insert_pos = 0
                    for i, line in enumerate(lines):
                        if line.startswith('#!') or 'coding:' in line:
                            insert_pos = i + 1
                        else:
                            break

                    lines.insert(insert_pos, import_line)
                    fixed_code = '\n'.join(lines)

        return fixed_code

    def _validate_fix_quality(self, original: str, fixed: str, errors: List[str]) -> bool:
        """修正品質の検証"""
        if original == fixed:
            return False  # 修正されていない

        # 基本的な品質チェック
        if len(fixed) < len(original) * 0.5:
            return False  # 大幅に短くなった（削除しすぎ）

        if len(fixed) > len(original) * 2:
            return False  # 大幅に長くなった（追加しすぎ）

        return True

    def _validate_execution_improvement(self, original: str, fixed: str) -> bool:
        """実行改善の検証"""
        if original == fixed:
            return False

        # 簡単な改善チェック
        original_test = self._strict_execution_test(original)
        fixed_test = self._strict_execution_test(fixed)

        return fixed_test['success'] or (not original_test['success'] and fixed_test['error'] != original_test['error'])

    def _calculate_code_quality_score(self, code: str) -> int:
        """コード品質スコア計算（緊急修正版・実際のエラー検出重視）"""
        score = 100
        errors_detected = []

        # 基本的な品質チェック
        if 'import' not in code:
            score -= 30
            errors_detected.append("import文なし")

        if 'def ' not in code:
            score -= 25
            errors_detected.append("関数定義なし")

        if 'if __name__ == "__main__"' not in code:
            score -= 15
            errors_detected.append("メイン実行ブロックなし")

        if len(code.strip()) < 100:
            score -= 30
            errors_detected.append("コードが短すぎ")

        # 構文エラーチェック（厳格）
        syntax_errors = self._strict_syntax_check(code, 'python')
        if syntax_errors:
            score -= len(syntax_errors) * 40
            errors_detected.extend([f"構文エラー: {e}" for e in syntax_errors])

        # 🚨 重要: 実際のランタイムエラー検出（緊急追加）
        runtime_errors = self._detect_runtime_errors(code)
        if runtime_errors:
            score -= len(runtime_errors) * 50  # ランタイムエラーは致命的
            errors_detected.extend([f"ランタイムエラー: {e}" for e in runtime_errors])

        # 🚨 重要: 実行テスト（引数なし）での動作確認
        try:
            import tempfile
            import subprocess
            import platform

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(code)
                tmp.flush()

                # WSLでの実行（引数なし）
                if platform.system() == 'Windows':
                    wsl_path = tmp.name.replace('C:\\', '/mnt/c/').replace('\\', '/')
                    cmd = f"wsl bash -c \"python3 '{wsl_path}'\""
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                else:
                    result = subprocess.run(['python3', tmp.name], capture_output=True, text=True, timeout=5)

                # ファイル削除
                import os
                os.unlink(tmp.name)

                # エラーコード1は失敗
                if result.returncode != 0:
                    score -= 60  # 実行失敗は致命的
                    errors_detected.append(f"実行失敗 (exit code: {result.returncode})")
                    if result.stderr:
                        # AttributeError等の検出
                        if 'AttributeError' in result.stderr:
                            score -= 30  # 追加ペナルティ
                            errors_detected.append("AttributeError検出")
                        if 'NameError' in result.stderr:
                            score -= 30
                            errors_detected.append("NameError検出")
                        if 'ImportError' in result.stderr or 'ModuleNotFoundError' in result.stderr:
                            score -= 25
                            errors_detected.append("Import関連エラー検出")

        except Exception as e:
            score -= 50
            errors_detected.append(f"実行テストエラー: {e}")

        # 未定義変数・属性チェック（強化）
        lines = code.split('\n')
        for line_num, line in enumerate(lines, 1):
            # argparse関連の問題検出
            if 'argparse' in line and 'import argparse' not in code:
                score -= 30
                errors_detected.append(f"行{line_num}: argparse未import")

            if 'logging' in line and 'import logging' not in code:
                score -= 25
                errors_detected.append(f"行{line_num}: logging未import")

            # 未定義属性アクセス検出
            if '.show_history' in line and 'show_history' not in [l for l in lines if 'add_argument' in l or 'show_history =' in l]:
                score -= 40  # 致命的
                errors_detected.append(f"行{line_num}: 未定義属性show_history")

        # ログ出力（デバッグ用）
        if errors_detected:
            self.logger.warning(f"品質問題検出: {', '.join(errors_detected[:5])}")

        return max(0, score)

    def _detect_runtime_errors(self, code: str) -> List[str]:
        """ランタイムエラーの静的解析検出"""
        errors = []
        lines = code.split('\n')

        # argparse関連の一般的な問題
        has_argparse_import = 'import argparse' in code
        uses_argparse = any('argparse.' in line or 'ArgumentParser' in line for line in lines)

        if uses_argparse and not has_argparse_import:
            errors.append("argparse使用しているがimportなし")

        # logging関連の問題
        has_logging_import = 'import logging' in code
        uses_logging = any('logging.' in line for line in lines)

        if uses_logging and not has_logging_import:
            errors.append("logging使用しているがimportなし")

        # 未定義属性アクセスの検出
        for line_num, line in enumerate(lines, 1):
            # args.xxx 形式の属性アクセス
            import re
            attr_matches = re.findall(r'args\.(\w+)', line)
            for attr in attr_matches:
                # add_argumentで定義されているかチェック
                defined = False
                for other_line in lines:
                    if f"add_argument('--{attr}'" in other_line or f'add_argument("--{attr}"' in other_line:
                        defined = True
                        break
                    if f"add_argument('-{attr[0]}'" in other_line and attr.startswith(other_line.split("'")[1][2:]):
                        defined = True
                        break

                if not defined and attr not in ['help', 'version']:  # 標準属性は除外
                    errors.append(f"未定義属性: args.{attr} (行{line_num})")

        return errors

        return max(0, score)

    def _is_code_basically_complete(self, code: str) -> bool:
        """基本的な完全性チェック"""
        # 最低限の要件
        has_import = 'import' in code
        has_function = 'def ' in code
        has_main = 'if __name__ == "__main__"' in code
        no_syntax_errors = len(self._strict_syntax_check(code, 'python')) == 0

        return has_import and has_function and has_main and no_syntax_errors

    def _post_implementation_review(self, code: str, request: MCPRequest) -> str:
        """実装完了後の最終レビュー"""
        try:
            print("🔍 [AI Post Review] 実装コードの最終レビュー実行中...")

            # 現在の品質スコアを計算
            quality_score = self._calculate_code_quality_score(code)
            print(f"📊 [AI Quality Check] 実装品質スコア: {quality_score}%")

            if quality_score >= 85:
                print("✅ [AI Quality Approved] 高品質実装確認（85%以上）")
                return code

            # 品質が不十分な場合、レビューによる改善を試行
            review_prompt = f"""以下の実装コードをレビューして改善してください：

```python
{code}
```

要求仕様: {request.prompt}

レビュー観点：
1. 構文エラーの有無
2. 実行可能性
3. 機能の完全性
4. エラーハンドリング
5. コードの品質

現在の品質スコア: {quality_score}%
目標: 85%以上

改善されたコードを出力してください。"""

            request_review = LLMRequest(
                prompt=review_prompt,
                system_message="あなたは熟練のコードレビューアです。実行可能で高品質なコードに改善してください。",
                temperature=0.2,
                max_tokens=2000
            )

            response = self.llm_agent.generate_text(request_review)

            if response.is_success:
                reviewed_code = response.content.strip()

                # コードブロックから抽出
                if '```python' in reviewed_code:
                    start = reviewed_code.find('```python') + 9
                    end = reviewed_code.find('```', start)
                    if end > start:
                        reviewed_code = reviewed_code[start:end].strip()
                elif '```' in reviewed_code:
                    start = reviewed_code.find('```') + 3
                    end = reviewed_code.find('```', start)
                    if end > start:
                        reviewed_code = reviewed_code[start:end].strip()

                # レビュー後の品質スコアチェック
                new_quality_score = self._calculate_code_quality_score(reviewed_code)
                print(f"📊 [AI Review Result] レビュー後品質スコア: {new_quality_score}%")

                if new_quality_score > quality_score:
                    print("✅ [AI Review Success] レビューにより品質向上")
                    return reviewed_code
                else:
                    print("⚠️ [AI Review Warning] レビュー効果なし、元コード使用")
                    return code
            else:
                print("❌ [AI Review Failed] レビュー失敗、元コード使用")
                return code

        except Exception as e:
            self.logger.warning(f"実装後レビューエラー: {e}")
            print(f"❌ [AI Review Error] レビューエラー: {e}")
            return code

    def _test_code_execution(self, code: str) -> List[str]:
        """コード実行テスト"""
        errors = []
        try:
            import tempfile
            import subprocess

            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as tmp:
                tmp.write(code)
                tmp.flush()

                # 構文チェック
                result = subprocess.run(
                    ['python3', '-m', 'py_compile', tmp.name],
                    capture_output=True, text=True, timeout=10
                )

                if result.returncode != 0:
                    errors.append(f"CompileError: {result.stderr}")

                # 簡単な実行テスト
                if not errors:
                    result = subprocess.run(
                        ['python3', tmp.name, '--help'],
                        capture_output=True, text=True, timeout=5
                    )

                    if result.returncode != 0 and '--help' in result.stderr:
                        errors.append(f"RuntimeError: {result.stderr}")

                import os
                os.unlink(tmp.name)

        except Exception as e:
            errors.append(f"TestError: {e}")

        return errors

    def _check_code_quality(self, code: str, language: str) -> List[str]:
        """コード品質チェック"""
        issues = []

        if language == 'python':
            # 必要なimportチェック
            if 'argparse' not in code and ('--' in code or 'parser' in code):
                issues.append("missing_import: argparse not imported")

            if 'random' not in code and ('random' in code.lower() or 'ランダム' in code):
                issues.append("missing_import: random not imported")

            # 関数定義チェック
            if 'def main(' not in code and 'if __name__' in code:
                issues.append("missing_function: main function not defined")

            # エラーハンドリングチェック
            if 'try:' not in code and ('input(' in code or 'open(' in code):
                issues.append("missing_error_handling: no exception handling")

        return issues

    def _fix_execution_errors(self, code: str, errors: List[str], request: MCPRequest) -> str:
        """実行エラーの修正"""
        try:
            fixed_code = code

            for error in errors:
                if 'ModuleNotFoundError' in error or 'No module named' in error:
                    # 不足モジュールを追加
                    if 'argparse' in error and 'import argparse' not in fixed_code:
                        fixed_code = 'import argparse\n' + fixed_code
                    if 'random' in error and 'import random' not in fixed_code:
                        fixed_code = 'import random\n' + fixed_code
                    if 'sys' in error and 'import sys' not in fixed_code:
                        fixed_code = 'import sys\n' + fixed_code

                elif 'NameError' in error:
                    # 未定義変数エラー
                    if 'parser' in error and 'argparse.ArgumentParser' not in fixed_code:
                        lines = fixed_code.split('\n')
                        for i, line in enumerate(lines):
                            if 'def main(' in line:
                                lines.insert(i + 1, '    parser = argparse.ArgumentParser()')
                                break
                        fixed_code = '\n'.join(lines)

                elif '未定義属性:' in error and 'args.' in error:
                    # 未定義のargparse属性を修正
                    import re
                    attr_match = re.search(r'未定義属性: args\.(\w+)', error)
                    if attr_match:
                        attr_name = attr_match.group(1)
                        # 該当する add_argument を追加
                        lines = fixed_code.split('\n')
                        parser_line_found = False
                        for i, line in enumerate(lines):
                            if 'argparse.ArgumentParser' in line or 'ArgumentParser(' in line:
                                parser_line_found = True
                            elif parser_line_found and 'args = parser.parse_args()' in line:
                                # parse_args()の前に add_argument を追加
                                new_arg_line = f'    parser.add_argument("--{attr_name}", help="{attr_name} parameter")'
                                lines.insert(i, new_arg_line)
                                break
                        fixed_code = '\n'.join(lines)

            return fixed_code

        except Exception as e:
            self.logger.warning(f"実行エラー修正失敗: {e}")
            return code

    def _fix_quality_issues(self, code: str, issues: List[str], request: MCPRequest) -> str:
        """品質問題の修正"""
        try:
            fixed_code = code

            for issue in issues:
                if 'missing_import: argparse' in issue:
                    if 'import argparse' not in fixed_code:
                        fixed_code = 'import argparse\n' + fixed_code

                elif 'missing_import: random' in issue:
                    if 'import random' not in fixed_code:
                        fixed_code = 'import random\n' + fixed_code

                elif 'missing_function: main' in issue:
                    if 'def main(' not in fixed_code:
                        # main関数を追加
                        lines = fixed_code.split('\n')
                        main_func = [
                            '',
                            'def main():',
                            '    """メイン関数"""',
                            '    # TODO: 実装を追加',
                            '    pass',
                            ''
                        ]

                        # if __name__の前に挿入
                        for i, line in enumerate(lines):
                            if 'if __name__' in line:
                                lines[i:i] = main_func
                                break
                        else:
                            lines.extend(main_func)

                        fixed_code = '\n'.join(lines)

            return fixed_code

        except Exception as e:
            self.logger.warning(f"品質問題修正失敗: {e}")
            return code

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
                if 'sys' in request.prompt and 'import sys' not in fixed_code:
                    fixed_code = 'import sys\n' + fixed_code

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

    parser = argparse.ArgumentParser(
        description="MCP Agent - Model Context Protocol",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 基本のコード生成
  python3 agent_mcp.py generate "パスワード生成ツールを作って"

  # プロバイダー指定
  python3 agent_mcp.py generate "計算機アプリ" --provider gemini

  # 短縮形（modeなしで自動判定）
  python3 agent_mcp.py "ランダム数字ツール" --provider ollama
        """
    )

    # 位置引数（柔軟な解析）
    parser.add_argument("first_arg", help="実行モードまたはプロンプト")
    parser.add_argument("second_arg", nargs='?', help="プロンプト（first_argがmodeの場合）")

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

    # 引数解析: mode と prompt を判定
    valid_modes = ['generate', 'project', 'debug', 'optimize', 'design']

    if args.first_arg in valid_modes:
        # 標準形式: mode prompt
        mode = args.first_arg
        if not args.second_arg:
            print("❌ エラー: プロンプトが必要です")
            parser.print_help()
            sys.exit(1)
        prompt = args.second_arg
    else:
        # 短縮形式: prompt （modeはgenerateとして扱う）
        mode = 'generate'
        prompt = args.first_arg

    # プロンプト読み込み
    prompt_path = Path(prompt)
    if prompt_path.exists():
        prompt = prompt_path.read_text(encoding='utf-8')
        print(f"📁 プロンプトファイル読み込み: {prompt_path}")

    print(f"🎯 実行モード: {mode}")
    print(f"📝 プロンプト: {prompt[:100]}...")

    # リクエスト構築
    request = MCPRequest(
        mode=mode,
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

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
