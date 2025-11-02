#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Agent - Pythonで実装されたGitコミット支援エージェント
tools/git_commit_aiのPython版
"""

import os
import sys
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.llm.llm_common import (
    load_env_from_config,
    load_config,
    get_prompt_template,
    get_system_message,
    auto_log_llm_request
)
from services.llm.provider_gemini import GeminiConfig
from services.llm.provider_huggingface import HuggingFaceConfig
from services.llm.provider_ollama import OllamaConfig
from services.db.llm_history_manager import LLMHistoryManager
from agents.common import BaseAgent


@dataclass
class GitStatus:
    """Git状態情報"""
    staged: List[str]
    modified: List[str]
    untracked: List[str]
    deleted: List[str]
    total_files: int


class GitAgent(BaseAgent):
    """Git操作を支援するPythonエージェント"""

    def __init__(self, config_path: str = None):
        # BaseAgent初期化
        super().__init__("git_agent")
        
        self.project_root = project_root
        self.config = load_config()
        self.history_manager = LLMHistoryManager()

        # 環境設定読み込み
        load_env_from_config()

        # LLMエージェント初期化
        from agents.llm_agent import LLMAgent
        self.llm_agent = LLMAgent()

        # LLMプロバイダー初期化
        self.providers = {
            'gemini': GeminiConfig(),
            'huggingface': HuggingFaceConfig(),
            'ollama': OllamaConfig()
        }

        # セッション開始
        self.session_id = self.history_manager.start_session("git_agent")

    def execute(self, prompt: str) -> str:
        """Execute git operation based on prompt.
        
        Args:
            prompt: User prompt (e.g., "git status確認", "コミットして")
            
        Returns:
            Result message
        """
        prompt_lower = prompt.lower()
        
        # Git status
        if 'status' in prompt_lower or '状態' in prompt_lower:
            status = self.get_git_status()
            result = f"📊 Git状態: {status.total_files}ファイル変更\n"
            result += f"  ✅ Staged: {len(status.staged)}\n"
            result += f"  📝 Modified: {len(status.modified)}\n"
            result += f"  ❓ Untracked: {len(status.untracked)}\n"
            
            if status.staged:
                result += f"\nStaged files:\n"
                for f in status.staged[:5]:
                    result += f"  - {f}\n"
                if len(status.staged) > 5:
                    result += f"  ... and {len(status.staged) - 5} more\n"
            
            return result
        
        # Generate commit message
        elif 'commit' in prompt_lower or 'コミット' in prompt_lower:
            try:
                message = self.generate_commit_message()
                if message:
                    return f"📝 Generated commit message:\n\n{message}\n\nℹ️ Use: python agents/git_agent.py --auto-commit"
                else:
                    return "⚠️ No changes to commit"
            except Exception as e:
                self.handle_error(e, "Commit message generation")
                return f"❌ Error: {e}"
        
        # Default: show status
        else:
            status = self.get_git_status()
            return f"Git status: {status.total_files} files changed"

    def get_git_status(self) -> GitStatus:
        """Git状態を取得"""

        def run_git(cmd: str) -> List[str]:
            try:
                result = subprocess.run(
                    f"git {cmd}",
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.project_root,
                    encoding='utf-8',
                    errors='replace'
                )
                if result.returncode == 0:
                    return [line.strip() for line in result.stdout.split('\n') if line.strip()]
                return []
            except Exception:
                return []

        staged = run_git("diff --cached --name-only")
        modified = run_git("diff --name-only")
        untracked = run_git("ls-files --others --exclude-standard")
        deleted = run_git("diff --name-only --diff-filter=D")

        all_files = list(set(staged + modified + untracked + deleted))

        return GitStatus(
            staged=staged,
            modified=modified,
            untracked=untracked,
            deleted=deleted,
            total_files=len(all_files)
        )

    def get_file_diff(self, file_path: str, staged: bool = True) -> str:
        """ファイルの差分を取得"""
        try:
            cmd = "git diff --cached" if staged else "git diff"
            result = subprocess.run(
                f"{cmd} -- {file_path}",
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                encoding='utf-8',
                errors='replace'
            )
            return result.stdout if result.returncode == 0 else ""
        except Exception:
            return ""

    def stage_file(self, file_path: str) -> bool:
        """ファイルをステージング"""
        try:
            if not Path(self.project_root / file_path).exists():
                # 削除されたファイル
                cmd = f"git rm {file_path}"
            else:
                cmd = f"git add {file_path}"

            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                encoding='utf-8',
                errors='replace'
            )
            return result.returncode == 0
        except Exception:
            return False

    @auto_log_llm_request
    def generate_commit_message(self,
                              file_path: str,
                              diff_content: str,
                              mode: str = "normal") -> str:
        """AIでコミットメッセージを生成"""

        # プロンプトテンプレート取得
        if mode == "detailed":
            prompt = get_prompt_template("git_commit", "detailed_prompt")
        else:
            prompt = get_prompt_template("git_commit", "base_prompt")

        # 差分が大きい場合は要約
        if len(diff_content) > 2000:
            lines = diff_content.split('\n')
            added_lines = len([l for l in lines if l.startswith('+')])
            removed_lines = len([l for l in lines if l.startswith('-')])

            diff_summary = f"Large diff: +{added_lines} -{removed_lines} lines\n"
            diff_summary += '\n'.join(lines[:20])
            diff_content = diff_summary

        full_prompt = f"{prompt}\n\n==== 対象ファイル ====\n{file_path}\n\n==== 差分 ====\n{diff_content}"

        # LLMリクエスト作成
        from agents.llm_agent import LLMRequest

        request = LLMRequest(
            prompt=full_prompt,
            system_message=get_system_message("commit_message_generator"),
            max_tokens=200,
            temperature=0.3
        )

        try:
            # LLMエージェントで生成
            response = self.llm_agent.generate_text(request)

            if response.is_success and response.content:
                # フォーマット検証
                message = response.content.strip()
                if message.startswith(':') and len(message) <= 120:
                    return message

        except Exception as e:
            print(f"LLM生成エラー: {e}")

        # 失敗した場合はスマートデフォルト
        return self._generate_smart_default(file_path, diff_content)

    def _generate_smart_default(self, file_path: str, diff_content: str) -> str:
        """スマートデフォルトメッセージ生成"""
        filename = Path(file_path).name

        # 変更量で判定
        lines = diff_content.split('\n')
        added_lines = len([l for l in lines if l.startswith('+')])
        removed_lines = len([l for l in lines if l.startswith('-')])

        if added_lines > removed_lines * 2:
            prefix = ":add:"
        elif removed_lines > added_lines * 2:
            prefix = ":fix:"
        else:
            prefix = ":update:"

        # ファイル種別判定
        if filename.endswith('.py'):
            return f"{prefix} {filename} Python機能更新"
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            return f":config: {filename} 設定更新"
        elif filename.endswith('.md'):
            return f":docs: {filename} ドキュメント更新"
        else:
            return f"{prefix} {filename} 更新"

    def commit_file(self, file_path: str, message: str) -> bool:
        """ファイルをコミット"""
        try:
            result = subprocess.run(
                f'git commit -m "{message}"',
                shell=True,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                encoding='utf-8',
                errors='replace'
            )
            return result.returncode == 0
        except Exception:
            return False

    def process_files(self, auto_commit: bool = False) -> Dict[str, Any]:
        """ファイルを処理してコミットメッセージを生成"""

        status = self.get_git_status()
        if status.total_files == 0:
            return {"status": "no_changes", "message": "変更ファイルがありません"}

        results = []

        # ステージングされていないファイルをステージング
        for file_path in status.modified + status.untracked:
            if file_path not in status.staged:
                self.stage_file(file_path)

        # ステージされたファイルを処理
        updated_status = self.get_git_status()
        for file_path in updated_status.staged:
            diff_content = self.get_file_diff(file_path, staged=True)
            if not diff_content:
                continue

            # コミットメッセージ生成
            message = self.generate_commit_message(file_path, diff_content)

            file_result = {
                "file": file_path,
                "message": message,
                "diff_lines": len(diff_content.split('\n')),
                "committed": False
            }

            # 自動コミット
            if auto_commit:
                if self.commit_file(file_path, message):
                    file_result["committed"] = True

            results.append(file_result)

        return {
            "status": "success",
            "total_files": len(results),
            "results": results,
            "session_id": self.session_id
        }

    def interactive_mode(self):
        """対話モード"""
        print("🤖 Git Agent - 対話モード")
        print("コマンド: status, process, commit <file>, quit")

        while True:
            try:
                command = input("\n> ").strip()

                if command == "quit":
                    break
                elif command == "status":
                    status = self.get_git_status()
                    print(f"📁 変更ファイル: {status.total_files}件")
                    print(f"   Staged: {len(status.staged)}")
                    print(f"   Modified: {len(status.modified)}")
                    print(f"   Untracked: {len(status.untracked)}")

                elif command == "process":
                    results = self.process_files(auto_commit=False)
                    print(f"✅ 処理完了: {results['total_files']}ファイル")
                    for result in results['results']:
                        print(f"   {result['file']}: {result['message']}")

                elif command.startswith("commit"):
                    parts = command.split()
                    if len(parts) > 1:
                        file_path = parts[1]
                        diff_content = self.get_file_diff(file_path)
                        if diff_content:
                            message = self.generate_commit_message(file_path, diff_content)
                            print(f"💬 生成メッセージ: {message}")

                            confirm = input("コミットしますか？ [y/N]: ")
                            if confirm.lower() == 'y':
                                if self.commit_file(file_path, message):
                                    print("✅ コミット完了")
                                else:
                                    print("❌ コミット失敗")
                        else:
                            print("❌ 差分が見つかりません")
                    else:
                        print("使用法: commit <file_path>")

                else:
                    print("未知のコマンド。使用可能: status, process, commit <file>, quit")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"エラー: {e}")

        # セッション終了
        self.history_manager.end_session(self.session_id)
        print("👋 Git Agent 終了")


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Git Agent - Python版コミット支援")
    parser.add_argument("--auto", action="store_true", help="自動コミットモード")
    parser.add_argument("--interactive", action="store_true", help="対話モード")
    parser.add_argument("--status", action="store_true", help="Git状態表示")

    args = parser.parse_args()

    agent = GitAgent()

    if args.status:
        status = agent.get_git_status()
        print(f"Git状態: {status.total_files}ファイル変更")
        print(f"  Staged: {len(status.staged)}")
        print(f"  Modified: {len(status.modified)}")
        print(f"  Untracked: {len(status.untracked)}")

    elif args.interactive:
        agent.interactive_mode()

    else:
        # デフォルト: Git状態表示
        status = agent.get_git_status()
        print(f"Git状態: {status.total_files}ファイル変更")
        print(f"  Staged: {len(status.staged)}")
        print(f"  Modified: {len(status.modified)}")
        print(f"  Untracked: {len(status.untracked)}")

        if status.total_files > 0:
            print("\n詳細な処理には --interactive オプションを使用してください")


if __name__ == "__main__":
    main()
