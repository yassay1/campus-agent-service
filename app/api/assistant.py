from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.schemas.chat import ChatRequest, ChatResponse
from app.graphs.assistant_graph import assistant_graph
from app.services.agent_run_service import create_run, update_run
from app.services.llm_service import check_llm_configured, LLM_NOT_CONFIGURED_MSG

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


@router.post("/chat", response_model=ChatResponse)
async def assistant_chat(req: ChatRequest):
    if not check_llm_configured():
        return ChatResponse(
            conversation_id=req.conversation_id or "new",
            message_id="error",
            role="assistant",
            content=LLM_NOT_CONFIGURED_MSG,
            agent_name=None,
            actions=[{"type": "error", "code": "LLM_CONFIG_MISSING"}],
            created_at=datetime.now(timezone.utc),
        )

    run_id = await create_run(
        db=None,
        graph_name="assistant_graph",
        input_data={"message": req.message, "external_user_id": req.external_user_id},
        conversation_id=req.conversation_id,
    )

    initial_state = {
        "user_message": req.message,
        "external_user_id": req.external_user_id,
        "conversation_id": req.conversation_id,
        "messages": [],
    }

    try:
        result = await assistant_graph.ainvoke(initial_state)
        await update_run(run_id, output_data=result, status="completed")
        return ChatResponse(
            conversation_id=req.conversation_id or "new",
            message_id=run_id,
            role="assistant",
            content=result.get("final_response") or result.get("response", ""),
            agent_name=result.get("suggested_agent"),
            actions=result.get("actions", []),
            created_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        await update_run(run_id, error=str(e), status="failed")
        return ChatResponse(
            conversation_id=req.conversation_id or "new",
            message_id=run_id,
            role="assistant",
            content=f"处理请求时出错：{e}",
            agent_name=None,
            actions=[],
            created_at=datetime.now(timezone.utc),
        )
