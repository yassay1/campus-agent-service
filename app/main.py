import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api import health, assistant, agents, community_agent, safety, confirmations, rag, agent_runs, reminders

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("campus_agent")

app = FastAPI(
    title="交小伴 Agent Service",
    description="校园生活智能体平台 - Agent 后端服务层。提供私人助理、专业 Agent、社区管理员 Agent 等 AI 能力。",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health.router)
app.include_router(assistant.router)
app.include_router(agents.router)
app.include_router(community_agent.router)
app.include_router(safety.router)
app.include_router(confirmations.router)
app.include_router(rag.router)
app.include_router(agent_runs.router)
app.include_router(reminders.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
