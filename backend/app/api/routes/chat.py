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


def generate_sse(conv_id: str, user_content: str, history: list[dict] | None = None):
    """生成 SSE 事件流 — 使用 ainvoke 单次执行，避免重复调用"""
    from langchain_core.messages import HumanMessage, AIMessage

    # 从历史构建消息列表
    messages = []
    if history:
        for m in history:
            if m["role"] == "user":
                messages.append(HumanMessage(content=m["content"]))
            elif m["role"] == "assistant":
                messages.append(AIMessage(content=m["content"]))

    # 确保最后一条是当前用户消息
    if not messages or messages[-1].content != user_content:
        messages.append(HumanMessage(content=user_content))

    initial_state: AgentState = {
        "messages": messages,
        "destination": "",
        "origin": "",
        "start_date": "",
        "end_date": "",
        "num_travelers": 1,
        "budget": 0,
        "preferences": [],
        "age": "",
        "taste": "",
        "travel_style": "",
        "companion": "",
        "intent": "",
        "thinking": "",
        "plan": None,
        "need_clarification": False,
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
            # 如果已有结构化行程卡片，只发送摘要（不发原始JSON代码块）
            if plan and not plan.get("error") and plan.get("summary"):
                yield f"event: content\ndata: {json.dumps({'delta': plan['summary']})}\n\n"
            else:
                messages = final_state.get("messages", [])
                if messages:
                    last_msg = messages[-1]
                    content = last_msg.content if hasattr(last_msg, "content") else ""
                    if content:
                        # 移除可能的代码块标记，只保留纯文本
                        cleaned = content
                        if "```" in cleaned:
                            # 去掉代码块，只保留外面的文字
                            parts = []
                            in_code = False
                            for line in cleaned.split("\n"):
                                if line.strip().startswith("```"):
                                    in_code = not in_code
                                    continue
                                if not in_code:
                                    parts.append(line)
                            cleaned = "\n".join(parts).strip()
                        if cleaned:
                            yield f"event: content\ndata: {json.dumps({'delta': cleaned})}\n\n"

            yield f"event: done\ndata: {json.dumps({'conv_id': conv_id, 'usage': {'tokens': 0}})}\n\n"

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

    # 返回 SSE 流（携带完整历史）
    return StreamingResponse(
        generate_sse(conv.id, req.content, history_messages),
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
