import pytest

from src.agents.support_agent import create_support_agent, build_support_prompt


def test_create_support_agent_tools_and_config():
    agent = create_support_agent()
    tool_names = [getattr(t, "name", "") for t in getattr(agent, "tools", [])]

    # Should include all support tools
    for expected in {"UserInfo", "AccountStatus", "TransactionHistory", "Ticket"}:
        assert expected in tool_names

    assert getattr(agent, "llm", None)
    assert getattr(agent, "max_iter", 0) >= 1


def test_build_support_prompt_contains_tools_and_instructions():
    prompt = build_support_prompt("Diagnostique queda nas vendas")

    assert "CRITICAL GUARDRAILS" in prompt
    assert "UserInfo(user_id)" in prompt
    assert "AccountStatus(user_id)" in prompt
    assert "TransactionHistory(user_id, limit=5)" in prompt
    assert "Ticket(user_id, issue)" in prompt
    assert "Diagnostique queda nas vendas" in prompt
