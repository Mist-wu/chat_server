import requests
from bs4 import BeautifulSoup, FeatureNotFound
import time

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

URLS = [
    "http://www.weather.com.cn/textFC/hb.shtml",
    "http://www.weather.com.cn/textFC/db.shtml",
    "http://www.weather.com.cn/textFC/hd.shtml",
    "http://www.weather.com.cn/textFC/hz.shtml",
    "http://www.weather.com.cn/textFC/hn.shtml",
    "http://www.weather.com.cn/textFC/xb.shtml",
    "http://www.weather.com.cn/textFC/xn.shtml",
]

# 用于存储天气数据的全局缓存
_weather_data_cache = {}

def make_soup(html: str) -> BeautifulSoup:
    for parser in ("html5lib", "lxml", "html.parser"):
        try:
            return BeautifulSoup(html, parser)
        except FeatureNotFound:
            continue
    raise RuntimeError("未找到可用的 HTML 解析器，请安装 html5lib 或 lxml。")

def _fetch_all_weather_data():
    """
    一次性爬取所有地区的天气数据并返回一个字典。
    """
    all_data = {}
    for url in URLS:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.encoding = resp.apparent_encoding or "utf-8"
            text = resp.text
        except requests.exceptions.RequestException as e:
            print(f"请求 {url} 失败: {e}")
            continue

        soup = make_soup(text)
        div_conMidtab = soup.find("div", class_="conMidtab")
        if not div_conMidtab:
            continue

        tables = div_conMidtab.find_all("table")
        for table in tables:
            trs = table.find_all("tr")
            if len(trs) <= 2:
                continue
            
            for tr in trs[2:]:
                tds = tr.find_all("td")
                if len(tds) < 8:
                    continue

                try:
                    city = next(tds[-8].stripped_strings, "")
                    if not city:
                        continue

                    high_temp = next(tds[-5].stripped_strings, "-")
                    low_temp = next(tds[-2].stripped_strings, "-")
                    weather_day = next(tds[-7].stripped_strings, "-")
                    weather_night = next(tds[-4].stripped_strings, "-")
                    wind_day_parts = list(tds[-6].stripped_strings)
                    wind_night_parts = list(tds[-3].stripped_strings)

                    wind_day = "".join(wind_day_parts[:2]) if wind_day_parts else "--"
                    wind_night = "".join(wind_night_parts[:2]) if wind_night_parts else "--"
                    
                    final_low = low_temp if low_temp != "-" else high_temp
                    final_high = high_temp if high_temp != "-" else low_temp
                    
                    all_data[city] = {
                        "city": city,
                        "temp": f"{final_low}至{final_high}摄氏度",
                        "weather_type": weather_day if weather_day != "-" else weather_night,
                        "wind": wind_day if wind_day != "--" else wind_night,
                    }
                except Exception:
                    continue
    return all_data

def update_weather_cache():
    """
    获取最新的天气数据并更新全局缓存。
    """
    global _weather_data_cache
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 开始更新天气数据缓存...")
    new_data = _fetch_all_weather_data()
    if new_data:
        _weather_data_cache = new_data
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 天气缓存更新成功，共加载 {len(new_data)} 个城市的数据。")
    else:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 天气缓存更新失败，未能获取到数据。")

def get_weather(my_city: str):
    """
    从缓存中获取指定城市的天气数据。
    """
    return _weather_data_cache.get(my_city)
