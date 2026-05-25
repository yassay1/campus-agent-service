from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.graphs.reminder_graph import reminder_graph
from app.services.agent_run_service import create_run, update_run
from app.services.llm_service import check_llm_configured, LLM_NOT_CONFIGURED_MSG

router = APIRouter(prefix="/api/reminders", tags=["reminders"])


class ReminderCreateRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2048, description="提醒描述")
    external_user_id: str = Field(..., min_length=1, max_length=128)
    conversation_id: str | None = None


class ReminderCreateResponse(BaseModel):
    conversation_id: str
    message_id: str
    response: str
    actions: list[dict]
    draft_id: str | None = None
    reminder_id: str | None = None
    created_at: datetime


@router.post("", response_model=ReminderCreateResponse)
async def create_reminder(req: ReminderCreateRequest):
    if not check_llm_configured():
        return ReminderCreateResponse(
            conversation_id=req.conversation_id or "new",
            message_id="error",
            response=LLM_NOT_CONFIGURED_MSG,
            actions=[{"type": "error", "code": "LLM_CONFIG_MISSING"}],
            created_at=datetime.now(timezone.utc),
        )

    run_id = await create_run(
        db=None,
        graph_name="reminder_graph",
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
        result = await reminder_graph.ainvoke(initial_state)
        await update_run(run_id, output_data=result, status="completed")
        return ReminderCreateResponse(
            conversation_id=req.conversation_id or "new",
            message_id=run_id,
            response=result.get("response", ""),
            actions=result.get("actions", []),
            draft_id=result.get("draft_id"),
            reminder_id=result.get("reminder_id"),
            created_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        await update_run(run_id, error=str(e), status="failed")
        return ReminderCreateResponse(
            conversation_id=req.conversation_id or "new",
            message_id=run_id,
            response=f"处理请求时出错：{e}",
            actions=[],
            created_at=datetime.now(timezone.utc),
        )
