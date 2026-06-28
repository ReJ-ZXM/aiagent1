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
