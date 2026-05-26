"""教学科石老师 Agent —— 规则类、教务类、培养方案类、办事流程类。"""

from app.graphs.professional_agent_graph import professional_agent_graph
from app.services.agent_run_service import create_run, update_run


async def run_teaching_agent(
    user_message: str,
    external_user_id: str,
    conversation_id: str | None = None,
    rag_context: list[dict] | None = None,
    recent_messages: list[dict] | None = None,
) -> dict:
    run_id = await create_run(
        db=None,
        graph_name="professional_agent_graph",
        input_data={
            "user_message": user_message,
            "agent_name": "teaching_agent",
            "external_user_id": external_user_id,
            "conversation_id": conversation_id,
        },
        conversation_id=conversation_id,
    )

    initial_state = {
        "user_message": user_message,
        "agent_name": "teaching_agent",
        "external_user_id": external_user_id,
        "conversation_id": conversation_id,
        "system_prompt": None,
        "rag_context": rag_context or [],
        "recent_messages": recent_messages or [],
        "sources": None,
        "response": None,
        "boundary_reminder": None,
        "error": None,
        "messages": [],
    }

    try:
        result = await professional_agent_graph.ainvoke(initial_state)
        await update_run(run_id, output_data=result, status="completed")
        return {
            "conversation_id": conversation_id or "new",
            "message_id": run_id,
            "agent_name": "teaching_agent",
            "role": "assistant",
            "content": result.get("response", ""),
            "boundary_reminder": result.get("boundary_reminder"),
        }
    except Exception as e:
        await update_run(run_id, error=str(e), status="failed")
        return {
            "conversation_id": conversation_id or "new",
            "message_id": run_id,
            "agent_name": "teaching_agent",
            "role": "assistant",
            "content": f"处理请求时出错：{e}",
            "boundary_reminder": None,
        }
