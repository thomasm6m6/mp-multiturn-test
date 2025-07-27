from abc import ABC, abstractmethod
from typing import Optional
from .types import Model, Message, Tool, Role, RoleMessage, Response

class LLM(ABC):
    def __init__(self, model: Model, system_prompt: Message, tools: Optional[dict[str, Tool]] = None):
        self.model = model
        self.system_prompt = system_prompt
        self.tools = tools or {}
        self.messages: list[RoleMessage] = []

    @abstractmethod
    def run(self, prompt: Optional[Message | str] = None) -> Response:
        pass

    def add_message(self, role: Role, message: Message | str):
        if isinstance(message, str):
            message = Message(message)
        self.messages.append(RoleMessage(role, message))
