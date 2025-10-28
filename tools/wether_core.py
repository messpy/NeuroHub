#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import yaml

LAT = 35.68
LON = 139.76
UA = "NeuroHub/1.0 (weather tool; contact: you@example.com)"
TIMEOUT = 10

def get_temperature(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m",
    }
    r = requests.get(url, params=params, timeout=TIMEOUT, headers={"User-Agent": UA})
    r.raise_for_status()
    current = r.json().get("current", {})
    return current.get("temperature_2m")

def reverse_geocode(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse"
    params = {
        "format": "jsonv2",
        "lat": lat,
        "lon": lon,
        "zoom": 10,
        "accept-language": "ja",
        "addressdetails": 1,
    }
    # User-Agent 必須
    r = requests.get(url, params=params, timeout=TIMEOUT, headers={"User-Agent": UA})
    r.raise_for_status()
    info = r.json()
    addr = info.get("address", {})

    # 市区町村の候補（存在チェック）
    city = (
        addr.get("city") or
        addr.get("town") or
        addr.get("village") or
        addr.get("municipality") or
        addr.get("suburb") or
        info.get("display_name")
    )

    # 緯度経度は str → float
    lat_num = float(info["lat"])
    lon_num = float(info["lon"])

    return {
        "location_name": city,
        "prefecture": addr.get("state"),
        "country": addr.get("country"),
        "latitude": lat_num,
        "longitude": lon_num,
    }

def main():
    result = {}

    try:
        result["temperature"] = float(get_temperature(LAT, LON))
    except Exception as e:
        result["temperature"] = None
        result["weather_error"] = str(e)

    try:
        result.update(reverse_geocode(LAT, LON))
    except Exception as e:
        result["geo_error"] = str(e)

    print(yaml.safe_dump(result, allow_unicode=True, sort_keys=False))


if __name__ == "__main__":
    main()

