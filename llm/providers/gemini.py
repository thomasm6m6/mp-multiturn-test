import logging
from google import genai
from google.genai import types
from typing import Optional

from ..base import LLM
from ..types import Model, Tool, Message, Response

logger = logging.getLogger(__name__)
client: Optional[genai.Client] = None

class GeminiLLM(LLM):
    def __init__(self, model: Model, system_prompt: Message, tools: Optional[dict[str, Tool]] = None):
        self.client = client or genai.Client()
    def run(self, prompt: Optional[Message | str] = None) -> Response:
        raise NotImplemented

# can maybe override Role enum to replace 'assistant' with 'model'?
