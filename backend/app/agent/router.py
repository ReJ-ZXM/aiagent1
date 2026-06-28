"""意图路由 — 使用 DeepSeek 快速分类用户意图"""
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agent.state import AgentState
from app.agent.prompts import INTENT_ROUTER_PROMPT, ENTITY_EXTRACTION_PROMPT


def _get_router_llm():
    """懒加载 router LLM"""
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0,
    )


async def classify_intent(state: AgentState) -> dict:
    """分类用户意图并抽取旅行实体"""
    user_input = state["messages"][-1].content if state["messages"] else ""

    # 构建已知信息上下文
    known_parts = []
    if state.get("destination"):
        known_parts.append(f"目的地={state['destination']}")
    if state.get("start_date"):
        known_parts.append(f"日期={state['start_date']}-{state.get('end_date', '')}")
    if state.get("budget"):
        known_parts.append(f"预算={state['budget']}元")
    if state.get("travel_style"):
        known_parts.append(f"旅行风格={state['travel_style']}")
    known_context = ", ".join(known_parts) if known_parts else "无"

    # 1. 意图分类
    router_llm = _get_router_llm()
    resp = await router_llm.ainvoke([
        SystemMessage(content=INTENT_ROUTER_PROMPT.format(
            context=known_context,
            user_input=user_input,
        )),
        HumanMessage(content=user_input),
    ])
    try:
        intent_data = json.loads(resp.content)
    except json.JSONDecodeError:
        intent_data = {"intent": "casual", "reason": "parse error"}

    intent = intent_data.get("intent", "casual")

    # 2. 抽取实体
    from datetime import date

    # 从已有 state 中继承已知值（但目的地/日期/预算总是用最新的）
    destination = state.get("destination", "")
    origin = state.get("origin", "")
    start_date = state.get("start_date", "")
    end_date = state.get("end_date", "")
    num_travelers = state.get("num_travelers", 1)
    budget = state.get("budget", 0.0)
    preferences = list(state.get("preferences", []))
    age = state.get("age", "")
    taste = state.get("taste", "")
    travel_style = state.get("travel_style", "")
    companion = state.get("companion", "")

    if intent in ("plan_trip", "clarify_answer"):
        entity_resp = await router_llm.ainvoke([
            SystemMessage(content=ENTITY_EXTRACTION_PROMPT.format(
                current_date=date.today().isoformat(),
                home_city="上海",
                known_info=known_context,
                user_input=user_input,
            )),
            HumanMessage(content=user_input),
        ])
        try:
            entity = json.loads(entity_resp.content)
            # 目的地/日期/预算：每次都用最新提取的值覆盖（用户可能在追问中更改）
            if entity.get("destination"):
                destination = entity["destination"]
            if entity.get("origin"):
                origin = entity["origin"]
            if entity.get("start_date"):
                start_date = entity["start_date"]
            if entity.get("end_date"):
                end_date = entity["end_date"]
            if entity.get("num_travelers"):
                num_travelers = entity["num_travelers"]
            if entity.get("budget"):
                budget = entity["budget"]
            # 偏好：累积合并
            if entity.get("preferences"):
                new_prefs = entity["preferences"]
                preferences = list(set(preferences + new_prefs))
            # 用户画像：用最新值覆盖
            if entity.get("age"):
                age = entity["age"]
            if entity.get("taste"):
                taste = entity["taste"]
            if entity.get("travel_style"):
                travel_style = entity["travel_style"]
            if entity.get("companion"):
                companion = entity["companion"]
        except json.JSONDecodeError:
            pass

    # 3. 判断是否需要追问 (首次规划 + 缺少关键偏好)
    need_clarification = (
        intent == "plan_trip"
        and not state.get("need_clarification")  # 还没追问过
        and (not travel_style or not taste or not age)
    )

    return {
        "intent": intent,
        "destination": destination,
        "origin": origin,
        "start_date": start_date,
        "end_date": end_date,
        "num_travelers": num_travelers,
        "budget": budget,
        "preferences": preferences,
        "age": age,
        "taste": taste,
        "travel_style": travel_style,
        "companion": companion,
        "need_clarification": need_clarification,
        "thinking": (
            f"识别意图: {intent}, 目的地: {destination}"
            if destination else f"识别意图: {intent}"
        ),
    }
