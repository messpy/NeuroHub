#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
weather_agent.py
- 引数なし → IP から位置推定
- 現在天気（気温＋天気コード→日本語＋絵文字）
- 時間予報 / 日次予報に対応
- YAML / JSON 出力
- 保存は --output 時のみ（自動命名）
- APIキー不要（Open-Meteo + ip-api + Nominatim）
"""

import sys
import argparse
import datetime
from typing import Dict, Any, Optional
import requests
import yaml
import json
import re
from pathlib import Path

UA = "NeuroHubWeather/1.0"
TIMEOUT = 8

# Weather code mapping
WEATHER_CODE = {
    0: "快晴 ☀️",
    1: "晴れ 🌤️",
    2: "薄曇り ⛅",
    3: "曇り ☁️",
    45: "霧 🌫️",
    48: "着氷性霧 🌫️🧊",
    51: "霧雨(弱) 🌦️",
    53: "霧雨(中) 🌦",
    55: "霧雨(強) 🌧",
    61: "雨(弱) 🌧",
    63: "雨(中) 🌧",
    65: "雨(強) 🌧🌧",
    71: "雪(弱) ❄️",
    73: "雪(中) ❄️❄️",
    75: "雪(強) ❄️❄️❄️",
    80: "にわか雨(弱) 🌦",
    81: "にわか雨(中) 🌧",
    82: "にわか雨(強) 🌧🌧",
    95: "雷雨 ⛈️",
    96: "雷雨(氷粒) ⛈️🧊",
    99: "雷雨(氷粒 強) ⛈️🧊🧊"
}

#========================
# Util
#========================

def geolocate_by_ip(lang="ja") -> Dict[str, Any]:
    headers = {"User-Agent": UA}
    try:
        r = requests.get("http://ip-api.com/json", headers=headers, timeout=TIMEOUT)
        if r.ok:
            j = r.json()
            if j.get("status") == "success":
                return {
                    "lat": float(j["lat"]),
                    "lon": float(j["lon"]),
                    "query_name": j.get("city"),
                    "admin1": j.get("regionName"),
                    "country": j.get("country"),
                    "lang": lang,
                    "ip_geo": {
                        "source": "ip-api.com",
                        "ip": j.get("query"),
                        "city": j.get("city"),
                        "region": j.get("regionName"),
                        "org": j.get("org"),
                        "asn": j.get("as"),
                        "scope": "external-ip"
                    }
                }
    except:
        pass
    raise RuntimeError("IP位置推定に失敗（ip-api.com）")


def forward_geocode(place: str, lang="ja") -> Optional[Dict[str, Any]]:
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": place, "language": lang}
    r = requests.get(url, params=params, timeout=TIMEOUT)
    if not r.ok:
        return None
    results = r.json().get("results")
    return results[0] if results else None


def reverse_geocode(lat: float, lon: float, lang="ja") -> Dict[str, Any]:
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "jsonv2",
        "lat": lat,
        "lon": lon,
        "zoom": 10,
        "addressdetails": 1,
        "accept-language": lang,
    }
    headers = {"User-Agent": UA}
    r = requests.get(url, params=params, timeout=TIMEOUT, headers=headers)
    r.raise_for_status()
    info = r.json()
    addr = info.get("address", {})

    city = addr.get("city") or addr.get("town") or addr.get("village") or \
           addr.get("suburb") or info.get("display_name")

    return {
        "location_name": city,
        "prefecture": addr.get("state"),
        "country": addr.get("country"),
        "latitude": float(info["lat"]),
        "longitude": float(info["lon"]),
    }


def fetch_weather(lat, lon, unit="c", forecast=None, hours=24, days=3):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "weather_code,temperature_2m",
        "timezone": "Asia/Tokyo",
    }
    if unit.lower() == "f":
        params["temperature_unit"] = "fahrenheit"

    if forecast == "hourly":
        params["hourly"] = "weather_code,temperature_2m"
    elif forecast == "daily":
        params["daily"] = "weather_code,temperature_2m_max,temperature_2m_min"

    url = "https://api.open-meteo.com/v1/forecast"
    r = requests.get(url, params=params, timeout=TIMEOUT)
    r.raise_for_status()
    j = r.json()

    wcode = j["current"].get("weather_code")

    res = {
        "current_time": j["current"].get("time"),
        "temperature": j["current"].get("temperature_2m"),
        "weather_code": wcode,
        "weather": WEATHER_CODE.get(wcode, "不明")
    }

    if forecast == "hourly":
        res["hourly"] = {
            "time": j["hourly"].get("time")[:hours],
            "temp": j["hourly"].get("temperature_2m")[:hours],
            "weather_code": j["hourly"].get("weather_code")[:hours],
        }

    if forecast == "daily":
        res["daily"] = {
            "date": j["daily"].get("time")[:days],
            "tmax": j["daily"].get("temperature_2m_max")[:days],
            "tmin": j["daily"].get("temperature_2m_min")[:days],
            "weather_code": j["daily"].get("weather_code")[:days],
        }

    return res

#========================
# Main
#========================

def resolve_location(args) -> Dict[str, Any]:
    if args.lat and args.lon:
        return {"lat": args.lat, "lon": args.lon, "lang": args.lang}

    if args.place:
        info = forward_geocode(args.place, lang=args.lang)
        if not info:
            raise RuntimeError(f"場所が見つからない: {args.place}")
        return {
            "lat": float(info["latitude"]),
            "lon": float(info["longitude"]),
            "query_name": info.get("name"),
            "lang": args.lang,
        }

    return geolocate_by_ip(lang=args.lang)


def build_filename(meta, w) -> str:
    name = meta.get("location_name", "Unknown")
    name = re.sub(r"[^A-Za-z0-9]+", "_", str(name))[:20]
    now = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"weather_{name}_{now}.yaml"


def output(meta, w, args):
    out = {}
    out.update(meta)
    out.update(w)

    text = yaml.safe_dump(out, allow_unicode=True, sort_keys=False) \
        if not args.json else json.dumps(out, ensure_ascii=False, indent=2)

    print(text)

    if args.output:
        out_dir = Path(args.output_dir).expanduser()
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / build_filename(meta, w)
        path.write_text(text, encoding="utf-8")
        print(f"[saved] {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("place", nargs="?", help="都市名")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--unit", choices=["c", "f"], default="c")
    ap.add_argument("--lang", default="ja")

    ap.add_argument("--forecast", choices=["hourly", "daily"])
    ap.add_argument("--hours", type=int, default=24)
    ap.add_argument("--days", type=int, default=3)

    ap.add_argument("--json", action="store_true")
    ap.add_argument("--output", action="store_true")
    ap.add_argument("--output-dir", default="./weather_logs")

    args = ap.parse_args()

    loc = resolve_location(args)
    lat, lon = loc["lat"], loc["lon"]

    w = fetch_weather(lat, lon, unit=args.unit,
                      forecast=args.forecast, hours=args.hours, days=args.days)

    try:
        meta = reverse_geocode(lat, lon, lang=args.lang)
    except Exception:
        meta = {
            "location_name": loc.get("query_name", None),
            "latitude": lat, "longitude": lon,
            "prefecture": None, "country": None,
        }

    if "ip_geo" in loc:
        meta["ip_geo"] = loc["ip_geo"]

    output(meta, w, args)


if __name__ == "__main__":
    main()

