"""Mock community service adapter — 模拟队友社区接口，后期替换为真实 HTTP 调用。"""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel


class HelpTaskSearchQuery(BaseModel):
    keyword: str | None = None
    category: str | None = None
    status: str | None = None
    limit: int = 10
    offset: int = 0


class HelpTaskItem(BaseModel):
    task_id: str
    title: str
    description: str
    category: str | None
    external_user_id: str
    status: str
    created_at: str


class PublishHelpTaskResult(BaseModel):
    task_id: str
    status: str


class DeleteHelpTaskResult(BaseModel):
    task_id: str
    status: str


# 内存模拟数据
_mock_tasks: list[HelpTaskItem] = []


def _generate_task_id() -> str:
    return f"task_{uuid.uuid4().hex[:12]}"


async def search_help_tasks(query: HelpTaskSearchQuery) -> list[HelpTaskItem]:
    results = _mock_tasks
    if query.keyword:
        keyword = query.keyword.lower()
        results = [t for t in results if keyword in t.title.lower() or keyword in t.description.lower()]
    if query.category:
        results = [t for t in results if t.category == query.category]
    return results[query.offset : query.offset + query.limit]


async def search_my_help_tasks(external_user_id: str, filters: dict | None = None) -> list[HelpTaskItem]:
    return [t for t in _mock_tasks if t.external_user_id == external_user_id]


async def publish_help_task(
    title: str,
    description: str,
    external_user_id: str,
    category: str | None = None,
) -> PublishHelpTaskResult:
    task_id = _generate_task_id()
    task = HelpTaskItem(
        task_id=task_id,
        title=title,
        description=description,
        category=category,
        external_user_id=external_user_id,
        status="published",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _mock_tasks.append(task)
    return PublishHelpTaskResult(task_id=task_id, status="published")


async def delete_help_task(external_user_id: str, task_id: str) -> DeleteHelpTaskResult:
    global _mock_tasks
    _mock_tasks = [t for t in _mock_tasks if not (t.task_id == task_id and t.external_user_id == external_user_id)]
    return DeleteHelpTaskResult(task_id=task_id, status="deleted")


# 预填充一些 mock 数据
async def _seed_mock_data():
    seeds = [
        ("找人帮忙取快递", "东区快递站，今天下午3点之前，帮忙取一个中通快递", "生活帮助"),
        ("求组队参加美赛", "大三，有编程基础，想找2-3个人一起参加美赛", "组队招募"),
        ("借一本线性代数教材", "需要借一本同济版线性代数，用一周", "物品借用"),
    ]
    for title, desc, cat in seeds:
        await publish_help_task(title, desc, "user_mock_001", cat)
