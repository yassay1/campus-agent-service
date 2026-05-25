from datetime import datetime, timedelta

from fastapi import APIRouter

from app.schemas.confirmation import (
    ConfirmationRequest,
    ConfirmationResponse,
    ConfirmationResolveRequest,
    ConfirmationResolveResponse,
)

router = APIRouter(prefix="/api/confirmations", tags=["confirmations"])

# 模拟确认记录存储
_confirmations: dict[str, dict] = {}


@router.post("", response_model=ConfirmationResponse)
async def create_confirmation(req: ConfirmationRequest):
    cid = f"confirm_{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"
    now = datetime.utcnow()
    expires = now + timedelta(seconds=req.expires_in_seconds or 300)
    _confirmations[cid] = {
        "confirmation_id": cid,
        "status": "pending",
        "action_type": req.action_type,
        "action_summary": req.action_summary,
        "risk_level": req.risk_level,
        "created_at": now,
        "expires_at": expires,
    }
    return ConfirmationResponse(
        confirmation_id=cid,
        status="pending",
        action_type=req.action_type,
        action_summary=req.action_summary,
        risk_level=req.risk_level,
        created_at=now,
        expires_at=expires,
    )


@router.post("/resolve", response_model=ConfirmationResolveResponse)
async def resolve_confirmation(req: ConfirmationResolveRequest):
    record = _confirmations.get(req.confirmation_id)
    if not record:
        return ConfirmationResolveResponse(
            confirmation_id=req.confirmation_id,
            status="not_found",
            approved=False,
            resolved_at=datetime.utcnow(),
        )
    record["status"] = "approved" if req.approved else "rejected"
    return ConfirmationResolveResponse(
        confirmation_id=req.confirmation_id,
        status=record["status"],
        approved=req.approved,
        resolved_at=datetime.utcnow(),
    )
