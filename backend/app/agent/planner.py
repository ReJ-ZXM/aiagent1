"""行程规划 Agent — 核心规划节点，使用 Claude + 工具"""
import json
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_anthropic import ChatAnthropic
from app.config import settings
from app.agent.state import AgentState
from app.agent.prompts import PLANNER_SYSTEM_PROMPT
from app.agent.tools import ALL_TOOLS


planner_llm = ChatAnthropic(
    model="claude-sonnet-4-6",
    api_key=settings.anthropic_api_key,
    temperature=0.7,
    max_tokens=4096,
)

# 绑定工具到 Claude
planner_with_tools = planner_llm.bind_tools(ALL_TOOLS)


async def plan_trip(state: AgentState) -> dict:
    """行程规划节点 — 调用工具搜集信息，然后生成行程"""
    thinking_messages = []

    # 构建上下文
    context = f"""用户旅行需求:
- 目的地: {state['destination']}
- 出发地: {state['origin']}
- 日期: {state['start_date']} 至 {state['end_date']}
- 人数: {state['num_travelers']}
- 预算: {state['budget']}元
- 偏好: {', '.join(state['preferences']) if state['preferences'] else '无特殊偏好'}
"""

    # Step 1: Claude 决定调用哪些工具
    thinking_messages.append("正在分析你的需求...")
    thinking_messages.append(f"目的地: {state['destination']}, 预算: {state['budget']}元")

    # Step 2: 并行搜集信息
    thinking_messages.append("正在搜索景点和酒店...")
    search_query = f"请根据以下信息规划行程: {context}"

    response = await planner_with_tools.ainvoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=search_query),
    ])

    # 处理工具调用
    tool_results = []
    if hasattr(response, "tool_calls") and response.tool_calls:
        from app.agent.tools.search import search_attractions, search_hotels
        from app.agent.tools.weather import get_weather
        from app.agent.tools.map_tools import geocode_address

        for tc in response.tool_calls:
            tool_name = tc.get("name", "")
            tool_args = tc.get("args", {})

            thinking_messages.append(f"正在调用: {tool_name}...")
            thinking_messages.append(f"查询参数: {tool_args}")

            # 执行工具
            tool_map = {
                "search_attractions": search_attractions,
                "search_hotels": search_hotels,
                "get_weather": get_weather,
                "geocode_address": geocode_address,
            }
            tool_fn = tool_map.get(tool_name)
            if tool_fn:
                result = await tool_fn.ainvoke(tool_args)
                tool_results.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    # Step 3: 用工具结果 + Claude 生成最终行程
    thinking_messages.append("正在生成行程方案...")

    final_messages = [
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=search_query),
        response,
        *tool_results,
        HumanMessage(content="请根据以上工具返回的数据，生成完整的行程 JSON 方案。严格按照 JSON 格式输出。"),
    ]

    final_response = await planner_llm.ainvoke(final_messages)

    # 解析行程 JSON
    plan = None
    try:
        content = final_response.content
        # 提取 JSON 块
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
