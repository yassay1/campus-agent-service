import pytest
from unittest.mock import AsyncMock, patch
from app.chains.assistant_planner_chain import plan_assistant_action, AssistantPlan


class TestAssistantPlannerFallback:
    @pytest.mark.asyncio
    async def test_non_json_output_falls_back_to_direct_chat(self):
        """当模型返回非 JSON 内容时，planner 应降级为 direct_chat_with_product_rag。"""
        with patch(
            "app.chains.assistant_planner_chain.llm_structured_output",
            new=AsyncMock(return_value="好的，我判断这是普通聊天"),
        ):
            plan = await plan_assistant_action("你好")
            assert isinstance(plan, AssistantPlan)
            assert plan.route == "direct_chat_with_product_rag"
            assert plan.confidence == 0.3
            assert "降级" in plan.reason

    @pytest.mark.asyncio
    async def test_empty_string_output_falls_back(self):
        """当模型返回空字符串时，planner 应降级。"""
        with patch(
            "app.chains.assistant_planner_chain.llm_structured_output",
            new=AsyncMock(return_value=""),
        ):
            plan = await plan_assistant_action("你好")
            assert isinstance(plan, AssistantPlan)
            assert plan.route == "direct_chat_with_product_rag"
            assert "降级" in plan.reason

    @pytest.mark.asyncio
    async def test_markdown_json_output_parses_correctly(self):
        """当模型返回 Markdown 代码块 JSON 时，planner 应正确解析。"""
        with patch(
            "app.chains.assistant_planner_chain.llm_structured_output",
            new=AsyncMock(return_value='```json\n{"route": "direct_chat_with_product_rag", "intent": "问候", "confidence": 0.9, "need_clarification": false, "clarification_question": null, "need_confirmation": false, "target_agent": null, "community_intent": null, "planned_tools": [], "reason": "简单问候"}\n```'),
        ):
            plan = await plan_assistant_action("你好")
            assert isinstance(plan, AssistantPlan)
            assert plan.route == "direct_chat_with_product_rag"
            assert plan.intent == "问候"
            assert plan.confidence == 0.9

    @pytest.mark.asyncio
    async def test_missing_fields_uses_defaults(self):
        """当 JSON 缺少字段时，Pydantic 使用默认值。"""
        with patch(
            "app.chains.assistant_planner_chain.llm_structured_output",
            new=AsyncMock(return_value='{"route": "direct_chat_with_product_rag", "intent": "test", "confidence": 0.5, "reason": "test"}'),
        ):
            plan = await plan_assistant_action("test")
            assert plan.route == "direct_chat_with_product_rag"
            assert plan.need_clarification is False
            assert plan.clarification_question is None
