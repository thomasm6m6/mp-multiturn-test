import logging
from google import genai
from google.genai import types
from typing import Optional
from contextlib import suppress

from ..base import LLM
from ..types import Model, Tool, Message, Response, Usage
from .. import models

logger = logging.getLogger(__name__)
client: Optional[genai.Client] = None

class GeminiLLM(LLM):
    def __init__(self, model: Model, system_prompt: Message, tools: Optional[dict[str, Tool]] = None):
        super().__init__(model, system_prompt, tools)
        self.client = client or genai.Client()

    def run(self, prompt: Optional[Message | str] = None) -> Response:
        role_map = {'assistant': 'model'}
        messages = [{'role': role_map.get(m.role, m.role), 'parts': [{'text': m.message.text}]} for m in self.messages]
        if prompt:
            messages.append({'role': 'user', 'parts': [{'text': prompt}]})
        config = types.GenerateContentConfig(
            system_instruction = self.system_prompt)
        if self.model.can_think:
            thinking_config = types.ThinkingConfig(include_thoughts=True)
            if self.model.think_budget:
                with suppress(ValueError):
                    thinking_config.thinking_budget = int(self.model.think_budget)
                config.thinking_config = thinking_config
        response = self.client.models.generate_content(
            model = self.model.name,
            contents = messages,
            config = config
        )
        logger.debug(response)

        ret_msg = Message(response.text or '')
        thoughts = []
        for candidate in response.candidates or []:
            for part in getattr(candidate.content, 'parts', []):
                if part.thought == True:
                    thoughts.append(part.text)
        if thoughts:
            ret_msg.thoughts = '\n\n'.join(thoughts)

        in_toks = getattr(response.usage_metadata, 'prompt_token_count', 0)
        out_toks = getattr(response.usage_metadata, 'candidates_token_count', 0) + \
                   getattr(response.usage_metadata, 'thoughts_token_count', 0)
        in_cost, out_cost = models.get_cost(self.model.name, in_toks, out_toks)
        usage = Usage(in_toks, out_toks, in_cost, out_cost)

        return Response(ret_msg, usage)

# can maybe override Role enum to replace 'assistant' with 'model'?
