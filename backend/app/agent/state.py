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

    # 多轮追问收集的用户画像
    age: str                  # 年龄范围, e.g. "25-30"
    taste: str                # 口味偏好, e.g. "清淡，不吃辣"
    travel_style: str         # 旅行风格: "自然风光" | "人文历史" | "城市购物" | "综合"
    companion: str            # 同行人: "独自" | "情侣" | "亲子" | "朋友"

    # Agent 工作状态
    intent: str               # 意图类型: "plan_trip" | "clarify_answer" | "qa" | "casual"
    thinking: str             # 当前 thinking 消息 (SSE 发送)
    plan: dict | None         # 最终生成的行程方案 (结构化 JSON)
    need_clarification: bool  # 是否需要追问
    error: str                # 错误信息
