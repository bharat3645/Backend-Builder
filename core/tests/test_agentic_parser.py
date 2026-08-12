"""
Tests for parsers/agentic_parser.py.

No real network calls are made: the OpenAI/Anthropic SDK client classes are
monkeypatched with tiny fakes, which also documents/verifies the modern
(1.x-style) call shape (`client.chat.completions.create(...)` /
`client.messages.create(...)`) the parser is expected to use.
"""

import pytest

from parsers.agentic_parser import AgenticParser


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeCompletions:
    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error

    def create(self, **kwargs):
        if self._error:
            raise self._error
        return type("Resp", (), {"choices": [_FakeChoice(self._content)]})()


class _FakeOpenAIClient:
    def __init__(self, content=None, error=None, **kwargs):
        self.chat = type("Chat", (), {"completions": _FakeCompletions(content, error)})()


class _FakeTextBlock:
    type = "text"

    def __init__(self, text):
        self.text = text


class _FakeAnthropicMessages:
    def __init__(self, content=None, error=None):
        self._content = content
        self._error = error

    def create(self, **kwargs):
        if self._error:
            raise self._error
        return type("Resp", (), {"content": [_FakeTextBlock(self._content)]})()


class _FakeAnthropicClient:
    def __init__(self, content=None, error=None, **kwargs):
        self.messages = _FakeAnthropicMessages(content, error)


VALID_YAML_DSL = """
meta:
  name: pet-api
  version: "1.0.0"
  framework: django
models:
  Pet:
    fields:
      id: { type: uuid, primary_key: true }
"""


class TestCoerceToDSL:
    def test_plain_yaml(self):
        result = AgenticParser()._coerce_to_dsl(VALID_YAML_DSL)
        assert result["meta"]["name"] == "pet-api"

    def test_strips_fenced_code_block_with_language_hint(self):
        fenced = f"```yaml\n{VALID_YAML_DSL}\n```"
        result = AgenticParser()._coerce_to_dsl(fenced)
        assert result["meta"]["name"] == "pet-api"

    def test_json_fallback(self):
        result = AgenticParser()._coerce_to_dsl('{"meta": {"name": "x"}}')
        assert result == {"meta": {"name": "x"}}

    def test_non_dict_returns_none(self):
        assert AgenticParser()._coerce_to_dsl("- just\n- a\n- list") is None

    def test_empty_returns_none(self):
        assert AgenticParser()._coerce_to_dsl("") is None

    def test_garbage_returns_none(self):
        assert AgenticParser()._coerce_to_dsl("not: valid: yaml: at: all: {[") is None


class TestOpenAIPath:
    def test_successful_call_returns_parsed_dsl(self, monkeypatch):
        monkeypatch.setattr(
            "openai.OpenAI",
            lambda **kwargs: _FakeOpenAIClient(content=VALID_YAML_DSL),
        )
        parser = AgenticParser(openai_api_key="fake-key")
        dsl = parser.parse_prompt("Build me a pet store API")
        assert dsl["meta"]["name"] == "pet-api"

    def test_sdk_failure_falls_back_to_deterministic_mock(self, monkeypatch):
        monkeypatch.setattr(
            "openai.OpenAI",
            lambda **kwargs: _FakeOpenAIClient(error=RuntimeError("rate limited")),
        )
        parser = AgenticParser(openai_api_key="fake-key")
        dsl = parser.parse_prompt("A blog with posts")
        # Falls through to _generate_mock_dsl rather than raising.
        assert "User" in dsl["models"]
        assert "Post" in dsl["models"]


class TestAnthropicPath:
    def test_used_when_only_anthropic_key_present(self, monkeypatch):
        monkeypatch.setattr(
            "anthropic.Anthropic",
            lambda **kwargs: _FakeAnthropicClient(content=VALID_YAML_DSL),
        )
        parser = AgenticParser(anthropic_api_key="fake-key")
        dsl = parser.parse_prompt("Build me a pet store API")
        assert dsl["meta"]["name"] == "pet-api"

    def test_sdk_failure_falls_back_to_deterministic_mock(self, monkeypatch):
        monkeypatch.setattr(
            "anthropic.Anthropic",
            lambda **kwargs: _FakeAnthropicClient(error=RuntimeError("down")),
        )
        parser = AgenticParser(anthropic_api_key="fake-key")
        dsl = parser.parse_prompt("A shop with products")
        assert "Product" in dsl["models"]


class TestNoKeysConfigured:
    def test_uses_deterministic_mock(self):
        parser = AgenticParser()
        dsl = parser.parse_prompt("A forum with comments")
        assert dsl["meta"]["framework"] == "django"
        assert "Comment" in dsl["models"]
