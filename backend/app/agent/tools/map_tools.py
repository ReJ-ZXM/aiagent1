"""地图工具 — 高德 API"""
import httpx
from langchain_core.tools import tool
from app.config import settings


def _use_mock():
    return not settings.amap_api_key or settings.amap_api_key == "xxx"


@tool
async def geocode_address(address: str, city: str = "") -> str:
    """地理编码：地址转经纬度。address: 详细地址，city: 所在城市。

    返回: JSON 字符串，包含经纬度坐标。
    """
    if _use_mock():
        return str({"address": address, "lng": 120.15, "lat": 30.27, "note": "(模拟数据)"})

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://restapi.amap.com/v3/geocode/geo", params={
                "key": settings.amap_api_key,
                "address": address,
                "city": city,
            })
            if resp.status_code != 200 or not resp.text.strip():
                return str({"error": f"地理编码服务不可用 (HTTP {resp.status_code})"})
            data = resp.json()
            geocodes = data.get("geocodes", [])
            if not geocodes:
                return str({"error": f"未找到坐标: {address}"})
            g = geocodes[0]
            location = g.get("location", "")
            lng, lat = location.split(",") if "," in location else ("0", "0")
            return str({"address": g.get("formatted_address"), "lng": float(lng), "lat": float(lat)})
    except Exception as e:
        return str({"error": f"地理编码失败: {str(e)}"})


@tool
async def route_planning(origin: str, destination: str, mode: str = "transit") -> str:
    """路线规划。origin: 起点坐标 "lng,lat"，destination: 终点坐标 "lng,lat"，mode: 'transit'(公交) | 'driving'(驾车)。

    返回: JSON 字符串，包含路线距离、时间、步骤。
    """
    if _use_mock():
        return str({"distance": "约5公里", "duration": "30分钟", "cost": "2元" if mode == "transit" else "0元", "note": "(模拟数据)"})

    try:
        mode_map = {"transit": "transit/integrated", "driving": "direction/driving"}
        path = mode_map.get(mode, "transit/integrated")

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://restapi.amap.com/v3/{path}", params={
                "key": settings.amap_api_key,
                "origin": origin,
                "destination": destination,
            })
            if resp.status_code != 200 or not resp.text.strip():
                return str({"error": f"路线规划服务不可用 (HTTP {resp.status_code})"})
            data = resp.json()
            route = data.get("route", {})
            if not route:
                return str({"error": "未找到路线"})

            if mode == "transit":
                transits = route.get("transits", [])
                if not transits:
                    return str({"error": "未找到公交路线"})
                t = transits[0]
                return str({
                    "distance": f"{t.get('distance', 0)}米",
                    "duration": f"{int(t.get('duration', 0)) // 60}分钟",
                    "cost": f"{t.get('cost', 0)}元",
                    "walking_distance": f"{t.get('walking_distance', 0)}米",
                })
            else:
                paths = route.get("paths", [])
                if not paths:
                    return str({"error": "未找到驾车路线"})
                p = paths[0]
                return str({
                    "distance": f"{p.get('distance', 0)}米",
                    "duration": f"{int(p.get('duration', 0)) // 60}分钟",
                    "tolls": f"{p.get('tolls', 0)}元",
                })
    except Exception as e:
        return str({"error": f"路线规划失败: {str(e)}"})
