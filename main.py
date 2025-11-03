#!/usr/bin/env python3
"""NeuroHub Main Entry Point

This is the central entry point for NeuroHub.
It analyzes user intent and routes to appropriate agents:
- Weather query → weather_agent
- Web search → web_agent
- Development task → mcp_agent
- Git operation → git_agent
- System command → command_agent
- Configuration → config_agent
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

# ログ設定
def setup_logging(debug: bool = False):
    """ログ設定を初期化"""
    log_level = logging.DEBUG if debug else logging.INFO

    # ログディレクトリ作成
    log_dir = PROJECT_ROOT / "logs"
    log_dir.mkdir(exist_ok=True)

    # ログファイル名
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"neurohub_{timestamp}.log"

    # ログフォーマット
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # ファイルハンドラー
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))

    # ルートロガー設定
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return logging.getLogger('neurohub')


class IntentDetector:
    """Detect user intent from natural language input."""

    def __init__(self):
        """Initialize intent detector with keyword patterns."""
        self.patterns = {
            'weather': [
                '天気', '気温', '降水', '予報',"今日の" 'weather', 'temperature', 'forecast',
                '晴れ', '雨', '雪', '曇り', 'sunny', 'rain', 'snow'
            ],
            'web': [
                '最新', 'ニュース', 'news', 'リアルタイム', '現在の', '今の状況',
                'トレンド', 'trend', 'URL', 'リンク', 'サイト教えて', 'ウェブサイト'
            ],
            'mcp': [
                '開発', '作成', 'プログラム', 'コード', 'develop', 'code', 'create',
                'プロジェクト', 'project', 'アプリ', 'app', 'cli', 'ツール', 'tool',
                '実装', 'implement', 'ファイル作成', 'make file,作って'
            ],
            'git': [
                'git', 'commit', 'push', 'pull', 'branch', 'コミット',
                'プッシュ', 'プル', 'ブランチ', 'status', 'diff', 'log'
            ],
            'command': [
                'コマンド', 'command', '実行', 'execute', 'run', 'ls', 'cd',
                'mkdir', 'rmdir', 'cat', 'echo', 'pwd', 'find', 'grep',
                'discord', 'Discord', 'チャンネル', 'channel', 'メッセージ', 'message',
                '送信', 'send', '送って', 'post'
            ],
            'config': [
                '設定', 'config', 'configuration', '環境', 'environment',
                'api key', 'token', 'パラメータ', 'paramter',"何ができる"
            ]
        }

    def detect(self, text: str) -> str:
        """Detect intent from user input.

        Args:
            text: User input text

        Returns:
            Agent name (weather/web/mcp/git/command/config/unknown)
        """
        text_lower = text.lower()

        # Count matches for each intent
        scores = {}
        for intent, keywords in self.patterns.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            scores[intent] = score

        # Get highest score
        if not scores or max(scores.values()) == 0:
            return 'unknown'

        return max(scores, key=scores.get)


class AgentRouter:
    """Route to appropriate agent based on detected intent."""

    def __init__(self, logger=None):
        """Initialize agent router."""
        self.intent_detector = IntentDetector()
        self.logger = logger or logging.getLogger('neurohub.router')

    def route(self, prompt: str, provider: Optional[str] = None, **kwargs) -> Any:
        """Route prompt to appropriate agent.

        Args:
            prompt: User prompt
            provider: LLM provider (ollama/gemini/huggingface)
            **kwargs: Additional arguments for agents

        Returns:
            Agent execution result
        """
        self.logger.info(f"🎯 Routing request: prompt='{prompt[:50]}...', provider={provider}")

        # If provider is specified, use LLM mode with provider
        if provider:
            self.logger.info(f"🤖 LLM mode with provider: {provider}")
            print(f"🤖 LLM mode with provider: {provider}")
            print("💬 Entering interactive chat mode...")
            return self._call_llm_with_provider(prompt, provider, **kwargs)

        intent = self.intent_detector.detect(prompt)
        self.logger.info(f"🔍 Detected intent: {intent}")

        print(f"🤖 Detected intent: {intent}")
        print(f"📝 Routing to {intent}_agent...")
        print()

        start_time = datetime.now()
        result = None

        try:
            if intent == 'weather':
                if self._confirm_agent_execution('weather', prompt):
                    result = self._call_weather_agent(prompt, **kwargs)
                else:
                    result = self._get_agent_description('weather')
            elif intent == 'web':
                result = self._call_web_agent(prompt, **kwargs)
            elif intent == 'mcp':
                if self._confirm_agent_execution('mcp', prompt):
                    result = self._call_mcp_agent(prompt, **kwargs)
                else:
                    result = self._get_agent_description('mcp')
            elif intent == 'git':
                result = self._call_git_agent(prompt, **kwargs)
            elif intent == 'command':
                if self._confirm_agent_execution('command', prompt):
                    result = self._call_command_agent(prompt, **kwargs)
                else:
                    result = self._get_agent_description('command')
            elif intent == 'config':
                result = self._call_config_agent(prompt, **kwargs)
            else:
                result = self._call_llm_fallback(prompt, **kwargs)

            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.info(f"✅ Agent execution completed: {intent}, time={execution_time:.2f}s")

            return result

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"❌ Agent execution failed: {intent}, error={e}, time={execution_time:.2f}s")
            raise

    def _call_weather_agent(self, prompt: str, **kwargs) -> Any:
        """Call weather agent."""
        self.logger.info("🌤️ Calling weather agent")
        try:
            from agents.specialized.weather_agent import WeatherAgent
            agent = WeatherAgent()
            result = agent.execute(prompt)
            self.logger.info("✅ Weather agent completed successfully")
            return result
        except ImportError as e:
            self.logger.warning(f"⚠️ Weather agent import failed: {e}")
            print("⚠️ Weather agent not implemented yet")
            return None
        except Exception as e:
            self.logger.error(f"❌ Weather agent error: {e}")
            raise

    def _call_web_agent(self, prompt: str, **kwargs) -> Any:
        """Call web agent."""
        self.logger.info("🌐 Calling web agent")
        try:
            from agents.specialized.web_agent import WebAgent
            agent = WebAgent()
            result = agent.execute(prompt)
            self.logger.info("✅ Web agent completed successfully")
            return result
        except ImportError as e:
            self.logger.warning(f"⚠️ Web agent import failed: {e}")
            print("⚠️ Web agent not implemented yet")
            return None
        except Exception as e:
            self.logger.error(f"❌ Web agent error: {e}")
            raise

    def _call_mcp_agent(self, prompt: str, **kwargs) -> Any:
        """Call MCP agent."""
        self.logger.info("🛠️ Calling MCP agent")
        try:
            import subprocess
            import platform
            print("🛠️ MCP Agent - Code Generation & Project Development")

            if platform.system() == "Windows":
                cmd = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_mcp.py generate \'{prompt}\'"'
                self.logger.debug(f"Executing Windows WSL command: {cmd[:100]}...")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            else:
                cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_mcp.py generate '{prompt}'"
                self.logger.debug(f"Executing Linux command: {cmd[:100]}...")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash", encoding='utf-8', errors='ignore')

            if result.returncode == 0 and result.stdout:
                self.logger.info("✅ MCP agent completed successfully")
                return result.stdout.strip()
            else:
                error_msg = result.stderr.strip() if result.stderr else 'No output'
                self.logger.error(f"❌ MCP Error: {error_msg}")
                print(f"❌ MCP Error: {error_msg}")
                return None
        except Exception as e:
            self.logger.error(f"❌ MCP agent error: {e}")
            print(f"⚠️ MCP agent error: {e}")
            print("ℹ️ You can use: python agents/agent_mcp.py generate '<project_description>'")
            return None

    def _call_git_agent(self, prompt: str, **kwargs) -> Any:
        """Call git agent."""
        try:
            import subprocess
            import platform
            print("🔧 Git Agent - Repository Management")

            if platform.system() == "Windows":
                cmd = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_git.py --status"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_git.py --status"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash")

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"❌ Git Error: {result.stderr.strip()}")
                return None
        except Exception as e:
            print(f"⚠️ Git agent error: {e}")
            print("ℹ️ You can use: python agents/agent_git.py --status")
            return None

    def _call_command_agent(self, prompt: str, **kwargs) -> Any:
        """Call command agent."""
        try:
            import subprocess
            import platform
            print("💻 Command Agent - System Commands & Discord")

            if platform.system() == "Windows":
                # Check if it's a Discord command
                if 'discord' in prompt.lower() or 'チャンネル' in prompt.lower():
                    cmd = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 services/discord/bot_message_sender.py \'{prompt}\'"'
                else:
                    cmd = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_command.py \'{prompt}\'"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                # Check if it's a Discord command
                if 'discord' in prompt.lower() or 'チャンネル' in prompt.lower():
                    cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 services/discord/bot_message_sender.py '{prompt}'"
                else:
                    cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_command.py '{prompt}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash")

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"❌ Command Error: {result.stderr.strip()}")
                return None
        except Exception as e:
            print(f"⚠️ Command agent error: {e}")
            print("ℹ️ You can use: python agents/agent_command.py '<command>'")
            return None

    def _call_config_agent(self, prompt: str, **kwargs) -> Any:
        """Call config agent."""
        try:
            import subprocess
            import platform
            print("⚙️ Config Agent - Project Configuration")

            if platform.system() == "Windows":
                cmd = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_config.py --status"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            else:
                cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_config.py --status"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash")

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"❌ Config Error: {result.stderr.strip()}")
                return None
        except Exception as e:
            print(f"⚠️ Config agent error: {e}")
            print("ℹ️ You can use: python agents/agent_config.py --status")
            return None

    def _call_llm_with_provider(self, prompt: str, provider: str, **kwargs) -> Any:
        """Call LLM with specific provider in interactive mode."""
        try:
            import subprocess

            # Interactive chat mode with provider
            print(f"🎯 Starting chat with {provider} provider")
            print("📝 Type 'quit' or 'exit' to end conversation")
            print()

            while True:
                # If it's the first prompt, use it
                if prompt:
                    user_input = prompt
                    prompt = None  # Clear after first use
                else:
                    user_input = input("You: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break

                if not user_input:
                    continue

                try:
                    # Check if user wants to switch to specific agent
                    intent = self.intent_detector.detect(user_input)
                    if intent != 'unknown' and intent != 'llm':
                        response = input(f"🤖 Switch to {intent} agent? (y/n): ").strip().lower()
                        if response in ['y', 'yes']:
                            return self.route(user_input)

                    # Call LLM with provider using unified interface
                    import platform
                    if platform.system() == "Windows":
                        cmd = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 unified_interface.py \'{user_input}\'"'
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
                    else:
                        cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 unified_interface.py '{user_input}'"
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash", encoding='utf-8', errors='ignore')

                    if result.returncode == 0:
                        print(f"{provider}: {result.stdout.strip()}")
                    else:
                        print(f"❌ Error: {result.stderr.strip()}")

                except KeyboardInterrupt:
                    print("\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"❌ Error: {e}")

            return "Chat session completed"

        except Exception as e:
            print(f"⚠️ LLM provider error: {e}")
            print(f"ℹ️ You can use: python services/llm/llm_cli.py '{prompt}' --provider {provider}")
            return None

    def _call_llm_fallback(self, prompt: str, **kwargs) -> Any:
        """Fallback to LLM for unknown intents, with smart web fallback."""
        print("🤔 Intent unclear, using LLM fallback...")
        try:
            import subprocess
            import os
            import platform

            # Determine if running on Windows or Linux
            if platform.system() == "Windows":
                # Use WSL command on Windows
                cmd = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 unified_interface.py \'{prompt}\'"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            else:
                # Direct execution on Linux
                cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 unified_interface.py '{prompt}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash", encoding='utf-8', errors='ignore')

            if result.returncode == 0 and result.stdout:
                llm_response = result.stdout.strip()

                # AIの回答が不十分かチェック
                if self._should_search_web(llm_response, prompt):
                    self.logger.info("🌐 LLM回答が不十分、Web検索を実行")
                    print("🌐 AIの回答が不十分なため、Web検索を実行...")
                    web_result = self._call_web_agent(prompt)

                    # Web検索結果とAI回答を組み合わせ
                    if web_result and "❌" not in str(web_result):
                        combined_prompt = f"以下の情報を参考に、'{prompt}'について詳しく説明してください:\n\n{web_result}"
                        final_answer = self._direct_llm_call(combined_prompt)
                        return f"{llm_response}\n\n🔍 Web検索による追加情報:\n{final_answer}"
                    else:
                        return llm_response
                else:
                    return llm_response
            else:
                print(f"❌ LLM Error: {result.stderr.strip() if result.stderr else 'No output'}")
                # Fallback: Try direct LLM call
                return self._direct_llm_call(prompt)
        except Exception as e:
            print(f"⚠️ LLM fallback error: {e}")
            return self._direct_llm_call(prompt)

    def _should_search_web(self, llm_response: str, original_prompt: str) -> bool:
        """LLM回答が不十分でWeb検索が必要かを判定"""
        # 短すぎる回答
        if len(llm_response) < 50:
            return True

        # 不明確な回答を示すキーワード
        unclear_keywords = [
            "わかりません", "知りません", "不明", "情報がありません",
            "詳しく知りません", "確認できません", "申し訳ございません",
            "具体的な情報", "詳細は不明", "最新の情報"
        ]

        for keyword in unclear_keywords:
            if keyword in llm_response:
                return True

        # 現在時間・最新情報が必要な質問
        time_sensitive_keywords = [
            "今日", "現在", "最新", "いま", "今の", "今年", "最近"
        ]

        for keyword in time_sensitive_keywords:
            if keyword in original_prompt:
                return True

        return False

    def _confirm_agent_execution(self, agent_name: str, prompt: str) -> bool:
        """特殊エージェント実行前の確認（対話型でない場合は自動承認）"""
        # 明確な実行意図がある場合は確認スキップ
        execution_keywords = [
            '実行', 'やって', 'して', '作成', '作って', 'お願い',
            'run', 'execute', 'create', 'make', 'do'
        ]

        prompt_lower = prompt.lower()
        for keyword in execution_keywords:
            if keyword in prompt_lower:
                return True

        # 疑問形の場合は説明を表示
        question_keywords = ['？', '?', 'とは', 'って何', 'について', 'どう', 'なに']
        for keyword in question_keywords:
            if keyword in prompt:
                return False

        # デフォルトは実行
        return True

    def _get_agent_description(self, agent_name: str) -> str:
        """エージェントの説明を取得"""
        descriptions = {
            'weather': '🌤️ 天気エージェント: 気象情報の取得と天気予報を提供します。現在の天気、週間予報、気温情報などを取得できます。',
            'mcp': '🛠️ MCPエージェント: コード生成とプロジェクト開発を行います。Python、JavaScript等のコード自動生成、プロジェクト作成、デバッグ支援を提供します。',
            'git': '🐙 Gitエージェント: Gitワークフローの自動化を行います。スマートコミット、ブランチ管理、変更履歴の分析などGit操作を支援します。',
            'command': '⚙️ コマンドエージェント: システムコマンドとDiscord連携を実行します。ファイル操作、システム情報取得、Discord Bot機能を提供します。',
            'config': '⚙️ 設定エージェント: システム設定の管理と環境設定を行います。API設定、プロバイダー管理、システム情報の表示を提供します。',
            'web': '🌐 Webエージェント: Web検索とサイト解析を行います。リアルタイム情報の検索、ウェブサイト内容の解析、最新ニュースの取得を提供します。'
        }

        base_description = descriptions.get(agent_name, f'{agent_name}エージェント: 特殊機能を提供します。')

        return f"""{base_description}

💡 実行したい場合は、具体的な指示を含めて再度お話しください。
例: 「{agent_name}で○○を実行して」「○○を作成して」「○○について調べて」

❓ より詳しく知りたい場合は、「{agent_name}エージェントの機能一覧」とお聞きください。"""

    def _direct_llm_call(self, prompt: str) -> str:
        """Direct LLM call without unified interface."""
        try:
            import subprocess
            import platform

            # Create temp test file for reliable execution
            temp_file_content = f'''#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from services.ai.provider_gemini import GeminiConfig
    gc = GeminiConfig()
    result = gc.infer("{prompt}")
    if result.is_success:
        print(result.content)
        print("\\n" + "="*60)
        print("🔧 プロバイダー情報:")
        print(f"   📡 Provider: Gemini")
        print(f"   🤖 Model: gemini-2.0-flash-exp")
        print("="*60)
    else:
        print(f"Error: {{result.error}}")
except Exception as e:
    print(f"Exception: {{e}}")
'''

            if platform.system() == "Windows":
                with open("temp_llm_test.py", "w", encoding="utf-8") as f:
                    f.write(temp_file_content)
                cmd = 'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 temp_llm_test.py"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8', errors='ignore')
            else:
                with open("temp_llm_test.py", "w", encoding="utf-8") as f:
                    f.write(temp_file_content)
                cmd = 'cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 temp_llm_test.py'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash", encoding='utf-8', errors='ignore')

            # Clean up temp file
            try:
                import os
                os.remove("temp_llm_test.py")
            except:
                pass

            if result.returncode == 0 and result.stdout:
                return result.stdout.strip()
            else:
                return f"❌ LLM処理エラー: {result.stderr.strip() if result.stderr else 'No output'}"
        except Exception as e:
            return f"❌ 直接LLM呼び出しエラー: {e}"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='NeuroHub - AI-powered smart assistant',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Weather query
  python main.py "今日の天気は？"

  # Web search
  python main.py "最新のAIニュースを検索して"

  # Development task
  python main.py "ファイル一覧ツールを作成して"

  # Git operation
  python main.py "git statusを確認"

  # System command
  python main.py "カレントディレクトリの内容を表示"

  # Configuration
  python main.py "設定ファイルの状態を確認"
        """
    )

    parser.add_argument(
        'prompt',
        type=str,
        help='Natural language prompt'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )

    parser.add_argument(
        '--force-agent',
        type=str,
        choices=['weather', 'web', 'mcp', 'git', 'command', 'config', 'llm'],
        help='Force specific agent (skip intent detection)'
    )

    parser.add_argument(
        '-p', '--provider',
        type=str,
        choices=['ollama', 'gemini', 'huggingface'],
        help='Select LLM provider (ollama/gemini/huggingface)'
    )

    args = parser.parse_args()

    # ログ設定
    logger = setup_logging(args.debug)
    logger.info(f"🚀 NeuroHub started: prompt='{args.prompt[:50]}...', debug={args.debug}")

    # Initialize router
    router = AgentRouter(logger)

    # Override intent detection if forced
    if args.force_agent:
        logger.info(f"🎯 Forced agent: {args.force_agent}")
        print(f"🎯 Forced agent: {args.force_agent}")
        if args.force_agent == 'weather':
            result = router._call_weather_agent(args.prompt)
        elif args.force_agent == 'web':
            result = router._call_web_agent(args.prompt)
        elif args.force_agent == 'mcp':
            result = router._call_mcp_agent(args.prompt)
        elif args.force_agent == 'git':
            result = router._call_git_agent(args.prompt)
        elif args.force_agent == 'command':
            result = router._call_command_agent(args.prompt)
        elif args.force_agent == 'config':
            result = router._call_config_agent(args.prompt)
        elif args.force_agent == 'llm':
            result = router._call_llm_fallback(args.prompt)
    else:
        # Auto-detect intent and route
        result = router.route(args.prompt, provider=args.provider)

    # Print result
    if result is not None:
        print("\n✅ Result:")
        print(result)
        logger.info("✅ NeuroHub completed successfully")
    else:
        logger.warning("⚠️ NeuroHub completed with no result")

    return 0


if __name__ == '__main__':
    sys.exit(main())
