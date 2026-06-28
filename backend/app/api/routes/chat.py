"""对话 API — SSE 流式 + 同步 + 历史"""
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select
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

            # 使用 astream_events 实时推送每个步骤
            async for event in agent_graph.astream_events(initial_state, version="v2"):
                kind = event.get("event", "")
                name = event.get("name", "")
                data = event.get("data", {})

                # 节点进入事件 → thinking 状态
                if kind == "on_chain_start":
                    if name == "classify_intent":
                        yield f"event: thinking\ndata: {json.dumps({'msg': '🤔 正在分析你的需求...'})}\n\n"
                    elif name == "plan_trip":
                        yield f"event: thinking\ndata: {json.dumps({'msg': '🗺️ 正在为你规划行程方案...'})}\n\n"
                    elif name == "clarify_needs":
                        yield f"event: thinking\ndata: {json.dumps({'msg': '💬 想多了解你一些...'})}\n\n"

                # 工具开始调用
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    yield f"event: tool_call\ndata: {json.dumps({'tool': tool_name, 'status': 'running'})}\n\n"
                    yield f"event: thinking\ndata: {json.dumps({'msg': f'🔍 正在查询: {tool_name}...'})}\n\n"

                # 工具调用结束
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    yield f"event: tool_result\ndata: {json.dumps({'tool': tool_name, 'elapsed_ms': 0})}\n\n"

                # 节点结束 → 捕获最终输出
                elif kind == "on_chain_end":
                    output = data.get("output", {})
                    if isinstance(output, dict):
                        # 收集 plan
                        p = output.get("plan")
                        if p and isinstance(p, dict) and not p.get("error"):
                            final_plan = p
                            yield f"event: card\ndata: {json.dumps({'type': 'itinerary', 'data': p})}\n\n"
                        # 收集 messages
                        msgs = output.get("messages", [])
                        if msgs:
                            final_messages = msgs
                        # thinking 推送
                        thinking_text = output.get("thinking", "")
                        if thinking_text:
                            for line in thinking_text.split("\n"):
                                if line.strip():
                                    yield f"event: thinking\ndata: {json.dumps({'msg': line.strip()})}\n\n"

            # 推送文本回复 — 有卡片时不再单独发文字，避免重复
            if not final_plan and final_messages:
                last_msg = final_messages[-1]
                content = last_msg.content if hasattr(last_msg, "content") else ""
                if content and "```" not in content:
                    yield f"event: content\ndata: {json.dumps({'delta': content})}\n\n"

            yield f"event: done\ndata: {json.dumps({'conv_id': conv_id})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'code': 'AGENT_ERROR', 'msg': str(e)})}\n\n"

    return event_stream()


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest):
    """SSE 流式对话"""
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
