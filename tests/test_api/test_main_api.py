import pytest
from fastapi.testclient import TestClient

from src.api.main import app, InfinitePayFlow
from src.flows.state import InfinitePayState


client = TestClient(app)


def test_health_endpoint():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") in {"healthy", "ok"}
    assert "framework" in data


def test_process_endpoint_monkeypatched_flow(monkeypatch):
    async def fake_kickoff(self, inputs: dict):
        # Mutate the existing state; Flow.state has no public setter
        self.state.message = inputs["message"]
        self.state.user_id = inputs["user_id"]
        self.state.planned_steps = []
        self.state.finished_steps = []
        self.state.raw_response = "raw"
        self.state.final_response = "final"
        self.state.processing_time = 0.12
        self.state.timestamp = self.__dict__.get("_now_for_test", None) or __import__("datetime").datetime.now()
        self.state.conversation_history = []
        self.state.user_data = None
        return None

    monkeypatch.setattr(InfinitePayFlow, "kickoff_async", fake_kickoff)

    payload = {"message": "Olá", "user_id": "u1"}
    resp = client.post("/process", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert set(["response", "processing_time"]).issubset(data.keys())
    assert data["response"] == "final"


def test_flow_plot_endpoint(monkeypatch):
    called = {"plot": False}

    def fake_plot(self, name: str):
        called["plot"] = True
        return None

    monkeypatch.setattr(InfinitePayFlow, "plot", fake_plot)

    resp = client.get("/flow/plot")
    assert resp.status_code == 200
    data = resp.json()
    assert called["plot"] is True
    assert "infinitepay_flow_plot" in data.get("message", "")
