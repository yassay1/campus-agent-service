import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.agent import AgentRecommendRequest, AgentChatRequest
from app.schemas.safety import SafetyCheckRequest
from app.schemas.confirmation import ConfirmationRequest
from app.schemas.rag import RAGSearchRequest
from app.chains.assistant_planner_chain import AssistantPlan


def test_chat_request_validation():
    req = ChatRequest(message="hello", external_user_id="u001")
    assert req.message == "hello"
    assert req.external_user_id == "u001"


def test_chat_request_empty_message():
    with pytest.raises(ValidationError):
        ChatRequest(message="", external_user_id="u001")


def test_agent_recommend_request():
    req = AgentRecommendRequest(message="我需要帮助", external_user_id="u001")
    assert req.message == "我需要帮助"


def test_safety_check_request():
    req = SafetyCheckRequest(action_type="create_task", content="test", external_user_id="u001")
    assert req.action_type == "create_task"


def test_confirmation_request():
    req = ConfirmationRequest(
        external_user_id="u001",
        action_type="create_task",
        action_summary="创建任务",
    )
    assert req.action_type == "create_task"


def test_rag_search_request():
    req = RAGSearchRequest(query="test query")
    assert req.query == "test query"
    assert req.top_k == 5


def test_assistant_plan_schema():
    plan = AssistantPlan(
        route="direct_chat_with_product_rag",
        intent="闲聊",
        confidence=0.9,
        reason="用户问好",
    )
    assert plan.route == "direct_chat_with_product_rag"
    assert plan.confidence == 0.9


def test_assistant_plan_invalid_route():
    with pytest.raises(ValidationError):
        AssistantPlan(route="invalid_route", intent="test", confidence=0.5, reason="test")
