from langchain_core.tools import tool


@tool
async def call_community_api(
    endpoint: str,
    method: str = "POST",
    data: dict | None = None,
) -> str:
    """调用队友社区系统的 API 接口。

    Args:
        endpoint: API 端点路径（如 /tasks/create）
        method: HTTP 方法
        data: 请求数据

    Returns:
        API 调用结果
    """
    return f"[社区 API 调用 - {method} {endpoint}] 队友社区接口待联调后可用。"
