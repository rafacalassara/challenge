import pytest
from fastapi.testclient import TestClient

from src.api.main import app, InfinitePayFlow

client = TestClient(app)


@pytest.mark.parametrize(
    "message, expected_substring",
    [
        ("Quais são as taxas da maquininha?", "taxas"),
        ("Minha conta está bloqueada, o que faço?", "conta"),
    ],
)
def test_process_endpoint_e2e_typical_queries(monkeypatch, message, expected_substring):
    async def fake_kickoff(self, inputs: dict):
        # Populate the state similarly to a real run
        self.state.message = inputs["message"]
        self.state.user_id = inputs["user_id"]
        if "taxa" in self.state.message.lower():
            self.state.final_response = "Resposta sobre taxas da maquininha."
        elif "bloquead" in self.state.message.lower() or "conta" in self.state.message.lower():
            self.state.final_response = "Desbloqueio da conta em andamento."
        else:
            self.state.final_response = "Resposta geral do assistente."
        self.state.processing_time = 0.05

    monkeypatch.setattr(InfinitePayFlow, "kickoff_async", fake_kickoff)

    payload = {"message": message, "user_id": "u42"}
    resp = client.post("/process", json=payload)
    assert resp.status_code == 200
    data = resp.json()

    assert set(["response", "processing_time"]).issubset(data.keys())
    assert expected_substring in data["response"].lower()
