import json
from types import SimpleNamespace

import pytest

import code_review_assistant.llm as llm
from code_review_assistant.llm import (
    AssistantConfigurationError,
    AssistantResponseError,
    _validate_response,
    review_code,
)


def test_ai_review_requires_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    with pytest.raises(AssistantConfigurationError, match="GEMINI_API_KEY"):
        review_code("def add(a, b): return a + b")


def test_review_passes_selected_language_to_model(monkeypatch: pytest.MonkeyPatch) -> None:
    response_payload = {
        "summary": "The function adds two values.",
        "findings": [],
        "tests": "test('adds values', () => expect(add(1, 2)).toBe(3));",
    }

    class FakeCompletions:
        messages: list[dict[str, str]] = []

        def create(self, **kwargs: object) -> SimpleNamespace:
            self.messages = kwargs["messages"]  # type: ignore[assignment]
            return SimpleNamespace(
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content=json.dumps(response_payload))
                    )
                ]
            )

    completions = FakeCompletions()

    class FakeClient:
        def __init__(self, **_: object) -> None:
            self.chat = SimpleNamespace(completions=completions)

    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(llm, "OpenAI", FakeClient)

    result = review_code("function add(a, b) { return a + b; }", "JavaScript")

    assert result["tests"] == response_payload["tests"]
    assert "JavaScript" in completions.messages[1]["content"]


def test_validates_well_formed_review() -> None:
    payload = {
        "summary": "Looks good.",
        "findings": [
            {
                "severity": "low",
                "title": "Consider a clearer name",
                "line": 2,
                "explanation": "The name is vague.",
                "suggestion": "Use a descriptive name.",
            }
        ],
        "tests": "def test_example():\n    assert True\n",
    }

    assert _validate_response(payload) == payload


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"summary": "ok", "findings": [], "tests": ""},
        {
            "summary": "ok",
            "findings": [{"severity": "unknown", "title": "x", "line": 1, "explanation": "x", "suggestion": "x"}],
            "tests": "def test_x(): pass",
        },
        {
            "summary": "ok",
            "findings": [{"severity": [], "title": "x", "line": 1, "explanation": "x", "suggestion": "x"}],
            "tests": "def test_x(): pass",
        },
    ],
)
def test_rejects_malformed_review(payload: dict[str, object]) -> None:
    with pytest.raises(AssistantResponseError):
        _validate_response(payload)
