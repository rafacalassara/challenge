import pytest

from src.agents.knowledge_agent import create_knowledge_agent, build_knowledge_prompt


def test_create_knowledge_agent_tools_and_config():
    agent = create_knowledge_agent()

    # Agent should expose RAG and WebSearch tools
    tool_names = [getattr(t, "name", "") for t in getattr(agent, "tools", [])]
    assert "InfinitePayRAG" in tool_names
    assert "WebSearch" in tool_names

    # Basic config sanity
    assert getattr(agent, "llm", None)
    assert getattr(agent, "max_iter", 0) >= 1


def test_build_knowledge_prompt_contains_guardrails_and_task():
    prompt = build_knowledge_prompt("Explique taxas da maquininha.")

    assert "CRITICAL GUARDRAILS" in prompt
    assert "InfinitePayRAG" in prompt
    assert "WebSearch" in prompt
    assert "Explique taxas da maquininha" in prompt
