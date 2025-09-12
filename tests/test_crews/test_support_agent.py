import pytest

from crewai import Agent
from src.agents.support_agent import create_support_agent


def test_support_agent_structure():
    agent = create_support_agent()
    assert isinstance(agent, Agent)
    assert getattr(agent, "llm", None)
    assert getattr(agent, "max_iter", 0) >= 1


def test_support_agent_has_tools():
    agent = create_support_agent()
    tool_names = [getattr(t, "name", "") for t in getattr(agent, "tools", [])]
    assert hasattr(agent, "tools") and len(agent.tools) >= 4
    for expected in {"UserInfo", "AccountStatus", "TransactionHistory", "Ticket"}:
        assert expected in tool_names
