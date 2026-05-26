"""Long-term memory persisted in PostgreSQL (user_memories table).

方案 B：使用项目自定义 PostgreSQL 表存储长期记忆。
不在此阶段引入向量检索，先做简单按 external_user_id 查询和保存。
"""

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import UserMemory


async def save_user_memory(
    db: AsyncSession,
    external_user_id: str,
    content: str,
    memory_type: str = "fact",
    source: str | None = None,
    importance: float = 0.5,
    metadata: dict | None = None,
) -> UserMemory:
    memory = UserMemory(
        id=str(uuid.uuid4()),
        external_user_id=external_user_id,
        memory_type=memory_type,
        content=content,
        source=source,
        importance=importance,
        metadata_=metadata or {},
    )
    db.add(memory)
    await db.flush()
    return memory


async def get_user_memories(
    db: AsyncSession,
    external_user_id: str,
    memory_type: str | None = None,
    limit: int = 20,
) -> list[UserMemory]:
    stmt = select(UserMemory).where(UserMemory.external_user_id == external_user_id)
    if memory_type:
        stmt = stmt.where(UserMemory.memory_type == memory_type)
    stmt = stmt.order_by(UserMemory.updated_at.desc()).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def delete_user_memory(db: AsyncSession, memory_id: str) -> bool:
    result = await db.execute(select(UserMemory).where(UserMemory.id == memory_id))
    memory = result.scalar_one_or_none()
    if memory:
        await db.delete(memory)
        await db.flush()
        return True
    return False
