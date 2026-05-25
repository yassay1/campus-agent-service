import pytest
from unittest.mock import patch
from app.config.settings import Settings
from app.services.llm_service import check_llm_configured, LLMNotConfiguredError, _get_chat_model


def test_llm_not_configured_when_empty():
    settings = Settings(
        llm_api_key="",
        llm_api_base="",
        llm_model_name="",
    )
    assert settings.llm_configured is False


def test_llm_configured_when_set():
    settings = Settings(
        llm_api_key="sk-test",
        llm_api_base="https://api.openai.com/v1",
        llm_model_name="gpt-4",
    )
    assert settings.llm_configured is True


def test_get_chat_model_raises_when_not_configured():
    with patch("app.services.llm_service.get_settings") as mock_settings:
        mock_settings.return_value = Settings(
            llm_api_key="",
            llm_api_base="",
            llm_model_name="",
        )
        with pytest.raises(LLMNotConfiguredError):
            _get_chat_model()


def test_llm_not_configured_error_message():
    from app.services.llm_service import LLM_NOT_CONFIGURED_MSG
    assert "LLM" in LLM_NOT_CONFIGURED_MSG
    assert ".env" in LLM_NOT_CONFIGURED_MSG
