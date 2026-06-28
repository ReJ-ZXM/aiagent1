"""天气工具 — 和风天气 API"""
import httpx
from langchain_core.tools import tool
from app.config import settings


@tool
async def get_weather(city: str, date: str = "") -> str:
    """查询天气。city: 城市名 (如"杭州")，date: 日期 (如"2026-06-29")。

    返回: JSON 字符串，包含天气、温度、风力等。
    """
    async with httpx.AsyncClient() as client:
        # 1. 城市搜索 → location_id
        geo_resp = await client.get("https://geoapi.qweather.com/v2/city/lookup", params={
            "key": settings.qweather_api_key,
            "location": city,
        })
        geo_data = geo_resp.json()
        loc_list = geo_data.get("location", [])
        if not loc_list:
            return str({"error": f"未找到城市: {city}"})

        location_id = loc_list[0]["id"]

        # 2. 天气预报
        weather_resp = await client.get("https://devapi.qweather.com/v7/weather/7d", params={
            "key": settings.qweather_api_key,
            "location": location_id,
        })
        weather_data = weather_resp.json()
        daily = weather_data.get("daily", [])
        if not daily:
            return str({"error": "天气数据不可用"})

        # 返回所有天的简要预报
        summary = []
        for d in daily[:7]:
            summary.append({
                "date": d.get("fxDate"),
                "weather": d.get("textDay"),
                "temp_high": f"{d.get('tempMax')}°C",
                "temp_low": f"{d.get('tempMin')}°C",
                "wind": d.get("windDirDay"),
            })
        return str(summary)
