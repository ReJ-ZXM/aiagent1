# 旅行 AI 助手 (Travel AI Agent)

> 面向中国国内游客的一站式旅行规划平台。用户一句话输入需求，Agent 多轮追问偏好，自动生成包含交通/酒店/行程的三档预算方案。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 18 + Vite + Tailwind CSS + TypeScript |
| 后端 | FastAPI + LangGraph + SQLAlchemy (async) |
| LLM | DeepSeek (deepseek-chat) |
| 数据 | Amap API (POI)、QWeather (未激活) |
| 数据库 | SQLite (开发) |

## 项目结构

```
travel-ai-agent/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置（从 .env 读取）
│   │   ├── agent/
│   │   │   ├── graph.py         # LangGraph 状态机（5节点）
│   │   │   ├── state.py         # AgentState 定义
│   │   │   ├── router.py        # 意图分类 + 实体提取
│   │   │   ├── planner.py       # 行程规划（季节感知、三档预算）
│   │   │   ├── prompts.py       # 所有 Prompt 模板
│   │   │   └── tools/
│   │   │       ├── search.py    # 搜索工具（mock → web → LLM 三级降级）
│   │   │       └── weather.py   # 天气工具（含 LLM 降级）
│   │   ├── api/routes/
│   │   │   ├── chat.py          # SSE 流式对话 + PDF 导出
│   │   │   └── auth.py          # 注册/登录/me
│   │   ├── models/
│   │   │   ├── conversation.py  # Conversation + Message 模型
│   │   │   └── user.py          # User 模型
│   │   ├── services/
│   │   │   └── auth_service.py  # JWT + hashlib 密码哈希
│   │   └── db/session.py        # 异步 SQLAlchemy session
│   └── .env                     # API 密钥
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── ChatPage.tsx     # 主聊天页
│   │   │   └── AuthPage.tsx     # 登录/注册页
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── MessageList.tsx   # 消息列表 + 卡片渲染
│   │   │   │   ├── InputBar.tsx      # 输入框 + 语音
│   │   │   │   └── VoiceButton.tsx   # Web Speech API 语音
│   │   │   └── cards/
│   │   │       ├── ItineraryCard.tsx  # 行程卡片容器
│   │   │       ├── DayPlanCard.tsx    # 每日行程（含预订链接）
│   │   │       ├── TransportCard.tsx  # 交通方案（含预订按钮）
│   │   │       └── HotelCard.tsx      # 住宿推荐（含预订按钮）
│   │   ├── context/AuthContext.tsx    # 认证状态管理
│   │   ├── lib/
│   │   │   ├── sse.ts          # SSE 流式客户端
│   │   │   └── bookingUrl.ts   # 预订链接生成（12306/携程/大众点评）
│   │   └── types/index.ts      # TypeScript 类型定义
│   └── vite.config.ts          # Vite 配置（含 /api 代理）
└── docs/
    └── superpowers/
        ├── specs/              # 设计规格书
        └── plans/              # 实现计划
```

## 启动方式

```bash
# 后端 (port 8000)
cd backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 前端 (port 5173)
cd frontend
npm run dev
```

## API 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/v1/chat/stream` | SSE 流式对话 |
| GET | `/api/v1/chat/history/{id}` | 对话历史 |
| GET | `/api/v1/trips/{id}/export` | 导出 PDF（浏览器自动下载） |
| POST | `/api/v1/auth/register` | 注册 |
| POST | `/api/v1/auth/login` | 登录 |
| GET | `/api/v1/auth/me` | 获取当前用户 |
| GET | `/api/health` | 健康检查 |

## LangGraph 流程

5 个节点：`classify_intent` → `clarify_needs` / `plan_trip` / `casual_reply` / `modify_trip`

## 关键设计决策

- **密码哈希**：hashlib SHA256（passlib/bcrypt 在 Windows 上有兼容问题）
- **PDF 导出**：fpdf2 + SimHei 字体（weasyprint 需要 GTK，Windows 不可用）
- **数据降级**：mock → DuckDuckGo → DeepSeek LLM 三级降级
- **三档预算**：经济(×0.7) / 舒适(×1.0) / 豪华(×1.3)
- **预算检测**：合并所有用户消息提取实体（解决上下文丢失）
- **防重复**：SSE `emitted_content` flag 防止卡片+文本双重输出
- **预订链接**：直接跳转 12306 / 携程 / 大众点评 官网首页

## 已知限制

- 火车票数据为 LLM 生成（非 12306 实时）
- QWeather API 未激活（返回 403）
- 无 Anthropic key，仅使用 DeepSeek
- ¥ 符号在 PDF 中可能显示异常（SimHei 字体缺该字形）
