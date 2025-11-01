#!/usr/bin/env python3
from agents.llm_agent import LLMAgent
from agents.llm_agent import LLMRequest

agent = LLMAgent()

# より詳細なテスト（実際のコミットメッセージ生成風）
print('=== コミットメッセージ生成テスト ===')

full_prompt = """以下のGit差分を分析して、適切なコミットメッセージを生成してください。

フォーマット: ':prefix: 説明'（30文字以内）
使用可能prefix: :add:, :fix:, :update:, :refactor:, :docs:, :test:, :config:, :remove:

例: ':update: テスト関数を改善'

分析対象の変更内容:
@@ -1,3 +1,5 @@
 def test_function():
-    return False
+    return True

コミットメッセージ:"""

# Geminiテスト
print('\n--- Gemini ---')
try:
    request = LLMRequest(
        prompt=full_prompt,
        system_message='Gitコミットメッセージを指定フォーマットで簡潔に生成してください',
        preferred_provider='gemini',
        max_tokens=50
    )
    response = agent.generate_text(request)
    print('状態:', response.status_code)
    print('内容:', response.content[:100] if response.content else 'なし')
    print('エラー:', response.error if response.error else 'なし')
except Exception as e:
    print('例外:', str(e))

# HuggingFaceテスト
print('\n--- HuggingFace ---')
try:
    request = LLMRequest(
        prompt=full_prompt,
        system_message='Gitコミットメッセージを指定フォーマットで簡潔に生成してください',
        preferred_provider='huggingface',
        max_tokens=50
    )
    response = agent.generate_text(request)
    print('状態:', response.status_code)
    print('内容:', response.content[:100] if response.content else 'なし')
    print('エラー:', response.error if response.error else 'なし')
except Exception as e:
    print('例外:', str(e))
