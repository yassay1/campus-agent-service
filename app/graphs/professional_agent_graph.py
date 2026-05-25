"""
professional_agent_graph: 专业 Agent 回答流程

UserQuestion → SelectAgentProfile → RAGSearch → LLMAnswer → BoundaryReminder → Response
"""

from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.services.llm_service import llm_chat, LLMNotConfiguredError, LLM_NOT_CONFIGURED_MSG


class ProfessionalAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    user_message: str
    agent_name: str
    external_user_id: str
    conversation_id: str | None
    system_prompt: str | None
    rag_context: list[str] | None
    response: str | None
    boundary_reminder: str | None
    error: str | None


AGENT_PROFILES = {
    "teaching_agent": {
        "system_prompt": (
            "你是教学科石老师，负责教务规则、培养方案、办事流程类咨询。"
            "回答风格：严谨、结构化、尽量给依据，不编造政策。"
            "涉及官方规则时提醒用户以学校最新通知为准。优先结合 RAG 检索资料。"
        ),
        "boundary": "以上内容基于已有知识库，具体以学校教务处最新通知为准。",
    },
    "postgraduate_agent": {
        "system_prompt": (
            "你是保研学长阿泽，负责保研经验、竞赛经验、科研入门、导师联系、升学规划。"
            "回答风格：经验型、规划型，给路径和避坑建议，不伪造具体保研数据。"
        ),
        "boundary": "以上为个人经验分享，具体政策请以学校和学院官方通知为准。",
    },
    "science_agent": {
        "system_prompt": (
            "你是理科学霸小林，负责高数、线代、大学物理、编程学习、复习计划、题目讲解思路。"
            "回答风格：步骤清楚，注重思路，不鼓励直接代写作业，引导用户理解。"
        ),
        "boundary": "以上为学习思路引导，请独立思考完成作业。",
    },
    "life_agent": {
        "system_prompt": (
            "你是生活辅导员友老师，负责宿舍、食堂、校医院、后勤、校园地图、新生入学、生活服务。"
            "回答风格：实用、温和、给下一步行动建议。"
            "涉及健康和安全时不替代专业机构判断。"
        ),
        "boundary": "如有健康或安全问题，请及时联系校医院或相关部门。",
    },
}


async def node_select_profile(state: ProfessionalAgentState) -> ProfessionalAgentState:
    profile = AGENT_PROFILES.get(state["agent_name"])
    if profile:
        state["system_prompt"] = profile["system_prompt"]
        state["boundary_reminder"] = profile["boundary"]
    else:
        state["error"] = f"未知 Agent: {state['agent_name']}"
    return state


async def node_rag_search(state: ProfessionalAgentState) -> ProfessionalAgentState:
    state["rag_context"] = []
    return state


async def node_llm_answer(state: ProfessionalAgentState) -> ProfessionalAgentState:
    if state.get("error"):
        state["response"] = state["error"]
        return state
    try:
        system_prompt = state.get("system_prompt", "你是交小伴的专业 Agent。")
        if state.get("rag_context"):
            system_prompt += "\n\n参考知识库：\n" + "\n".join(state["rag_context"])

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": state["user_message"]},
        ]
        state["response"] = await llm_chat(messages)
    except LLMNotConfiguredError:
        state["response"] = LLM_NOT_CONFIGURED_MSG
    return state


async def node_boundary_reminder(state: ProfessionalAgentState) -> ProfessionalAgentState:
    if state.get("response") and state.get("boundary_reminder"):
        state["response"] += f"\n\n---\n{state['boundary_reminder']}"
    return state


def build_professional_agent_graph() -> StateGraph:
    workflow = StateGraph(ProfessionalAgentState)

    workflow.add_node("select_profile", node_select_profile)
    workflow.add_node("rag_search", node_rag_search)
    workflow.add_node("llm_answer", node_llm_answer)
    workflow.add_node("boundary_reminder", node_boundary_reminder)

    workflow.set_entry_point("select_profile")
    workflow.add_edge("select_profile", "rag_search")
    workflow.add_edge("rag_search", "llm_answer")
    workflow.add_edge("llm_answer", "boundary_reminder")
    workflow.add_edge("boundary_reminder", END)

    return workflow.compile()


professional_agent_graph = build_professional_agent_graph()
