"""对话 API — SSE 流式 + 历史 + 导出"""
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, Response
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
            emitted_content = False

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

        user_msg = Message(
            conversation_id=conv.id,
            role="user",
            content=req.content,
            content_type="text",
        )
        db.add(user_msg)
        await db.commit()

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


def _build_trip_pdf(plan: dict) -> bytes:
    """用 fpdf2 生成行程 PDF 字节流"""
    from fpdf import FPDF

    FONT_PATH = r"C:\Windows\Fonts\simhei.ttf"
    destination = plan.get('destination', '旅行')

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("zh", fname=FONT_PATH)
    pdf.set_auto_page_break(auto=True, margin=15)

    # === 标题 ===
    pdf.set_font("zh", size=20)
    pdf.set_text_color(2, 132, 199)
    pdf.cell(170, 12, f"旅行方案 · {destination}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)

    # === 概要 ===
    summary = plan.get('summary', '')
    if summary:
        pdf.set_font("zh", size=10)
        pdf.set_text_color(100, 116, 139)
        pdf.multi_cell(170, 6, summary, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # === 预算对比 ===
    pdf.set_font("zh", size=14)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(170, 10, "预算对比", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    tier_labels = {"economy": "经济档", "comfort": "舒适档", "premium": "豪华档"}
    tiers = plan.get("budget_tiers", {})

    col_w = [38, 38, 52, 52]
    headers = ["档次", "总价", "交通方式", "住宿标准"]
    pdf.set_font("zh", size=9)
    pdf.set_fill_color(240, 249, 255)
    pdf.set_text_color(12, 74, 110)
    for h, w in zip(headers, col_w):
        pdf.cell(w, 8, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_text_color(30, 41, 59)
    for k, v in tiers.items():
        label = tier_labels.get(k, k)
        row = [label, f"¥{v.get('total','')}", v.get('transport', ''), v.get('hotel', '')]
        for cell, w in zip(row, col_w):
            pdf.cell(w, 8, str(cell), border=1, align="C")
        pdf.ln()
    pdf.ln(6)

    # === 交通 & 住宿 ===
    pdf.set_font("zh", size=14)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(170, 10, "交通 & 住宿", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    transport = plan.get("transport", {}).get("to", {})
    hotel = plan.get("hotel", {})

    pdf.set_font("zh", size=10)
    pdf.set_text_color(30, 41, 59)
    t_text = (
        f"交通：{transport.get('number','')}  {transport.get('from','')} → {transport.get('to','')}"
        f"  ·  {transport.get('type','')}  ·  约{transport.get('estimated_hours','')}小时"
        f"  ·  ¥{transport.get('price','')}"
    )
    pdf.multi_cell(170, 7, t_text, new_x="LMARGIN", new_y="NEXT")
    h_text = (
        f"酒店：{hotel.get('name','')}  ·  ¥{hotel.get('price_per_night','')}/晚"
        f" × {hotel.get('total_nights','')}晚 = ¥{hotel.get('total_price','')}"
        f"  ·  {hotel.get('address','')}"
    )
    pdf.multi_cell(170, 7, h_text, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    # === 每日行程 ===
    pdf.set_font("zh", size=14)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(170, 10, "每日行程", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    for d in plan.get("days", []):
        # Day 标题条
        pdf.set_fill_color(240, 249, 255)
        pdf.set_font("zh", size=11)
        pdf.set_text_color(2, 132, 199)
        day_title = f"  DAY {d.get('day_number')}  ·  {d.get('date','')}  —  {d.get('title','')}"
        pdf.cell(170, 9, day_title, fill=True, new_x="LMARGIN", new_y="NEXT")

        pdf.set_text_color(30, 41, 59)
        for item in d.get("items", []):
            time_str = f"{item.get('start','')}-{item.get('end','')}"
            title = item.get('title', '')
            desc = item.get('description', '')
            cost = item.get('cost', 0)

            pdf.set_font("zh", size=9)
            pdf.set_text_color(2, 132, 199)
            pdf.cell(32, 6, f"  {time_str}")
            pdf.set_text_color(30, 41, 59)
            line = f"{title}"
            if desc:
                line += f"  ·  {desc}"
            if cost > 0:
                line += f"  ·  ¥{cost}"
            pdf.cell(138, 6, line, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # === 页脚 ===
    pdf.ln(6)
    pdf.set_font("zh", size=8)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(170, 6, "由 旅行 AI 助手 生成", align="C")

    return bytes(pdf.output())


@router.get("/trips/{conv_id}/export")
async def export_trip(conv_id: str):
    """导出行程为 PDF 文件（浏览器自动下载）"""
    async with async_session() as db:
        conv = await db.get(Conversation, conv_id)
        if not conv or not conv.plan_snapshot:
            raise HTTPException(404, "行程不存在，请先完成一次旅行规划对话")
        plan = conv.plan_snapshot

    from urllib.parse import quote

    destination = plan.get('destination', '旅行')
    pdf_bytes = _build_trip_pdf(plan)

    filename = f"{destination}旅行方案.pdf"
    filename_encoded = quote(filename)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}",
            "Content-Length": str(len(pdf_bytes)),
        },
    )
