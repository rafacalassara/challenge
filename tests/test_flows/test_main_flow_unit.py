import pytest
import asyncio

from src.flows.main_flow import InfinitePayFlow
from src.flows.state import PlannedSteps, Step


def _fresh_flow():
    initial_state = {
        "message": "",
        "user_id": "",
        "planned_steps": [],
        "finished_steps": [],
        "raw_response": "",
        "final_response": "",
        "processing_time": 0.0,
        "timestamp": __import__("datetime").datetime.now(),
        "conversation_history": [],
        "user_data": None,
    }
    return InfinitePayFlow(initial_state=initial_state)


def test_create_agent_and_task_mapping_basic():
    flow = _fresh_flow()

    for label in ["KNOWLEDGE", "SUPPORT", "GENERAL"]:
        agent, prompt = flow._create_agent_and_task(label, "task details")
        assert agent is not None
        assert isinstance(prompt, str) and len(prompt) > 0

    # Unknown agent should yield None
    assert flow._create_agent_and_task("UNKNOWN", "x") is None


def test_agent_manager_plan_sets_planned_steps(monkeypatch):
    flow = _fresh_flow()
    flow.state.message = "hello"

    class FakeManagerAgent:
        async def kickoff_async(self, messages, response_format):
            class R:
                def __init__(self):
                    self.pydantic = PlannedSteps(steps=[Step(agent="GENERAL", agent_task="Say hi")])
            return R()

    import src.flows.main_flow as mf
    monkeypatch.setattr(mf, "create_manager_agent", lambda: FakeManagerAgent())

    nxt = asyncio.run(flow.agent_manager_plan())

    assert nxt == "execute_next_step"
    assert len(flow.state.planned_steps) == 1
    step0 = flow.state.planned_steps[0]
    assert getattr(step0, "agent", None) == "GENERAL"


def test_apply_personality_layer_sets_final_response(monkeypatch):
    flow = _fresh_flow()
    flow.state.finished_steps = [
        {"agent": "KNOWLEDGE", "result": "Info K"},
        {"agent": "SUPPORT", "result": "Info S"},
    ]

    class FakeGeneralAgent:
        async def kickoff_async(self, messages):
            class R:
                raw = "Final message with personality"
            return R()

    monkeypatch.setattr(
        InfinitePayFlow,
        "_create_agent_and_task",
        lambda self, agent, task: (FakeGeneralAgent(), task),
    )

    nxt = asyncio.run(flow.apply_personality_layer())

    assert nxt == "complete"
    assert flow.state.final_response == "Final message with personality"
