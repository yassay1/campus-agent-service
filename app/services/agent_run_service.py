import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import AgentRun, utc_now


def _uuid() -> str:
    return str(uuid.uuid4())


async def create_run(
    db: AsyncSession | None,
    graph_name: str,
    input_data: dict,
    conversation_id: str | None = None,
) -> str:
    run_id = _uuid()
    if db is not None:
        run = AgentRun(
            id=run_id,
            conversation_id=conversation_id,
            graph_name=graph_name,
            input_data=input_data,
            status="running",
        )
        db.add(run)
        await db.flush()
    # 同时保留内存存储作为 fallback（当没有 DB session 时）
    _cleanup_run_store()
    _run_store[run_id] = {
        "run_id": run_id,
        "graph_name": graph_name,
        "input_data": input_data,
        "output_data": None,
        "status": "running",
        "error_message": None,
        "started_at": utc_now().isoformat(),
        "finished_at": None,
    }
    return run_id


async def update_run(
    run_id: str,
    db: AsyncSession | None = None,
    output_data: dict | None = None,
    status: str = "completed",
    error: str | None = None,
) -> None:
    if db is not None:
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one_or_none()
        if run:
            run.output_data = output_data
            run.status = status
            run.error_message = error
            run.finished_at = utc_now()
            await db.flush()
    if run_id in _run_store:
        _run_store[run_id]["status"] = status
        _run_store[run_id]["output_data"] = output_data
        _run_store[run_id]["error_message"] = error
        _run_store[run_id]["finished_at"] = utc_now().isoformat()


async def get_run(run_id: str, db: AsyncSession | None = None) -> dict | None:
    if db is not None:
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one_or_none()
        if run:
            return {
                "run_id": run.id,
                "graph_name": run.graph_name,
                "input_data": run.input_data,
                "output_data": run.output_data,
                "status": run.status,
                "error_message": run.error_message,
                "started_at": run.started_at.isoformat() if run.started_at else None,
                "finished_at": run.finished_at.isoformat() if run.finished_at else None,
            }
    return _run_store.get(run_id)


_run_store: dict[str, dict] = {}
_MAX_RUN_STORE_SIZE = 10_000


def _cleanup_run_store() -> None:
    """超过上限时清理最早的一半记录，防止内存无限增长."""
    if len(_run_store) > _MAX_RUN_STORE_SIZE:
        remove_count = len(_run_store) // 2
        keys_to_remove = list(_run_store.keys())[:remove_count]
        for key in keys_to_remove:
            del _run_store[key]
