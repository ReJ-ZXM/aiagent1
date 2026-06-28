# 旅游 AI Agent — 设计规格书

> 版本: v1.0 | 日期: 2026-06-28 | 状态: 待实现

---

## 一、项目概述

一个面向国内游的一站式 AI 旅行助手。用户通过**语音或文字**一次性输入出行意图（目的地、日期、预算、偏好），Agent 自动完成交通/酒店/路线的全自动规划并呈现结构化方案。Web 优先，架构预留微信小程序扩展空间。

### 核心场景

> 用户: *"我明天一个人去杭州，7.2 返回，预算 5000"*
>
> Agent: 并行查票/酒店/天气/景点 → 综合生成方案 → 结构化卡片 + 地图 + 预算呈现 → 用户确认或调整

### 目标用户

- 国内游的中国用户（MVP 聚焦）
- 偏好一站式自动化体验（少交互、多结果）

---

## 二、技术栈

| 层级 | 选型 | 说明 |
|---|---|---|
| **Agent 框架** | LangGraph (LangChain 生态) | 状态图驱动，支持条件分支、工具编排、检查点 |
| **后端** | FastAPI (Python 3.11+) | 异步、OpenAPI 文档、SSE/WebSocket |
| **前端** | React 18 + Vite | SPA，组件化 |
| **UI** | Tailwind CSS + shadcn/ui | 快速出 UI，暗色模式 |
| **关系库** | PostgreSQL 15 | 用户、行程、订单 |
| **缓存/队列** | Redis | 会话、限流、后台任务 |
| **向量库** | Chroma | 景点知识库 RAG |
| **LLM 主模型** | Claude API (Anthropic) | 核心 Agent 推理、复杂规划 |
| **LLM 辅助** | DeepSeek API | 意图分类、内容润色、降成本 |
| **语音 ASR** | 百度语音识别 / Whisper | 语音→文字 |
| **地图** | 高德地图 API | POI 搜索、路线规划、地理编码 |
| **搜索** | Bing Search API / 聚合数据 | 实时旅游信息 |

---

## 三、Agent 核心架构

采用 **LangGraph 状态图** 模式，一文输入 → 路由器分发 → 并行搜集 → 综合生成：

```
用户输入
  │
  ▼
意图识别 (DeepSeek 快速分类)
  │
  ▼
实体抽取 (日期/目的地/预算/人数/偏好)
  │
  ▼
并行信息搜集 ─┬─ 查车票 (火车/高铁 API)
              ├─ 查酒店 (高德 POI + 价格)
              ├─ 查天气 (天气 API)
              └─ 查景点 (高德 + RAG 知识库)
  │
  ▼
Claude 主模型合成 → 结构化行程 JSON
  │
  ▼
SSE 流式返回前端 → 卡片化渲染
```

### 子 Agent

| Agent | 职责 | 模型 |
|---|---|---|
| 行程规划 Agent | 全自动方案生成（核心） | Claude |
| 实时问答 Agent | 天气/交通/美食/景点快问 | DeepSeek + 工具 |
| 攻略生成 Agent | 深度攻略、主题游长文 | Claude (生成) + DeepSeek (润色) |
| 闲聊兜底 Agent | 旅游相关闲聊 | DeepSeek |

### 状态管理

- **State**: TypedDict + Pydantic，含历史消息、用户偏好、当前任务
- **Memory**: Redis (短期上下文) + PostgreSQL (长期用户画像)
- **Checkpoint**: LangGraph SqliteSaver，支持中断恢复

---

## 四、工具生态

### 工具矩阵

| 类别 | 工具 | 数据源 |
|---|---|---|
| 🔍 信息 | `search_attractions` 景点搜索 | 高德 POI API |
| 🔍 信息 | `search_hotels` 酒店搜索 | 高德 + 第三方比价 |
| 🔍 信息 | `get_weather` 实时天气 | 和风天气 API |
| 🔍 信息 | `web_search` 网页搜索 | Bing Search API |
| 🗺️ 地图 | `geocode_address` 地址→坐标 | 高德地理编码 |
| 🗺️ 地图 | `route_planning` 路线规划 | 高德路径规划 |
| 🗺️ 地图 | `nearby_search` 周边搜索 | 高德周边 API |
| 🗺️ 地图 | `poi_detail` 景点详情 | 高德 POI 详情 |
| 📝 生成 | `generate_itinerary` 结构化行程 | Claude |
| 📝 生成 | `summarize_reviews` 评论摘要 | DeepSeek |
| 🧠 知识 | `rag_search` 向量检索 | Chroma |
| 🧠 记忆 | `get_user_profile` / `save_preference` | PostgreSQL |

### 模型调度

| 任务 | 模型 | 原因 |
|---|---|---|
| 意图路由 | DeepSeek | 高频、低延迟、便宜 |
| 复杂行程规划 | Claude | 强推理 + 多工具编排 |
| 工具选择决策 | Claude | 精确判断 |
| 景点/攻略内容润色 | DeepSeek | 量大、中文好 |
| 闲聊兜底 | DeepSeek | 成本控制 |

---

## 五、功能 & API

### 功能模块

- **A. 智能对话**: 语音/文字输入 → 全自动方案生成 → 流式输出 → 结构化卡片 → 多轮调整
- **B. 行程管理**: 行程 CRUD → 日视图 → 地图联动 → 导出/分享 → 预算统计
- **C. 用户系统**: 注册/登录 (JWT) → 偏好画像 → 旅行历史 → 收藏夹
- **D. 发现探索**: 目的地浏览 → 主题推荐 → 攻略阅读 → 热门榜单

### API 路由

```
/api/v1
├── /chat
│   ├── POST /stream            SSE 流式对话 (核心)
│   ├── POST /message           同步对话 (备用)
│   └── GET  /history/{conv_id} 对话历史
│
├── /trips
│   ├── POST   /                创建行程
│   ├── GET    /                行程列表
│   ├── GET    /{id}            行程详情
│   ├── PUT    /{id}            编辑行程
│   ├── DELETE /{id}            删除行程
│   ├── POST   /{id}/days/{n}   调整某天
│   └── GET    /{id}/export     导出
│
├── /auth
│   ├── POST /register          注册
│   ├── POST /login             登录 → JWT
│   ├── POST /refresh           刷新 token
│   └── GET  /me                当前用户
│
├── /users
│   ├── PUT  /profile           更新偏好
│   ├── GET  /favorites         收藏列表
│   └── GET  /history           历史行程
│
├── /discover
│   ├── GET /destinations       热门目的地
│   ├── GET /themes/{type}      主题推荐
│   └── GET /search             搜索景点/攻略
│
└── /tools (内部)
    ├── GET /weather             天气查询
    ├── GET /attractions         景点搜索
    ├── GET /route               路线规划
    └── GET /nearby              周边搜索
```

### SSE 流式协议

```
event: thinking     → {"msg": "正在搜索杭州自然风光景点..."}
event: tool_call    → {"tool": "search_attractions", "args": {...}}
event: tool_result  → {"tool": "search_attractions", "result": [...]}
event: content      → {"delta": "根据你的偏好，推荐以下行程：\n"}
event: card         → {"type": "itinerary"|"hotel"|"transport", "data": {...}}
event: done         → {"conv_id": "xxx", "usage": {"tokens": 2500}}
event: error        → {"code": "...", "msg": "..."}
```

---

## 六、数据库 Schema

```sql
users (id, username, email, password_hash, avatar_url, home_city, created_at, updated_at)

user_preferences (id, user_id FK, travel_style, budget_level, preferred_transport,
                  hotel_preference, food_taboos[], travel_pace, updated_at)

conversations (id, user_id FK, title, status, trip_id FK, message_count, created_at, updated_at)

messages (id, conversation_id FK, role, content, content_type, voice_url, metadata JSONB, created_at)

trips (id, user_id FK, conversation_id FK, title, destination, start_date, end_date,
       total_days, budget, estimated_cost, status, snapshot JSONB, created_at, updated_at)

trip_days (id, trip_id FK, day_number, date, title, weather JSONB)

trip_items (id, trip_day_id FK, type, title, description, start_time, end_time,
            location, lat, lng, cost, booking_url, booking_status, notes, sort_order)

favorites (id, user_id FK, item_type, item_id, item_data JSONB, created_at)
```

### 向量存储 (Chroma)
- `attractions` collection — 景点百科 embedding
- `guides` collection — 攻略文章 embedding

---

## 七、前端组件结构

### 路由

```
/              → 首页
/chat          → 智能对话 (核心)    [/chat/:id → 历史对话]
/trips         → 我的行程           [/trips/:id → 行程详情 + 地图]
/discover      → 探索目的地         [/discover/:dest → 目的地详情]
/login         → 登录
/register      → 注册
/profile       → 个人中心 & 偏好
```

### 核心组件

| 组件 | 功能 |
|---|---|
| `ChatPage` | 对话主页面，消息列表 + 输入栏 |
| `MessageList` | 虚拟滚动消息流 |
| `TransportCard` | 高铁/飞机信息卡片 |
| `HotelCard` | 酒店信息卡片（图片+价格+预订） |
| `ItineraryCard` | 行程概览卡片（天列表） |
| `DayPlanCard` | 单日时间线卡片 |
| `BudgetChart` | 预算饼图 |
| `MapPreview` / `FullMap` | 地图组件（高德 JS API） |
| `VoiceRecordButton` | 语音录制按钮 (MediaRecorder) |
| `InputBar` | 文字输入 + 语音 + 发送 |

### 关键交互

- **语音**: 长按录音 → MediaRecorder → WAV → 百度 ASR → 自动填入
- **流式**: EventSource SSE → 逐字 + 卡片分类型渲染
- **地图联动**: 行程 hover → 地图 marker 定位
- **方案调整**: 自然语言指令 → Agent 局部修改 → 局部刷新

---

## 八、项目结构

```
travel-ai-agent/
├── backend/
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── config.py                # 配置管理
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── chat.py          # 对话路由
│   │   │   │   ├── trips.py         # 行程路由
│   │   │   │   ├── auth.py          # 认证路由
│   │   │   │   ├── users.py         # 用户路由
│   │   │   │   └── discover.py      # 发现路由
│   │   │   └── deps.py              # 依赖注入
│   │   ├── agent/
│   │   │   ├── graph.py             # LangGraph 状态图定义
│   │   │   ├── state.py             # State 类型定义
│   │   │   ├── router.py            # 意图路由器
│   │   │   ├── sub_agents/
│   │   │   │   ├── planner.py       # 行程规划 Agent
│   │   │   │   ├── qa.py            # 实时问答 Agent
│   │   │   │   ├── guide.py         # 攻略生成 Agent
│   │   │   │   └── casual.py        # 闲聊 Agent
│   │   │   ├── tools/
│   │   │   │   ├── search.py        # 搜索类工具
│   │   │   │   ├── map_tools.py     # 地图类工具
│   │   │   │   ├── generate.py      # 生成类工具
│   │   │   │   └── weather.py       # 天气工具
│   │   │   └── memory.py            # 记忆管理
│   │   ├── models/
│   │   │   ├── user.py              # 用户模型
│   │   │   ├── trip.py              # 行程模型
│   │   │   └── conversation.py      # 对话模型
│   │   ├── services/
│   │   │   ├── auth_service.py      # 认证服务
│   │   │   ├── trip_service.py      # 行程服务
│   │   │   ├── asr_service.py       # 语音识别服务
│   │   │   └── rag_service.py       # RAG 服务
│   │   └── db/
│   │       ├── session.py           # 数据库连接
│   │       └── migrations/          # Alembic 迁移
│   ├── requirements.txt
│   └── alembic.ini
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   ├── pages/
│   │   │   ├── ChatPage.tsx
│   │   │   ├── TripDetailPage.tsx
│   │   │   ├── DiscoverPage.tsx
│   │   │   ├── AuthPage.tsx
│   │   │   └── ProfilePage.tsx
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── MessageList.tsx
│   │   │   │   ├── InputBar.tsx
│   │   │   │   └── VoiceButton.tsx
│   │   │   ├── cards/
│   │   │   │   ├── TransportCard.tsx
│   │   │   │   ├── HotelCard.tsx
│   │   │   │   ├── ItineraryCard.tsx
│   │   │   │   └── DayPlanCard.tsx
│   │   │   ├── map/
│   │   │   │   └── MapView.tsx
│   │   │   └── ui/                  # shadcn/ui 组件
│   │   ├── hooks/
│   │   ├── lib/
│   │   │   └── sse.ts               # SSE 客户端
│   │   └── types/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-06-28-travel-ai-agent-design.md
```

---

## 九、MVP 实施优先级

| 阶段 | 内容 | 预计时间 |
|---|---|---|
| **P0 (核心)** | FastAPI 骨架 + LangGraph Agent + 行程规划工具 + 基础对话 API | 第 1-2 周 |
| **P0 (核心)** | React ChatPage + SSE 流式 + 卡片渲染 + 语音输入 | 第 2-3 周 |
| **P1 (增强)** | 用户系统 (JWT) + 偏好画像 + 行程 CRUD | 第 3-4 周 |
| **P1 (增强)** | RAG 知识库 (景点百科) + 地图集成 | 第 4-5 周 |
| **P2 (完善)** | 发现页 + 主题推荐 + 攻略生成 + 导出 | 第 5-6 周 |
| **P3 (扩展)** | 微信小程序前端 + 预订跳转 + 多语言 | 后续迭代 |
