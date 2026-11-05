import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.llm import LLMError
from app.main import create_app


class FakeLLM:
    def __init__(self):
        self.calls = []

    def complete(self, messages):
        self.calls.append(messages)
        return f"reply-{len(self.calls)}"


class FailingLLM:
    def complete(self, messages):
        raise LLMError("boom")


@pytest.fixture
def llm():
    return FakeLLM()


@pytest.fixture
def client(llm):
    app = create_app(Settings(database_path=":memory:"), llm=llm)
    return TestClient(app)


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_chat_creates_conversation_and_persists(client):
    r = client.post("/api/chat", json={"message": "hello"})
    assert r.status_code == 200
    cid = r.json()["conversation_id"]
    msgs = client.get(f"/api/conversations/{cid}/messages").json()
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    assert client.get("/api/conversations").json()[0]["title"] == "hello"


def test_history_is_sent_to_model(client, llm):
    cid = client.post("/api/chat", json={"message": "one"}).json()["conversation_id"]
    client.post("/api/chat", json={"message": "two", "conversation_id": cid})
    roles = [m["role"] for m in llm.calls[1]]
    assert roles == ["system", "user", "assistant", "user"]


def test_unknown_conversation_404(client):
    assert client.post("/api/chat", json={"message": "x", "conversation_id": "nope"}).status_code == 404
    assert client.get("/api/conversations/nope/messages").status_code == 404


def test_blank_message_rejected(client):
    assert client.post("/api/chat", json={"message": "   "}).status_code == 422
    assert client.post("/api/chat", json={"message": ""}).status_code == 422


def test_delete_conversation(client):
    cid = client.post("/api/chat", json={"message": "bye"}).json()["conversation_id"]
    assert client.delete(f"/api/conversations/{cid}").status_code == 204
    assert client.delete(f"/api/conversations/{cid}").status_code == 404


def test_upstream_failure_returns_502_and_stores_nothing():
    app = create_app(Settings(database_path=":memory:"), llm=FailingLLM())
    c = TestClient(app)
    assert c.post("/api/chat", json={"message": "hi"}).status_code == 502


def test_index_served(client):
    assert "AIfullStackApp" in client.get("/").text
