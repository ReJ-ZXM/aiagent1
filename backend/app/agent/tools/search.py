"""搜索类工具 — 高德 POI API"""
import httpx
from langchain_core.tools import tool
from app.config import settings


@tool
async def search_attractions(keywords: str, city: str = "", limit: int = 5) -> str:
    """搜索景点。keywords: 搜索关键词 (如"自然风光")，city: 城市名 (如"杭州")，limit: 返回数量。

    返回: JSON 字符串，包含景点名称、地址、评分、类型。
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://restapi.amap.com/v3/place/text", params={
            "key": settings.amap_api_key,
            "keywords": f"{keywords} 景点" if keywords else "热门景点",
            "city": city or keywords,
            "types": "风景名胜",
            "offset": limit,
            "extensions": "all",
        })
        data = resp.json()
        pois = data.get("pois", [])
        results = []
        for p in pois[:limit]:
            results.append({
                "name": p.get("name"),
                "address": p.get("address"),
                "type": p.get("type"),
                "rating": p.get("biz_ext", {}).get("rating", "暂无"),
                "location": p.get("location"),
            })
        return str(results)


@tool
async def search_hotels(city: str, max_price: int = 300, location_hint: str = "") -> str:
    """搜索酒店。city: 城市名，max_price: 最高每晚价格，location_hint: 位置偏好 (如"西湖附近")。

    返回: JSON 字符串，包含酒店名称、地址、价格范围。
    """
    keywords = f"{location_hint} 酒店" if location_hint else f"{city} 酒店"
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://restapi.amap.com/v3/place/text", params={
            "key": settings.amap_api_key,
            "keywords": keywords,
            "city": city,
            "types": "住宿服务",
            "offset": 5,
            "extensions": "all",
        })
        data = resp.json()
        pois = data.get("pois", [])
        results = []
        for p in pois[:5]:
            results.append({
                "name": p.get("name"),
                "address": p.get("address"),
                "rating": p.get("biz_ext", {}).get("rating", "暂无"),
                "location": p.get("location"),
            })
        return str(results)
