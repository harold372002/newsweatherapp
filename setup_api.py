#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, json

def main():
    cd = os.path.join(os.path.expanduser("~"), ".newsweatherapp")
    cf = os.path.join(cd, "config.json")
    if os.path.exists(cf):
        try:
            with open(cf, "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            config = {}
    else:
        config = {}
    config.setdefault("city", "beijing")
    config.setdefault("city_id", "101010100")
    config.setdefault("news_provider", "newsapi")
    config.setdefault("tts_rate", 1.0)
    config.setdefault("tts_voice", "")
    config.setdefault("broadcast_mode", "mixed")
    config.setdefault("update_interval", 600)
    print("API Key Auto-Config Tool")
    eq = os.environ.get("QWEATHER_API_KEY", "")
    en = os.environ.get("NEWSAPI_KEY", "")
    if eq and not config.get("qweather_api_key"):
        config["qweather_api_key"] = eq
        print("QWeather: env var")
    elif not config.get("qweather_api_key"):
        k = input("QWeather Key (Enter to skip): ").strip()
        if k:
            config["qweather_api_key"] = k
            print("QWeather: set")
    else:
        print("QWeather: exists")
    if en and not config.get("newsapi_key"):
        config["newsapi_key"] = en
        print("NewsAPI: env var")
    elif not config.get("newsapi_key"):
        k = input("NewsAPI Key (Enter to skip): ").strip()
        if k:
            config["newsapi_key"] = k
            print("NewsAPI: set")
    else:
        print("NewsAPI: exists")
    os.makedirs(cd, exist_ok=True)
    with open(cf, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    print("Saved: " + cf)

if __name__ == "__main__":
    main()
