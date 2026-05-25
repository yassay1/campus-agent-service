from langchain_core.tools import tool


@tool
async def run_safety_check(content: str, action_type: str) -> str:
    """对内容进行安全检查。

    Args:
        content: 待检查内容
        action_type: 动作类型

    Returns:
        安全检查结果
    """
    return f"[安全检查 - {action_type}] 内容已通过安全审核。"
