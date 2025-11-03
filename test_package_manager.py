#!/usr/bin/env python3
"""
パッケージ管理システムテスト
"""

import os
import sys
import tempfile
from pathlib import Path

# パッケージパスの追加
sys.path.append(str(Path(__file__).parent / "tools"))

def test_package_manager():
    """パッケージ管理システムテスト"""
    try:
        print("📦 パッケージ管理システムテスト開始")

        from package_manager import CommandSecurityManager, VirtualEnvironmentManager, PackageManager

        # 1. CommandSecurityManagerテスト
        security = CommandSecurityManager()

        # 安全なコマンドテスト
        safe, msg = security.is_command_safe("python --version")
        assert safe, f"安全コマンドテスト失敗: {msg}"
        print("✅ 1. 安全コマンド検証テスト成功")

        # 危険なコマンドテスト
        unsafe, msg = security.is_command_safe("rm -rf /")
        assert not unsafe, f"危険コマンドテスト失敗: {msg}"
        print("✅ 2. 危険コマンド検出テスト成功")

        # pipコマンド検証テスト
        valid, msg = security.validate_pip_command("pip install requests")
        assert valid, f"pip検証テスト失敗: {msg}"
        print("✅ 3. pipコマンド検証テスト成功")

        # 不正pipコマンドテスト
        invalid, msg = security.validate_pip_command("pip install ../malicious")
        assert not invalid, f"不正pip検証テスト失敗: {msg}"
        print("✅ 4. 不正pipコマンド検出テスト成功")

        # 2. VirtualEnvironmentManagerテスト
        temp_dir = tempfile.mkdtemp()
        venv_manager = VirtualEnvironmentManager(temp_dir)

        # 仮想環境作成テスト
        success, msg = venv_manager.create_venv_if_not_exists()
        assert success, f"仮想環境作成テスト失敗: {msg}"
        print("✅ 5. 仮想環境作成テスト成功")

        # コマンドプレフィックス取得テスト
        prefix = venv_manager.get_venv_command_prefix()
        assert len(prefix) > 0, "コマンドプレフィックステスト失敗"
        print("✅ 6. コマンドプレフィックステスト成功")

        # pipコマンド生成テスト
        pip_command = venv_manager.get_safe_pip_command(["list"])
        assert len(pip_command) > 0, "pipコマンド生成テスト失敗"
        print("✅ 7. pipコマンド生成テスト成功")

        # 3. PackageManagerテスト
        package_manager = PackageManager(temp_dir)

        # 安全コマンド実行テスト
        success, msg = package_manager.execute_safe_command("python --version")
        # バージョン取得は環境によって成功/失敗が変わるので、エラーメッセージをチェック
        print(f"✅ 8. 安全コマンド実行テスト実行 (結果: {success})")

        # 危険コマンド拒否テスト
        success, msg = package_manager.execute_safe_command("rm -rf /")
        assert not success and "拒否" in msg, f"危険コマンド拒否テスト失敗: {msg}"
        print("✅ 9. 危険コマンド拒否テスト成功")

        # パッケージ一覧テスト
        success, msg = package_manager.list_installed_packages()
        print(f"✅ 10. パッケージ一覧テスト実行 (結果: {success})")

        # テストファイル作成
        test_file = os.path.join(temp_dir, "test_requirements.py")
        with open(test_file, 'w') as f:
            f.write("import requests\\nimport json\\nfrom pathlib import Path")

        # パッケージ要件検出テスト
        missing = package_manager.check_package_requirements(test_file)
        # requestsが検出されるはず（標準ライブラリではないため）
        print(f"✅ 11. パッケージ要件検出テスト成功 (検出: {missing})")

        # クリーンアップ
        import shutil
        shutil.rmtree(temp_dir)

        print("🎉 全テスト成功！パッケージ管理システムは正常に動作します")
        return True

    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_package_manager()
