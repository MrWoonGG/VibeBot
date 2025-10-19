import requests
import config

def validate_city(city_name: str):
    url = "https://api.opencagedata.com/geocode/v1/json"
    params = {
        "q": city_name,
        "key": config.OPENCAGE_TOKEN,
        "language": "ru",
        "no_annotations": 1,
        "limit": 1
    }

    if config.DEBUG:
        print(f"[DEBUG] Отправка запроса в OpenCage для: {city_name}")

    try:
        resp = requests.get(url, params=params)
        if resp.status_code != 200:
            if config.DEBUG:
                print(f"[DEBUG] Ошибка ответа от API: {resp.status_code}")
            return None
    except Exception as e:
        if config.DEBUG:
            print(f"[DEBUG] Ошибка при запросе: {e}")
        return None

    data = resp.json()
    if not data.get("results"):
        if config.DEBUG:
            print("[DEBUG] Ничего не найдено по этому запросу")
        return None

    comp = data["results"][0].get("components", {})

    city = comp.get("_normalized_city") or comp.get("city") or comp.get("town") or comp.get("village")
    country = comp.get("country")
    country_code = comp.get("country_code")

    if not city or not country:
        if config.DEBUG:
            print("[DEBUG] Город или страна отсутствует в результатах")
        return None

    if config.DEBUG:
        print(f"[DEBUG] Найдено: {city}, {country} ({country_code.upper()})")

    return {
        "city": city,
        "country": country,
        "country_code": country_code.upper() if country_code else None
    }
