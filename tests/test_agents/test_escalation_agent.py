import pytest

from src.agents.escalation_agent import create_escalation_agent, build_escalation_prompt


def test_create_escalation_agent_tools_and_config():
    agent = create_escalation_agent()
    tool_names = [getattr(t, "name", "") for t in getattr(agent, "tools", [])]

    # Should include SlackNotify tool
    assert "SlackNotify" in tool_names

    # Basic config sanity
    assert getattr(agent, "llm", None)
    assert getattr(agent, "max_iter", 0) >= 1


def test_build_escalation_prompt_contains_guardrails_and_tool():
    prompt = build_escalation_prompt("Acione um humano para revisar dados sensíveis.")

    assert "CRITICAL GUARDRAILS" in prompt
    assert "SlackNotify(message: str" in prompt or "SlackNotify(" in prompt
    assert "Acione um humano para revisar dados sensíveis." in prompt
