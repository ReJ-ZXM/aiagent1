"""Agent 工具集合"""
from app.agent.tools.search import search_attractions, search_hotels
from app.agent.tools.weather import get_weather
from app.agent.tools.map_tools import geocode_address, route_planning

ALL_TOOLS = [search_attractions, search_hotels, get_weather, geocode_address, route_planning]
