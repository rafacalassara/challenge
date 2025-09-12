import pytest

from src.agents.general_agent import create_general_agent, build_general_prompt


def test_create_general_agent_config():
    agent = create_general_agent()

    # General agent should not use tools
    assert not getattr(agent, "tools", [])

    # Basic config sanity
    assert getattr(agent, "llm", None)
    assert getattr(agent, "max_iter", 0) >= 1


def test_build_general_prompt_contains_guardrails_and_no_tools():
    prompt = build_general_prompt("Formate uma resposta final amigável.")

    assert "CRITICAL GUARDRAILS" in prompt
    # Explicitly states no tools and should not mention other agents' tools
    assert "(Nenhuma) — Este agente não utiliza ferramentas." in prompt
    for forbidden in ["SlackNotify(", "WebSearch(", "InfinitePayRAG", "Ticket(", "UserInfo(", "AccountStatus(", "TransactionHistory("]:
        assert forbidden not in prompt

    assert "Formate uma resposta final amigável." in prompt
