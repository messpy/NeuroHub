#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_remo_local.py

Nature Remo ローカルAPI 照明制御テスト
ローカルネットワーク経由で直接赤外線信号を送信
"""

import os
import sys
import json
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from dotenv import load_dotenv

# .env読み込み
load_dotenv()

# Nature Remo Cloud API設定（デバイス情報取得用）
REMO_API_KEY = os.getenv('REMO_API')
CLOUD_API_URL = "https://api.nature.global/1/"

# ローカルAPI設定
REMO_LOCAL_IP = None  # 自動検出または手動設定


def print_header(title):
    """ヘッダー表示"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def get_remo_devices():
    """Cloud API経由でRemoデバイス一覧を取得"""
    print_header("🌐 Remoデバイス情報取得（Cloud API）")

    try:
        url = f"{CLOUD_API_URL}devices"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            devices = json.loads(response.read().decode())

        print(f"✅ デバイス取得成功: {len(devices)}台")

        for i, device in enumerate(devices, 1):
            name = device.get('name', '不明')
            firmware = device.get('firmware_version', '不明')
            mac = device.get('mac_address', '不明')
            local_ip = device.get('newest_events', {}).get('te', {}).get('val', 'N/A')

            print(f"\n{i}. {name}")
            print(f"   MAC: {mac}")
            print(f"   ファームウェア: {firmware}")
            print(f"   温度: {local_ip}°C (最新イベント)")

        return devices

    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def discover_remo_local():
    """ローカルネットワーク上のRemoを検出"""
    print_header("🔍 Remo ローカルIP検出")

    # 一般的なローカルIPレンジをスキャン
    # 実際の環境に合わせて調整してください
    ip_ranges = [
        "192.168.1.",
        "192.168.0.",
        "192.168.11.",
        "10.0.1.",
    ]

    print("⏳ ローカルネットワークをスキャン中...")
    print("   (この処理には時間がかかる場合があります)")

    found_devices = []

    for ip_prefix in ip_ranges:
        print(f"\n🔎 {ip_prefix}* をスキャン中...")

        for i in range(1, 255):
            ip = f"{ip_prefix}{i}"

            try:
                # ローカルAPIのエンドポイントにアクセス
                url = f"http://{ip}/messages"
                headers = {"X-Requested-With": "curl"}

                request = Request(url, headers=headers)
                request.timeout = 0.5  # タイムアウト短縮

                with urlopen(request, timeout=0.5) as response:
                    if response.status == 200:
                        print(f"✅ Remo検出: {ip}")
                        found_devices.append(ip)

            except (HTTPError, URLError, TimeoutError):
                # タイムアウトやエラーは無視
                pass
            except Exception:
                pass

    if found_devices:
        print(f"\n✅ {len(found_devices)}台のRemoを検出:")
        for ip in found_devices:
            print(f"   - {ip}")
        return found_devices[0]  # 最初に見つかったデバイス
    else:
        print("\n❌ Remoが見つかりませんでした")
        print("\n💡 手動でIPアドレスを指定してください:")
        print("   例: REMO_LOCAL_IP = '192.168.1.10'")
        return None


def get_latest_signal(remo_ip):
    """最新の受信赤外線信号を取得"""
    print_header(f"📡 最新の赤外線信号取得: {remo_ip}")

    try:
        url = f"http://{remo_ip}/messages"
        headers = {"X-Requested-With": "curl"}

        request = Request(url, headers=headers)
        with urlopen(request, timeout=5) as response:
            signal = json.loads(response.read().decode())

        print("✅ 信号取得成功:")
        print(f"   周波数: {signal.get('freq')} kHz")
        print(f"   フォーマット: {signal.get('format')}")
        print(f"   データ長: {len(signal.get('data', []))} ポイント")

        return signal

    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def send_ir_signal(remo_ip, signal):
    """赤外線信号を送信"""
    print_header(f"📤 赤外線信号送信: {remo_ip}")

    try:
        url = f"http://{remo_ip}/messages"
        headers = {
            "X-Requested-With": "curl",
            "Content-Type": "application/json",
            "Expect": ""  # curlの-H "Expect: "に相当
        }

        # JSONデータ
        data = json.dumps(signal).encode()

        print(f"📊 送信データ:")
        print(f"   周波数: {signal.get('freq')} kHz")
        print(f"   データ長: {len(signal.get('data', []))} ポイント")

        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request, timeout=5) as response:
            result = response.read().decode()

        print("✅ 信号送信成功")
        return True

    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        print(f"   詳細: {e.read().decode()}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def get_light_signals_from_cloud():
    """Cloud API経由で照明のON/OFF信号を取得"""
    print_header("☁️ 照明信号取得（Cloud API）")

    try:
        # 家電一覧取得
        url = f"{CLOUD_API_URL}appliances"
        headers = {"Authorization": f"Bearer {REMO_API_KEY}"}

        request = Request(url, headers=headers)
        with urlopen(request) as response:
            appliances = json.loads(response.read().decode())

        # TAKIZUMIを検索
        light = None
        for appliance in appliances:
            if appliance.get('type') == 'LIGHT' and appliance.get('nickname') == 'TAKIZUMI':
                light = appliance
                break

        if not light:
            print("❌ TAKIZUMI が見つかりません")
            return None

        print(f"✅ 照明検出: {light.get('nickname')}")

        # ボタン一覧
        light_data = light.get('light', {})
        buttons = light_data.get('buttons', [])

        print(f"\n🎯 利用可能なボタン ({len(buttons)}個):")
        for btn in buttons:
            print(f"   - {btn.get('label')} (name: {btn.get('name')})")

        # ON/OFFボタンを取得
        signals = {}
        for btn in buttons:
            name = btn.get('name', '')
            label = btn.get('label', '')

            if name in ['on', 'off']:
                # ボタンのイメージ（赤外線信号）を取得
                image = btn.get('image', '')
                if image:
                    signals[name] = {
                        'label': label,
                        'image': image
                    }
                    print(f"\n✅ {label} (name: {name})")
                    print(f"   Image ID: {image[:20]}...")

        return signals

    except Exception as e:
        print(f"❌ エラー: {e}")
        return None


def test_light_control(remo_ip):
    """照明制御テスト（ローカルAPI経由）"""
    print_header("💡 照明制御テスト")

    print("\n⚠️ 注意:")
    print("   ローカルAPIで赤外線信号を送信するには、")
    print("   事前に信号を学習・記録しておく必要があります。")
    print("\n📝 手順:")
    print("   1. Remoアプリで照明のON/OFFボタンを登録")
    print("   2. Cloud API経由で信号データを取得")
    print("   3. ローカルAPI経由で信号を送信")

    # Cloud API経由で信号データ取得を試みる
    signals = get_light_signals_from_cloud()

    if not signals:
        print("\n❌ Cloud APIからの信号取得に失敗しました")
        print("💡 代わりに、リモコンから信号を学習してください:")
        print("   1. リモコンをRemoに向けてボタンを押す")
        print("   2. GET /messagesで最新の受信信号を取得")
        print("   3. その信号をJSONファイルに保存")
        print("   4. POST /messagesで信号を再送信")
        return False

    # 実際の赤外線信号データは別途取得が必要
    print("\n💡 次のステップ:")
    print("   Cloud APIのsignalエンドポイントから実際の赤外線データを取得するか、")
    print("   Remoアプリで学習した信号を使用してください。")

    return True


def manual_ip_input():
    """手動でIPアドレスを入力"""
    print_header("🔧 手動IP設定")
    print("\n💡 RemoのIPアドレスを手動で入力してください:")
    print("   例: 192.168.1.10")

    ip = input("\nIPアドレス: ").strip()

    if ip:
        print(f"\n✅ IPアドレスを '{ip}' に設定しました")
        return ip
    else:
        print("\n❌ 入力がキャンセルされました")
        return None


def main():
    """メイン処理"""
    print("\n" + "=" * 60)
    print("  🏠 Nature Remo ローカルAPI テストスクリプト")
    print("=" * 60)

    # Cloud API経由でデバイス情報取得
    devices = get_remo_devices()

    # ローカルIPの設定方法を選択
    print("\n" + "=" * 60)
    print("RemoのローカルIPアドレス設定方法を選択してください:")
    print("  1. 自動検出（スキャン）")
    print("  2. 手動入力")
    print("=" * 60)

    choice = input("\n選択 (1/2): ").strip()

    remo_ip = None

    if choice == "1":
        # 自動検出
        remo_ip = discover_remo_local()
    elif choice == "2":
        # 手動入力
        remo_ip = manual_ip_input()
    else:
        print("❌ 無効な選択です")
        return

    if not remo_ip:
        print("\n❌ RemoのIPアドレスが設定されていません")
        print("💡 ルーターの管理画面でRemoのIPアドレスを確認してください")
        return

    # ローカルAPI接続確認
    print_header(f"🔌 ローカルAPI接続確認: {remo_ip}")

    try:
        url = f"http://{remo_ip}/messages"
        headers = {"X-Requested-With": "curl"}

        request = Request(url, headers=headers)
        with urlopen(request, timeout=5) as response:
            if response.status == 200:
                print("✅ ローカルAPI接続成功")
            else:
                print(f"⚠️ レスポンスコード: {response.status}")

    except Exception as e:
        print(f"❌ 接続失敗: {e}")
        print("\n💡 確認事項:")
        print("   - Remoが同じネットワークに接続されているか")
        print("   - ファイアウォールがHTTP通信を許可しているか")
        print("   - IPアドレスが正しいか")
        return

    # 最新の受信信号を取得
    signal = get_latest_signal(remo_ip)

    # 照明制御テスト
    test_light_control(remo_ip)

    print("\n" + "=" * 60)
    print("  ✅ テスト完了")
    print("=" * 60)

    print("\n📝 次のステップ:")
    print("   1. リモコンから照明のON/OFF信号を学習")
    print("   2. GET /messages で信号データを取得")
    print("   3. 信号データをJSONファイルに保存")
    print("   4. POST /messages で保存した信号を送信")
    print("\n💡 または、Cloud API経由で制御する方が簡単です:")
    print("   python3 test_nature_remo.py")


if __name__ == "__main__":
    main()
