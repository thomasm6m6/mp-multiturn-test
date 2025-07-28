import logging
from google import genai
from google.genai import types
from typing import Optional
from contextlib import suppress

from ..base import LLM
from ..types import Model, Tool, Message, Response, Usage, ToolCall
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
        config_args = {}
        if self.model.can_think:
            if self.model.think_budget:
                with suppress(ValueError):
                    config_args['thinking_config'] = types.ThinkingConfig(
                        include_thoughts=True, thinking_budget=int(self.model.think_budget))
            else:
                config_args['thinking_config'] = types.ThinkingConfig(include_thoughts=True)
        if self.tools:
            config_args['tools'] = [types.Tool(function_declarations=[tool]) for tool in self.get_tools()] # type: ignore

        logger.debug(f'Calling generate_content with model={self.model.name}, contents={messages}, system_instruction={self.system_prompt}, and config args: {config_args}')
        response = self.client.models.generate_content(
            model = self.model.name,
            contents = messages,
            config = types.GenerateContentConfig(
                system_instruction = self.system_prompt,
                **config_args
            )
        )
        logger.debug(response)

        ret_msg = Message(response.text or '')
        thoughts = []
        for candidate in response.candidates or []:
            for part in getattr(candidate.content, 'parts', []):
                if part.thought == True:
                    thoughts.append(part.text)
                if part.function_call and part.function_call.name in self.tools:
                    args = part.function_call.args
                    output = self.tools[part.function_call.name].callback(args)
                    ret_msg.tool_calls.append(ToolCall(part.function_call.name, args, output))

        if thoughts:
            ret_msg.thoughts = '\n\n'.join(thoughts)

        if response.usage_metadata is None:
            usage = Usage(0, 0, 0, 0)
        else:
            in_toks = response.usage_metadata.prompt_token_count or 0
            out_toks = (response.usage_metadata.candidates_token_count or 0) + \
                    (response.usage_metadata.thoughts_token_count or 0)
            in_cost, out_cost = models.get_cost(self.model.name, in_toks, out_toks)
            usage = Usage(in_toks, out_toks, in_cost, out_cost)

        return Response(ret_msg, usage)

    def get_tools(self):
        return [{
            "name": tool_name,
            "description": tool.desc,
            "parameters": {
                "type": "object",
                "properties": {
                    arg_name: {
                        "type": arg.kind,
                        "description": arg.desc,
                    } for arg_name, arg in tool.args.items()
                },
                "required": list(tool.args.keys()),
            },
        } for tool_name, tool in self.tools.items()]

# can maybe override Role enum to replace 'assistant' with 'model'?
