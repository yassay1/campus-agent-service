import logging
from pydantic import BaseModel, Field, ValidationError
from typing import Literal, Optional

from app.services.llm_service import llm_structured_output
from app.utils.json_utils import safe_json_loads

logger = logging.getLogger(__name__)


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

## 路由规则（严格按优先级判断）

### 1. direct_chat_with_product_rag（普通聊天 / 产品引导）— 默认兜底
以下情况走此路由：
- 问候、闲聊、自我介绍类（如"你好""你叫什么""今天天气不错"）
- 泛化求助，用户没有指明具体要做什么（如"我需要帮助""帮帮我""你能做什么""有什么功能""这个平台怎么用""介绍一下你自己"）
- 对平台功能、专业 Agent、求助任务、提醒等功能的询问和了解（用户只是问问，没有明确说"帮我做X"）
- 任何不属于下面 2/3/4 类的输入
**关键判断：用户如果只是表达需要帮助但没说要做什么具体操作，就是 direct_chat_with_product_rag。**

### 2. professional_agent_dispatch（专业 Agent 调度）
用户在问具体的**专业知识问题**，需要专业 Agent 来回答：
- teaching_agent（教学科石老师）：教务规则、培养方案、办事流程、选课
- postgraduate_agent（保研学长阿泽）：保研经验、竞赛、科研入门、升学规划
- science_agent（理科学霸小林）：高数、线代、大物、编程学习、具体题目
- life_agent（生活辅导员友老师）：宿舍、食堂、校医院、校园地图、生活服务
**关键判断：用户问的是一个专业领域的具体问题，不是泛泛说需要帮助。**

### 3. community_agent（社区求助任务）
用户**明确表达了要操作社区求助任务**，且必须满足以下条件之一：
- create_help_task：用户明确说"帮我发布求助""帮我发一个任务""我想找人帮忙做X"（X 是具体的事）
- delete_own_help_task：用户明确说"删除/取消我的求助任务"
- search_help_task：用户明确说"查找/搜索求助任务""有没有人需要帮忙"
**关键判断：仅仅说"我需要帮助"不是 community_agent。必须是用户明确要创建/删除/查找求助任务。**

### 4. reminder_create_tool_node（创建提醒）
用户**明确表达了要设置提醒**，且包含时间信息：
- 如"提醒我明天交作业""每周三提醒我开会""设置一个提醒"
- 如果用户说要创建提醒但没有给出时间，仍需走此路由，后续节点会追问
**关键判断：必须有明确的"提醒"意图，不是泛泛的"帮助"。**

## 可用的专业 Agent
- teaching_agent（教学科石老师）：教务规则、培养方案、办事流程
- postgraduate_agent（保研学长阿泽）：保研经验、竞赛、科研入门、升学规划
- science_agent（理科学霸小林）：高数、线代、大物、编程学习、复习计划
- life_agent（生活辅导员友老师）：宿舍、食堂、校医院、校园地图、生活服务

## 社区操作
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
        output_schema={
            "route": "direct_chat_with_product_rag | professional_agent_dispatch | community_agent | reminder_create_tool_node",
            "intent": "string",
            "confidence": "number between 0 and 1",
            "need_clarification": "boolean",
            "clarification_question": "string or null",
            "need_confirmation": "boolean",
            "target_agent": "teaching_agent | postgraduate_agent | science_agent | life_agent | null",
            "community_intent": "create_help_task | delete_own_help_task | search_help_task | null",
            "planned_tools": ["string"],
            "reason": "string",
        },
        temperature=0.3,
    )

    logger.info("assistant_planner 原始输出：%r", raw)

    try:
        data = safe_json_loads(raw, source="assistant_planner")
        return AssistantPlan(**data)
    except (ValueError, ValidationError) as e:
        logger.exception("assistant_planner 输出解析失败，已降级为普通聊天。raw=%r", raw)

        return AssistantPlan(
            route="direct_chat_with_product_rag",
            intent="普通聊天或兜底回复",
            confidence=0.3,
            need_clarification=False,
            clarification_question=None,
            need_confirmation=False,
            target_agent=None,
            community_intent=None,
            planned_tools=[],
            reason=f"planner 输出解析失败，已降级：{e}",
        )
