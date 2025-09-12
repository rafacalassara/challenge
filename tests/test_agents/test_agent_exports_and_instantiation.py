import pytest

from src.agents import (
    create_knowledge_agent,
    build_knowledge_prompt,
    create_support_agent,
    build_support_prompt,
    create_general_agent,
    build_general_prompt,
    create_escalation_agent,
    build_escalation_prompt,
)


def _tool_name_set(agent):
    return {getattr(t, "name", "") for t in getattr(agent, "tools", [])}


def test_agents_are_reexported_and_callable():
    # Sanity: functions are callable and return strings/agents as expected
    assert callable(create_knowledge_agent)
    assert callable(build_knowledge_prompt)
    assert callable(create_support_agent)
    assert callable(build_support_prompt)
    assert callable(create_general_agent)
    assert callable(build_general_prompt)
    assert callable(create_escalation_agent)
    assert callable(build_escalation_prompt)


def test_multiple_instantiations_produce_distinct_agents_and_tools():
    creators = [
        (create_knowledge_agent, {"InfinitePayRAG", "WebSearch"}),
        (create_support_agent, {"UserInfo", "AccountStatus", "TransactionHistory", "Ticket"}),
        (create_general_agent, set()),
        (create_escalation_agent, {"SlackNotify"}),
    ]

    for make, expected_tools in creators:
        a1 = make()
        a2 = make()
        # Different object instances
        assert a1 is not a2
        # Tools should be separate instances too (not same list object)
        assert getattr(a1, "tools", None) is not getattr(a2, "tools", None)
        # Tool name sets should match expected
        assert _tool_name_set(a1) == expected_tools
        assert _tool_name_set(a2) == expected_tools


def test_all_prompts_include_sections_and_guardrails():
    prompts = [
        build_knowledge_prompt("Tarefa X"),
        build_support_prompt("Tarefa Y"),
        build_general_prompt("Tarefa Z"),
        build_escalation_prompt("Tarefa W"),
    ]
    for p in prompts:
        assert "Identidade e Objetivo" in p
        assert "CRITICAL GUARDRAILS" in p

    # Knowledge-specific expectations mentioned no RAG source disclosure, but indicates source label
    kp = build_knowledge_prompt("Explique taxas")
    assert "Base InfinitePay" in kp
