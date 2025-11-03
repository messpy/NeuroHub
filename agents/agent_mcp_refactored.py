#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MCP (Model Context Protocol) Agent - Refactored Version

MCPサービスを統合管理し、プロンプトからコード生成・プロジェクト作成を行うエージェント。
弱いLLMでもエラーなしで動作することを目指す。

主要機能:
- プロジェクト生成（仕様書→実装）
- コード生成（プロンプト→コード）
- デバッグサポート
- プロンプト最適化
- 設計書参照生成

アーキテクチャ:
- コア実行機能
- プロンプト処理機能
- プロジェクト生成機能
- コード品質・デバッグ機能
- ヘルパー・ユーティリティ機能
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


# ============================================================================
# データクラス定義
# ============================================================================

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


# ============================================================================
# メインクラス
# ============================================================================

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

    # ========================================================================
    # コア実行機能
    # ========================================================================

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
        """コード生成（AI思考プロセス表示・統一命名付き）"""
        print("🎯 [AI Thinking...] コード生成モード開始")
        self.logger.info("コード生成モード")

        # プロジェクト名生成
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

        # 実装完了後レビュー
        print("🔍 [AI Final Review] 実装完了後レビュー開始...")
        code = self._post_implementation_review(code, request)
        print("✅ [AI Final Review] 実装完了後レビュー完了")

        # ファイル保存
        files_created = self._save_generated_code(code, request, project_name)

        # README生成
        readme_content = self._generate_readme(project_name, request, '.py')
        readme_path = self._save_readme(project_name, readme_content)
        files_created.append(readme_path)

        # 実行テストとAIレビュー
        self._execute_final_tests_and_review(files_created)

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
        """プロジェクト生成"""
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

        # プロジェクトディレクトリ作成
        project_dir = self._create_project_directory(request.project_name)
        files_created = []
        warnings = []

        try:
            # 設計書作成
            design_document = self._create_design_document(request, request.project_name)

            # メインコード生成
            main_result = self._generate_main_code(request, design_document)
            main_file = project_dir / f"main.py"
            main_file.write_text(main_result.content, encoding='utf-8')
            files_created.append(str(main_file))

            # テスト生成
            if request.include_tests:
                test_content = self._generate_test_code(main_result.content, request)
                test_file = project_dir / f"test_{request.project_name}.py"
                test_file.write_text(test_content, encoding='utf-8')
                files_created.append(str(test_file))

            # README生成
            if request.include_docs:
                readme_content = self._generate_readme(request.project_name, request, '.py')
                readme_file = project_dir / "README.md"
                readme_file.write_text(readme_content, encoding='utf-8')
                files_created.append(str(readme_file))

            # requirements.txt生成
            requirements_content = self._extract_requirements(main_result.content)
            requirements_file = project_dir / "requirements.txt"
            requirements_file.write_text(requirements_content, encoding='utf-8')
            files_created.append(str(requirements_file))

            # プロジェクトテスト
            test_success = self._test_generated_project(project_dir)

            # 期待値との比較検証
            validation_success, issues, suggestions = self._validate_against_expectations(project_dir, design_document)

            if not validation_success and len(issues) > 2:
                return self._regenerate_project_with_fixes(request, request.project_name, issues, design_document)

            return MCPResult(
                success=test_success and validation_success,
                content=f"プロジェクト '{request.project_name}' が正常に生成されました",
                files_created=files_created,
                errors=[],
                warnings=warnings,
                metadata={
                    "project_name": request.project_name,
                    "design_document": design_document,
                    "test_success": test_success,
                    "validation_success": validation_success,
                    "issues": issues,
                    "suggestions": suggestions
                }
            )

        except Exception as e:
            self.logger.error(f"プロジェクト生成エラー: {e}", exc_info=True)
            return MCPResult(
                success=False,
                content="",
                files_created=files_created,
                errors=[str(e)],
                warnings=warnings,
                metadata={}
            )

    def _debug_code(self, request: MCPRequest) -> MCPResult:
        """デバッグサポート"""
        # 実装省略 - 元のコードから移植
        pass

    def _optimize_prompt(self, request: MCPRequest) -> MCPResult:
        """プロンプト最適化"""
        # 実装省略 - 元のコードから移植
        pass

    def _generate_from_design(self, request: MCPRequest) -> MCPResult:
        """設計書参照生成"""
        # 実装省略 - 元のコードから移植
        pass

    # ========================================================================
    # プロンプト処理機能
    # ========================================================================

    def _build_system_message(self, request: MCPRequest) -> str:
        """システムメッセージ構築"""
        return f"""あなたは優秀な{request.language}プログラマーです。

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
- if __name__ == "__main__": の構造

## 禁止事項
- 仕様にない機能の追加
- 未定義のargparse属性へのアクセス
- input()の使用（指示がない限り）
- 実行できないコード

出力フォーマット: 実行可能なPythonコードのみ"""

    def _build_full_prompt(self, request: MCPRequest) -> str:
        """完全なプロンプト構築"""
        prompt_parts = []
        prompt_parts.append(f"## 開発要求\n{request.prompt}")

        # ヒント追加
        if request.use_hints:
            hints = self._get_relevant_hints(request)
            if hints:
                prompt_parts.append("\n## 開発ヒント:")
                for hint in hints[:3]:
                    prompt_parts.append(f"- {hint['title']}: {hint['description']}")

        return "\n".join(prompt_parts)

    # ========================================================================
    # プロジェクト生成機能
    # ========================================================================

    def _create_project_directory(self, project_name: str) -> Path:
        """プロジェクトディレクトリ作成"""
        mcp_projects_dir = project_root / "services" / "mcp" / "generated_projects"
        mcp_projects_dir.mkdir(parents=True, exist_ok=True)
        project_dir = mcp_projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def _generate_project_name(self, prompt: str) -> str:
        """プロジェクト名生成"""
        print("🤖 [AI Thinking...] プロジェクト名を正規表現で解析中...")

        # 基本的な正規化
        name = re.sub(r'[^\w\s]', '', prompt.lower())
        name = re.sub(r'\s+', '_', name.strip())
        name = name[:50]  # 長さ制限

        if not name:
            name = f"project_{hash(prompt) % 10000:04d}"

        return self._validate_and_fix_project_name(name)

    def _validate_and_fix_project_name(self, name: str) -> str:
        """プロジェクト名検証・修正"""
        # 予約語チェック
        python_keywords = ['and', 'as', 'assert', 'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except', 'exec', 'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is', 'lambda', 'not', 'or', 'pass', 'print', 'raise', 'return', 'try', 'while', 'with', 'yield']

        if name in python_keywords:
            name = f"{name}_app"

        # 数字から始まる場合の修正
        if name and name[0].isdigit():
            name = f"app_{name}"

        # 空の場合のデフォルト
        if not name:
            name = "default_project"

        return name

    # ========================================================================
    # コード品質・デバッグ機能
    # ========================================================================

    def _comprehensive_auto_fix_loop(self, code: str, request: MCPRequest) -> str:
        """包括的な自動修正ループ"""
        try:
            max_attempts = 5
            current_code = code
            previous_codes = set()

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

                # 構文チェック
                syntax_errors = self._strict_syntax_check(current_code, request.language)
                if syntax_errors:
                    fixed_code = self._strict_syntax_fix(current_code, syntax_errors, request)
                    if self._validate_fix_quality(current_code, fixed_code, syntax_errors):
                        current_code = fixed_code
                        continue

                # 実行テスト
                if request.language == 'python':
                    execution_result = self._strict_execution_test(current_code)
                    if not execution_result['success']:
                        fixed_code = self._strict_execution_fix(current_code, execution_result['error'], request)
                        if self._validate_execution_improvement(current_code, fixed_code):
                            current_code = fixed_code
                            continue

                # 未定義属性エラーの修正
                runtime_errors = self._detect_runtime_errors(current_code)
                if runtime_errors:
                    fixed_code = self._fix_execution_errors(current_code, runtime_errors, request)
                    if self._validate_fix_quality(current_code, fixed_code, runtime_errors):
                        current_code = fixed_code
                        continue

                # 品質検証
                quality_score = self._calculate_code_quality_score(current_code)
                if quality_score >= 85:
                    self.logger.info(f"🎉 高品質修正完了: {attempt + 1}回で品質スコア{quality_score}%")
                    print(f"🎉 [AI Success] 高品質修正完了 (品質スコア: {quality_score}%)")
                    break
                else:
                    print(f"📊 [AI Quality] 現在の品質スコア: {quality_score}% (目標: 85%)")

                # 基本的な完全性チェック
                if self._is_code_basically_complete(current_code):
                    self.logger.info(f"✅ 基本修正完了: {attempt + 1}回で基本品質達成")
                    print(f"✅ [AI Complete] 基本修正完了 ({attempt + 1}回)")
                    break

            final_score = self._calculate_code_quality_score(current_code)
            print(f"📊 [AI Final] 最終品質スコア: {final_score}%")
            return current_code

        except Exception as e:
            self.logger.error(f"自動修正エラー: {e}", exc_info=True)
            return code

    def _detect_runtime_errors(self, code: str) -> List[str]:
        """ランタイムエラーの静的解析検出"""
        errors = []
        lines = code.split('\n')

        # 未定義属性アクセスの検出
        for line_num, line in enumerate(lines, 1):
            # args.xxx 形式の属性アクセス
            attr_matches = re.findall(r'args\.(\w+)', line)
            for attr in attr_matches:
                # add_argumentで定義されているかチェック
                defined = False
                for other_line in lines:
                    if f"add_argument('--{attr}'" in other_line or f'add_argument("--{attr}"' in other_line:
                        defined = True
                        break
                    if f"add_argument('-{attr[0]}'" in other_line and len(attr) > 0:
                        defined = True
                        break

                if not defined and attr not in ['help', 'version']:
                    errors.append(f"未定義属性: args.{attr} (行{line_num})")

        return errors

    def _fix_execution_errors(self, code: str, errors: List[str], request: MCPRequest) -> str:
        """実行エラーの修正"""
        try:
            fixed_code = code

            for error in errors:
                if '未定義属性:' in error and 'args.' in error:
                    # 未定義のargparse属性を修正
                    attr_match = re.search(r'未定義属性: args\.(\w+)', error)
                    if attr_match:
                        attr_name = attr_match.group(1)
                        # 該当する add_argument を追加
                        lines = fixed_code.split('\n')
                        for i, line in enumerate(lines):
                            if 'args = parser.parse_args()' in line:
                                # parse_args()の前に add_argument を追加
                                new_arg_line = f'    parser.add_argument("--{attr_name}", help="{attr_name} parameter")'
                                lines.insert(i, new_arg_line)
                                break
                        fixed_code = '\n'.join(lines)

            return fixed_code

        except Exception as e:
            self.logger.warning(f"実行エラー修正失敗: {e}")
            return code

    # ========================================================================
    # ヘルパー・ユーティリティ機能
    # ========================================================================

    def _extract_code(self, text: str) -> str:
        """LLM出力からコード抽出"""
        # コードフェンス検出
        code_fence_pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(code_fence_pattern, text, re.DOTALL)

        if matches:
            # 最も長いコードブロックを選択
            return max(matches, key=len).strip()

        return text.strip()

    def _save_generated_code(self, code: str, request: MCPRequest, project_name: str) -> List[str]:
        """生成されたコードを保存"""
        files_created = []

        # 拡張子決定
        extension = '.py' if request.language == 'python' else '.txt'

        if request.output_path:
            output_file = Path(request.output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text(code, encoding='utf-8')
            files_created.append(str(output_file))
        else:
            # プロジェクトベースのディレクトリ作成
            project_dir = self._create_project_directory(project_name)
            output_file = project_dir / f"main{extension}"
            output_file.write_text(code, encoding='utf-8')
            files_created.append(str(output_file))

        print(f"✅ [File Created] {files_created[-1]}")
        self.logger.info(f"コード保存: {files_created[-1]}")

        return files_created

    def _save_readme(self, project_name: str, readme_content: str) -> str:
        """README保存"""
        project_dir = self._create_project_directory(project_name)
        readme_file = project_dir / "README.md"
        readme_file.write_text(readme_content, encoding='utf-8')
        print(f"✅ [README Created] {readme_file}")
        return str(readme_file)

    def _execute_final_tests_and_review(self, files_created: List[str]):
        """最終テストとレビューの実行"""
        print("\n" + "=" * 60)
        print("=== 🎉 生成結果 ===")
        print("=" * 60)

        # 実行テスト
        for file_path in files_created:
            if file_path.endswith('.py'):
                self._test_python_file(Path(file_path))
                break

    # これ以降は、元のコードから必要な関数を順次移植していく
    # 簡潔さのため、この例では主要な構造のみを示している

    # ========================================================================
    # 省略された関数群（元のコードから移植する必要あり）
    # ========================================================================

    def _strict_syntax_check(self, code: str, language: str) -> List[str]:
        """構文チェック（省略 - 元のコードから移植）"""
        pass

    def _strict_execution_test(self, code: str) -> dict:
        """実行テスト（省略 - 元のコードから移植）"""
        pass

    def _calculate_code_quality_score(self, code: str) -> int:
        """品質スコア計算（省略 - 元のコードから移植）"""
        pass

    # 他の必要な関数も同様に移植...


# ============================================================================
# CLI インターフェース
# ============================================================================

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
    parser.add_argument("--project-type", choices=['cli', 'web', 'api', 'lib'], help="プロジェクトタイプ")
    parser.add_argument("--language", "-l", default='python', help="プログラミング言語")
    parser.add_argument("--framework", "-f", help="フレームワーク名")
    parser.add_argument("--provider", default='ollama', help="LLMプロバイダー")
    parser.add_argument("--model", "-m", help="LLMモデル名")
    parser.add_argument("--temperature", "-t", type=float, default=0.3, help="Temperature")
    parser.add_argument("--max-tokens", type=int, default=4000, help="最大トークン数")

    args = parser.parse_args()

    # 引数解析: mode と prompt を判定
    valid_modes = ['generate', 'project', 'debug', 'optimize', 'design']

    if args.first_arg in valid_modes:
        mode = args.first_arg
        if not args.second_arg:
            print("❌ エラー: プロンプトが必要です")
            parser.print_help()
            sys.exit(1)
        prompt = args.second_arg
    else:
        mode = 'generate'
        prompt = args.first_arg

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
        temperature=args.temperature,
        max_tokens=args.max_tokens
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

    if result.errors:
        print("\nエラー:")
        for error in result.errors:
            print(f"  ❌ {error}")

    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()
