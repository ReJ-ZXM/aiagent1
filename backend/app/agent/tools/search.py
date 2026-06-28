"""搜索类工具 — 高德 POI API + 联网搜索回退"""
import re
import httpx
from langchain_core.tools import tool
from app.config import settings


async def _web_search(query: str, num: int = 5) -> list[dict]:
    """联网搜索 — DuckDuckGo，带超时保护"""
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.get(
                "https://lite.duckduckgo.com/lite/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0"},
            )
            if resp.status_code != 200:
                return []
            html = resp.text
            results = []
            links = re.findall(
                r'<a[^>]*href="([^"]+)"[^>]*>([^<]+)</a>\s*<span[^>]*>([^<]*)</span>',
                html, re.DOTALL
            )
            for url, title, snippet in links[:num]:
                title = title.strip()
                snippet = snippet.strip() if snippet else title
                if title and url.startswith("http"):
                    results.append({"title": title, "url": url, "snippet": snippet})
            return results
    except Exception:
        return []


async def _llm_generate_info(city: str, info_type: str, count: int = 5) -> list[dict]:
    """LLM 兜底 — 用 DeepSeek 的知识生成城市旅游数据"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    try:
        llm = ChatOpenAI(
            model="deepseek-chat",
            api_key=settings.deepseek_api_key,
            base_url=settings.deepseek_base_url,
            temperature=0,
            max_tokens=1000,
        )
        if info_type == "attractions":
            prompt = f"列出{city}最热门的{count}个旅游景点，输出JSON数组，每个元素包含name、address、type、rating、location字段。只输出JSON。"
        else:
            prompt = f"列出{city}热门的{count}家酒店，输出JSON数组，每个元素包含name、address、rating字段。只输出JSON。"
        resp = await llm.ainvoke([
            SystemMessage(content="你是中国旅游专家。只输出JSON数组，不要任何解释。"),
            HumanMessage(content=prompt),
        ])
        content = resp.content.strip()
        # 提取 JSON
        if "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        if content.startswith("json"):
            content = content[4:].strip()
        import json
        results = json.loads(content)
        if isinstance(results, list):
            return results
    except Exception:
        pass
    return []

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
    "拉萨": [
        {"name": "布达拉宫", "address": "拉萨市城关区北京中路35号", "type": "风景名胜;宫殿;世界遗产", "rating": "4.9", "location": "91.117,29.657"},
        {"name": "大昭寺", "address": "拉萨市城关区八廓街", "type": "风景名胜;寺庙;世界遗产", "rating": "4.8", "location": "91.132,29.653"},
        {"name": "纳木错", "address": "拉萨市当雄县纳木错乡", "type": "风景名胜;湖泊;自然保护区", "rating": "4.9", "location": "90.750,30.717"},
        {"name": "羊卓雍措", "address": "山南市浪卡子县", "type": "风景名胜;湖泊", "rating": "4.8", "location": "90.618,28.936"},
        {"name": "八廓街", "address": "拉萨市城关区八廓街", "type": "风景名胜;历史街区", "rating": "4.7", "location": "91.133,29.653"},
        {"name": "罗布林卡", "address": "拉萨市城关区罗布林卡路21号", "type": "风景名胜;园林;世界遗产", "rating": "4.6", "location": "91.099,29.656"},
        {"name": "色拉寺", "address": "拉萨市城关区色拉路1号", "type": "风景名胜;寺庙", "rating": "4.7", "location": "91.142,29.693"},
        {"name": "哲蚌寺", "address": "拉萨市城关区北京西路276号", "type": "风景名胜;寺庙", "rating": "4.7", "location": "91.064,29.678"},
    ],
    "西藏": [
        {"name": "布达拉宫", "address": "拉萨市城关区北京中路35号", "type": "风景名胜;宫殿;世界遗产", "rating": "4.9", "location": "91.117,29.657"},
        {"name": "纳木错", "address": "拉萨市当雄县纳木错乡", "type": "风景名胜;湖泊", "rating": "4.9", "location": "90.750,30.717"},
        {"name": "大昭寺", "address": "拉萨市城关区八廓街", "type": "风景名胜;寺庙", "rating": "4.8", "location": "91.132,29.653"},
        {"name": "羊卓雍措", "address": "山南市浪卡子县", "type": "风景名胜;湖泊", "rating": "4.8", "location": "90.618,28.936"},
        {"name": "雅鲁藏布大峡谷", "address": "林芝市米林县", "type": "风景名胜;峡谷", "rating": "4.8", "location": "94.899,29.489"},
        {"name": "巴松措", "address": "林芝市工布江达县", "type": "风景名胜;湖泊", "rating": "4.7", "location": "93.940,30.010"},
        {"name": "扎什伦布寺", "address": "日喀则市桑珠孜区", "type": "风景名胜;寺庙", "rating": "4.7", "location": "88.872,29.272"},
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
    "拉萨": [
        {"name": "拉萨香格里拉大酒店", "address": "拉萨市城关区罗布林卡路19号", "rating": "4.7", "location": "91.105,29.653"},
        {"name": "拉萨瑞吉度假酒店", "address": "拉萨市城关区江苏路22号", "rating": "4.8", "location": "91.137,29.649"},
        {"name": "拉萨圣地天堂洲际大饭店", "address": "拉萨市城关区江苏大道1号", "rating": "4.7", "location": "91.154,29.650"},
        {"name": "7天连锁酒店(拉萨布达拉宫店)", "address": "拉萨市城关区北京中路182号", "rating": "4.0", "location": "91.121,29.655"},
        {"name": "如家快捷酒店(拉萨大昭寺店)", "address": "拉萨市城关区林廓东路105号", "rating": "4.1", "location": "91.138,29.655"},
    ],
    "西藏": [
        {"name": "拉萨香格里拉大酒店", "address": "拉萨市城关区罗布林卡路19号", "rating": "4.7", "location": "91.105,29.653"},
        {"name": "拉萨瑞吉度假酒店", "address": "拉萨市城关区江苏路22号", "rating": "4.8", "location": "91.137,29.649"},
        {"name": "拉萨圣地天堂洲际大饭店", "address": "拉萨市城关区江苏大道1号", "rating": "4.7", "location": "91.154,29.650"},
        {"name": "7天连锁酒店(拉萨布达拉宫店)", "address": "拉萨市城关区北京中路182号", "rating": "4.0", "location": "91.121,29.655"},
        {"name": "如家快捷酒店(拉萨大昭寺店)", "address": "拉萨市城关区林廓东路105号", "rating": "4.1", "location": "91.138,29.655"},
    ],
}


@tool
async def search_attractions(keywords: str, city: str = "", limit: int = 5) -> str:
    """搜索景点。keywords: 搜索关键词 (如"自然风光")，city: 城市名 (如"杭州")，limit: 返回数量。

    返回: JSON 字符串，包含景点名称、地址、评分、类型。
    """
    # 无 API Key → 模拟 → 联网 → LLM 三级回退
    if not settings.amap_api_key or settings.amap_api_key == "xxx":
        results = _MOCK_ATTRACTIONS.get(city, [])
        if not results:
            results = _MOCK_ATTRACTIONS.get(city.rstrip("市"), [])
        if not results:
            results = await _web_search(f"{city} 热门景点 旅游攻略", num=limit)
        if not results:
            results = await _llm_generate_info(city, "attractions", limit)
        if results:
            return str(results[:limit])
        return str([{"name": f"{city}热门景点", "address": city, "note": "无数据"}])

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
    # 无 API Key → 模拟 → 联网 → LLM 三级回退
    if not settings.amap_api_key or settings.amap_api_key == "xxx":
        results = _MOCK_HOTELS.get(city, [])
        if not results:
            results = _MOCK_HOTELS.get(city.rstrip("市"), [])
        if not results:
            results = await _web_search(f"{city} 酒店 住宿推荐 价格", num=5)
        if not results:
            results = await _llm_generate_info(city, "hotels", 5)
        if results:
            return str(results)
        return str([{"name": f"{city}经济型酒店", "address": city, "note": "无数据"}])

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
