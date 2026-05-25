from langchain_core.tools import tool


@tool
async def request_user_confirmation(
    action_type: str,
    action_summary: str,
    risk_level: str = "low",
) -> str:
    """请求用户确认某项操作。

    Args:
        action_type: 动作类型
        action_summary: 动作摘要
        risk_level: 风险等级

    Returns:
        确认请求 ID
    """
    return f"[用户确认请求 - {action_type}: {action_summary}] 确认记录已创建。"
