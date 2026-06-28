"""行程规划 Agent — DeepSeek + 工具 + 重试"""
import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agent.state import AgentState
from app.agent.prompts import PLANNER_SYSTEM_PROMPT
from app.agent.tools import ALL_TOOLS

def _get_planner_llm():
    return ChatOpenAI(
        model="deepseek-chat", api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url, temperature=0.7, max_tokens=4096,
    )

async def _call_llm_with_retry(messages, max_retries=2):
    """带重试的 LLM 调用"""
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            llm = _get_planner_llm()
            return await llm.ainvoke(messages)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                import asyncio
                await asyncio.sleep(1.5 ** attempt)
    raise last_error

async def plan_trip(state: AgentState) -> dict:
    planner_llm = _get_planner_llm()
    planner_with_tools = planner_llm.bind_tools(ALL_TOOLS)
    thinking_messages = []

    # 注入季节/节假日感知
    from datetime import date
    today = date.today()
    month = today.month
    if month in [1,2,12]: season = "冬季，注意保暖防寒"
    elif month in [3,4,5]: season = "春季，适合赏花踏青"
    elif month in [6,7,8]: season = "夏季，注意防晒避暑，暑期旅游旺季人多涨价"
    elif month in [9,10]: season = "秋季，国庆黄金周人多价高，秋色最美"
    else: season = "秋季，天气转凉"

    context = f"""用户旅行需求:
- 目的地: {state['destination']} 出发地: {state['origin']}
- 日期: {state['start_date']} 至 {state['end_date']}
- 人数: {state['num_travelers']} 预算: {state['budget']}元
- 偏好: {', '.join(state['preferences']) if state['preferences'] else '无'}
- 当前季节提示: {season}
"""
    thinking_messages.append(f"正在分析需求...{state['destination']}, 预算{state['budget']}元, {season}")
    thinking_messages.append("正在搜索景点和酒店...")
    search_query = f"请规划行程: {context}"

    try:
        response = await _call_llm_with_retry([
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=search_query),
        ])
    except Exception as e:
        return {"plan": {"error": f"规划服务暂时不可用，请稍后重试"}, "thinking": "", "messages": []}

    # 处理工具调用
    tool_results = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        from app.agent.tools.search import search_attractions, search_hotels, search_trains
        from app.agent.tools.weather import get_weather
        from app.agent.tools.map_tools import geocode_address
        tool_map = {
            "search_attractions": search_attractions, "search_hotels": search_hotels,
            "search_trains": search_trains, "get_weather": get_weather,
            "geocode_address": geocode_address,
        }
        for tc in response.tool_calls:
            tool_name = tc.get("name", "")
            tool_fn = tool_map.get(tool_name)
            if tool_fn:
                thinking_messages.append(f"正在调用: {tool_name}...")
                try:
                    result = await tool_fn.ainvoke(tc.get("args", {}))
                    tool_results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                except Exception:
                    tool_results.append(ToolMessage(
                        content=str({"error": "工具暂时不可用"}),
                        tool_call_id=tc["id"],
                    ))
            else:
                tool_results.append(ToolMessage(
                    content=str({"error": f"未知工具: {tool_name}"}),
                    tool_call_id=tc["id"],
                ))

    thinking_messages.append("正在生成行程方案...")
    if tool_results:
        final_messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=search_query), response,
            *tool_results,
            HumanMessage(content="请根据以上数据生成完整行程JSON方案。三档预算必须按公式计算。只输出JSON。"),
        ]
    else:
        final_messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=search_query),
            HumanMessage(content="请直接生成完整行程JSON方案。三档预算必须按公式计算。只输出JSON。"),
        ]

    try:
        final_response = await _call_llm_with_retry(final_messages)
    except Exception as e:
        return {"plan": {"error": f"方案生成失败，请重试"}, "thinking": "\n".join(thinking_messages), "messages": []}

    plan = None
    try:
        content = final_response.content
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content.strip()
        plan = json.loads(json_str)
    except Exception:
        plan = {"error": "行程生成失败，请重新描述需求", "raw": final_response.content[:300]}

    return {"plan": plan, "thinking": "\n".join(thinking_messages), "messages": [final_response]}
