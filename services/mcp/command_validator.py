#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
services/mcp/command_validator.py

禁止コマンド検知と代替案提示モジュール
"""

from typing import Dict, List, Optional, Tuple
import re


class CommandValidator:
    """禁止コマンド検証クラス"""
    
    # 禁止コマンドと代替案のマッピング
    FORBIDDEN_COMMANDS = {
        "rm -rf": {
            "reason": "危険な削除コマンド",
            "alternatives": [
                "特定ファイル削除: rm <filename>",
                "ディレクトリ削除: rmdir <dirname>（空の場合のみ）",
                "Pythonで削除: os.remove() または shutil.rmtree()"
            ]
        },
        "chmod 777": {
            "reason": "セキュリティリスクのある権限設定",
            "alternatives": [
                "適切な権限: chmod 755 <file>（実行可能）",
                "読み書きのみ: chmod 644 <file>",
                "Pythonで設定: os.chmod(<file>, 0o755)"
            ]
        },
        "sudo su": {
            "reason": "不必要なroot権限昇格",
            "alternatives": [
                "特定コマンドのみsudo: sudo <command>",
                "Pythonで実行: subprocess.run(['sudo', '<command>'])"
            ]
        },
        "dd if=/dev/zero": {
            "reason": "データ破壊の可能性",
            "alternatives": [
                "ファイル作成: touch <filename>",
                "Pythonで作成: open(<filename>, 'w').close()"
            ]
        },
        "mkfs": {
            "reason": "ファイルシステム初期化（データ消失）",
            "alternatives": [
                "ディレクトリ作成: mkdir <dirname>",
                "Pythonで作成: os.makedirs(<dirname>)"
            ]
        },
        ":(){ :|:& };:": {
            "reason": "Fork爆弾（システム破壊）",
            "alternatives": [
                "並列処理: multiprocessing モジュール使用",
                "非同期処理: asyncio モジュール使用"
            ]
        }
    }
    
    # 危険なパターン（正規表現）
    DANGEROUS_PATTERNS = [
        (r"rm\s+-rf\s+/", "ルートディレクトリの削除"),
        (r"chmod\s+777\s+/", "ルートディレクトリの権限変更"),
        (r">\s*/dev/sd[a-z]", "ディスクへの直接書き込み"),
        (r"mv\s+/\w+\s+/dev/null", "システムディレクトリの削除"),
    ]
    
    def __init__(self):
        """初期化"""
        self.violation_log = []
    
    def validate_command(self, command: str) -> Tuple[bool, Optional[Dict]]:
        """
        コマンドを検証し、禁止コマンドをチェック
        
        Args:
            command: 検証するコマンド文字列
            
        Returns:
            (is_safe, violation_info)
            - is_safe: Trueなら安全、Falseなら禁止コマンド検出
            - violation_info: 違反情報（禁止コマンド、理由、代替案）
        """
        # 禁止コマンドの完全一致チェック
        for forbidden, info in self.FORBIDDEN_COMMANDS.items():
            if forbidden in command:
                violation = {
                    "command": forbidden,
                    "reason": info["reason"],
                    "alternatives": info["alternatives"],
                    "original_command": command
                }
                self._log_violation(violation)
                return False, violation
        
        # 危険なパターンチェック
        for pattern, reason in self.DANGEROUS_PATTERNS:
            if re.search(pattern, command):
                violation = {
                    "command": command,
                    "reason": reason,
                    "alternatives": ["安全な方法を検討してください"],
                    "original_command": command
                }
                self._log_violation(violation)
                return False, violation
        
        return True, None
    
    def suggest_alternative(self, command: str) -> Optional[List[str]]:
        """
        禁止コマンドに対する代替案を提示
        
        Args:
            command: 検証するコマンド
            
        Returns:
            代替案リスト（安全な場合はNone）
        """
        is_safe, violation = self.validate_command(command)
        
        if not is_safe and violation:
            return violation["alternatives"]
        
        return None
    
    def _log_violation(self, violation: Dict):
        """違反ログ記録"""
        self.violation_log.append(violation)
    
    def get_violation_report(self) -> str:
        """違反レポート生成"""
        if not self.violation_log:
            return "✅ 違反なし"
        
        report = "⚠️ 禁止コマンド検出レポート\n"
        report += "=" * 60 + "\n"
        
        for i, violation in enumerate(self.violation_log, 1):
            report += f"\n違反 {i}:\n"
            report += f"  コマンド: {violation['command']}\n"
            report += f"  理由: {violation['reason']}\n"
            report += f"  代替案:\n"
            for alt in violation['alternatives']:
                report += f"    - {alt}\n"
        
        return report
    
    def validate_code_snippet(self, code: str) -> List[Dict]:
        """
        コードスニペット内の全コマンドを検証
        
        Args:
            code: Pythonコードまたはシェルスクリプト
            
        Returns:
            違反リスト
        """
        violations = []
        
        # subprocess/os.systemコール検出
        subprocess_pattern = r"subprocess\.(run|call|Popen)\(\s*['\"]([^'\"]+)['\"]"
        os_system_pattern = r"os\.system\(\s*['\"]([^'\"]+)['\"]"
        
        for match in re.finditer(subprocess_pattern, code):
            command = match.group(2)
            is_safe, violation = self.validate_command(command)
            if not is_safe:
                violations.append(violation)
        
        for match in re.finditer(os_system_pattern, code):
            command = match.group(1)
            is_safe, violation = self.validate_command(command)
            if not is_safe:
                violations.append(violation)
        
        return violations


# 使用例とテスト
if __name__ == "__main__":
    validator = CommandValidator()
    
    # テストコマンド
    test_commands = [
        "ls -la",  # 安全
        "rm -rf /tmp/test",  # 危険
        "chmod 777 /var/www",  # 危険
        "sudo apt update",  # 安全
        "dd if=/dev/zero of=/dev/sda",  # 非常に危険
        "python script.py",  # 安全
    ]
    
    print("=== コマンド検証テスト ===\n")
    
    for cmd in test_commands:
        print(f"コマンド: {cmd}")
        is_safe, violation = validator.validate_command(cmd)
        
        if is_safe:
            print("✅ 安全なコマンドです")
        else:
            print(f"❌ 禁止コマンド検出: {violation['reason']}")
            print("代替案:")
            for alt in violation['alternatives']:
                print(f"  - {alt}")
        
        print("-" * 60 + "\n")
    
    # 違反レポート
    print(validator.get_violation_report())
    
    # コードスニペットテスト
    print("\n=== コードスニペット検証 ===\n")
    
    test_code = '''
import subprocess
import os

subprocess.run("rm -rf /tmp/test", shell=True)
os.system("chmod 777 /var/www")
subprocess.run("ls -la", shell=True)
'''
    
    violations = validator.validate_code_snippet(test_code)
    
    if violations:
        print(f"⚠️ {len(violations)}件の違反を検出:")
        for v in violations:
            print(f"  - {v['command']}: {v['reason']}")
    else:
        print("✅ 違反なし")
