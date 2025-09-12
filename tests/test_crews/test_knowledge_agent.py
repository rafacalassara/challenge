import pytest

from crewai import Agent
from src.agents.knowledge_agent import create_knowledge_agent


def test_knowledge_agent_structure():
    agent = create_knowledge_agent()
    assert isinstance(agent, Agent)
    assert getattr(agent, "llm", None)
    assert getattr(agent, "max_iter", 0) >= 1


def test_knowledge_agent_has_tools():
    agent = create_knowledge_agent()
    tool_names = [getattr(t, "name", "") for t in getattr(agent, "tools", [])]

    # knowledge_agent should have access to both tools (RAG and WebSearch)
    assert hasattr(agent, "tools")
    assert len(agent.tools) >= 2
    assert "InfinitePayRAG" in tool_names
    assert "WebSearch" in tool_names
