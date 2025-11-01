#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_status.py - MCPシステムの現在の状況を表示
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime


def check_projects():
    """プロジェクトディレクトリの状況確認"""
    projects_dir = Path("projects")
    if not projects_dir.exists():
        return {"count": 0, "projects": [], "status": "no_projects_dir"}

    projects = []
    for item in projects_dir.iterdir():
        if item.is_dir():
            project_info = {
                "name": item.name,
                "path": str(item),
                "has_main": (item / "main.py").exists(),
                "has_readme": (item / "README.md").exists(),
                "has_tests": (item / "test_results.json").exists()
            }
            projects.append(project_info)

    return {
        "count": len(projects),
        "projects": projects,
        "status": "ok" if projects else "empty"
    }


def check_logs():
    """ログディレクトリの確認"""
    logs_dir = Path("logs/ai_prj")
    if not logs_dir.exists():
        return {"count": 0, "logs": [], "status": "no_logs_dir"}

    logs = []
    for item in logs_dir.glob("*.yaml"):
        log_info = {
            "name": item.name,
            "type": "design" if "design" in item.name else
                   "codegen" if "codegen" in item.name else
                   "test" if "test" in item.name else "unknown",
            "size": item.stat().st_size,
            "modified": datetime.fromtimestamp(item.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        }
        logs.append(log_info)

    return {
        "count": len(logs),
        "logs": sorted(logs, key=lambda x: x["modified"], reverse=True),
        "status": "ok" if logs else "empty"
    }


def check_mcp_exec_log():
    """MCP実行ログの確認"""
    log_file = Path("logs/mcp_exec.log")
    if not log_file.exists():
        return {"status": "no_log", "entries": 0, "recent": []}

    try:
        with log_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        entries = []
        for line in lines[-10:]:  # 最新の10エントリ
            try:
                entry = json.loads(line.strip())
                entries.append({
                    "timestamp": entry.get("timestamp", "unknown"),
                    "kind": entry.get("kind", "unknown"),
                    "goal": entry.get("goal", "")[:50] + "..." if len(entry.get("goal", "")) > 50 else entry.get("goal", ""),
                    "cmd": entry.get("cmd", "")[:30] + "..." if len(entry.get("cmd", "")) > 30 else entry.get("cmd", ""),
                    "rc": entry.get("rc", "unknown")
                })
            except json.JSONDecodeError:
                continue

        return {
            "status": "ok",
            "entries": len(lines),
            "recent": entries
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "entries": 0, "recent": []}


def check_llm_config():
    """LLM設定の確認"""
    config_file = Path("config/config.yaml")
    if not config_file.exists():
        return {"status": "no_config", "providers": []}

    try:
        with config_file.open("r", encoding="utf-8") as f:
            content = f.read()

        # 簡易的なYAML解析（設定確認用）
        providers = []
        lines = content.split('\n')
        current_provider = None

        for line in lines:
            line = line.strip()
            if line.endswith(':') and not line.startswith(' '):
                if line.replace(':', '') in ['ollama', 'gemini', 'huggingface']:
                    current_provider = {"name": line.replace(':', ''), "enabled": "unknown", "model": "unknown"}
            elif current_provider and line.startswith('enabled:'):
                current_provider["enabled"] = line.split(':', 1)[1].strip()
            elif current_provider and line.startswith('model:'):
                current_provider["model"] = line.split(':', 1)[1].strip()
                providers.append(current_provider)
                current_provider = None

        return {
            "status": "ok",
            "providers": providers
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "providers": []}


def main():
    """メイン関数"""
    print("🔍 NeuroHub MCP システム状況")
    print("=" * 50)

    # プロジェクト状況
    print("\n📁 プロジェクト状況:")
    projects_status = check_projects()
    print(f"   プロジェクト数: {projects_status['count']}")

    if projects_status['projects']:
        print("   プロジェクト一覧:")
        for project in projects_status['projects']:
            status_icons = []
            if project['has_main']:
                status_icons.append("🐍")
            if project['has_readme']:
                status_icons.append("📖")
            if project['has_tests']:
                status_icons.append("✅")

            print(f"     - {project['name']} {''.join(status_icons)}")

    # ログ状況
    print("\n📊 ログ状況:")
    logs_status = check_logs()
    print(f"   ログファイル数: {logs_status['count']}")

    if logs_status['logs']:
        print("   最新のログ:")
        for log in logs_status['logs'][:5]:
            type_icon = {"design": "📝", "codegen": "🔧", "test": "🧪"}.get(log['type'], "📄")
            print(f"     {type_icon} {log['name']} ({log['modified']})")

    # MCP実行ログ
    print("\n⚡ MCP実行履歴:")
    exec_log = check_mcp_exec_log()
    print(f"   実行回数: {exec_log['entries']}")

    if exec_log['recent']:
        print("   最近の実行:")
        for entry in exec_log['recent'][-5:]:
            status_icon = "✅" if entry['rc'] == 0 else "❌"
            print(f"     {status_icon} {entry['timestamp']} - {entry['goal']}")
            print(f"        $ {entry['cmd']}")

    # LLM設定
    print("\n🤖 LLM設定:")
    llm_config = check_llm_config()

    if llm_config['providers']:
        for provider in llm_config['providers']:
            enabled_icon = "🟢" if provider['enabled'] == '1' else "🔴" if provider['enabled'] == '0' else "❓"
            print(f"   {enabled_icon} {provider['name']}: {provider['model']}")
    else:
        print("   設定ファイルが見つからないか解析に失敗しました")

    # 環境変数チェック
    print("\n🌍 環境変数:")
    env_vars = ['PYTHONPATH', 'OLLAMA_HOST', 'GEMINI_API_KEY', 'HF_TOKEN']
    for var in env_vars:
        value = os.environ.get(var)
        icon = "✅" if value else "❌"
        display_value = value[:50] + "..." if value and len(value) > 50 else value or "未設定"
        print(f"   {icon} {var}: {display_value}")

    print("\n" + "=" * 50)
    print("💡 MCP使用方法:")
    print("   python3 simple_mcp_test.py projects/your_project  # プロジェクトテスト")
    print("   python3 services/mcp/cmd_exec.py --cmd 'ls -la'   # コマンド実行")
    print("   詳細: docs/MCP_GUIDE.md を参照")


if __name__ == "__main__":
    main()
