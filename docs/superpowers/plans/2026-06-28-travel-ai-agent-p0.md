# 旅游 AI Agent P0 核心实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 搭建旅游 AI Agent 的核心闭环 — 用户输入出行意图 → Agent 自动规划 → 流式返回结构化方案。

**Architecture:** FastAPI 后端提供 SSE 流式 API + LangGraph 管理 Agent 状态图 + Claude/DeepSeek 双模型调度 + React 前端渲染对话卡片。P0 阶段使用 SQLite 替代 PostgreSQL，Redis/Chroma 暂用内存模拟，先跑通核心流程。

**Tech Stack:** Python 3.11+, FastAPI, LangGraph, LangChain, Claude API (anthropic), DeepSeek API (openai-compatible), React 18, Vite, Tailwind CSS, SQLite (dev)

---

## 文件结构

```
travel-ai-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口, CORS, 路由注册
│   │   ├── config.py                # 环境变量配置
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py              # 依赖注入 (get_db, get_agent)
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       └── chat.py          # POST /stream, POST /message, GET /history/{conv_id}
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── state.py             # AgentState TypedDict + Pydantic
│   │   │   ├── graph.py             # LangGraph 状态图构建 + 编译
│   │   │   ├── router.py            # 意图分类 (DeepSeek)
│   │   │   ├── planner.py           # 行程规划节点 (Claude + 工具)
│   │   │   ├── tools/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── search.py        # search_attractions, search_hotels (高德API)
│   │   │   │   ├── weather.py       # get_weather (和风天气API)
│   │   │   │   └── map_tools.py     # geocode, route_planning (高德API)
│   │   │   └── prompts.py           # 所有 prompt 模板
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py      # Conversation, Message ORM
│   │   │   └── trip.py              # Trip, TripDay, TripItem ORM
│   │   └── db/
│   │       ├── __init__.py
│   │       └── session.py           # SQLAlchemy async engine + session
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx                  # React Router 路由
│   │   ├── main.tsx                 # 入口
│   │   ├── index.css                # Tailwind 指令
│   │   ├── pages/
│   │   │   └── ChatPage.tsx         # 对话主页面
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── MessageList.tsx  # 消息列表
│   │   │   │   ├── InputBar.tsx     # 输入栏 (文字+语音)
│   │   │   │   └── VoiceButton.tsx  # 语音录制按钮
│   │   │   └── cards/
│   │   │       ├── TransportCard.tsx
│   │   │       ├── HotelCard.tsx
│   │   │       ├── ItineraryCard.tsx
│   │   │       └── DayPlanCard.tsx
│   │   ├── lib/
│   │   │   └── sse.ts              # SSE EventSource 封装
│   │   └── types/
│   │       └── index.ts            # TypeScript 类型定义
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   └── tsconfig.json
└── docs/superpowers/
    ├── specs/2026-06-28-travel-ai-agent-design.md
    └── plans/2026-06-28-travel-ai-agent-p0.md
```

---

### Task 1: 后端项目脚手架

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `backend/app/__init__.py`
- Create: `backend/app/config.py`
- Create: `backend/app/main.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi==0.115.6
uvicorn[standard]==0.34.0
langgraph==0.2.60
langchain==0.3.14
langchain-openai==0.2.14
langchain-anthropic==0.3.8
anthropic==0.42.0
sqlalchemy[asyncio]==2.0.36
aiosqlite==0.20.0
httpx==0.28.1
python-dotenv==1.0.1
sse-starlette==2.2.1
pydantic==2.10.4
pydantic-settings==2.7.1
```

- [ ] **Step 2: 安装依赖**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/backend && pip install -r requirements.txt
```

- [ ] **Step 3: 创建 .env.example**

```env
# LLM
ANTHROPIC_API_KEY=sk-ant-xxx
DEEPSEEK_API_KEY=sk-xxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 高德地图 (https://lbs.amap.com)
AMAP_API_KEY=xxx

# 和风天气 (https://dev.qweather.com)
QWEATHER_API_KEY=xxx

# Database
DATABASE_URL=sqlite+aiosqlite:///./travel_agent.db

# App
SECRET_KEY=change-me-in-production
DEBUG=true
```

- [ ] **Step 4: 创建 config.py**

```python
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
```

- [ ] **Step 5: 创建 main.py**

```python
"""FastAPI 应用入口"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.db.session import init_db
from app.api.routes import chat


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="旅游AI助手", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router, prefix="/api/v1")


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 6: 验证启动**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/backend && python -m uvicorn app.main:app --reload --port 8000
```

Expected: `INFO: Uvicorn running on http://127.0.0.1:8000` (Ctrl+C 退出)

- [ ] **Step 7: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add backend/ && git commit -m "feat: 后端项目脚手架 — FastAPI + 配置管理"
```

---

### Task 2: 数据库层 (SQLAlchemy + SQLite)

**Files:**
- Create: `backend/app/db/__init__.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/conversation.py`
- Create: `backend/app/models/trip.py`

- [ ] **Step 1: 创建 session.py**

```python
"""数据库引擎和会话管理"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

engine = create_async_engine(settings.database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

- [ ] **Step 2: 创建 conversation.py 模型**

```python
"""对话和消息 ORM 模型"""
import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(200), default="新对话")
    trip_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    message_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", order_by="Message.created_at")


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # 'user' | 'assistant' | 'system'
    content: Mapped[str] = mapped_column(Text, default="")
    content_type: Mapped[str] = mapped_column(String(20), default="text")  # 'text' | 'voice' | 'card'
    voice_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    metadata_: Mapped[dict | None] = mapped_column(JSON, nullable=True, name="metadata")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
```

- [ ] **Step 3: 创建 trip.py 模型**

```python
"""行程 ORM 模型"""
import uuid
from datetime import datetime, date, time
from sqlalchemy import String, Integer, Float, Date, Time, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base


class Trip(Base):
    __tablename__ = "trips"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(String(36), ForeignKey("conversations.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), default="未命名行程")
    destination: Mapped[str] = mapped_column(String(100), default="")
    start_date: Mapped[date] = mapped_column(Date, nullable=True)
    end_date: Mapped[date] = mapped_column(Date, nullable=True)
    total_days: Mapped[int] = mapped_column(Integer, default=0)
    budget: Mapped[float] = mapped_column(Float, default=0)
    estimated_cost: Mapped[float] = mapped_column(Float, default=0)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft | confirmed | completed
    snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    days: Mapped[list["TripDay"]] = relationship(back_populates="trip", order_by="TripDay.day_number")


class TripDay(Base):
    __tablename__ = "trip_days"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_id: Mapped[str] = mapped_column(String(36), ForeignKey("trips.id"), nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(String(200), default="")
    weather: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    trip: Mapped["Trip"] = relationship(back_populates="days")
    items: Mapped[list["TripItem"]] = relationship(back_populates="trip_day", order_by="TripItem.sort_order")


class TripItem(Base):
    __tablename__ = "trip_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    trip_day_id: Mapped[str] = mapped_column(String(36), ForeignKey("trip_days.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # transport | hotel | attraction | meal
    title: Mapped[str] = mapped_column(String(200), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str] = mapped_column(String(300), default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float] = mapped_column(Float, default=0)
    booking_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    trip_day: Mapped["TripDay"] = relationship(back_populates="items")
```

- [ ] **Step 4: 更新 api/deps.py**

```python
"""FastAPI 依赖注入"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db as _get_db


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session
```

- [ ] **Step 5: 验证数据库初始化**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/backend && python -c "
import asyncio
from app.db.session import init_db, engine
asyncio.run(init_db())
print('DB initialized successfully')
"
```

Expected: `DB initialized successfully`，且 `backend/travel_agent.db` 文件存在。

- [ ] **Step 6: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add backend/app/db/ backend/app/models/ && git commit -m "feat: 数据库层 — SQLAlchemy 异步 + SQLite + 对话/行程模型"
```

---

### Task 3: Agent State & Prompts

**Files:**
- Create: `backend/app/agent/__init__.py`
- Create: `backend/app/agent/state.py`
- Create: `backend/app/agent/prompts.py`

- [ ] **Step 1: 创建 agent/state.py**

```python
"""Agent 状态定义 — LangGraph StateGraph 的核心数据结构"""
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """旅游 Agent 的全局状态"""
    # 消息历史 (LangGraph 自动追加)
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 从用户输入中抽取的结构化信息
    destination: str          # 目的地, e.g. "杭州"
    origin: str               # 出发地, e.g. "上海"
    start_date: str           # 出发日期, e.g. "2026-06-29"
    end_date: str             # 返回日期, e.g. "2026-07-02"
    num_travelers: int        # 人数
    budget: float             # 预算金额
    preferences: list[str]    # 偏好标签, e.g. ["自然风光", "美食"]

    # Agent 工作状态
    intent: str               # 意图类型: "plan_trip" | "qa" | "casual"
    thinking: str             # 当前 thinking 消息 (SSE 发送)
    plan: dict | None         # 最终生成的行程方案 (结构化 JSON)
    error: str                # 错误信息
```

- [ ] **Step 2: 创建 agent/prompts.py**

```python
"""Agent 所有 prompt 模板"""

INTENT_ROUTER_PROMPT = """你是一个旅游助手意图分类器。分析用户输入，输出 JSON。

分类规则:
- "plan_trip": 用户想要规划一次旅行 (提到目的地、日期、行程安排等)
- "qa": 用户询问旅游相关信息 (天气、景点、交通、美食、住宿等)
- "casual": 闲聊、打招呼、无关话题

用户输入: {user_input}

只输出 JSON，格式: {{"intent": "...", "reason": "..."}}"""


ENTITY_EXTRACTION_PROMPT = """从用户输入中提取旅行关键信息，输出 JSON。

当前日期: {current_date}
用户出发城市: {home_city}

用户输入: {user_input}

输出 JSON (缺失字段用 null):
{{
    "destination": "目的地城市名",
    "origin": "出发城市 (如未提及，默认用home_city)",
    "start_date": "YYYY-MM-DD 格式的出发日期",
    "end_date": "YYYY-MM-DD 格式的返回日期",
    "num_travelers": 人数,
    "budget": 预算金额(数字),
    "preferences": ["偏好标签1", "偏好标签2"]
}}"""


PLANNER_SYSTEM_PROMPT = """你是一个资深的旅行规划师。根据搜集到的信息，为用户生成一份完整的旅行方案。

要求:
1. 交通: 推荐合适的火车/高铁车次 (含时间、价格)
2. 酒店: 推荐位置便利、预算合理的酒店 (含价格、位置优势)
3. 行程: 每天 3-5 个景点，路线合理不绕路，含时间安排
4. 预算: 各项费用明细 + 总计 + 剩余
5. 语言风格: 热情、专业、口语化，像朋友在帮忙规划

输出必须是严格的 JSON 格式:

{{
    "summary": "方案概要，一段话总结",
    "transport": {{
        "to": {{"type": "高铁", "number": "G7313", "from": "上海虹桥", "to": "杭州东", "departure": "08:30", "arrival": "09:20", "price": 78}},
        "back": {{"type": "高铁", "number": "G7328", "from": "杭州东", "to": "上海虹桥", "departure": "17:00", "arrival": "17:50", "price": 78}}
    }},
    "hotel": {{
        "name": "酒店名",
        "address": "详细地址",
        "price_per_night": 299,
        "total_nights": 3,
        "total_price": 897,
        "highlights": ["近西湖", "地铁口", "含早"]
    }},
    "days": [
        {{
            "day_number": 1,
            "date": "2026-06-29",
            "title": "西湖经典一日",
            "items": [
                {{"type": "attraction", "title": "西湖", "start": "09:30", "end": "12:00", "description": "...", "cost": 0}},
                {{"type": "meal", "title": "楼外楼 午餐", "start": "12:00", "end": "13:00", "description": "西湖醋鱼", "cost": 120}},
                {{"type": "attraction", "title": "雷峰塔", "start": "13:30", "end": "15:00", "description": "...", "cost": 40}}
            ]
        }}
    ],
    "budget_breakdown": {{
        "transport": 156,
        "hotel": 897,
        "attractions": 300,
        "meals": 600,
        "total": 1953,
        "remaining": 3047
    }}
}}"""


QA_SYSTEM_PROMPT = """你是一个旅游知识助手，回答用户关于旅游的问题。
要求: 简洁、准确、实用。如果不知道，诚实说不知道。
优先引用实际数据而不是编造。"""
```

- [ ] **Step 3: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add backend/app/agent/ && git commit -m "feat: Agent State 定义 + Prompt 模板"
```

---

### Task 4: Agent 工具层 (Tool Layer)

**Files:**
- Create: `backend/app/agent/tools/__init__.py`
- Create: `backend/app/agent/tools/search.py`
- Create: `backend/app/agent/tools/weather.py`
- Create: `backend/app/agent/tools/map_tools.py`

- [ ] **Step 1: 创建 agent/tools/__init__.py**

```python
"""Agent 工具集合"""
from app.agent.tools.search import search_attractions, search_hotels
from app.agent.tools.weather import get_weather
from app.agent.tools.map_tools import geocode_address, route_planning

ALL_TOOLS = [search_attractions, search_hotels, get_weather, geocode_address, route_planning]
```

- [ ] **Step 2: 创建 agent/tools/search.py**

```python
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
```

- [ ] **Step 3: 创建 agent/tools/weather.py**

```python
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
```

- [ ] **Step 4: 创建 agent/tools/map_tools.py**

```python
"""地图工具 — 高德 API"""
import httpx
from langchain_core.tools import tool
from app.config import settings


@tool
async def geocode_address(address: str, city: str = "") -> str:
    """地理编码：地址转经纬度。address: 详细地址，city: 所在城市。

    返回: JSON 字符串，包含经纬度坐标。
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://restapi.amap.com/v3/geocode/geo", params={
            "key": settings.amap_api_key,
            "address": address,
            "city": city,
        })
        data = resp.json()
        geocodes = data.get("geocodes", [])
        if not geocodes:
            return str({"error": f"未找到坐标: {address}"})
        g = geocodes[0]
        location = g.get("location", "")
        lng, lat = location.split(",") if "," in location else ("0", "0")
        return str({"address": g.get("formatted_address"), "lng": float(lng), "lat": float(lat)})


@tool
async def route_planning(origin: str, destination: str, mode: str = "transit") -> str:
    """路线规划。origin: 起点坐标 "lng,lat"，destination: 终点坐标 "lng,lat"，mode: 'transit'(公交) | 'driving'(驾车)。

    返回: JSON 字符串，包含路线距离、时间、步骤。
    """
    mode_map = {"transit": "transit/integrated", "driving": "direction/driving"}
    path = mode_map.get(mode, "transit/integrated")

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://restapi.amap.com/v3/{path}", params={
            "key": settings.amap_api_key,
            "origin": origin,
            "destination": destination,
        })
        data = resp.json()
        route = data.get("route", {})
        if not route:
            return str({"error": "未找到路线"})

        # 提取关键信息
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
```

- [ ] **Step 5: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add backend/app/agent/tools/ && git commit -m "feat: Agent 工具层 — 景点/酒店搜索 + 天气 + 地理编码 + 路线规划"
```

---

### Task 5: Agent 核心图 (LangGraph StateGraph)

**Files:**
- Create: `backend/app/agent/router.py`
- Create: `backend/app/agent/planner.py`
- Create: `backend/app/agent/graph.py`

- [ ] **Step 1: 创建 agent/router.py**

```python
"""意图路由 — 使用 DeepSeek 快速分类用户意图"""
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agent.state import AgentState
from app.agent.prompts import INTENT_ROUTER_PROMPT, ENTITY_EXTRACTION_PROMPT


router_llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    temperature=0,
)


async def classify_intent(state: AgentState) -> dict:
    """分类用户意图并抽取旅行实体"""
    user_input = state["messages"][-1].content if state["messages"] else ""

    # 1. 意图分类
    resp = await router_llm.ainvoke([
        SystemMessage(content=INTENT_ROUTER_PROMPT),
        HumanMessage(content=user_input),
    ])
    try:
        intent_data = json.loads(resp.content)
    except json.JSONDecodeError:
        intent_data = {"intent": "casual", "reason": "parse error"}

    intent = intent_data.get("intent", "casual")

    # 2. 如果是规划意图，抽取实体
    destination = ""
    origin = ""
    start_date = ""
    end_date = ""
    num_travelers = 1
    budget = 0.0
    preferences: list[str] = []

    if intent == "plan_trip":
        from datetime import date
        # 简化：用 DeepSeek 抽取实体
        entity_resp = await router_llm.ainvoke([
            SystemMessage(content=ENTITY_EXTRACTION_PROMPT.format(
                current_date=date.today().isoformat(),
                home_city="上海",
                user_input=user_input,
            )),
            HumanMessage(content=user_input),
        ])
        try:
            entity = json.loads(entity_resp.content)
            destination = entity.get("destination") or ""
            origin = entity.get("origin") or "上海"
            start_date = entity.get("start_date") or ""
            end_date = entity.get("end_date") or ""
            num_travelers = entity.get("num_travelers") or 1
            budget = entity.get("budget") or 0.0
            preferences = entity.get("preferences") or []
        except json.JSONDecodeError:
            pass

    return {
        "intent": intent,
        "destination": destination,
        "origin": origin,
        "start_date": start_date,
        "end_date": end_date,
        "num_travelers": num_travelers,
        "budget": budget,
        "preferences": preferences,
        "thinking": f"识别意图: {intent}" + (f", 目的地: {destination}" if destination else ""),
    }
```

- [ ] **Step 2: 创建 agent/planner.py**

```python
"""行程规划 Agent — 核心规划节点，使用 Claude + 工具"""
import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_anthropic import ChatAnthropic
from app.config import settings
from app.agent.state import AgentState
from app.agent.prompts import PLANNER_SYSTEM_PROMPT
from app.agent.tools import ALL_TOOLS


planner_llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    temperature=0.7,
    max_tokens=4096,
)

# 绑定工具到 Claude
planner_with_tools = planner_llm.bind_tools(ALL_TOOLS)


async def plan_trip(state: AgentState) -> dict:
    """行程规划节点 — 调用工具搜集信息，然后生成行程"""
    thinking_messages = []

    # 构建上下文
    context = f"""用户旅行需求:
- 目的地: {state['destination']}
- 出发地: {state['origin']}
- 日期: {state['start_date']} 至 {state['end_date']}
- 人数: {state['num_travelers']}
- 预算: {state['budget']}元
- 偏好: {', '.join(state['preferences']) if state['preferences'] else '无特殊偏好'}
"""

    # Step 1: Claude 决定调用哪些工具
    thinking_messages.append("正在分析你的需求...")
    thinking_messages.append(f"目的地: {state['destination']}, 预算: {state['budget']}元")

    # Step 2: 并行搜集信息
    thinking_messages.append("正在搜索景点和酒店...")
    search_query = f"请根据以下信息规划行程: {context}"

    response = await planner_with_tools.ainvoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=search_query),
    ])

    # 处理工具调用
    tool_results = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        from app.agent.tools.search import search_attractions, search_hotels
        from app.agent.tools.weather import get_weather
        from app.agent.tools.map_tools import geocode_address

        for tc in response.tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})

            thinking_messages.append(f"正在调用: {tool_name}...")
            thinking_messages.append(f"查询参数: {tool_args}")

            # 执行工具
            tool_map = {
                "search_attractions": search_attractions,
                "search_hotels": search_hotels,
                "get_weather": get_weather,
                "geocode_address": geocode_address,
            }
            tool_fn = tool_map.get(tool_name)
            if tool_fn:
                result = await tool_fn.ainvoke(tool_args)
                tool_results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    # Step 3: 用工具结果 + Claude 生成最终行程
    thinking_messages.append("正在生成行程方案...")

    final_messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=search_query),
        response,
        *tool_results,
        HumanMessage(content="请根据以上工具返回的数据，生成完整的行程 JSON 方案。严格按照 JSON 格式输出。"),
    ]

    final_response = await planner_llm.ainvoke(final_messages)

    # 解析行程 JSON
    plan = None
    try:
        content = final_response.content
        # 提取 JSON 块
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content.strip()
        plan = json.loads(json_str)
    except (json.JSONDecodeError, IndexError):
        plan = {"error": "行程生成失败", "raw": final_response.content[:500]}

    return {
        "plan": plan,
        "thinking": "\n".join(thinking_messages),
        "messages": [final_response],
    }
```

- [ ] **Step 3: 创建 agent/graph.py**

```python
"""LangGraph 状态图 — 定义 Agent 的完整工作流"""
from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.router import classify_intent
from app.agent.planner import plan_trip


def route_by_intent(state: AgentState) -> str:
    """根据意图路由到不同的处理节点"""
    intent = state.get("intent", "casual")
    if intent == "plan_trip":
        return "plan_trip"
    return "casual_reply"


async def casual_reply(state: AgentState) -> dict:
    """闲聊/问答节点 — 简单回复"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from app.config import settings
    from app.agent.prompts import QA_SYSTEM_PROMPT

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7,
    )
    user_msg = state["messages"][-1].content if state["messages"] else ""
    resp = await llm.ainvoke([
        SystemMessage(content=QA_SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ])
    return {"messages": [resp], "thinking": "知识问答中..."}


def build_graph():
    """构建并编译 Agent 状态图"""
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("plan_trip", plan_trip)
    workflow.add_node("casual_reply", casual_reply)

    # 设置入口
    workflow.set_entry_point("classify_intent")

    # 条件路由
    workflow.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {"plan_trip": "plan_trip", "casual_reply": "casual_reply"},
    )

    # 结束
    workflow.add_edge("plan_trip", END)
    workflow.add_edge("casual_reply", END)

    return workflow.compile()


# 全局 Agent 实例
agent_graph = build_graph()
```

- [ ] **Step 4: 编写 graph 构建验证脚本**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/backend && python -c "
import asyncio
from app.agent.graph import build_graph
graph = build_graph()
print('Graph nodes:', list(graph.nodes.keys()))
print('Graph compiled successfully')
"
```

Expected: `Graph compiled successfully`

- [ ] **Step 5: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add backend/app/agent/ && git commit -m "feat: Agent 核心图 — LangGraph 状态图 + 意图路由 + 行程规划"
```

---

### Task 6: Chat API (SSE 流式端点)

**Files:**
- Create: `backend/app/api/__init__.py`
- Create: `backend/app/api/routes/__init__.py`
- Create: `backend/app/api/routes/chat.py`
- Create: `backend/app/api/deps.py`

- [ ] **Step 1: 创建 api/__init__.py 和 api/routes/__init__.py**

```python
# api/__init__.py (空文件)
```

```python
# api/routes/__init__.py (空文件)
```

- [ ] **Step 2: 创建 api/routes/chat.py**

```python
"""对话 API — SSE 流式 + 同步 + 历史"""
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from app.api.deps import get_db
from app.db.session import async_session
from app.models.conversation import Conversation, Message
from app.agent.graph import agent_graph
from app.agent.state import AgentState

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, description="对话ID，新建对话可不传")
    content: str = Field(..., min_length=1, description="用户输入内容")


async def generate_sse(conv_id: str, user_content: str):
    """生成 SSE 事件流 — 使用 ainvoke 单次执行，避免重复调用"""
    from langchain_core.messages import HumanMessage

    initial_state: AgentState = {
        "messages": [HumanMessage(content=user_content)],
        "destination": "",
        "origin": "",
        "start_date": "",
        "end_date": "",
        "num_travelers": 1,
        "budget": 0,
        "preferences": [],
        "intent": "",
        "thinking": "",
        "plan": None,
        "error": "",
    }

    async def event_stream():
        try:
            # 发送初始 thinking
            yield f"event: thinking\ndata: {json.dumps({'msg': '正在分析你的需求...'})}\n\n"
            await asyncio.sleep(0.1)

            # 单次执行 Agent 图 (不重复调用)
            yield f"event: thinking\ndata: {json.dumps({'msg': '正在为你规划行程...'})}\n\n"

            final_state = await agent_graph.ainvoke(initial_state)

            # 输出 Agent 的 thinking 日志
            thinking_text = final_state.get("thinking", "")
            if thinking_text:
                for line in thinking_text.split("\n"):
                    if line.strip():
                        yield f"event: thinking\ndata: {json.dumps({'msg': line.strip()})}\n\n"

            # 输出结构化行程卡片
            plan = final_state.get("plan")
            if plan and not plan.get("error"):
                yield f"event: card\ndata: {json.dumps({'type': 'itinerary', 'data': plan})}\n\n"

            # 输出 assistant 最后的文本回复
            messages = final_state.get("messages", [])
            if messages:
                last_msg = messages[-1]
                content = last_msg.content if hasattr(last_msg, "content") else ""
                if content:
                    yield f"event: content\ndata: {json.dumps({'delta': content})}\n\n"

            yield f"event: done\ndata: {json.dumps({'conv_id': conv_id, 'usage': {'tokens': 0}})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'code': 'AGENT_ERROR', 'msg': str(e)})}\n\n"

    return event_stream()


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE 流式对话"""
    # 创建或获取对话
    async with async_session() as db:
        if req.conversation_id:
            conv = await db.get(Conversation, req.conversation_id)
            if not conv:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            conv = Conversation(title=req.content[:50])
            db.add(conv)
            await db.commit()
            await db.refresh(conv)

        # 保存用户消息
        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=req.content,
            content_type="text",
        )
        db.add(user_msg)
        await db.commit()

    # 返回 SSE 流
    return StreamingResponse(
        generate_sse(conv.id, req.content),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/chat/history/{conv_id}")
async def get_history(conv_id: str, db: AsyncSession = Depends(get_db)):
    """获取对话历史"""
    conv = await db.get(Conversation, conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")

    messages = (
        (await db.execute(
            __import__("sqlalchemy").sql.select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at)
        ))
        .scalars()
        .all()
    )

    return {
        "conversation": {
            "id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at.isoformat(),
        },
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "content_type": m.content_type,
                "created_at": m.created_at.isoformat(),
            }
            for m in messages
        ],
    }
```

- [ ] **Step 3: 创建 api/deps.py (如果不存在则覆盖)**

```python
"""FastAPI 依赖注入"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db as _get_db


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in _get_db():
        yield session
```

- [ ] **Step 4: 验证 API 启动**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/backend && timeout 5 python -m uvicorn app.main:app --port 8000 2>&1 || true
```

Expected: 服务正常启动，自动文档可访问 `http://localhost:8000/docs`

- [ ] **Step 5: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add backend/app/api/ && git commit -m "feat: Chat API — SSE 流式对话 + 历史查询"
```

---

### Task 7: 前端项目脚手架

**Files:**
- Create: `frontend/index.html`
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/tsconfig.app.json`
- Create: `frontend/tsconfig.node.json`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/index.css`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "travel-ai-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.28.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.12",
    "@types/react-dom": "^18.3.1",
    "@vitejs/plugin-react": "^4.3.4",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.49",
    "tailwindcss": "^3.4.16",
    "typescript": "^5.6.3",
    "vite": "^6.0.3"
  }
}
```

- [ ] **Step 2: 安装前端依赖**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/frontend && npm install
```

- [ ] **Step 3: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

- [ ] **Step 4: 创建 tsconfig.json**

```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ]
}
```

- [ ] **Step 5: 创建 tsconfig.app.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

- [ ] **Step 6: 创建 tsconfig.node.json**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["ES2023"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 7: 创建 tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

- [ ] **Step 8: 创建 postcss.config.js**

```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
}
```

- [ ] **Step 9: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>✈️</text></svg>" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>旅行AI助手</title>
  </head>
  <body class="bg-gray-50 text-gray-900">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 10: 创建 src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

- [ ] **Step 11: 创建 src/main.tsx**

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
)
```

- [ ] **Step 12: 创建 src/App.tsx**

```tsx
import { Routes, Route } from 'react-router-dom'
import ChatPage from './pages/ChatPage'

export default function App() {
  return (
    <div className="h-screen flex flex-col">
      <Routes>
        <Route path="/" element={<ChatPage />} />
        <Route path="/chat" element={<ChatPage />} />
        <Route path="/chat/:conversationId" element={<ChatPage />} />
      </Routes>
    </div>
  )
}
```

- [ ] **Step 13: 验证前端启动**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/frontend && timeout 5 npx vite --host 2>&1 || true
```

Expected: Vite dev server 启动在 `http://localhost:5173`

- [ ] **Step 14: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add frontend/ && git commit -m "feat: 前端项目脚手架 — React 18 + Vite + Tailwind CSS + React Router"
```

---

### Task 8: TypeScript 类型 & SSE 客户端

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/lib/sse.ts`

- [ ] **Step 1: 创建 src/types/index.ts**

```typescript
// === 行程相关类型 ===

export interface TransportLeg {
  type: string       // "高铁" | "飞机" | "大巴"
  number: string     // "G7313"
  from: string       // "上海虹桥"
  to: string         // "杭州东"
  departure: string  // "08:30"
  arrival: string    // "09:20"
  price: number      // 78
}

export interface HotelInfo {
  name: string
  address: string
  price_per_night: number
  total_nights: number
  total_price: number
  highlights: string[]
}

export interface TripItem {
  type: 'transport' | 'hotel' | 'attraction' | 'meal'
  title: string
  start?: string
  end?: string
  description: string
  cost: number
}

export interface DayPlan {
  day_number: number
  date: string
  title: string
  items: TripItem[]
}

export interface BudgetBreakdown {
  transport: number
  hotel: number
  attractions: number
  meals: number
  total: number
  remaining: number
}

export interface TripPlan {
  summary: string
  transport?: {
    to: TransportLeg
    back: TransportLeg
  }
  hotel?: HotelInfo
  days: DayPlan[]
  budget_breakdown: BudgetBreakdown
}

// === 消息相关类型 ===

export type ContentType = 'text' | 'voice' | 'card'

export interface Message {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  content_type: ContentType
  cards?: SSECardData[]
  created_at: string
}

// === SSE 事件类型 ===

export interface SSEThinking {
  msg: string
}

export interface SSEToolCall {
  tool: string
  status: 'running' | 'done'
}

export interface SSEToolResult {
  tool: string
  elapsed_ms: number
}

export interface SSECardData {
  type: 'itinerary' | 'transport' | 'hotel'
  data: TripPlan
}

export interface SSEDone {
  conv_id: string
  usage: { tokens: number }
}

export interface SSEError {
  code: string
  msg: string
}

export type SSEEvent =
  | { event: 'thinking'; data: SSEThinking }
  | { event: 'tool_call'; data: SSEToolCall }
  | { event: 'tool_result'; data: SSEToolResult }
  | { event: 'content'; data: { delta: string } }
  | { event: 'card'; data: SSECardData }
  | { event: 'done'; data: SSEDone }
  | { event: 'error'; data: SSEError }
```

- [ ] **Step 2: 创建 src/lib/sse.ts**

```typescript
import type { SSEEvent } from '../types'

interface SSECallbacks {
  onThinking?: (msg: string) => void
  onToolCall?: (tool: string) => void
  onToolResult?: (tool: string, elapsed: number) => void
  onContent?: (delta: string) => void
  onCard?: (type: string, data: unknown) => void
  onDone?: (convId: string) => void
  onError?: (code: string, msg: string) => void
}

export function streamChat(
  content: string,
  conversationId: string | null,
  callbacks: SSECallbacks
): AbortController {
  const controller = new AbortController()

  const body = JSON.stringify({
    content,
    conversation_id: conversationId,
  })

  fetch('/api/v1/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body,
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        callbacks.onError?.('HTTP_ERROR', `HTTP ${response.status}`)
        return
      }

      const reader = response.body?.getReader()
      if (!reader) return

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let currentEvent = ''
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            currentEvent = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            const dataStr = line.slice(6)
            try {
              const data = JSON.parse(dataStr)
              switch (currentEvent) {
                case 'thinking':
                  callbacks.onThinking?.(data.msg)
                  break
                case 'tool_call':
                  callbacks.onToolCall?.(data.tool)
                  break
                case 'tool_result':
                  callbacks.onToolResult?.(data.tool, data.elapsed_ms)
                  break
                case 'content':
                  callbacks.onContent?.(data.delta)
                  break
                case 'card':
                  callbacks.onCard?.(data.type, data.data)
                  break
                case 'done':
                  callbacks.onDone?.(data.conv_id)
                  break
                case 'error':
                  callbacks.onError?.(data.code, data.msg)
                  break
              }
            } catch {
              // skip malformed JSON
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== 'AbortError') {
        callbacks.onError?.('NETWORK_ERROR', err.message)
      }
    })

  return controller
}
```

- [ ] **Step 3: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add frontend/src/types/ frontend/src/lib/ && git commit -m "feat: TypeScript 类型定义 + SSE 流式客户端"
```

---

### Task 9: ChatPage 核心页面 & 消息组件

**Files:**
- Create: `frontend/src/pages/ChatPage.tsx`
- Create: `frontend/src/components/chat/MessageList.tsx`
- Create: `frontend/src/components/chat/InputBar.tsx`

- [ ] **Step 1: 创建 src/pages/ChatPage.tsx**

```tsx
import { useState, useRef, useCallback } from 'react'
import { useParams } from 'react-router-dom'
import MessageList from '../components/chat/MessageList'
import InputBar from '../components/chat/InputBar'
import { streamChat } from '../lib/sse'
import type { Message, SSEEvent } from '../types'

export default function ChatPage() {
  const { conversationId } = useParams<{ conversationId: string }>()
  const [messages, setMessages] = useState<Message[]>([])
  const [thinking, setThinking] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const [convId, setConvId] = useState<string | null>(conversationId || null)
  const abortRef = useRef<AbortController | null>(null)

  const handleSend = useCallback((content: string) => {
    // 添加用户消息
    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content,
      content_type: 'text',
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])
    setIsStreaming(true)
    setThinking('思考中...')

    // 添加 assistant 占位
    const assistantMsg: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      content_type: 'text',
      cards: [],
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, assistantMsg])

    abortRef.current = streamChat(content, convId, {
      onThinking: (msg) => setThinking(msg),
      onToolCall: (tool) => setThinking(`正在调用: ${tool}...`),
      onContent: (delta) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last && last.role === 'assistant') {
            updated[updated.length - 1] = { ...last, content: last.content + delta }
          }
          return updated
        })
      },
      onCard: (type, data) => {
        setMessages((prev) => {
          const updated = [...prev]
          const last = updated[updated.length - 1]
          if (last && last.role === 'assistant') {
            const existing = last.cards || []
            updated[updated.length - 1] = { ...last, cards: [...existing, { type: type as 'itinerary', data }] }
          }
          return updated
        })
      },
      onDone: (id) => {
        setConvId(id)
        setIsStreaming(false)
        setThinking('')
      },
      onError: (code, msg) => {
        setThinking(`错误: ${msg}`)
        setIsStreaming(false)
      },
    })
  }, [convId])

  const handleStop = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
    setThinking('')
  }, [])

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-white border-b px-4 py-3 flex items-center gap-4 shrink-0">
        <h1 className="text-lg font-bold">✈️ 旅行AI助手</h1>
        {thinking && (
          <span className="text-sm text-gray-500 animate-pulse truncate max-w-md">
            {thinking}
          </span>
        )}
      </header>

      {/* Messages */}
      <MessageList messages={messages} />

      {/* Input */}
      <InputBar
        onSend={handleSend}
        onStop={handleStop}
        disabled={isStreaming}
      />
    </div>
  )
}
```

- [ ] **Step 2: 创建 src/components/chat/MessageList.tsx**

```tsx
import { useEffect, useRef } from 'react'
import type { Message } from '../../types'
import TransportCard from '../cards/TransportCard'
import HotelCard from '../cards/HotelCard'
import ItineraryCard from '../cards/ItineraryCard'

interface Props {
  messages: Message[]
}

export default function MessageList({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  if (messages.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400">
        <div className="text-center">
          <p className="text-4xl mb-4">✈️</p>
          <p className="text-lg mb-2">告诉我你的旅行计划吧！</p>
          <p className="text-sm">例如："明天去杭州，7月2号回，预算5000"</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
      {messages.map((msg) => (
        <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-1' : ''}`}>
            {/* 文字内容 */}
            {msg.content && (
              <div
                className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-blue-500 text-white rounded-br-sm'
                    : 'bg-white border text-gray-800 rounded-bl-sm shadow-sm'
                }`}
              >
                {msg.content}
                {!msg.content && msg.role === 'assistant' && (
                  <span className="inline-flex gap-1">
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }} />
                    <span className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }} />
                  </span>
                )}
              </div>
            )}

            {/* 结构化卡片 */}
            {msg.cards?.map((card, i) => {
              if (card.type === 'itinerary') {
                const plan = card.data
                return (
                  <div key={i} className="mt-3 space-y-3">
                    {plan.summary && (
                      <div className="bg-white border rounded-xl p-3 shadow-sm text-sm text-gray-700">
                        {plan.summary}
                      </div>
                    )}
                    {plan.transport && <TransportCard transport={plan.transport} />}
                    {plan.hotel && <HotelCard hotel={plan.hotel} />}
                    <ItineraryCard plan={plan} />
                    {plan.budget_breakdown && (
                      <BudgetBar breakdown={plan.budget_breakdown} budget={plan.budget_breakdown.total + plan.budget_breakdown.remaining} />
                    )}
                  </div>
                )
              }
              return null
            })}
          </div>
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  )
}

function BudgetBar({ breakdown, budget }: { breakdown: { total: number; remaining: number; [key: string]: unknown }; budget: number }) {
  const pct = budget > 0 ? Math.round((breakdown.total / budget) * 100) : 0
  return (
    <div className="bg-white border rounded-xl p-4 shadow-sm">
      <div className="flex justify-between text-sm mb-2">
        <span className="font-medium">💰 预算概览</span>
        <span className="text-gray-500">{pct}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2.5 mb-2">
        <div
          className="bg-green-500 h-2.5 rounded-full transition-all duration-500"
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <div className="flex justify-between text-sm">
        <span className="text-green-600 font-medium">已用 ¥{breakdown.total.toLocaleString()}</span>
        <span className="text-gray-400">剩余 ¥{breakdown.remaining.toLocaleString()}</span>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: 创建 src/components/chat/InputBar.tsx**

```tsx
import { useState, useRef, KeyboardEvent } from 'react'
import VoiceButton from './VoiceButton'

interface Props {
  onSend: (content: string) => void
  onStop: () => void
  disabled: boolean
}

export default function InputBar({ onSend, onStop, disabled }: Props) {
  const [text, setText] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const handleSend = () => {
    const trimmed = text.trim()
    if (!trimmed) return
    onSend(trimmed)
    setText('')
  }

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleVoiceResult = (transcript: string) => {
    if (transcript.trim()) {
      onSend(transcript.trim())
    }
  }

  return (
    <div className="border-t bg-white px-4 py-3 shrink-0">
      <div className="max-w-3xl mx-auto flex items-center gap-2">
        <VoiceButton onResult={handleVoiceResult} disabled={disabled} />

        <input
          ref={inputRef}
          type="text"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={disabled ? 'AI 正在回复...' : '输入旅行需求，如"明天去杭州3天，预算5000"...'}
          disabled={disabled}
          className="flex-1 border rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400 disabled:bg-gray-50 disabled:text-gray-400"
        />

        {disabled ? (
          <button
            onClick={onStop}
            className="bg-red-500 text-white rounded-full w-9 h-9 flex items-center justify-center hover:bg-red-600 transition shrink-0"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="1" /></svg>
          </button>
        ) : (
          <button
            onClick={handleSend}
            disabled={!text.trim()}
            className="bg-blue-500 text-white rounded-full w-9 h-9 flex items-center justify-center hover:bg-blue-600 transition shrink-0 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        )}
      </div>
    </div>
  )
}
```

- [ ] **Step 4: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add frontend/src/pages/ frontend/src/components/chat/ && git commit -m "feat: ChatPage 核心页面 — 消息列表 + 输入栏 + SSE 流式渲染"
```

---

### Task 10: 卡片组件 (行程/交通/酒店)

**Files:**
- Create: `frontend/src/components/cards/TransportCard.tsx`
- Create: `frontend/src/components/cards/HotelCard.tsx`
- Create: `frontend/src/components/cards/ItineraryCard.tsx`
- Create: `frontend/src/components/cards/DayPlanCard.tsx`

- [ ] **Step 1: 创建 TransportCard.tsx**

```tsx
import type { TransportLeg } from '../../types'

interface Props {
  transport: {
    to: TransportLeg
    back: TransportLeg
  }
}

export default function TransportCard({ transport }: Props) {
  return (
    <div className="bg-white border rounded-xl p-4 shadow-sm space-y-3">
      <h3 className="text-sm font-bold flex items-center gap-2">
        <span>🚂</span> 交通方案
      </h3>

      {/* 去程 */}
      <TransportRow leg={transport.to} label="去程" />

      {/* 分隔线 */}
      <div className="border-t border-dashed" />

      {/* 返程 */}
      <TransportRow leg={transport.back} label="返程" />

      {/* 总价 */}
      <div className="text-right text-sm text-gray-500">
        交通合计: <span className="font-bold text-gray-800">
          ¥{((transport.to?.price || 0) + (transport.back?.price || 0)).toLocaleString()}
        </span>
      </div>
    </div>
  )
}

function TransportRow({ leg, label }: { leg: TransportLeg; label: string }) {
  if (!leg) return null
  return (
    <div className="flex items-center gap-3 text-sm">
      <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-medium">{label}</span>
      <span className="font-mono font-bold">{leg.number}</span>
      <span className="text-gray-600">{leg.type}</span>
      <span className="ml-auto text-gray-500">{leg.from} {leg.departure} → {leg.to} {leg.arrival}</span>
      <span className="font-bold text-orange-600">¥{leg.price}</span>
    </div>
  )
}
```

- [ ] **Step 2: 创建 HotelCard.tsx**

```tsx
import type { HotelInfo } from '../../types'

interface Props {
  hotel: HotelInfo
}

export default function HotelCard({ hotel }: Props) {
  if (!hotel) return null
  return (
    <div className="bg-white border rounded-xl p-4 shadow-sm">
      <h3 className="text-sm font-bold flex items-center gap-2 mb-3">
        <span>🏨</span> 住宿推荐
      </h3>
      <div className="flex justify-between items-start">
        <div>
          <p className="font-bold text-base">{hotel.name}</p>
          <p className="text-sm text-gray-500 mt-1">{hotel.address}</p>
          <div className="flex gap-2 mt-2 flex-wrap">
            {hotel.highlights?.map((h, i) => (
              <span key={i} className="text-xs bg-green-50 text-green-700 px-2 py-0.5 rounded-full">
                {h}
              </span>
            ))}
          </div>
        </div>
        <div className="text-right shrink-0">
          <p className="text-xs text-gray-400">每晚</p>
          <p className="text-xl font-bold text-orange-600">¥{hotel.price_per_night}</p>
          <p className="text-xs text-gray-400 mt-1">
            {hotel.total_nights}晚共 ¥{hotel.total_price?.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 3: 创建 DayPlanCard.tsx**

```tsx
import type { DayPlan, TripItem } from '../../types'

interface Props {
  day: DayPlan
}

export default function DayPlanCard({ day }: Props) {
  const typeIcons: Record<string, string> = {
    attraction: '📍',
    meal: '🍜',
    transport: '🚂',
    hotel: '🏨',
  }

  return (
    <div className="border-l-2 border-blue-200 pl-4 py-1">
      <h4 className="text-sm font-bold text-gray-700 mb-2">
        Day {day.day_number} · {day.date} — {day.title}
      </h4>
      <div className="space-y-2">
        {day.items?.map((item, i) => (
          <TimelineItem key={i} item={item} icon={typeIcons[item.type] || '📍'} />
        ))}
      </div>
    </div>
  )
}

function TimelineItem({ item, icon }: { item: TripItem; icon: string }) {
  return (
    <div className="flex gap-3 text-sm">
      <span className="shrink-0 mt-0.5">{icon}</span>
      <div className="flex-1 min-w-0">
        <div className="flex justify-between">
          <span className="font-medium truncate">{item.title}</span>
          {item.cost > 0 && <span className="text-orange-500 shrink-0 ml-2">¥{item.cost}</span>}
        </div>
        <div className="flex gap-2 text-xs text-gray-400 mt-0.5">
          {item.start && <span>{item.start}</span>}
          {item.start && item.end && <span>-</span>}
          {item.end && <span>{item.end}</span>}
          {item.description && <span className="truncate">· {item.description}</span>}
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: 创建 ItineraryCard.tsx**

```tsx
import type { TripPlan } from '../../types'
import DayPlanCard from './DayPlanCard'

interface Props {
  plan: TripPlan
}

export default function ItineraryCard({ plan }: Props) {
  if (!plan?.days) return null

  return (
    <div className="bg-white border rounded-xl p-4 shadow-sm">
      <h3 className="text-sm font-bold flex items-center gap-2 mb-3">
        <span>🗺️</span> 行程详情
      </h3>
      <div className="space-y-4">
        {plan.days.map((day) => (
          <DayPlanCard key={day.day_number} day={day} />
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 5: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add frontend/src/components/cards/ && git commit -m "feat: 卡片组件 — 交通/酒店/行程/日计划卡片"
```

---

### Task 11: 语音输入组件

**Files:**
- Create: `frontend/src/components/chat/VoiceButton.tsx`

- [ ] **Step 1: 创建 VoiceButton.tsx**

```tsx
import { useState, useRef, useCallback } from 'react'

interface Props {
  onResult: (transcript: string) => void
  disabled: boolean
}

export default function VoiceButton({ onResult, disabled }: Props) {
  const [recording, setRecording] = useState(false)
  const [supported] = useState(
    () => !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia)
  )
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
          ? 'audio/webm;codecs=opus'
          : 'audio/webm',
      })
      mediaRecorderRef.current = mediaRecorder
      chunksRef.current = []

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data)
        }
      }

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(chunksRef.current, { type: 'audio/webm' })
        chunksRef.current = []

        // P0: 若浏览器支持 Web Speech API，直接本地识别
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
          const SpeechRecognition =
            (window as Record<string, unknown>).SpeechRecognition ||
            (window as Record<string, unknown>).webkitSpeechRecognition
          const recognition = new (SpeechRecognition as new () => SpeechRecognition)()
          recognition.lang = 'zh-CN'
          recognition.interimResults = false
          recognition.onresult = (event: SpeechRecognitionEvent) => {
            const transcript = event.results[0][0].transcript
            onResult(transcript)
          }
          recognition.onerror = () => {
            // Web Speech 失败，降级为提示用户手动输入
            onResult('')
          }
          recognition.start()
        } else {
          // 没有 Web Speech API，提示用户
          console.warn('浏览器不支持语音识别')
          onResult('')
        }
      }

      mediaRecorder.start()
      setRecording(true)
    } catch {
      console.warn('无法访问麦克风')
    }
  }, [onResult])

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    setRecording(false)
  }, [])

  if (!supported) return null

  return (
    <button
      onMouseDown={startRecording}
      onMouseUp={stopRecording}
      onMouseLeave={stopRecording}
      onTouchStart={startRecording}
      onTouchEnd={stopRecording}
      disabled={disabled}
      className={`rounded-full w-9 h-9 flex items-center justify-center transition shrink-0 ${
        recording
          ? 'bg-red-500 text-white animate-pulse scale-110'
          : 'bg-gray-100 text-gray-500 hover:bg-gray-200'
      } disabled:opacity-40 disabled:cursor-not-allowed`}
      title="按住说话"
    >
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
          d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
      </svg>
    </button>
  )
}
```

- [ ] **Step 2: 提交**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add frontend/src/components/chat/VoiceButton.tsx && git commit -m "feat: 语音输入 — 浏览器 Web Speech API 语音识别"
```

---

### Task 12: 端到端集成验证

- [ ] **Step 1: 确保 .env 配置就绪**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/backend && cp .env.example .env
# 编辑 .env，填入 ANTHROPIC_API_KEY 和 DEEPSEEK_API_KEY
echo "请确保 backend/.env 中填入了 API Key"
```

- [ ] **Step 2: 启动后端**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/backend && python -m uvicorn app.main:app --reload --port 8000
```

验证: `http://localhost:8000/docs` — Swagger 文档可见，`/api/v1/chat/stream` 端点存在。

- [ ] **Step 3: 启动前端**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent/frontend && npx vite --host
```

验证: `http://localhost:5173` — 聊天页面可见。

- [ ] **Step 4: 端到端测试**

在聊天输入框输入: `我明天想去杭州玩3天，预算3000，喜欢自然风光`

验证:
- [ ] 输入栏显示消息
- [ ] 顶部状态栏显示 "正在分析/搜索/生成..."
- [ ] 流式返回内容
- [ ] 结构化卡片渲染 (交通、酒店、行程、预算)

- [ ] **Step 5: 提交最终版本**

```bash
cd c:/Users/30938/Desktop/travel-ai-agent && git add -A && git commit -m "feat: P0 核心闭环完成 — 端到端可运行"
```

---

## 验收标准

| # | 验收项 | 通过条件 |
|---|---|---|
| 1 | 后端启动 | `uvicorn app.main:app` 无报错，`/docs` 可访问 |
| 2 | 前端启动 | `vite` 启动，`/chat` 页面正常渲染 |
| 3 | SSE 流式 | `POST /api/v1/chat/stream` 返回 `text/event-stream` |
| 4 | Agent 规划 | 输入 "杭州3天预算3000" → Agent 返回结构化行程 JSON |
| 5 | 卡片渲染 | 前端收到 card 事件 → 正确显示交通/酒店/行程卡片 |
| 6 | 语音输入 | 长按麦克风按钮 → 说话 → 文字自动填入输入框 |
| 7 | 对话历史 | 对话 ID 可查询 `/api/v1/chat/history/{conv_id}` |
| 8 | 数据库 | SQLite 自动创建 `travel_agent.db`，表结构正确 |
