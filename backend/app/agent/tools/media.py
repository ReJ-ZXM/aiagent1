"""媒体搜索工具 — 图片 & 视频链接"""
from langchain_core.tools import tool


@tool
async def search_images(query: str, count: int = 3) -> str:
    """搜索景点相关图片链接。query: 搜索关键词 (如"杭州西湖 风景")，count: 返回数量。

    返回: JSON 字符串，包含 Unsplash 图片链接。
    """
    # 使用 Unsplash 公开搜索 (无需 API Key)
    encoded = query.replace(" ", "+")
    results = []
    for i in range(min(count, 5)):
        results.append({
            "query": query,
            "image_url": f"https://source.unsplash.com/800x600/?{encoded}&sig={i}",
            "source": "Unsplash",
            "note": "免费图片，可能在GFW内加载较慢"
        })
    return str(results)


@tool
async def search_douyin_videos(query: str, count: int = 3) -> str:
    """搜索抖音高赞视频链接。query: 搜索关键词 (如"杭州西湖攻略")，count: 返回数量。

    返回: JSON 字符串，包含抖音搜索链接。
    """
    encoded = query.replace(" ", "+")
    results = []
    for i in range(min(count, 5)):
        results.append({
            "query": query,
            "douyin_link": f"https://www.douyin.com/search/{encoded}?sort=like",
            "note": "抖音搜索结果页，按点赞排序"
        })
    return str(results)
