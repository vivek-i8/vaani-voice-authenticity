"""V1 LLM seam tests: MockLLM behavior, factory wiring, OpenRouter prompt
construction and response parsing. No network calls — the OpenRouter HTTP
layer is exercised only for parsing/prompt logic with a fake transport.
"""
from app.llm import LLMService, MockLLM, get_llm_service
from app.llm.openrouter_llm import OpenRouterLLM
from app.core.config import settings


def test_mock_llm_returns_structured_contract_for_label():
    llm = MockLLM()
    result = llm.generate(
        {
            "label": "AI",
            "classification": "ai",
            "confidence": 0.9,
            "pitch_variance": 0.0,
            "spectral_drift": 0.0,
            "zcr_variance": 0.0,
            "entropy": 0.1,
        },
        language="en",
    )
    assert set(result.keys()) == {"summary", "technical_analysis", "recommendation", "model"}
    assert result["model"] == "mock"
    assert result["summary"]


def test_mock_llm_handles_classification_only_payload():
    llm = MockLLM()
    result = llm.generate({"classification": "human", "confidence": 0.8}, language="en")
    assert "human" in result["summary"].lower()


def test_factory_defaults_to_mock_without_key():
    assert settings.use_llm is False or settings.openrouter_api_key
    service = get_llm_service()
    assert isinstance(service, LLMService)
    assert isinstance(service, MockLLM)


def test_openrouter_requires_key():
    import app.llm.openrouter_llm as module

    original = settings.openrouter_api_key
    try:
        settings.openrouter_api_key = ""
        import pytest

        with pytest.raises(RuntimeError):
            OpenRouterLLM()
    finally:
        settings.openrouter_api_key = original


def _provider_with_transport(handler):
    settings.openrouter_api_key = "test-key"
    provider = OpenRouterLLM()
    provider._send = handler
    return provider


def test_openrouter_prompt_contains_metrics_and_format():
    provider = _provider_with_transport(lambda url, payload: {})
    prompt = provider._construct_prompt(
        {
            "label": "Human",
            "confidence": 0.87,
            "pitch_variance": 12.5,
            "spectral_drift": 340.2,
            "zcr_variance": 0.0021,
            "entropy": 0.21,
        },
        language="en",
    )
    assert "Human" in prompt
    assert "0.87" in prompt
    assert "12.50" in prompt
    assert "summary" in prompt and "technical_analysis" in prompt
    assert "Respond in English" in prompt


def test_openrouter_parses_structured_json_response():
    provider = _provider_with_transport(lambda url, payload: {})
    parsed = provider._parse_response(
        '{"summary": "s", "technical_analysis": "t", "recommendation": "r", "model": "m"}'
    )
    assert parsed == {
        "summary": "s",
        "technical_analysis": "t",
        "recommendation": "r",
        "model": "m",
    }


def test_openrouter_parses_old_format_response():
    provider = _provider_with_transport(lambda url, payload: {})
    parsed = provider._parse_response(
        '{"summary": "s", "analysis": "a", "recommendation": "r"}'
    )
    assert parsed["technical_analysis"] == "a"
    assert parsed["model"]  # defaulted to the configured model


def test_openrouter_plain_text_becomes_structured_explanation():
    provider = _provider_with_transport(lambda url, payload: {})
    parsed = provider._parse_response("This voice seems human.")
    assert parsed["summary"] == "This voice seems human."
    assert parsed["recommendation"]


def test_openrouter_malformed_json_falls_back_to_plain_text():
    provider = _provider_with_transport(lambda url, payload: {})
    parsed = provider._parse_response('{"summary": "broken", "technical_analysi')
    assert parsed["summary"]
    assert parsed["recommendation"]


def test_openrouter_generate_falls_back_on_provider_error(monkeypatch):
    provider = OpenRouterLLM()

    def boom(url, payload):
        raise RuntimeError("provider down")

    monkeypatch.setattr(provider, "_send", boom)
    result = provider.generate(
        {
            "label": "Human",
            "classification": "human",
            "confidence": 0.9,
            "entropy": 0.1,
            "pitch_variance": 1,
            "spectral_drift": 1,
            "zcr_variance": 1,
        },
        language="en",
    )
    assert result["model"] == "fallback"
    assert "human" in result["summary"].lower()
