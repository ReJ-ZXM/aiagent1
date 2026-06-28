"""Agent 工具集合"""
from app.agent.tools.search import search_attractions, search_hotels
from app.agent.tools.weather import get_weather
from app.agent.tools.map_tools import geocode_address, route_planning
from app.agent.tools.media import search_images, search_douyin_videos

ALL_TOOLS = [
    search_attractions, search_hotels, get_weather,
    geocode_address, route_planning,
    search_images, search_douyin_videos,
]
