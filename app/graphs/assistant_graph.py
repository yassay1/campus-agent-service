"""
assistant_graph: 私人助理 Agent 主流程 (LangGraph StateGraph)

流程:
  START → create_run → load_memory → save_user_msg
  → assistant_planner → route_by_plan
    ├─ direct_chat_with_product_rag → END
    ├─ professional_agent_dispatch → END
    ├─ community_agent → END
    └─ reminder_create → END
"""

from typing import TypedDict, Annotated, Literal

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.chains.assistant_planner_chain import plan_assistant_action, AssistantPlan
from app.chains.direct_chat_chain import direct_chat
from app.services.llm_service import LLMNotConfiguredError, LLM_NOT_CONFIGURED_MSG


class AssistantState(TypedDict, total=False):
    run_id: str
    conversation_id: str
    external_user_id: str
    user_message: str

    recent_messages: list[dict]       #最近消息
    memory_context: dict              #记忆上下文
    product_rag_context: list[dict]   #Rag检索结果
    pending_state: dict | None        #待处理状态

    assistant_plan: dict | None
    route_result: dict | None

    final_response: str | None
    navigation_action: dict | None
    confirmations: list[dict]
    tool_calls: list[dict]
    errors: list[dict]
    # 兼容旧版字段
    messages: Annotated[list, add_messages]

    intent: str | None
    confidence: float | None
    suggested_agent: str | None
    clarification_question: str | None
    response: str | None
    actions: list
    error: str | None
    community_intent: str | None


async def node_create_run(state: AssistantState) -> AssistantState:
    import uuid
    state["run_id"] = str(uuid.uuid4())
    state["errors"] = []
    state["confirmations"] = []
    state["tool_calls"] = []
    state["actions"] = []
    return state


async def node_load_memory(state: AssistantState) -> AssistantState:
    state["recent_messages"] = []
    state["memory_context"] = {}
    state["product_rag_context"] = []
    state["pending_state"] = None
    return state


async def node_save_user_message(state: AssistantState) -> AssistantState:
    return state


async def node_assistant_planner(state: AssistantState) -> AssistantState:
    try:
        plan: AssistantPlan = await plan_assistant_action(state["user_message"])
        state["assistant_plan"] = {
            "route": plan.route,
            "intent": plan.intent,
            "confidence": plan.confidence,
            "need_clarification": plan.need_clarification,
            "clarification_question": plan.clarification_question,
            "need_confirmation": plan.need_confirmation,
            "target_agent": plan.target_agent,
            "community_intent": plan.community_intent,
            "planned_tools": plan.planned_tools,
            "reason": plan.reason,
        }
        state["intent"] = plan.intent
        state["confidence"] = plan.confidence
        state["suggested_agent"] = plan.target_agent
        state["clarification_question"] = plan.clarification_question
        state["community_intent"] = plan.community_intent
    except LLMNotConfiguredError:
        state["error"] = LLM_NOT_CONFIGURED_MSG
        state["assistant_plan"] = {"route": "direct_chat_with_product_rag", "intent": "error", "reason": "LLM not configured"}
    return state


def route_by_plan(state: AssistantState) -> Literal[
    "direct_chat_with_product_rag",
    "professional_agent_dispatch",
    "community_agent",
    "reminder_create",
]:
    if state.get("error"):
        return "direct_chat_with_product_rag"
    plan = state.get("assistant_plan", {})
    route = plan.get("route", "direct_chat_with_product_rag")
    route_map = {
        "direct_chat_with_product_rag": "direct_chat_with_product_rag",
        "professional_agent_dispatch": "professional_agent_dispatch",
        "community_agent": "community_agent",
        "reminder_create_tool_node": "reminder_create",
    }
    return route_map.get(route, "direct_chat_with_product_rag")


async def node_direct_chat(state: AssistantState) -> AssistantState:
    if state.get("error"):
        state["response"] = state["error"]
        state["final_response"] = state["error"]
        return state
    try:
        answer = await direct_chat(state["user_message"])
        state["response"] = answer
        state["final_response"] = answer
    except LLMNotConfiguredError:
        state["response"] = LLM_NOT_CONFIGURED_MSG
        state["final_response"] = LLM_NOT_CONFIGURED_MSG
    return state


async def node_professional_agent_dispatch(state: AssistantState) -> AssistantState:
    target = state.get("suggested_agent", "teaching_agent")
    display_names = {
        "teaching_agent": "教学科石老师",
        "postgraduate_agent": "保研学长阿泽",
        "science_agent": "理科学霸小林",
        "life_agent": "生活辅导员友老师",
    }
    display = display_names.get(target, target)
    state["navigation_action"] = {
        "action_type": "navigate",
        "target_page": "professional_agent_chat",
        "target_agent": target,
        "agent_session_id": None,
        "handoff_context": state.get("user_message", ""),
        "display_name": display,
    }
    msg = f"这个问题更适合交给{display}来讲。我已经为你创建好了对话，点击后可以继续。"
    state["response"] = msg
    state["final_response"] = msg
    state["actions"] = [{"type": "handoff", "target_agent": target}]
    return state


async def node_community_agent_entry(state: AssistantState) -> AssistantState:
    state["response"] = "正在为你处理社区求助任务..."
    state["final_response"] = state["response"]
    state["actions"] = [{"type": "community_agent", "intent": state.get("community_intent")}]
    return state


async def node_reminder_create(state: AssistantState) -> AssistantState:
    state["response"] = "正在为你创建提醒..."
    state["final_response"] = state["response"]
    state["actions"] = [{"type": "reminder_create"}]
    return state


async def node_save_assistant_message(state: AssistantState) -> AssistantState:
    return state


def build_assistant_graph() -> StateGraph:
    workflow = StateGraph(AssistantState)

    workflow.add_node("create_run", node_create_run)
    workflow.add_node("load_memory", node_load_memory)
    workflow.add_node("save_user_message", node_save_user_message)
    workflow.add_node("assistant_planner", node_assistant_planner)
    workflow.add_node("direct_chat_with_product_rag", node_direct_chat)
    workflow.add_node("professional_agent_dispatch", node_professional_agent_dispatch)
    workflow.add_node("community_agent", node_community_agent_entry)
    workflow.add_node("reminder_create", node_reminder_create)
    workflow.add_node("save_assistant_message", node_save_assistant_message)

    workflow.set_entry_point("create_run")
    workflow.add_edge("create_run", "load_memory")
    workflow.add_edge("load_memory", "save_user_message")
    workflow.add_edge("save_user_message", "assistant_planner")

    workflow.add_conditional_edges("assistant_planner", route_by_plan, {
        "direct_chat_with_product_rag": "direct_chat_with_product_rag",
        "professional_agent_dispatch": "professional_agent_dispatch",
        "community_agent": "community_agent",
        "reminder_create": "reminder_create",
    })

    for node in ["direct_chat_with_product_rag", "professional_agent_dispatch",
                  "community_agent", "reminder_create"]:
        workflow.add_edge(node, "save_assistant_message")
    workflow.add_edge("save_assistant_message", END)

    return workflow.compile()


assistant_graph = build_assistant_graph()
