"""Tests for Manager Agent catalog, prompt and config."""

from src.agents.manager_agent import get_agent_catalog, build_manager_prompt, create_manager_agent


def test_get_agent_catalog_structure_and_tools():
    catalog = get_agent_catalog()

    assert set(catalog.keys()) == {"KNOWLEDGE", "SUPPORT", "GENERAL", "ESCALATION"}

    # Knowledge tools
    knowledge_tools = [t.get("name") for t in catalog["KNOWLEDGE"]["tools"]]
    assert "InfinitePayRAG" in knowledge_tools
    assert "WebSearch" in knowledge_tools

    # Support tools
    support_tools = [t.get("name") for t in catalog["SUPPORT"]["tools"]]
    for expected in {"UserInfo", "AccountStatus", "TransactionHistory", "Ticket"}:
        assert expected in support_tools

    # Escalation tools
    escalation_tools = [t.get("name") for t in catalog["ESCALATION"]["tools"]]
    assert "SlackNotify" in escalation_tools

    # General has no tools
    assert catalog["GENERAL"]["tools"] == []


def test_build_manager_prompt_includes_catalog_and_schema():
    prompt = build_manager_prompt("quero taxas", history=[])

    assert "Equipes disponíveis" in prompt
    for team in ["KNOWLEDGE", "SUPPORT", "GENERAL", "ESCALATION"]:
        assert team in prompt

    # JSON schema hint
    assert '"steps":' in prompt and '"agent":' in prompt and '"agent_task":' in prompt

    # Inputs rendered
    assert "Mensagem: quero taxas" in prompt


def test_create_manager_agent_config():
    agent = create_manager_agent()
    assert getattr(agent, "llm", None)
    assert getattr(agent, "max_iter", 0) >= 1
