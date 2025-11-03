#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_discord_remo.py

Discord Bot + Nature Remo 統合テスト
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# プロジェクトルートをPYTHONPATHに追加
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def test_remo_control():
    """Nature Remo制御テスト"""
    print("=" * 60)
    print("Discord Bot + Nature Remo 統合テスト")
    print("=" * 60)

    # 環境変数確認
    print("\n📋 環境変数確認:")
    discord_token = os.getenv('DISCORD_BOT_TOKEN')
    remo_api = os.getenv('REMO_API')

    print(f"  DISCORD_BOT_TOKEN: {'✅ 設定済み' if discord_token else '❌ 未設定'}")
    print(f"  REMO_API: {'✅ 設定済み' if remo_api else '❌ 未設定'}")

    if not remo_api:
        print("\n❌ REMO_APIが設定されていません")
        return

    # Nature Remo Controller テスト
    print("\n🏠 Nature Remo Controller テスト:")
    from services.discord.plugins.remo_plugin import NatureRemoController

    controller = NatureRemoController(remo_api)

    # 家電一覧取得
    print("\n  📋 家電一覧取得中...")
    appliances = controller.get_appliances()

    if not appliances:
        print("  ❌ 家電の取得に失敗しました")
        return

    print(f"  ✅ {len(appliances)}個の家電を取得")

    # 照明検索
    print("\n  🔍 TAKIZUMI 照明検索中...")
    light = controller.find_appliance("LIGHT", "TAKIZUMI")

    if not light:
        print("  ❌ TAKIZUMI が見つかりません")
        print("\n  💡 利用可能な照明:")
        for app in appliances:
            if app.get('type') == 'LIGHT':
                print(f"    - {app.get('nickname')}")
        return

    print(f"  ✅ {light.get('nickname')} を検出")

    # ボタン一覧
    buttons = controller.get_light_buttons(light)
    print(f"\n  🎯 利用可能なボタン ({len(buttons)}個):")
    for btn in buttons:
        print(f"    - {btn.get('label')} ({btn.get('name')})")

    # ON/OFFテスト
    print("\n" + "=" * 60)
    response = input("照明制御テストを実行しますか？ (y/N): ")

    if response.lower() == 'y':
        print("\n🔆 照明ON テスト:")
        success, message = controller.light_on("TAKIZUMI")
        print(f"  {'✅' if success else '❌'} {message}")

        input("\nEnterキーを押して続行（OFFテスト）...")

        print("\n🌙 照明OFF テスト:")
        success, message = controller.light_off("TAKIZUMI")
        print(f"  {'✅' if success else '❌'} {message}")
    else:
        print("テストをスキップしました")

    print("\n✅ テスト完了")


async def test_discord_commands():
    """Discordコマンド登録確認"""
    print("\n" + "=" * 60)
    print("Discord コマンド登録確認")
    print("=" * 60)

    # Discord Botプロセス確認
    import subprocess
    result = subprocess.run(
        ["wsl", "bash", "-c", "ps aux | grep 'python3.*bot_core.py' | grep -v grep"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0 and result.stdout.strip():
        print("\n✅ Discord Bot起動中:")
        print(f"  {result.stdout.strip()}")
    else:
        print("\n⚠️ Discord Botが起動していません")
        print("\n起動コマンド:")
        print("  wsl bash -c \"cd /mnt/c/Users/kenny/sandbox/NeuroHub && source venv_linux/bin/activate && python3 services/discord/bot_core.py\"")

    print("\n📝 Discordチャンネルでテストしてください:")
    print("  !remo              # ヘルプ表示")
    print("  !remo devices      # 家電一覧")
    print("  !remo light on     # 照明ON")
    print("  !remo light off    # 照明OFF")


async def main():
    """メイン処理"""
    try:
        await test_remo_control()
        await test_discord_commands()
    except KeyboardInterrupt:
        print("\n\n⚠️ テスト中断")
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
