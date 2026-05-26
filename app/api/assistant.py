from datetime import datetime, timezone
import logging
import traceback
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.db.session import get_db, AsyncSession
from app.db.models import ProfessionalAgentSession, HandoffRecord
from app.schemas.chat import ChatRequest, ChatResponse
from app.graphs.assistant_graph import build_assistant_graph
from app.services.agent_run_service import create_run, update_run
from app.services.conversation_service import get_or_create_conversation
from app.services.message_service import save_message, get_recent_messages
from app.services.llm_service import check_llm_configured, LLM_NOT_CONFIGURED_MSG

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assistant", tags=["assistant"])

class ResumeRequest(BaseModel):
    conversation_id: str = Field(..., description="会话 ID")
    decision: str = Field(..., description="approve | reject | revise")
    payload: dict = Field(default_factory=dict, description="附加数据")


class ResumeResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: str = "assistant"
    content: str
    agent_name: str | None = None
    actions: list[dict] = []
    status: str = "completed"
    created_at: datetime


@router.post("/chat", response_model=ChatResponse)
async def assistant_chat(req: ChatRequest, request: Request, db: AsyncSession = Depends(get_db)):
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

    conv = await get_or_create_conversation(db, req.external_user_id, req.conversation_id)
    conversation_id = conv.id

    await save_message(db, conversation_id, "user", req.message)

    recent_msgs = await get_recent_messages(db, conversation_id, limit=10)
    recent_dicts = [
        {"role": m.role, "content": m.content}
        for m in reversed(recent_msgs)
    ]

    run_id = await create_run(
        db=db,
        graph_name="assistant_graph",
        input_data={"message": req.message, "external_user_id": req.external_user_id},
        conversation_id=conversation_id,
    )

    initial_state = {
        "user_message": req.message,
        "external_user_id": req.external_user_id,
        "conversation_id": conversation_id,
        "messages": [],
        "recent_messages": recent_dicts,
    }

    try:
        graph = build_assistant_graph(checkpointer=request.app.state.checkpointer)
        config = {"configurable": {"thread_id": conversation_id}}
        result = await graph.ainvoke(initial_state, config)

        # 检查是否被 interrupt 暂停
        if result and result.get("__interrupt__"):
            interrupt_tuple = result["__interrupt__"]
            last_interrupt = interrupt_tuple[-1]
            interrupt_value = last_interrupt.value if hasattr(last_interrupt, "value") else last_interrupt
            if isinstance(interrupt_value, dict):
                msg = interrupt_value.get("message", "请确认此操作。")
            else:
                msg = str(interrupt_value)
            return ChatResponse(
                conversation_id=conversation_id,
                message_id=run_id,
                role="assistant",
                content=msg,
                agent_name=result.get("suggested_agent"),
                actions=[{
                    "type": "interrupt",
                    "needs_confirm": True,
                    "interrupt_data": interrupt_value,
                }],
                created_at=datetime.now(timezone.utc),
            )

        await update_run(run_id, db=db, output_data=result, status="completed")

        final_response = result.get("final_response") or result.get("response", "")
        await save_message(db, conversation_id, "assistant", final_response)

        actions = result.get("actions", [])

        # 处理 handoff：创建真实 session
        nav_action = result.get("navigation_action")
        if nav_action and nav_action.get("action_type") == "navigate":
            target_agent = nav_action.get("target_agent", "")
            agent_session = ProfessionalAgentSession(
                id=str(uuid.uuid4()),
                external_user_id=req.external_user_id,
                agent_name=target_agent,
                conversation_id=conversation_id,
                handoff_context=req.message,
                status="active",
            )
            db.add(agent_session)
            await db.flush()

            handoff = HandoffRecord(
                id=str(uuid.uuid4()),
                external_user_id=req.external_user_id,
                agent_run_id=run_id,
                from_agent="assistant",
                to_agent=target_agent,
                agent_session_id=agent_session.id,
                handoff_context=req.message,
                status="completed",
            )
            db.add(handoff)
            await db.flush()

            nav_action["agent_session_id"] = agent_session.id
            for action in actions:
                if action.get("type") == "handoff":
                    action["agent_session_id"] = agent_session.id

        return ChatResponse(
            conversation_id=conversation_id,
            message_id=run_id,
            role="assistant",
            content=final_response,
            agent_name=result.get("suggested_agent"),
            actions=actions,
            created_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error("assistant_chat 处理失败：%s\n%s", e, traceback.format_exc())
        await db.rollback()
        await update_run(run_id, db=db, error=str(e), status="failed")
        return ChatResponse(
            conversation_id=conversation_id,
            message_id=run_id,
            role="assistant",
            content=f"处理请求时出错：{e}",
            agent_name=None,
            actions=[],
            created_at=datetime.now(timezone.utc),
        )


@router.post("/resume", response_model=ResumeResponse)
async def assistant_resume(req: ResumeRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """恢复被 interrupt 暂停的会话。"""
    from langgraph.types import Command

    conversation_id = req.conversation_id
    if not conversation_id or conversation_id == "new":
        raise HTTPException(status_code=400, detail="需要有效的 conversation_id")

    run_id = str(uuid.uuid4())

    resume_value = {
        "decision": req.decision,
        "payload": req.payload,
    }

    try:
        graph = build_assistant_graph(checkpointer=request.app.state.checkpointer)
        config = {"configurable": {"thread_id": conversation_id}}
        result = await graph.ainvoke(
            Command(resume=resume_value),
            config,
        )

        await update_run(run_id, db=db, output_data=result, status="completed")

        final_response = result.get("final_response") or result.get("response", "")
        await save_message(db, conversation_id, "assistant", final_response)

        actions = result.get("actions", [])

        # 处理 resumed handoff
        nav_action = result.get("navigation_action")
        if nav_action and nav_action.get("action_type") == "navigate":
            target_agent = nav_action.get("target_agent", "")
            external_user_id = result.get("external_user_id", "resume")
            agent_session = ProfessionalAgentSession(
                id=str(uuid.uuid4()),
                external_user_id=external_user_id,
                agent_name=target_agent,
                conversation_id=conversation_id,
                handoff_context=final_response,
                status="active",
            )
            db.add(agent_session)
            await db.flush()
            handoff = HandoffRecord(
                id=str(uuid.uuid4()),
                external_user_id=external_user_id,
                agent_run_id=run_id,
                from_agent="assistant",
                to_agent=target_agent,
                agent_session_id=agent_session.id,
                handoff_context=final_response,
                status="completed",
            )
            db.add(handoff)
            await db.flush()
            nav_action["agent_session_id"] = agent_session.id
            for action in actions:
                if action.get("type") == "handoff":
                    action["agent_session_id"] = agent_session.id

        status = "rejected" if req.decision == "reject" else "completed"

        return ResumeResponse(
            conversation_id=conversation_id,
            message_id=run_id,
            role="assistant",
            content=final_response,
            agent_name=result.get("suggested_agent"),
            actions=actions,
            status=status,
            created_at=datetime.now(timezone.utc),
        )
    except Exception as e:
        logger.error("assistant_resume 处理失败：%s\n%s", e, traceback.format_exc())
        await db.rollback()
        return ResumeResponse(
            conversation_id=conversation_id,
            message_id=run_id,
            role="assistant",
            content=f"恢复执行时出错：{e}",
            agent_name=None,
            actions=[],
            status="failed",
            created_at=datetime.now(timezone.utc),
        )
