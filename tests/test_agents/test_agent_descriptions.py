import pytest

from src.agents.knowledge_agent import create_knowledge_description
from src.agents.support_agent import create_support_description
from src.agents.general_agent import create_general_description
from src.agents.escalation_agent import create_escalation_description


def _tool_names(spec):
    return [t.get("name", "") for t in spec.get("tools", [])]


def test_descriptions_structure_and_titles():
    knowledge = create_knowledge_description()
    support = create_support_description()
    general = create_general_description()
    escalation = create_escalation_description()

    # Basic structure
    for spec in [knowledge, support, general, escalation]:
        assert set(spec.keys()) == {"title", "capabilities", "tools"}
        assert isinstance(spec["capabilities"], str) and spec["capabilities"].strip()
        assert isinstance(spec["tools"], list)

    # Titles
    assert knowledge["title"] == "KNOWLEDGE"
    assert support["title"] == "SUPPORT"
    assert general["title"] == "GENERAL"
    assert escalation["title"] == "ESCALATION"


def test_descriptions_tool_lists_and_names():
    knowledge = create_knowledge_description()
    support = create_support_description()
    general = create_general_description()
    escalation = create_escalation_description()

    # Knowledge tools
    ktools = _tool_names(knowledge)
    assert len(ktools) == 2
    assert "InfinitePayRAG" in ktools and "WebSearch" in ktools

    # Support tools
    stools = _tool_names(support)
    assert len(stools) == 4
    for expected in {"UserInfo", "AccountStatus", "TransactionHistory", "Ticket"}:
        assert expected in stools

    # General has no tools
    assert _tool_names(general) == []

    # Escalation tools
    etools = _tool_names(escalation)
    assert len(etools) == 1 and etools[0] == "SlackNotify"
