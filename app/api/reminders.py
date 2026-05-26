from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.graphs.reminder_graph import build_reminder_graph
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


class ReminderResumeRequest(BaseModel):
    conversation_id: str = Field(..., description="会话 ID")
    decision: str = Field(..., description="approve | reject")
    payload: dict = Field(default_factory=dict)


@router.post("", response_model=ReminderCreateResponse)
async def create_reminder(req: ReminderCreateRequest, request: Request):
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

    conversation_id = req.conversation_id or f"rem_{run_id[:12]}"

    initial_state = {
        "user_message": req.message,
        "external_user_id": req.external_user_id,
        "conversation_id": conversation_id,
        "messages": [],
    }

    try:
        graph = build_reminder_graph(checkpointer=request.app.state.checkpointer)
        config = {"configurable": {"thread_id": conversation_id}}
        result = await graph.ainvoke(initial_state, config)

        # 检查是否被 interrupt 暂停
        if result and result.get("__interrupt__"):
            interrupt_tuple = result["__interrupt__"]
            last_interrupt = interrupt_tuple[-1]
            interrupt_value = last_interrupt.value if hasattr(last_interrupt, "value") else last_interrupt
            if isinstance(interrupt_value, dict):
                msg = interrupt_value.get("message", "请确认")
            else:
                msg = str(interrupt_value)
            return ReminderCreateResponse(
                conversation_id=conversation_id,
                message_id=run_id,
                response=msg,
                actions=[{
                    "type": "interrupt",
                    "needs_confirm": True,
                    "interrupt_data": interrupt_value,
                }],
                draft_id=result.get("draft_id"),
                created_at=datetime.now(timezone.utc),
            )

        await update_run(run_id, output_data=result, status="completed")
        return ReminderCreateResponse(
            conversation_id=conversation_id,
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
            conversation_id=conversation_id,
            message_id=run_id,
            response=f"处理请求时出错：{e}",
            actions=[],
            created_at=datetime.now(timezone.utc),
        )


@router.post("/resume", response_model=ReminderCreateResponse)
async def resume_reminder(req: ReminderResumeRequest, request: Request):
    """恢复被 interrupt 暂停的提醒创建。"""
    from langgraph.types import Command

    if not req.conversation_id:
        raise HTTPException(status_code=400, detail="需要有效的 conversation_id")

    run_id = str(__import__("uuid").uuid4())

    resume_value = {
        "decision": req.decision,
        "payload": req.payload,
    }

    try:
        graph = build_reminder_graph(checkpointer=request.app.state.checkpointer)
        config = {"configurable": {"thread_id": req.conversation_id}}
        result = await graph.ainvoke(Command(resume=resume_value), config)

        await update_run(run_id, output_data=result, status="completed")
        return ReminderCreateResponse(
            conversation_id=req.conversation_id,
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
            conversation_id=req.conversation_id,
            message_id=run_id,
            response=f"恢复执行时出错：{e}",
            actions=[],
            created_at=datetime.now(timezone.utc),
        )
