"""意图路由 — 使用 DeepSeek 快速分类用户意图"""
import json
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agent.state import AgentState
from app.agent.prompts import INTENT_ROUTER_PROMPT, ENTITY_EXTRACTION_PROMPT


router_llm = ChatOpenAI(
    model="deepseek-chat",
    api_key=settings.deepseek_api_key,
    base_url=settings.deepseek_base_url,
    temperature=0,
)


async def classify_intent(state: AgentState) -> dict:
    """分类用户意图并抽取旅行实体"""
    user_input = state["messages"][-1].content if state["messages"] else ""

    # 1. 意图分类
    resp = await router_llm.ainvoke([
        SystemMessage(content=INTENT_ROUTER_PROMPT),
        HumanMessage(content=user_input),
    ])
    try:
        intent_data = json.loads(resp.content)
    except json.JSONDecodeError:
        intent_data = {"intent": "casual", "reason": "parse error"}

    intent = intent_data.get("intent", "casual")

    # 2. 如果是规划意图，抽取实体
    destination = ""
    origin = ""
    start_date = ""
    end_date = ""
    num_travelers = 1
    budget = 0.0
    preferences: list[str] = []

    if intent == "plan_trip":
        from datetime import date
        # 简化：用 DeepSeek 抽取实体
        entity_resp = await router_llm.ainvoke([
            SystemMessage(content=ENTITY_EXTRACTION_PROMPT.format(
                current_date=date.today().isoformat(),
                home_city="上海",
                user_input=user_input,
            )),
            HumanMessage(content=user_input),
        ])
        try:
            entity = json.loads(entity_resp.content)
            destination = entity.get("destination") or ""
            origin = entity.get("origin") or "上海"
            start_date = entity.get("start_date") or ""
            end_date = entity.get("end_date") or ""
            num_travelers = entity.get("num_travelers") or 1
            budget = entity.get("budget") or 0.0
            preferences = entity.get("preferences") or []
        except json.JSONDecodeError:
            pass

    return {
        "intent": intent,
        "destination": destination,
        "origin": origin,
        "start_date": start_date,
        "end_date": end_date,
        "num_travelers": num_travelers,
        "budget": budget,
        "preferences": preferences,
        "thinking": f"识别意图: {intent}" + (f", 目的地: {destination}" if destination else ""),
    }
