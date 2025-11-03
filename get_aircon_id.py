#!/usr/bin/env python3
import os
from urllib.request import urlopen, Request
from json import loads
from dotenv import load_dotenv

load_dotenv()
key = os.getenv('REMO_API')
url = 'https://api.nature.global/1/appliances'
req = Request(url, headers={'Authorization': f'Bearer {key}'})
apps = loads(urlopen(req).read().decode())

print("\n=== エアコン一覧 ===")
for app in apps:
    if app.get('type') == 'AC':
        print(f"家電: {app.get('nickname'):15s} ID: {app.get('id')}")
