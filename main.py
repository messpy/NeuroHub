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
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))


class IntentDetector:
    """Detect user intent from natural language input."""

    def __init__(self):
        """Initialize intent detector with keyword patterns."""
        self.patterns = {
            'weather': [
                '天気', '気温', '降水', '予報', 'weather', 'temperature', 'forecast',
                '晴れ', '雨', '雪', '曇り', 'sunny', 'rain', 'snow'
            ],
            'web': [
                '検索', 'ググ', 'google', 'search', 'トレンド', 'trend',
                'ニュース', 'news', 'web', 'サイト', 'ウェブ'
            ],
            'mcp': [
                '開発', '作成', 'プログラム', 'コード', 'develop', 'code', 'create',
                'プロジェクト', 'project', 'アプリ', 'app', 'cli', 'ツール', 'tool',
                '実装', 'implement', 'ファイル作成', 'make file'
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
                'api key', 'token', 'パラメータ', 'parameter'
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

    def __init__(self):
        """Initialize agent router."""
        self.intent_detector = IntentDetector()

    def route(self, prompt: str, provider: Optional[str] = None, **kwargs) -> Any:
        """Route prompt to appropriate agent.

        Args:
            prompt: User prompt
            provider: LLM provider (ollama/gemini/huggingface)
            **kwargs: Additional arguments for agents

        Returns:
            Agent execution result
        """
        # If provider is specified, use LLM mode with provider
        if provider:
            print(f"🤖 LLM mode with provider: {provider}")
            print("💬 Entering interactive chat mode...")
            return self._call_llm_with_provider(prompt, provider, **kwargs)

        intent = self.intent_detector.detect(prompt)

        print(f"🤖 Detected intent: {intent}")
        print(f"📝 Routing to {intent}_agent...")
        print()

        if intent == 'weather':
            return self._call_weather_agent(prompt, **kwargs)
        elif intent == 'web':
            return self._call_web_agent(prompt, **kwargs)
        elif intent == 'mcp':
            return self._call_mcp_agent(prompt, **kwargs)
        elif intent == 'git':
            return self._call_git_agent(prompt, **kwargs)
        elif intent == 'command':
            return self._call_command_agent(prompt, **kwargs)
        elif intent == 'config':
            return self._call_config_agent(prompt, **kwargs)
        else:
            return self._call_llm_fallback(prompt, **kwargs)

    def _call_weather_agent(self, prompt: str, **kwargs) -> Any:
        """Call weather agent."""
        try:
            from agents.specialized.weather_agent import WeatherAgent
            agent = WeatherAgent()
            return agent.execute(prompt)
        except ImportError:
            print("⚠️ Weather agent not implemented yet")
            return None

    def _call_web_agent(self, prompt: str, **kwargs) -> Any:
        """Call web agent."""
        try:
            from agents.specialized.web_agent import WebAgent
            agent = WebAgent()
            return agent.execute(prompt)
        except ImportError:
            print("⚠️ Web agent not implemented yet")
            return None

    def _call_mcp_agent(self, prompt: str, **kwargs) -> Any:
        """Call MCP agent."""
        try:
            import subprocess
            print("🛠️ MCP Agent - Code Generation & Project Development")
            cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 agents/agent_mcp.py generate '{prompt}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash")
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"❌ MCP Error: {result.stderr.strip()}")
                return None
        except Exception as e:
            print(f"⚠️ MCP agent error: {e}")
            print("ℹ️ You can use: python agents/agent_mcp.py generate '<project_description>'")
            return None

    def _call_git_agent(self, prompt: str, **kwargs) -> Any:
        """Call git agent."""
        try:
            import subprocess
            print("🔧 Git Agent - Repository Management")
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
            print("💻 Command Agent - System Commands & Discord")
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
            print("⚙️ Config Agent - Project Configuration")
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
                    cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 unified_interface.py '{user_input}'"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash")
                    
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
        """Fallback to LLM for unknown intents."""
        print("🤔 Intent unclear, using LLM fallback...")
        try:
            import subprocess
            # Call LLM CLI using unified interface
            cmd = f"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && export PYTHONPATH=/mnt/c/Users/kenny/sandbox/NeuroHub && python3 unified_interface.py '{prompt}'"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, executable="/bin/bash")
            
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"❌ LLM Error: {result.stderr.strip()}")
                return None
        except Exception as e:
            print(f"⚠️ LLM fallback error: {e}")
            print("ℹ️ You can use: python services/llm/llm_cli.py '<prompt>'")
            return None


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

    # Initialize router
    router = AgentRouter()

    # Override intent detection if forced
    if args.force_agent:
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

    return 0


if __name__ == '__main__':
    sys.exit(main())
