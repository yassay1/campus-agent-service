import json
from pydantic import BaseModel, Field
from typing import Literal, Optional

from app.services.llm_service import llm_structured_output


class AssistantPlan(BaseModel):
    route: Literal[
        "direct_chat_with_product_rag",
        "professional_agent_dispatch",
        "community_agent",
        "reminder_create_tool_node",
    ]
    intent: str
    confidence: float = Field(ge=0, le=1)
    need_clarification: bool = False
    clarification_question: Optional[str] = None
    need_confirmation: bool = False
    target_agent: Optional[Literal[
        "teaching_agent",
        "postgraduate_agent",
        "science_agent",
        "life_agent",
    ]] = None
    community_intent: Optional[Literal[
        "create_help_task",
        "delete_own_help_task",
        "search_help_task",
    ]] = None
    planned_tools: list[str] = []
    reason: str


ASSISTANT_PLANNER_PROMPT = """你是"交小伴"校园生活智能体平台的私人助理，负责分析用户意图并规划下一步行动。

你的职责：
- 普通聊天、产品介绍、功能说明 → direct_chat_with_product_rag
- 识别专业问题（教务/保研/学业/生活）→ professional_agent_dispatch，推荐合适的专业 Agent
- 识别求助任务需求（创建/删除/查找）→ community_agent
- 识别提醒设置需求 → reminder_create_tool_node

可用的专业 Agent：
- teaching_agent（教学科石老师）：教务规则、培养方案、办事流程
- postgraduate_agent（保研学长阿泽）：保研经验、竞赛、科研入门、升学规划
- science_agent（理科学霸小林）：高数、线代、大物、编程学习、复习计划
- life_agent（生活辅导员友老师）：宿舍、食堂、校医院、校园地图、生活服务

社区操作：
- create_help_task：用户想找人帮忙、发布求助
- delete_own_help_task：用户想取消/删除自己的求助
- search_help_task：用户想查找/搜索求助任务

请认真分析用户输入，返回以下 JSON 格式：
{
  "route": "路由目标",
  "intent": "一句话总结用户意图",
  "confidence": 0.0-1.0,
  "need_clarification": true/false,
  "clarification_question": null 或 "追问内容",
  "need_confirmation": true/false,
  "target_agent": null 或 "teaching_agent"/"postgraduate_agent"/"science_agent"/"life_agent",
  "community_intent": null 或 "create_help_task"/"delete_own_help_task"/"search_help_task",
  "planned_tools": ["需要调用的工具列表"],
  "reason": "判断理由"
}"""


async def plan_assistant_action(user_message: str) -> AssistantPlan:
    raw = await llm_structured_output(
        system_prompt=ASSISTANT_PLANNER_PROMPT,
        user_message=user_message,
        temperature=0.3,
    )
    return AssistantPlan(**json.loads(raw))
