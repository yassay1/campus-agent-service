from fastapi import APIRouter

from app.services.agent_run_service import get_run

router = APIRouter(prefix="/api/agent-runs", tags=["agent-runs"])


@router.get("/{run_id}")
async def get_agent_run(run_id: str):
    run = await get_run(run_id)
    if run is None:
        return {"error": "Agent 运行记录未找到", "run_id": run_id}
    return run
