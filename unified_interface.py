#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NeuroHub 統一インターフェース
main.py → LLMエージェント判断 → 各エージェント実行

フロー:
1. ユーザープロンプト受信
2. LLMエージェントがプロンプト解析・意図判定
3. 適切なエージェントに自動ルーティング
4. 結果を統一形式で返却
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
import traceback

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from agents.agent_llm import LLMAgent, LLMRequest


@dataclass
class UnifiedRequest:
    """統一リクエスト形式"""
    prompt: str
    user_id: str = "default"
    session_id: Optional[str] = None
    context: Dict[str, Any] = None
    preferences: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}
        if self.preferences is None:
            self.preferences = {}


@dataclass
class UnifiedResponse:
    """統一レスポンス形式"""
    success: bool
    agent_used: str
    content: str
    metadata: Dict[str, Any]
    execution_time: float
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'success': self.success,
            'agent_used': self.agent_used,
            'content': self.content,
            'metadata': self.metadata,
            'execution_time': self.execution_time,
            'timestamp': self.timestamp
        }


class SmartIntentAnalyzer:
    """LLMを活用した高度な意図解析"""

    def __init__(self, llm_agent: LLMAgent):
        """初期化"""
        self.llm_agent = llm_agent
        self.agent_descriptions = {
            'weather': '天気予報・気象情報の取得',
            'web': 'Web検索・ページ解析・トレンド調査',
            'mcp': 'プログラム開発・コード生成・プロジェクト作成',
            'git': 'Gitリポジトリ操作・コミット・ブランチ管理',
            'command': 'システムコマンド実行・ファイル操作',
            'config': '設定管理・環境設定・APIキー管理',
            'discord': 'Discord Bot機能・チャット操作',
            'db': 'データベース操作・クエリ実行・データ管理',
            'package': 'パッケージ管理・依存関係解決・仮想環境'
        }

    def analyze(self, prompt: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """プロンプトを解析して最適なエージェントを決定"""
        try:
            analysis_prompt = self._build_analysis_prompt(prompt, context)

            request = LLMRequest(
                prompt=analysis_prompt,
                system_message="あなたはプロンプト解析の専門家です。ユーザーの要求を正確に理解し、最適なエージェントを選択してください。",
                temperature=0.1,  # 一貫した判断のため低温度
                max_tokens=500
            )

            response = self.llm_agent.generate_text(request)

            if response.is_success:
                return self._parse_analysis_result(response.content)
            else:
                # LLM失敗時はフォールバック
                return self._fallback_analysis(prompt)

        except Exception as e:
            print(f"❌ 意図解析エラー: {e}")
            return self._fallback_analysis(prompt)

    def _build_analysis_prompt(self, prompt: str, context: Dict[str, Any] = None) -> str:
        """解析用プロンプト構築"""

        agents_info = "\\n".join([
            f"- {name}: {desc}"
            for name, desc in self.agent_descriptions.items()
        ])

        context_info = ""
        if context:
            context_info = f"\\nコンテキスト情報:\\n{json.dumps(context, ensure_ascii=False, indent=2)}"

        return f"""
ユーザーのプロンプトを解析し、最適なエージェントを決定してください。

利用可能なエージェント:
{agents_info}

ユーザープロンプト: "{prompt}"{context_info}

以下のJSON形式で回答してください:
{{
    "agent": "最適なエージェント名",
    "confidence": 0.0-1.0の信頼度,
    "reasoning": "選択理由",
    "parameters": {{
        "param1": "エージェント固有のパラメータ"
    }}
}}

例:
- "今日の天気は？" → agent: "weather"
- "Node.jsアプリを作成して" → agent: "mcp"
- "gitの状態を確認" → agent: "git"
- "ファイル一覧を表示" → agent: "command"
"""

    def _parse_analysis_result(self, content: str) -> Dict[str, Any]:
        """LLM解析結果をパース"""
        try:
            # JSONの抽出
            import re
            json_match = re.search(r'\\{[^}]+\\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                result = json.loads(json_str)

                # 必須フィールドの確認
                if 'agent' in result:
                    return {
                        'agent': result['agent'],
                        'confidence': result.get('confidence', 0.8),
                        'reasoning': result.get('reasoning', ''),
                        'parameters': result.get('parameters', {})
                    }

            # JSON抽出に失敗した場合、テキストから推測
            return self._extract_agent_from_text(content)

        except Exception as e:
            print(f"⚠️ 解析結果パースエラー: {e}")
            return {'agent': 'unknown', 'confidence': 0.1, 'reasoning': 'パースエラー', 'parameters': {}}

    def _extract_agent_from_text(self, content: str) -> Dict[str, Any]:
        """テキストからエージェント名を抽出"""
        content_lower = content.lower()

        for agent_name in self.agent_descriptions.keys():
            if agent_name in content_lower:
                return {
                    'agent': agent_name,
                    'confidence': 0.6,
                    'reasoning': f'テキストから{agent_name}を検出',
                    'parameters': {}
                }

        return {'agent': 'unknown', 'confidence': 0.1, 'reasoning': 'エージェント検出失敗', 'parameters': {}}

    def _fallback_analysis(self, prompt: str) -> Dict[str, Any]:
        """フォールバック解析（キーワードベース）"""
        prompt_lower = prompt.lower()

        # キーワードベースの簡易判定
        keyword_map = {
            'weather': ['天気', '気温', '降水', '予報', 'weather'],
            'web': ['検索', 'ググ', 'google', 'search', 'web'],
            'mcp': ['開発', '作成', 'プログラム', 'コード', 'develop', 'code'],
            'git': ['git', 'commit', 'push', 'pull', 'branch'],
            'command': ['コマンド', 'command', '実行', 'ls', 'cd'],
            'config': ['設定', 'config', 'api key']
        }

        for agent, keywords in keyword_map.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return {
                    'agent': agent,
                    'confidence': 0.7,
                    'reasoning': f'キーワードマッチング: {agent}',
                    'parameters': {}
                }

        return {'agent': 'llm', 'confidence': 0.5, 'reasoning': '汎用LLM対応', 'parameters': {}}


class UnifiedAgentExecutor:
    """統一エージェント実行システム"""

    def __init__(self):
        """初期化"""
        self.llm_agent = LLMAgent()
        self.intent_analyzer = SmartIntentAnalyzer(self.llm_agent)
        self.execution_history = []

        # エージェント実行関数マッピング
        self.agent_executors = {
            'weather': self._execute_weather,
            'web': self._execute_web,
            'mcp': self._execute_mcp,
            'git': self._execute_git,
            'command': self._execute_command,
            'config': self._execute_config,
            'discord': self._execute_discord,
            'db': self._execute_db,
            'package': self._execute_package,
            'llm': self._execute_llm
        }

    def execute(self, request: UnifiedRequest) -> UnifiedResponse:
        """統一リクエストを実行"""
        start_time = datetime.now()

        try:
            print(f"🤖 NeuroHub統一インターフェース")
            print(f"📝 プロンプト: {request.prompt}")
            print(f"⏰ 開始時間: {start_time.strftime('%H:%M:%S')}")
            print()

            # 1. 意図解析
            print("🔍 Step 1: LLMによる意図解析...")
            analysis = self.intent_analyzer.analyze(request.prompt, request.context)

            agent_name = analysis.get('agent', 'unknown')
            confidence = analysis.get('confidence', 0.0)
            reasoning = analysis.get('reasoning', '')
            parameters = analysis.get('parameters', {})

            print(f"   🎯 選択エージェント: {agent_name}")
            print(f"   📊 信頼度: {confidence:.1%}")
            print(f"   💭 理由: {reasoning}")
            print()

            # 2. エージェント実行
            print(f"🚀 Step 2: {agent_name}エージェント実行...")

            if agent_name in self.agent_executors:
                result = self.agent_executors[agent_name](request, parameters)
            else:
                result = self._execute_unknown(request, parameters)

            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            response = UnifiedResponse(
                success=result.get('success', False),
                agent_used=agent_name,
                content=result.get('content', ''),
                metadata={
                    'analysis': analysis,
                    'parameters': parameters,
                    **result.get('metadata', {})
                },
                execution_time=execution_time
            )

            print(f"✅ 実行完了 ({execution_time:.2f}秒)")
            print()

            # 3. 履歴保存
            self.execution_history.append({
                'request': request,
                'response': response,
                'timestamp': start_time.isoformat()
            })

            return response

        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()

            error_msg = f"実行エラー: {str(e)}"
            print(f"❌ {error_msg}")
            print(f"🔧 デバッグ情報:")
            traceback.print_exc()

            return UnifiedResponse(
                success=False,
                agent_used="error",
                content=error_msg,
                metadata={'error': str(e), 'traceback': traceback.format_exc()},
                execution_time=execution_time
            )

    def _execute_weather(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """天気エージェント実行"""
        try:
            from agents.specialized.weather_agent import WeatherAgent
            agent = WeatherAgent()
            result = agent.execute(request.prompt)
            return {'success': True, 'content': str(result), 'metadata': {'source': 'weather_agent'}}
        except ImportError:
            print("⚠️ WeatherAgentが見つかりません。代替実行中...")
            # WSL環境で直接実行
            import subprocess
            try:
                cmd = f'wsl bash -c "cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && python3 services/agent/weather_agent.py"'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
                return {'success': True, 'content': result.stdout, 'metadata': {'source': 'weather_script'}}
            except Exception as e:
                return {'success': False, 'content': f"天気情報取得エラー: {e}", 'metadata': {}}

    def _execute_web(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Webエージェント実行"""
        try:
            from agents.specialized.web_agent import WebAgent
            agent = WebAgent()
            result = agent.execute(request.prompt)
            return {'success': True, 'content': str(result), 'metadata': {'source': 'web_agent'}}
        except ImportError:
            return {'success': False, 'content': "WebAgent未実装", 'metadata': {}}

    def _execute_mcp(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """MCPエージェント実行"""
        try:
            from agents.agent_mcp import MCPAgent, MCPRequest
            agent = MCPAgent()

            # MCPRequestオブジェクトを作成
            mcp_request = MCPRequest(
                mode="generate",  # 必須引数
                prompt=request.prompt,  # 必須引数
                language="python",
                output_path="./output"
            )

            result = agent.execute(mcp_request)
            return {'success': True, 'content': str(result), 'metadata': {'source': 'mcp_agent'}}
        except ImportError:
            print("⚠️ MCPAgentが見つかりません。")
            return {'success': False, 'content': "MCPAgent未実装", 'metadata': {}}
        except Exception as e:
            return {'success': False, 'content': f"MCP実行エラー: {e}", 'metadata': {}}

    def _execute_git(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Gitエージェント実行"""
        try:
            from agents.agent_git import GitAgent
            agent = GitAgent()
            result = agent.execute(request.prompt)
            return {'success': True, 'content': str(result), 'metadata': {'source': 'git_agent'}}
        except Exception as e:
            return {'success': False, 'content': f"Git実行エラー: {e}", 'metadata': {}}

    def _execute_command(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """コマンドエージェント実行"""
        try:
            from agents.agent_command import CommandAgent
            agent = CommandAgent()
            result = agent.execute(request.prompt)
            return {'success': True, 'content': str(result), 'metadata': {'source': 'command_agent'}}
        except Exception as e:
            return {'success': False, 'content': f"コマンド実行エラー: {e}", 'metadata': {}}

    def _execute_config(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """設定エージェント実行"""
        try:
            from agents.agent_config import ConfigAgent
            agent = ConfigAgent()
            result = agent.execute(request.prompt)
            return {'success': True, 'content': str(result), 'metadata': {'source': 'config_agent'}}
        except Exception as e:
            return {'success': False, 'content': f"設定エラー: {e}", 'metadata': {}}

    def _execute_discord(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Discordエージェント実行"""
        try:
            from services.discord.bot_core import DiscordBot
            # Discord Bot関連処理
            return {'success': True, 'content': "Discord機能は開発中です", 'metadata': {'source': 'discord_placeholder'}}
        except Exception as e:
            return {'success': False, 'content': f"Discord実行エラー: {e}", 'metadata': {}}

    def _execute_db(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """データベースエージェント実行"""
        try:
            from agents.agent_db import DatabaseAgent
            agent = DatabaseAgent()
            result = agent.execute(request.prompt)
            return {'success': True, 'content': str(result), 'metadata': {'source': 'db_agent'}}
        except Exception as e:
            return {'success': False, 'content': f"DB実行エラー: {e}", 'metadata': {}}

    def _execute_package(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """パッケージ管理エージェント実行"""
        try:
            from tools.package_manager import PackageManager
            manager = PackageManager(str(PROJECT_ROOT))

            # プロンプトからコマンドを抽出
            if "install" in request.prompt.lower():
                # パッケージインストール
                return {'success': True, 'content': "パッケージ管理機能は利用可能です", 'metadata': {'source': 'package_manager'}}
            else:
                # 状態確認
                return {'success': True, 'content': "パッケージ管理システム稼働中", 'metadata': {'source': 'package_manager'}}
        except Exception as e:
            return {'success': False, 'content': f"パッケージ管理エラー: {e}", 'metadata': {}}

    def _execute_llm(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """汎用LLM実行（フォールバック）"""
        try:
            llm_request = LLMRequest(
                prompt=request.prompt,
                system_message="あなたは親切なAIアシスタントです。ユーザーの質問に丁寧に答えてください。",
                temperature=0.7
            )

            response = self.llm_agent.generate_text(llm_request)

            return {
                'success': response.is_success,
                'content': response.content,
                'metadata': {
                    'source': 'llm_fallback',
                    'provider': self.llm_agent.get_first_available_provider(),
                    'model': response.model_name if hasattr(response, 'model_name') else 'unknown'
                }
            }
        except Exception as e:
            return {'success': False, 'content': f"LLM実行エラー: {e}", 'metadata': {}}

    def _execute_unknown(self, request: UnifiedRequest, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """不明な要求の処理"""
        return {
            'success': False,
            'content': "申し訳ございません。要求を理解できませんでした。",
            'metadata': {'source': 'unknown_handler'}
        }


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description='NeuroHub統一インターフェース - LLM判断による自動エージェント選択',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python unified_interface.py "今日の東京の天気を教えて"
  python unified_interface.py "Node.jsのWebアプリを作成して"
  python unified_interface.py "git statusを確認して"
  python unified_interface.py "設定ファイルの状態を見せて"
  python unified_interface.py "Hello world を作るプログラムを書いて"

特徴:
  - LLMによる高度な意図解析
  - 自動エージェント選択
  - 統一された応答形式
  - 実行履歴の保存
  - エラー処理とフォールバック
        """
    )

    parser.add_argument('prompt', nargs='?', help='自然言語プロンプト')
    parser.add_argument('--user-id', default='default', help='ユーザーID')
    parser.add_argument('--debug', action='store_true', help='デバッグモード')
    parser.add_argument('--json', action='store_true', help='JSON形式で出力')
    parser.add_argument('--history', action='store_true', help='実行履歴を表示')

    args = parser.parse_args()

    try:
        # 統一エージェント実行システム初期化
        executor = UnifiedAgentExecutor()

        if args.history:
            # 履歴表示
            print("📚 実行履歴:")
            if executor.execution_history:
                for i, entry in enumerate(executor.execution_history[-10:], 1):
                    print(f"  {i}. {entry['timestamp']}: {entry['request'].prompt[:50]}...")
            else:
                print("  実行履歴がありません")
            return 0

        # プロンプトが提供されていない場合
        if not args.prompt:
            print("❌ プロンプトを指定してください")
            parser.print_help()
            return 1

        # リクエスト作成
        request = UnifiedRequest(
            prompt=args.prompt,
            user_id=args.user_id,
            context={'debug': args.debug}
        )

        # 実行
        response = executor.execute(request)

        # 結果出力
        if args.json:
            print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))
        else:
            print("=" * 60)
            print("📋 実行結果")
            print("=" * 60)
            print(f"エージェント: {response.agent_used}")
            print(f"成功: {'✅' if response.success else '❌'}")
            print(f"実行時間: {response.execution_time:.2f}秒")
            print()
            print("💬 内容:")
            print(response.content)
            print()
            if args.debug:
                print("🔧 メタデータ:")
                print(json.dumps(response.metadata, ensure_ascii=False, indent=2))

        return 0 if response.success else 1

    except KeyboardInterrupt:
        print("\\n👋 中断しました")
        return 1
    except Exception as e:
        print(f"❌ エラー: {e}")
        if args.debug:
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
