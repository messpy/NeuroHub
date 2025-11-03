#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
send_learned_signal.py

学習した赤外線信号を送信
"""

import os
import sys
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError

# RemoローカルIP
REMO_LOCAL_IP = "192.168.3.3"


def send_signal(signal):
    """赤外線信号を送信"""
    try:
        url = f"http://{REMO_LOCAL_IP}/messages"
        headers = {
            "X-Requested-With": "curl",
            "Content-Type": "application/json"
        }
        
        data = json.dumps(signal).encode()
        
        request = Request(url, data=data, headers=headers, method='POST')
        with urlopen(request, timeout=5) as response:
            result = response.read().decode()
        
        return True
    
    except HTTPError as e:
        print(f"❌ HTTPエラー: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


def main():
    """メイン処理"""
    if len(sys.argv) < 2:
        print("\n使い方:")
        print("  python3 send_learned_signal.py on   # 照明ON")
        print("  python3 send_learned_signal.py off  # 照明OFF")
        return
    
    signal_name = sys.argv[1].lower()
    filename = f"light_{signal_name}.json"
    
    print(f"\n💡 {signal_name.upper()}信号送信")
    
    # 信号ファイル読み込み
    if not os.path.exists(filename):
        print(f"❌ 信号ファイルが見つかりません: {filename}")
        print(f"\n最初に信号を学習してください:")
        print(f"  python3 learn_light_signals.py")
        return
    
    with open(filename, 'r') as f:
        signal = json.load(f)
    
    print(f"📂 信号読み込み: {filename}")
    print(f"   周波数: {signal.get('freq')} kHz")
    print(f"   データ長: {len(signal.get('data', []))} ポイント")
    
    # 信号送信
    print(f"\n📤 信号送信中...")
    
    if send_signal(signal):
        print(f"✅ {signal_name.upper()}信号送信成功")
        print(f"💡 照明が{signal_name}しましたか？")
    else:
        print(f"❌ 送信失敗")


if __name__ == "__main__":
    main()
