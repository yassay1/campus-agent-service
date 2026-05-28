"""Community service adapter — unified interface between graph nodes and community backend.

Default: mock (in-memory). Set COMMUNITY_SERVICE_MODE=real to use HTTP client.
"""

import os
import logging

from app.services.mock_community_adapter import (
    HelpTaskSearchQuery,
    HelpTaskItem,
    PublishHelpTaskResult,
    DeleteHelpTaskResult,
)

logger = logging.getLogger(__name__)

_USE_MOCK = os.getenv("COMMUNITY_SERVICE_MODE", "mock") != "real"


async def search_help_tasks(query: HelpTaskSearchQuery) -> list[HelpTaskItem]:
    if _USE_MOCK:
        from app.services.mock_community_adapter import search_help_tasks as _fn
        return await _fn(query)
    logger.warning("Real community search not implemented, returning empty")
    return []


async def search_my_help_tasks(
    external_user_id: str, filters: dict | None = None
) -> list[HelpTaskItem]:
    if _USE_MOCK:
        from app.services.mock_community_adapter import search_my_help_tasks as _fn
        return await _fn(external_user_id, filters)
    logger.warning("Real community my-tasks search not implemented, returning empty")
    return []


async def publish_help_task(
    title: str,
    description: str,
    external_user_id: str,
    category: str | None = None,
) -> PublishHelpTaskResult:
    if _USE_MOCK:
        from app.services.mock_community_adapter import publish_help_task as _fn
        return await _fn(
            title=title,
            description=description,
            external_user_id=external_user_id,
            category=category,
        )
    from app.services.community_client import community_client
    result = await community_client.create_task({
        "title": title,
        "description": description,
        "external_user_id": external_user_id,
        "category": category,
    })
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(result["error"])
    return PublishHelpTaskResult(
        task_id=result.get("id", result.get("task_id", "")),
        status="published",
    )


async def delete_help_task(external_user_id: str, task_id: str) -> DeleteHelpTaskResult:
    if _USE_MOCK:
        from app.services.mock_community_adapter import delete_help_task as _fn
        return await _fn(external_user_id, task_id)
    raise NotImplementedError("Delete via real community API not yet implemented")
