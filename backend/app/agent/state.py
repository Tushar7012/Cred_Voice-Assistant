from app.memory.memory_store import SessionMemory


class AgentState:
    def __init__(self, session_memory: SessionMemory):
        self.memory = session_memory
