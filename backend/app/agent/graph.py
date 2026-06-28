"""LangGraph 状态图 — 定义 Agent 的完整工作流"""
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from app.agent.state import AgentState
from app.agent.router import classify_intent
from app.agent.planner import plan_trip


def route_by_intent(state: AgentState) -> str:
    """根据意图和状态路由到不同节点"""
    intent = state.get("intent", "casual")

    # 有已有计划 + 用户想修改 → 修改计划
    if intent == "modify_trip":
        return "modify_trip"

    # 首次规划 + 缺少偏好 → 先追问
    if intent == "plan_trip" and state.get("need_clarification"):
        return "clarify_needs"

    # 用户回答了追问 → 去规划
    if intent == "clarify_answer":
        return "plan_trip"

    # 已有详情 + 规划意图 → 直接规划
    if intent == "plan_trip":
        return "plan_trip"

    return "casual_reply"


async def modify_trip(state: AgentState) -> dict:
    """修改已有行程"""
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    from app.config import settings
    import json as _json

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7, max_tokens=4096,
    )

    existing_plan = state.get("plan") or {}
    user_request = state["messages"][-1].content if state["messages"] else ""

    prompt = f"""用户想要修改已有的旅行计划。请根据修改需求更新计划。

已有计划: {_json.dumps(existing_plan, ensure_ascii=False, indent=2)}

修改需求: {user_request}

只输出更新后的完整JSON计划（与原有结构一致）。如果修改需求不明确，尽量理解用户意图并给出合理调整。"""

    resp = await llm.ainvoke([
        SystemMessage(content="你是旅行规划专家。输出完整JSON计划。"),
        HumanMessage(content=prompt),
    ])
    content = resp.content.strip()
    if "```" in content:
        content = content.split("```")[1].split("```")[0].strip()
    if content.startswith("json"): content = content[4:].strip()
    try:
        plan = _json.loads(content)
    except Exception:
        plan = {"error": "修改失败", "raw": content[:500]}

    return {
        "plan": plan,
        "thinking": "正在根据你的要求调整行程...",
        "messages": [resp],
    }


async def clarify_needs(state: AgentState) -> dict:
    """追问节点 — 收集用户偏好信息"""
    from langchain_openai import ChatOpenAI
    from app.config import settings
    from app.agent.prompts import CLARIFY_PROMPT

    llm = ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7,
    )

    prompt = CLARIFY_PROMPT.format(
        destination=state.get("destination", "未知"),
        origin=state.get("origin", "上海"),
        start_date=state.get("start_date", "未知"),
        end_date=state.get("end_date", "未知"),
        num_travelers=state.get("num_travelers", 1),
        budget=state.get("budget", 0),
        preferences=", ".join(state.get("preferences", [])) or "未提及",
    )

    resp = await llm.ainvoke([
        SystemMessage(content=prompt),
        HumanMessage(content="请根据已知信息生成友好的追问"),
    ])

    return {
        "messages": [resp],
        "thinking": "需要多了解一些你的偏好...",
    }


async def casual_reply(state: AgentState) -> dict:
    """闲聊/问答节点 — 简单回复"""
    from langchain_openai import ChatOpenAI
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
    workflow.add_node("clarify_needs", clarify_needs)
    workflow.add_node("plan_trip", plan_trip)
    workflow.add_node("modify_trip", modify_trip)
    workflow.add_node("casual_reply", casual_reply)

    # 设置入口
    workflow.set_entry_point("classify_intent")

    # 条件路由
    workflow.add_conditional_edges(
        "classify_intent",
        route_by_intent,
        {
            "clarify_needs": "clarify_needs",
            "plan_trip": "plan_trip",
            "modify_trip": "modify_trip",
            "casual_reply": "casual_reply",
        },
    )

    # 结束
    workflow.add_edge("clarify_needs", END)
    workflow.add_edge("plan_trip", END)
    workflow.add_edge("modify_trip", END)
    workflow.add_edge("casual_reply", END)

    return workflow.compile()


# 全局 Agent 实例
agent_graph = build_graph()
