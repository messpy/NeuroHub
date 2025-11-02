# main.py 詳細仕様

[← プロジェクト概要に戻る](PROJECT_OVERVIEW.md)

---

## 📋 概要

NeuroHubの中央エントリーポイント。自然言語の意図を判定し、適切なエージェントにルーティングします。

**ファイルパス**: `main.py`

---

## 🎯 主要クラス

### IntentDetector

**責務**: ユーザー入力から意図を自動判定

**キーワードパターン**:

| 意図 | キーワード例 |
|-----|------------|
| weather | 天気、気温、降水、予報、晴れ、雨、雪 |
| web | 検索、google、トレンド、ニュース |
| mcp | 開発、作成、プログラム、コード、プロジェクト |
| git | git, commit, push, pull, branch |
| command | コマンド、実行、ls, cd, mkdir |
| config | 設定、config、api key、token |

**メソッド**:
- `detect(text: str) -> str`: テキストから意図を判定

**判定ロジック**:
1. 入力テキストを小文字化
2. 各意図のキーワード一致数をカウント
3. 最もスコアが高い意図を返す
4. スコア0の場合は'unknown'

---

### AgentRouter

**責務**: 判定された意図に基づいて適切なエージェントを呼び出し

**ルーティングテーブル**:

| 意図 | エージェント | メソッド |
|-----|------------|---------|
| weather | WeatherAgent | `_call_weather_agent()` |
| web | WebAgent | `_call_web_agent()` |
| mcp | MCPAgent | `_call_mcp_agent()` |
| git | GitAgent | `_call_git_agent()` |
| command | CommandAgent | `_call_command_agent()` |
| config | ConfigAgent | `_call_config_agent()` |
| unknown | LLM Fallback | `_call_llm_fallback()` |

**メソッド**:
- `route(prompt: str, **kwargs) -> Any`: プロンプトをルーティング
- `_call_*_agent()`: 各エージェント呼び出しメソッド

**エラーハンドリング**:
- エージェントが未実装の場合: 警告メッセージと代替コマンド提示
- エージェント実行エラー: エラーログとフォールバック

---

## 🚀 使用方法

### 基本的な使い方

```bash
# 天気クエリ
python main.py "今日の天気は？"

# 開発タスク
python main.py "ファイル一覧ツールを作成"

# Git操作
python main.py "git statusを確認"

# システムコマンド
python main.py "カレントディレクトリの内容を表示"
```

### オプション

```bash
# デバッグモード
python main.py "質問" --debug

# エージェント強制指定（意図判定スキップ）
python main.py "質問" --force-agent weather
python main.py "質問" --force-agent mcp
python main.py "質問" --force-agent git
```

---

## 📊 処理フロー

```
ユーザー入力
    ↓
IntentDetector.detect()
    ↓
意図判定（weather/web/mcp/git/command/config/unknown）
    ↓
AgentRouter.route()
    ↓
該当エージェントのexecute()実行
    ↓
結果返却
```

---

## 🔧 カスタマイズ

### 新しい意図を追加

1. **IntentDetectorにパターン追加**:
```python
self.patterns = {
    # 既存パターン...
    'new_intent': [
        'keyword1', 'keyword2', 'keyword3'
    ]
}
```

2. **AgentRouterにルーティング追加**:
```python
def route(self, prompt: str, **kwargs) -> Any:
    intent = self.intent_detector.detect(prompt)

    # 新しいケースを追加
    elif intent == 'new_intent':
        return self._call_new_agent(prompt, **kwargs)
```

3. **エージェント呼び出しメソッド追加**:
```python
def _call_new_agent(self, prompt: str, **kwargs) -> Any:
    try:
        from agents.new_agent import NewAgent
        agent = NewAgent()
        return agent.execute(prompt)
    except Exception as e:
        print(f"⚠️ New agent error: {e}")
        return None
```

---

## 🧪 テスト

### 意図判定テスト

```python
detector = IntentDetector()

# 天気
assert detector.detect("今日の天気は？") == "weather"

# 開発
assert detector.detect("ToDoアプリを作成") == "mcp"

# Git
assert detector.detect("git push origin main") == "git"
```

### ルーティングテスト

```bash
# 各エージェントが正しく呼ばれるか確認
python main.py "天気を教えて" --debug
python main.py "開発して" --debug
python main.py "git status" --debug
```

---

## 📝 実装例

### 実際の実行例

```bash
$ python main.py "今日の天気を教えて"
🤖 Detected intent: weather
📝 Routing to weather_agent...

📍 Tokyo, Japan

🌡️ 現在: 18°C ☀️ 晴れ
💨 風速: 5 km/h

📅 今日 (2025-11-02):
  🌡️ 最高: 22°C
  🌡️ 最低: 15°C
```

```bash
$ python main.py "git statusを確認"
🤖 Detected intent: git
📝 Routing to git_agent...

✅ Result:
📊 Git状態: 15ファイル変更
  ✅ Staged: 0
  📝 Modified: 15
  ❓ Untracked: 0
```

---

## 🔗 関連ファイル

- [agents/common.py](../agents/common.py) - BaseAgentクラス
- [agents/git_agent.py](../agents/git_agent.py) - Git操作エージェント
- [agents/specialized/weather_agent.py](../agents/specialized/weather_agent.py) - 天気エージェント
- [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) - プロジェクト概要

---

[← プロジェクト概要に戻る](PROJECT_OVERVIEW.md)
