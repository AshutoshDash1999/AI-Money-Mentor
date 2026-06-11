import pytest
from unittest.mock import MagicMock

from app import app
import app as app_module


@pytest.fixture
def chat_client():
    """Test client with the Groq client mocked to simulate "online" mode."""
    original_client = app_module.client

    mock_choice = MagicMock()
    mock_choice.message.content = "Mocked AI reply."
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    app_module.client = mock_client
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client, mock_client

    app_module.client = original_client


def _sent_messages(mock_client):
    _, kwargs = mock_client.chat.completions.create.call_args
    return kwargs["messages"]


class TestChatContext:
    """Covers conversation history handling for the /chat endpoint (#256)."""

    def test_no_history_sends_only_current_message(self, chat_client):
        client, mock_client = chat_client
        res = client.post("/chat", json={"message": "What is SIP?"})
        assert res.status_code == 200

        messages = _sent_messages(mock_client)
        assert messages[0]["role"] == "system"
        assert messages[-1] == {"role": "user", "content": "What is SIP?"}
        assert len(messages) == 2

    def test_history_is_passed_to_groq_in_order(self, chat_client):
        client, mock_client = chat_client
        history = [
            {"role": "user", "content": "What is SIP?"},
            {"role": "assistant", "content": "SIP stands for Systematic Investment Plan."},
        ]
        res = client.post("/chat", json={"message": "How do I start one?", "history": history})
        assert res.status_code == 200

        messages = _sent_messages(mock_client)
        assert messages[1:3] == history
        assert messages[-1] == {"role": "user", "content": "How do I start one?"}

    def test_history_is_capped_to_last_ten_messages(self, chat_client):
        client, mock_client = chat_client
        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"msg-{i}"}
            for i in range(15)
        ]
        res = client.post("/chat", json={"message": "latest", "history": history})
        assert res.status_code == 200

        messages = _sent_messages(mock_client)
        # system prompt + last 10 history entries + current message
        assert len(messages) == 12
        assert messages[1]["content"] == "msg-5"
        assert messages[-2]["content"] == "msg-14"

    def test_malformed_history_entries_are_dropped(self, chat_client):
        client, mock_client = chat_client
        history = [
            {"role": "user", "content": "valid message"},
            {"role": "system", "content": "should be dropped"},
            {"content": "missing role"},
            {"role": "assistant", "content": 123},
            "not-a-dict",
        ]
        res = client.post("/chat", json={"message": "follow up", "history": history})
        assert res.status_code == 200

        contents = [m.get("content") for m in _sent_messages(mock_client)]
        assert "valid message" in contents
        assert "should be dropped" not in contents
        assert "missing role" not in contents
        assert 123 not in contents

    def test_history_must_be_a_list(self, chat_client):
        client, _ = chat_client
        res = client.post("/chat", json={"message": "hi", "history": "not-a-list"})
        assert res.status_code == 400
        assert "history" in res.get_json()["message"]

    def test_missing_history_defaults_to_empty(self, chat_client):
        client, mock_client = chat_client
        res = client.post("/chat", json={"message": "hi"})
        assert res.status_code == 200

        messages = _sent_messages(mock_client)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[-1] == {"role": "user", "content": "hi"}
