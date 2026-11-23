import json
from unittest.mock import MagicMock

from agent import orchestrator


class MockMessage:
    def __init__(self, content=None, tool_calls=None):
        self.role = "assistant"
        self.content = content
        self.tool_calls = tool_calls or []

    def __getattr__(self, name):
        if name == "tool_call_id":
            return getattr(self, "_tool_call_id", None)
        if name == "name":
            return getattr(self, "_name", None)
        raise AttributeError(name)


def _make_chat_resp(content=None, tool_calls=None):
    msg = MockMessage(content=content, tool_calls=tool_calls)
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _tool_call(name, args):
    tc = MagicMock()
    tc.id = "call_1"
    tc.function = MagicMock()
    tc.function.name = name
    tc.function.arguments = json.dumps(args)
    return tc


def test_policy_question_triggers_vector_search():
    client = MagicMock()
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call: LLM decides to search for policy
            return _make_chat_resp(
                tool_calls=[_tool_call("vector_search_hr_policy", {"query": "casual leave allowance"})]
            )
        else:
            # Second call: LLM answers with retrieved policy
            return _make_chat_resp(content="Employees get 12 casual leaves per year.")

    client.chat.completions.create.side_effect = side_effect
    orchestrator.set_client_for_testing(client)
    try:
        result = orchestrator.run_agentic_workflow("How many casual leaves?")
    finally:
        orchestrator.set_client_for_testing(None)
    assert "vector_search_hr_policy" in result["tools"]
    assert result["answer"] != ""
    assert "history" in result


def test_booking_question_skips_vector_search():
    client = MagicMock()
    client.chat.completions.create.return_value = _make_chat_resp(
        tool_calls=[_tool_call("submit_leave_request", {"employee_id": "EMP101", "leave_type": "casual", "start_date": "2026-06-10", "total_days": 2})]
    )
    orchestrator.set_client_for_testing(client)
    try:
        result = orchestrator.run_agentic_workflow("Book casual leave 2026-06-10 for 2 days", employee_id="EMP101")
    finally:
        orchestrator.set_client_for_testing(None)
    assert "submit_leave_request" in result["tools"]
    assert "vector_search_hr_policy" not in result["tools"]


def test_multi_turn_context():
    client = MagicMock()
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_chat_resp(
                tool_calls=[_tool_call("vector_search_hr_policy", {"query": "casual leave allowance"})]
            )
        elif call_count == 2:
            return _make_chat_resp(content="You get 12 casual leaves per year.")
        else:
            return _make_chat_resp(content="Your balance is 10 days.")

    client.chat.completions.create.side_effect = side_effect
    orchestrator.set_client_for_testing(client)
    try:
        # First turn
        r1 = orchestrator.run_agentic_workflow("How many casual leaves?", employee_id="EMP101")
        assert "vector_search_hr_policy" in r1["tools"]
        # Second turn with history
        r2 = orchestrator.run_agentic_workflow("What's my balance?", employee_id="EMP101", history=r1["history"])
        assert r2["history"] is not None
        assert len(r2["history"]) > len(r1["history"])
    finally:
        orchestrator.set_client_for_testing(None)


def test_multi_turn_booking_succeeds_with_split_keywords():
    client = MagicMock()
    call_count = 0

    def side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Turn 1: user says "Book casual leave for 2 days" -> assistant asks for start date
            return _make_chat_resp(content="Please provide the start date in YYYY-MM-DD.")
        elif call_count == 2:
            # Turn 2: user replies "2026-06-10" -> model calls submit_leave_request
            return _make_chat_resp(
                tool_calls=[_tool_call("submit_leave_request", {
                    "employee_id": "EMP101",
                    "leave_type": "casual",
                    "start_date": "2026-06-10",
                    "total_days": 2
                })]
            )
        else:
            return _make_chat_resp(content="Casual leave approved.")

    client.chat.completions.create.side_effect = side_effect
    orchestrator.set_client_for_testing(client)
    try:
        # Turn 1: "Book 2 casual days"
        r1 = orchestrator.run_agentic_workflow("Book 2 casual days", employee_id="EMP101", history=[])
        assert r1["tools"] == []

        # Turn 2: "2026-06-10" - keyword "Book" was in turn 1, date is in turn 2
        r2 = orchestrator.run_agentic_workflow("2026-06-10", employee_id="EMP101", history=r1["history"])
        assert "submit_leave_request" in r2["tools"]
    finally:
        orchestrator.set_client_for_testing(None)


def test_session_history_bounded_by_window():
    client = MagicMock()
    captured_messages = []

    def side_effect(*args, **kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        return _make_chat_resp(content="ok")

    client.chat.completions.create.side_effect = side_effect
    orchestrator.set_client_for_testing(client)
    try:
        large_history = [{"role": "user", "content": f"msg {i}"} for i in range(30)]
        orchestrator.run_agentic_workflow("New query", employee_id="EMP101", history=large_history)

        assert len(captured_messages) <= 22
        assert "Today's Date:" in captured_messages[0]["content"]
    finally:
        orchestrator.set_client_for_testing(None)


