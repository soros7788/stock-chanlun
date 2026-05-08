"""轻量 AI 诊股会话（进程内内存）。"""


class ChatSession:
    def __init__(self, max_turns: int = 10):
        self.messages: list[dict] = []
        self.max_turns = max_turns

    def add(self, role: str, content: str) -> None:
        self.messages.append({"role": role, "content": content})
        if len(self.messages) > self.max_turns * 2:
            self.messages = self.messages[-self.max_turns * 2 :]

    def history(self) -> list[dict]:
        return self.messages


_chat_sessions: dict[str, ChatSession] = {}


def get_or_create_session(session_id: str) -> ChatSession:
    if session_id not in _chat_sessions:
        _chat_sessions[session_id] = ChatSession(max_turns=10)
    return _chat_sessions[session_id]
