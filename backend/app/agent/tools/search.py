"""搜索类工具 — 高德 POI API"""
import httpx
from langchain_core.tools import tool
from app.config import settings

# 无 API Key 时的模拟数据
_MOCK_ATTRACTIONS = {
    "杭州": [
        {"name": "西湖", "address": "杭州市西湖区龙井路1号", "type": "风景名胜;公园", "rating": "4.9", "location": "120.142,30.238"},
        {"name": "灵隐寺", "address": "杭州市西湖区法云弄1号", "type": "风景名胜;寺庙", "rating": "4.8", "location": "120.102,30.244"},
        {"name": "雷峰塔", "address": "杭州市西湖区南山路15号", "type": "风景名胜;塔", "rating": "4.7", "location": "120.157,30.231"},
        {"name": "九溪烟树", "address": "杭州市西湖区九溪路", "type": "风景名胜;自然", "rating": "4.7", "location": "120.121,30.209"},
        {"name": "西溪湿地", "address": "杭州市西湖区天目山路518号", "type": "风景名胜;湿地", "rating": "4.6", "location": "120.069,30.267"},
    ],
    "北京": [
        {"name": "故宫", "address": "北京市东城区景山前街4号", "type": "风景名胜;博物馆", "rating": "4.9", "location": "116.397,39.918"},
        {"name": "长城", "address": "北京市延庆区八达岭", "type": "风景名胜;古迹", "rating": "4.8", "location": "115.988,40.354"},
        {"name": "颐和园", "address": "北京市海淀区新建宫门路19号", "type": "风景名胜;公园", "rating": "4.8", "location": "116.279,39.999"},
    ],
}

_MOCK_HOTELS = {
    "杭州": [
        {"name": "杭州西湖希尔顿花园酒店", "address": "杭州市西湖区北山路82号", "rating": "4.5", "location": "120.140,30.254"},
        {"name": "杭州君悦酒店", "address": "杭州市上城区湖滨路28号", "rating": "4.7", "location": "120.167,30.249"},
        {"name": "杭州香格里拉饭店", "address": "杭州市西湖区北山路78号", "rating": "4.6", "location": "120.139,30.255"},
        {"name": "如家精选酒店(西湖店)", "address": "杭州市西湖区保俶路150号", "rating": "4.2", "location": "120.144,30.263"},
        {"name": "汉庭酒店(杭州西湖湖滨店)", "address": "杭州市上城区延安路238号", "rating": "4.1", "location": "120.167,30.249"},
    ],
}


@tool
async def search_attractions(keywords: str, city: str = "", limit: int = 5) -> str:
    """搜索景点。keywords: 搜索关键词 (如"自然风光")，city: 城市名 (如"杭州")，limit: 返回数量。

    返回: JSON 字符串，包含景点名称、地址、评分、类型。
    """
    # 无 API Key 时返回模拟数据
    if not settings.amap_api_key or settings.amap_api_key == "xxx":
        results = _MOCK_ATTRACTIONS.get(city, _MOCK_ATTRACTIONS.get("杭州", []))
        return str(results[:limit])

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://restapi.amap.com/v3/place/text", params={
                "key": settings.amap_api_key,
                "keywords": f"{keywords} 景点" if keywords else "热门景点",
                "city": city or keywords,
                "types": "风景名胜",
                "offset": limit,
                "extensions": "all",
            })
            if resp.status_code != 200 or not resp.text.strip():
                return str({"error": f"景点搜索服务不可用 (HTTP {resp.status_code})"})
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
    except Exception as e:
        return str({"error": f"景点搜索失败: {str(e)}"})


@tool
async def search_hotels(city: str, max_price: int = 300, location_hint: str = "") -> str:
    """搜索酒店。city: 城市名，max_price: 最高每晚价格，location_hint: 位置偏好 (如"西湖附近")。

    返回: JSON 字符串，包含酒店名称、地址、价格范围。
    """
    # 无 API Key 时返回模拟数据
    if not settings.amap_api_key or settings.amap_api_key == "xxx":
        results = _MOCK_HOTELS.get(city, _MOCK_HOTELS.get("杭州", []))
        return str(results)

    try:
        keywords = f"{location_hint} 酒店" if location_hint else f"{city} 酒店"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://restapi.amap.com/v3/place/text", params={
                "key": settings.amap_api_key,
                "keywords": keywords,
                "city": city,
                "types": "住宿服务",
                "offset": 5,
                "extensions": "all",
            })
            if resp.status_code != 200 or not resp.text.strip():
                return str({"error": f"酒店搜索服务不可用 (HTTP {resp.status_code})"})
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
    except Exception as e:
        return str({"error": f"酒店搜索失败: {str(e)}"})
