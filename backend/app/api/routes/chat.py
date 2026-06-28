"""对话 API — SSE 流式 + 历史 + 导出"""
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select
from pydantic import BaseModel, Field

from app.api.deps import get_db, security
from app.services.auth_service import decode_token
from app.db.session import async_session
from app.models.conversation import Conversation, Message
from app.agent.graph import agent_graph
from app.agent.state import AgentState

router = APIRouter(tags=["chat"])


class ChatRequest(BaseModel):
    conversation_id: str | None = Field(default=None, description="对话ID，新建对话可不传")
    content: str = Field(..., min_length=1, description="用户输入内容")


def generate_sse(conv_id: str, user_content: str, history: list[dict] | None = None, previous_plan: dict | None = None):
    """生成 SSE 事件流 — 使用 astream_events 实现真正的实时流式推送"""
    from langchain_core.messages import HumanMessage, AIMessage

    messages = []
    if history:
        for m in history:
            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                messages.append(AIMessage(content=m["content"]))
    if not messages or messages[-1].content != user_content:
        messages.append(HumanMessage(content=user_content))

    initial_state: AgentState = {
        "messages": messages,
        "destination": "", "origin": "", "start_date": "", "end_date": "",
        "num_travelers": 1, "budget": 0, "preferences": [],
        "age": "", "taste": "", "travel_style": "", "companion": "",
        "intent": "", "thinking": "", "plan": previous_plan,
        "need_clarification": False, "error": "",
    }

    async def event_stream():
        try:
            final_plan = None
            final_messages = []
            emitted_content = False  # 防止重复发送

            async for event in agent_graph.astream_events(initial_state, version="v2"):
                kind = event.get("event", "")
                name = event.get("name", "")
                data = event.get("data", {})

                if kind == "on_chain_start":
                    if name == "classify_intent":
                        yield f"event: thinking\ndata: {json.dumps({'msg': '正在分析你的需求...'})}\n\n"
                    elif name == "plan_trip":
                        yield f"event: thinking\ndata: {json.dumps({'msg': '正在为你规划行程方案...'})}\n\n"
                    elif name == "clarify_needs":
                        yield f"event: thinking\ndata: {json.dumps({'msg': '想多了解你一些...'})}\n\n"

                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    yield f"event: tool_call\ndata: {json.dumps({'tool': tool_name, 'status': 'running'})}\n\n"

                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    yield f"event: tool_result\ndata: {json.dumps({'tool': tool_name})}\n\n"

                elif kind == "on_chain_end" and name in ("plan_trip", "clarify_needs", "casual_reply"):
                    output = data.get("output", {})
                    if isinstance(output, dict):
                        # 只捕获最终节点的 plan
                        p = output.get("plan")
                        if p and isinstance(p, dict) and not p.get("error"):
                            final_plan = p
                            yield f"event: card\ndata: {json.dumps({'type': 'itinerary', 'data': p})}\n\n"
                            emitted_content = True

                        msgs = output.get("messages", [])
                        if msgs:
                            final_messages = msgs

                        thinking_text = output.get("thinking", "")
                        if thinking_text:
                            for line in thinking_text.split("\n"):
                                if line.strip():
                                    yield f"event: thinking\ndata: {json.dumps({'msg': line.strip()})}\n\n"

            # 只在没有卡片时发送纯文本回复
            if not emitted_content and final_messages:
                last_msg = final_messages[-1]
                content = last_msg.content if hasattr(last_msg, "content") else ""
                if content:
                    yield f"event: content\ndata: {json.dumps({'delta': content})}\n\n"

            yield f"event: done\ndata: {json.dumps({'conv_id': conv_id})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'code': 'AGENT_ERROR', 'msg': str(e)})}\n\n"

    return event_stream()


@router.post("/chat/stream")
async def chat_stream(
    req: ChatRequest,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
):
    """SSE 流式对话"""
    user_id = None
    if credentials:
        uid = decode_token(credentials.credentials)
        if uid:
            user_id = uid

    async with async_session() as db:
        if req.conversation_id:
            conv = await db.get(Conversation, req.conversation_id)
            if not conv:
                raise HTTPException(status_code=404, detail="对话不存在")
        else:
            conv = Conversation(title=req.content[:50], user_id=user_id)
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

        # 加载历史消息（当前这条 + 之前所有的）
        result = await db.execute(
            sa_select(Message)
            .where(Message.conversation_id == conv.id)
            .order_by(Message.created_at)
        )
        history = result.scalars().all()
        history_messages = [
            {"role": m.role, "content": m.content}
            for m in history
        ]
        previous_plan = conv.plan_snapshot
        conv_id_for_stream = conv.id

    # 返回 SSE 流 + 自动保存计划
    async def stream_and_save():
        final_plan = None
        async for sse_chunk in generate_sse(conv_id_for_stream, req.content, history_messages, previous_plan):
            yield sse_chunk
            if sse_chunk.startswith("event: card"):
                try:
                    data_part = sse_chunk.split("data: ")[1].strip()
                    card_data = json.loads(data_part)
                    if card_data.get("type") == "itinerary":
                        final_plan = card_data.get("data")
                except Exception:
                    pass
        if final_plan:
            async with async_session() as db2:
                c = await db2.get(Conversation, conv_id_for_stream)
                if c:
                    c.plan_snapshot = final_plan
                    await db2.commit()

    return StreamingResponse(
        stream_and_save(),
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

    result = await db.execute(
        sa_select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

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

@router.get("/trips/{conv_id}/export")
async def export_trip(conv_id: str):
    """导出行程为简单 HTML（可打印/保存PDF）"""
    async with async_session() as db:
        conv = await db.get(Conversation, conv_id)
        if not conv or not conv.plan_snapshot:
            raise HTTPException(404, "行程不存在")
        plan = conv.plan_snapshot
        days_html = ""
        for d in plan.get("days", []):
            items_html = ""
            for item in d.get("items", []):
                items_html += f"<li>{item.get('start','')}-{item.get('end','')} {item.get('title','')} - {item.get('description','')} ¥{item.get('cost',0)}</li>"
            days_html += f"<h3>Day {d.get('day_number')} · {d.get('date')} — {d.get('title')}</h3><ul>{items_html}</ul>"
        tiers = plan.get("budget_tiers", {})
        tiers_html = ""
        for k, v in tiers.items():
            tiers_html += f"<tr><td>{k}</td><td>¥{v.get('total','')}</td><td>{v.get('transport','')}</td><td>{v.get('hotel','')}</td></tr>"
        html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="UTF-8"><title>{plan.get('summary','行程')[:50]}</title>
<style>body{{font-family:'Microsoft YaHei',sans-serif;max-width:800px;margin:0 auto;padding:20px}}h1{{color:#0284c7}}h2{{color:#333}}table{{width:100%;border-collapse:collapse}}td,th{{border:1px solid #ddd;padding:8px}}th{{background:#f0f9ff}}ul{{line-height:1.8}}@media print{{body{{padding:0}}}}</style></head>
<body><h1>旅行方案</h1><p>{plan.get('summary','')}</p><h2>预算对比</h2><table><tr><th>档次</th><th>总价</th><th>交通</th><th>酒店</th></tr>{tiers_html}</table>
<p>交通: {plan.get('transport',{}).get('to',{}).get('number','')} {plan.get('transport',{}).get('to',{}).get('from','')}→{plan.get('transport',{}).get('to',{}).get('to','')}</p>
<p>酒店: {plan.get('hotel',{}).get('name','')} ¥{plan.get('hotel',{}).get('price_per_night','')}/晚</p>
<h2>行程详情</h2>{days_html}</body></html>"""
        from fastapi.responses import HTMLResponse
        return HTMLResponse(html)
