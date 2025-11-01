#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
simple_mcp_test.py - LLMを使わないシンプルなMCPテスト
"""

import subprocess
import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def run_command(cmd: str, cwd: str, timeout: int = 60) -> Tuple[int, str, str]:
    """コマンドを実行して結果を返す"""
    try:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return proc.returncode, proc.stdout or "", proc.stderr or ""
    except subprocess.TimeoutExpired:
        return 124, "", "Command timed out"
    except Exception as e:
        return 1, "", str(e)

def test_mcp_tool(project_dir: str, test_specs: List[Dict]) -> Dict:
    """MCPツールをテストする"""
    results = []
    status = "success"

    print(f"Testing MCP tool in: {project_dir}")
    print("=" * 60)

    for test_spec in test_specs:
        test_name = test_spec.get("name", "unknown")
        cmd = test_spec.get("cmd", "")
        expect_rc = int(test_spec.get("expect_rc", "0"))

        print(f"\n🧪 Test: {test_name}")
        print(f"   Command: {cmd}")

        rc, stdout, stderr = run_command(cmd, project_dir)

        success = (rc == expect_rc)
        if not success:
            status = "failed"

        result = {
            "name": test_name,
            "cmd": cmd,
            "expected_rc": expect_rc,
            "actual_rc": rc,
            "success": success,
            "stdout": stdout[:1000],  # 最初の1000文字のみ
            "stderr": stderr[:500]    # 最初の500文字のみ
        }
        results.append(result)

        # 結果表示
        status_icon = "✅" if success else "❌"
        print(f"   Result: {status_icon} RC={rc} (expected {expect_rc})")

        if stdout.strip():
            print(f"   Output: {stdout[:200]}{'...' if len(stdout) > 200 else ''}")
        if stderr.strip():
            print(f"   Error: {stderr[:200]}{'...' if len(stderr) > 200 else ''}")

    print("\n" + "=" * 60)
    print(f"Overall Status: {'✅ SUCCESS' if status == 'success' else '❌ FAILED'}")

    return {
        "status": status,
        "results": results,
        "summary": {
            "total_tests": len(results),
            "passed": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]])
        }
    }

def check_keywords_and_patterns(output_text: str, keywords: List[str], patterns: List[str]) -> Dict:
    """キーワードとパターンをチェック"""
    analysis = {
        "keywords_found": [],
        "keywords_missing": [],
        "patterns_matched": [],
        "patterns_failed": []
    }

    # キーワードチェック
    for keyword in keywords:
        if keyword.lower() in output_text.lower():
            analysis["keywords_found"].append(keyword)
        else:
            analysis["keywords_missing"].append(keyword)

    # 正規表現パターンチェック
    for pattern in patterns:
        try:
            if re.search(pattern, output_text):
                analysis["patterns_matched"].append(pattern)
            else:
                analysis["patterns_failed"].append(pattern)
        except re.error:
            analysis["patterns_failed"].append(f"{pattern} (invalid regex)")

    return analysis

def main():
    """メイン関数"""
    if len(sys.argv) != 2:
        print("Usage: python simple_mcp_test.py <project_directory>")
        sys.exit(1)

    project_dir = Path(sys.argv[1]).resolve()

    if not project_dir.exists():
        print(f"Error: Project directory not found: {project_dir}")
        sys.exit(1)

    # デフォルトテストケース
    default_tests = [
        {"name": "help", "cmd": "python3 main.py --help", "expect_rc": "0"},
        {"name": "run", "cmd": "python3 main.py", "expect_rc": "0"},
        {"name": "count", "cmd": "python3 main.py --count", "expect_rc": "0"},
        {"name": "filter_py", "cmd": "python3 main.py --filter .py", "expect_rc": "0"},
        {"name": "json_format", "cmd": "python3 main.py --format json", "expect_rc": "0"}
    ]

    # テスト実行
    print(f"🚀 Starting MCP Tool Test")
    print(f"Project: {project_dir}")
    print(f"Working Directory: {os.getcwd()}")

    try:
        result = test_mcp_tool(str(project_dir), default_tests)

        # 詳細結果の保存
        result_file = project_dir / "test_results.json"
        with result_file.open("w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        print(f"\n📄 Detailed results saved to: {result_file}")

        # 終了コード
        sys.exit(0 if result["status"] == "success" else 1)

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
