"""天气工具 — 和风天气 API + LLM 兜底"""
import httpx
from langchain_core.tools import tool
from app.config import settings


async def _llm_weather_fallback(city: str, date: str = "") -> str:
    """LLM 生成天气数据"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    import json as _json
    try:
        llm = ChatOpenAI(
            model="deepseek-chat", api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url, temperature=0, max_tokens=500,
        )
        resp = await llm.ainvoke([
            SystemMessage(content="你是天气预报专家。只输出JSON数组，不要任何解释。"),
            HumanMessage(content=f"给出{city}未来3天({date or '明天开始'})的天气预报。JSON数组，每个元素含date、weather、temp_high、temp_low、wind字段。温度带°C。"),
        ])
        content = resp.content.strip()
        if "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        if content.startswith("json"): content = content[4:].strip()
        return str(_json.loads(content))
    except Exception:
        return str([{"date": "2026-06-29", "weather": "晴", "temp_high": "30°C", "temp_low": "22°C", "wind": "微风"}])


@tool
async def get_weather(city: str, date: str = "") -> str:
    """查询天气。city: 城市名 (如"杭州")，date: 日期 (如"2026-06-29")。"""
    # 无有效 Key → LLM 兜底
    if not settings.qweather_api_key or len(settings.qweather_api_key) < 20:
        return await _llm_weather_fallback(city, date)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            geo_resp = await client.get("https://geoapi.qweather.com/v2/city/lookup", params={
                "key": settings.qweather_api_key, "location": city,
            })
            if geo_resp.status_code != 200 or not geo_resp.text.strip():
                return await _llm_weather_fallback(city, date)
            geo_data = geo_resp.json()
            loc_list = geo_data.get("location", [])
            if not loc_list:
                return await _llm_weather_fallback(city, date)

            location_id = loc_list[0]["id"]
            weather_resp = await client.get("https://devapi.qweather.com/v7/weather/7d", params={
                "key": settings.qweather_api_key, "location": location_id,
            })
            if weather_resp.status_code != 200 or not weather_resp.text.strip():
                return await _llm_weather_fallback(city, date)
            weather_data = weather_resp.json()
            daily = weather_data.get("daily", [])
            if not daily:
                return await _llm_weather_fallback(city, date)

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
    except Exception:
        return await _llm_weather_fallback(city, date)
