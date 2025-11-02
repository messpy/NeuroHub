#!/usr/bin/env python3
from agents.git_smart_agent import GitSmartAgent

# テスト用差分
agent = GitSmartAgent()
agent.debug = True

# 簡単な差分でテスト
simple_diff = """@@ -1,3 +1,5 @@
 def test_function():
-    return False
+    return True
+
+def new_test():
+    return 'updated'"""

print('差分長:', len(simple_diff))
result = agent._generate_better_commit_message('test.py', simple_diff)
print('結果:', result)
