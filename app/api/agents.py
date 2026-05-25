from datetime import datetime

from fastapi import APIRouter

from app.schemas.agent import (
    AgentRecommendRequest,
    AgentRecommendResponse,
    AgentChatRequest,
    AgentChatResponse,
    AgentInfo,
)
from pydantic import BaseModel, Field

from app.chains.agent_recommend_chain import recommend_agent
from app.agents.teaching_agent import run_teaching_agent
from app.agents.postgraduate_agent import run_postgraduate_agent
from app.agents.science_agent import run_science_agent
from app.agents.life_agent import run_life_agent

router = APIRouter(prefix="/api/agents", tags=["agents"])


class CreateSessionRequest(BaseModel):
    agent_name: str = Field(..., description="目标 Agent 名称")
    external_user_id: str = Field(..., min_length=1, max_length=128)
    handoff_context: str | None = Field(None, description="交接上下文")


class CreateSessionResponse(BaseModel):
    session_id: str
    agent_name: str
    external_user_id: str
    handoff_context: str | None = None
    status: str = "active"
    created_at: datetime

_AGENT_RUNNER = {
    "teaching_agent": run_teaching_agent,
    "postgraduate_agent": run_postgraduate_agent,
    "science_agent": run_science_agent,
    "life_agent": run_life_agent,
}


@router.post("/recommend", response_model=AgentRecommendResponse)
async def agent_recommend(req: AgentRecommendRequest):
    result = await recommend_agent(req.message)
    agents = []
    for a in result.get("recommended_agents", []):
        agents.append(AgentInfo(
            agent_name=a["agent_name"],
            display_name=a.get("display_name", a["agent_name"]),
            description=a.get("reason", ""),
            capabilities=[],
        ))
    return AgentRecommendResponse(
        recommended_agents=agents,
        reason=result.get("overall_reason", ""),
    )


@router.post("/chat", response_model=AgentChatResponse)
async def agent_chat(req: AgentChatRequest):
    runner = _AGENT_RUNNER.get(req.agent_name)
    if runner is None:
        return AgentChatResponse(
            conversation_id=req.conversation_id or "new",
            message_id="error",
            agent_name=req.agent_name,
            role="assistant",
            content=f"未找到 Agent: {req.agent_name}。可用的 Agent: teaching_agent, postgraduate_agent, science_agent, life_agent",
            boundary_reminder=None,
            created_at=datetime.utcnow(),
        )

    result = await runner(
        user_message=req.message,
        external_user_id=req.external_user_id,
        conversation_id=req.conversation_id,
    )
    return AgentChatResponse(
        conversation_id=result["conversation_id"],
        message_id=result["message_id"],
        agent_name=result["agent_name"],
        role=result["role"],
        content=result["content"],
        boundary_reminder=result.get("boundary_reminder"),
        created_at=datetime.utcnow(),
    )


@router.post("/sessions", response_model=CreateSessionResponse)
async def create_agent_session(req: CreateSessionRequest):
    import uuid
    session_id = f"pas_{uuid.uuid4().hex[:12]}"
    return CreateSessionResponse(
        session_id=session_id,
        agent_name=req.agent_name,
        external_user_id=req.external_user_id,
        handoff_context=req.handoff_context,
        status="active",
        created_at=datetime.utcnow(),
    )
