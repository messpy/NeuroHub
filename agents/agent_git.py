#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Git Agent - Git操作専用エージェント
コミットメッセージ生成とGit基本操作のみを提供
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# プロジェクトパスを追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.ai.llm_common import (
    load_env_from_config,
    load_config,
    get_prompt_template,
    get_system_message,
    auto_log_llm_request
)
from services.ai.provider_ollama import OllamaConfig
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
    """Git操作専用エージェント - シンプルで高速"""

    def __init__(self, config_path: str = None):
        super().__init__("git_agent")

        self.project_root = project_root
        self.config = load_config()
        self.history_manager = LLMHistoryManager()

        load_env_from_config()

        # LLMエージェント初期化
        from agents.agent_llm import LLMAgent
        self.llm_agent = LLMAgent()

        self.providers = {
            'ollama': OllamaConfig()
        }

        self.session_id = self.history_manager.start_session("git_agent")

    def execute(self, prompt: str) -> str:
        """Git操作実行"""
        prompt_lower = prompt.lower()

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

        elif 'commit' in prompt_lower or 'コミット' in prompt_lower:
            try:
                message = self.generate_commit_message()
                if message:
                    return f"📝 Generated commit message:\n\n{message}\n\nℹ️ Use: python agents/agent_git.py --auto-commit"
                else:
                    return "⚠️ No changes to commit"
            except Exception as e:
                self.handle_error(e, "Commit message generation")
                return f"❌ Error: {e}"

        else:
            status = self.get_git_status()
            return f"Git status: {status.total_files} files changed"

    def get_git_status(self) -> GitStatus:
        """Git状態取得"""

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
        """ファイル差分取得"""
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
        """ファイルステージング"""
        try:
            if not Path(self.project_root / file_path).exists():
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
        """AIコミットメッセージ生成"""

        if mode == "detailed":
            prompt = get_prompt_template("git_commit", "detailed_prompt")
        else:
            prompt = get_prompt_template("git_commit", "base_prompt")

        if len(diff_content) > 2000:
            lines = diff_content.split('\n')
            added_lines = len([l for l in lines if l.startswith('+')])
            removed_lines = len([l for l in lines if l.startswith('-')])

            diff_summary = f"Large diff: +{added_lines} -{removed_lines} lines\n"
            diff_summary += '\n'.join(lines[:20])
            diff_content = diff_summary

        full_prompt = f"{prompt}\n\n==== 対象ファイル ====\n{file_path}\n\n==== 差分 ====\n{diff_content}"

        from agents.agent_llm import LLMRequest

        request = LLMRequest(
            prompt=full_prompt,
            system_message=get_system_message("commit_message_generator"),
            max_tokens=200,
            temperature=0.3
        )

        try:
            response = self.llm_agent.generate_text(request)

            if response.is_success and response.content:
                message = response.content.strip()
                if message.startswith(':') and len(message) <= 120:
                    return message

        except Exception as e:
            print(f"LLM生成エラー: {e}")

        return self._generate_smart_default(file_path, diff_content)

    def _generate_smart_default(self, file_path: str, diff_content: str) -> str:
        """スマートデフォルトメッセージ"""
        filename = Path(file_path).name

        lines = diff_content.split('\n')
        added_lines = len([l for l in lines if l.startswith('+')])
        removed_lines = len([l for l in lines if l.startswith('-')])

        if added_lines > removed_lines * 2:
            prefix = ":add:"
        elif removed_lines > added_lines * 2:
            prefix = ":fix:"
        else:
            prefix = ":update:"

        if filename.endswith('.py'):
            return f"{prefix} {filename} Python機能更新"
        elif filename.endswith('.yaml') or filename.endswith('.yml'):
            return f":config: {filename} 設定更新"
        elif filename.endswith('.md'):
            return f":docs: {filename} ドキュメント更新"
        else:
            return f"{prefix} {filename} 更新"

    def commit_file(self, file_path: str, message: str) -> bool:
        """ファイルコミット"""
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
        """ファイル処理とコミット"""

        status = self.get_git_status()
        if status.total_files == 0:
            return {"status": "no_changes", "message": "変更ファイルがありません"}

        results = []

        for file_path in status.modified + status.untracked:
            if file_path not in status.staged:
                self.stage_file(file_path)

        updated_status = self.get_git_status()
        for file_path in updated_status.staged:
            diff_content = self.get_file_diff(file_path, staged=True)
            if not diff_content:
                continue

            message = self.generate_commit_message(file_path, diff_content)

            file_result = {
                "file": file_path,
                "message": message,
                "diff_lines": len(diff_content.split('\n')),
                "committed": False
            }

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


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(description="Git Agent - コミット支援")
    parser.add_argument("--auto", action="store_true", help="自動コミット")
    parser.add_argument("--status", action="store_true", help="Git状態表示")

    args = parser.parse_args()

    agent = GitAgent()

    if args.status:
        status = agent.get_git_status()
        print(f"Git状態: {status.total_files}ファイル変更")
        print(f"  Staged: {len(status.staged)}")
        print(f"  Modified: {len(status.modified)}")
        print(f"  Untracked: {len(status.untracked)}")

    else:
        status = agent.get_git_status()
        print(f"Git状態: {status.total_files}ファイル変更")
        print(f"  Staged: {len(status.staged)}")
        print(f"  Modified: {len(status.modified)}")
        print(f"  Untracked: {len(status.untracked)}")

        if status.total_files > 0:
            print("\n詳細: python agents/agent_git.py --status")


if __name__ == "__main__":
    main()
