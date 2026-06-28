"""应用配置，从环境变量加载"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # LLM
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # 高德地图
    amap_api_key: str = ""

    # 和风天气
    qweather_api_key: str = ""

    # Database
    database_url: str = "sqlite+aiosqlite:///./travel_agent.db"

    # App
    secret_key: str = "change-me-in-production"
    debug: bool = True

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
