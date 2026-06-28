"""行程规划 Agent — 核心规划节点，使用 DeepSeek + 工具"""
import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from app.config import settings
from app.agent.state import AgentState
from app.agent.prompts import PLANNER_SYSTEM_PROMPT
from app.agent.tools import ALL_TOOLS


def _get_planner_llm():
    return ChatOpenAI(
        model="deepseek-chat",
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        temperature=0.7, max_tokens=4096,
    )


async def plan_trip(state: AgentState) -> dict:
    """行程规划节点 — 调用工具搜集信息，然后生成行程"""
    planner_llm = _get_planner_llm()
    planner_with_tools = planner_llm.bind_tools(ALL_TOOLS)

    thinking_messages = []
    context = f"""用户旅行需求:
- 目的地: {state['destination']}
- 出发地: {state['origin']}
- 日期: {state['start_date']} 至 {state['end_date']}
- 人数: {state['num_travelers']}
- 预算: {state['budget']}元
- 偏好: {', '.join(state['preferences']) if state['preferences'] else '无特殊偏好'}
"""
    thinking_messages.append("正在分析你的需求...")
    thinking_messages.append(f"目的地: {state['destination']}, 预算: {state['budget']}元")
    thinking_messages.append("正在搜索景点和酒店...")
    search_query = f"请根据以下信息规划行程: {context}"

    response = await planner_with_tools.ainvoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=search_query),
    ])

    # 处理工具调用 — 每个 tool_call 必须有对应的 ToolMessage
    tool_results = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        from app.agent.tools.search import search_attractions, search_hotels, search_trains
        from app.agent.tools.weather import get_weather
        from app.agent.tools.map_tools import geocode_address

        tool_map = {
            "search_attractions": search_attractions,
            "search_hotels": search_hotels,
            "search_trains": search_trains,
            "get_weather": get_weather,
            "geocode_address": geocode_address,
        }

        for tc in response.tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})
            thinking_messages.append(f"正在调用: {tool_name}...")
            tool_fn = tool_map.get(tool_name)
            if tool_fn:
                try:
                    result = await tool_fn.ainvoke(tool_args)
                    tool_results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))
                except Exception as tool_err:
                    tool_results.append(ToolMessage(
                        content=str({"error": f"工具失败: {str(tool_err)}"}),
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
            HumanMessage(content=search_query),
            response,
            *tool_results,
            HumanMessage(content="请根据以上数据生成完整行程JSON方案。只输出JSON。"),
        ]
    else:
        final_messages = [
            SystemMessage(content=PLANNER_SYSTEM_PROMPT),
            HumanMessage(content=search_query),
            HumanMessage(content="请直接根据你的知识生成完整行程JSON方案。只输出JSON。"),
        ]

    final_response = await planner_llm.ainvoke(final_messages)

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
    except (json.JSONDecodeError, IndexError):
        plan = {"error": "行程生成失败", "raw": final_response.content[:500]}

    return {
        "plan": plan,
        "thinking": "\n".join(thinking_messages),
        "messages": [final_response],
    }
