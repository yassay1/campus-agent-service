"""保研学长阿泽 Agent —— 保研经验、竞赛经验、科研入门、导师联系、升学规划。"""

from app.graphs.professional_agent_graph import professional_agent_graph
from app.services.agent_run_service import create_run, update_run


async def run_postgraduate_agent(
    user_message: str,
    external_user_id: str,
    conversation_id: str | None = None,
) -> dict:
    run_id = await create_run("professional_agent_graph", {
        "user_message": user_message,
        "agent_name": "postgraduate_agent",
        "external_user_id": external_user_id,
        "conversation_id": conversation_id,
    })

    initial_state = {
        "user_message": user_message,
        "agent_name": "postgraduate_agent",
        "external_user_id": external_user_id,
        "conversation_id": conversation_id,
        "system_prompt": None,
        "rag_context": None,
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
            "agent_name": "postgraduate_agent",
            "role": "assistant",
            "content": result.get("response", ""),
            "boundary_reminder": result.get("boundary_reminder"),
        }
    except Exception as e:
        await update_run(run_id, error=str(e), status="failed")
        return {
            "conversation_id": conversation_id or "new",
            "message_id": run_id,
            "agent_name": "postgraduate_agent",
            "role": "assistant",
            "content": f"处理请求时出错：{e}",
            "boundary_reminder": None,
        }
