import json
import logging
from openai import OpenAI
from typing import Optional

from ..base import LLM
from ..types import Model, Tool, Message, ToolCall, Response, Usage
from .. import models

logger = logging.getLogger(__name__)
client: Optional[OpenAI] = None

class OpenAILLM(LLM):
    def __init__(self, model: Model, system_prompt: Message, tools: Optional[dict[str, Tool]] = None):
        super().__init__(model, system_prompt, tools)
        self.client = client or OpenAI()

    def run(self, prompt: Optional[Message | str] = None) -> Response:
        if isinstance(prompt, str):
            prompt = Message(prompt)
        args = {}
        if self.model.can_think:
            args["reasoning"] = {"summary": "auto"}
            if self.model.think_budget:
                args["reasoning"]["effort"] = self.model.think_budget

        msgs = [{"role": msg.role, "content": str(msg.message)} for msg in self.messages]
        if prompt:
            msgs.append({"role": "user", "content": str(prompt)})

        tools = self.get_tools()

        logger.debug(f'Calling openai with model={self.model!r}, instructions={self.system_prompt}, input={msgs!r}, tools={tools!r}, args={args!r}')
        response = self.client.responses.create(
            model = self.model.name,
            instructions = str(self.system_prompt),
            input = msgs, # type: ignore
            tools = tools, # type: ignore
            **args)
        logger.debug(f'Response from openai: {response}')

        in_toks, out_toks = response.usage.input_tokens, response.usage.output_tokens
        in_cost, out_cost = models.get_cost(self.model.name, in_toks, out_toks)
        usage = Usage(in_toks, out_toks, in_cost, out_cost)

        ret_message = Message(response.output_text)
        for msg in response.output:
            if msg.type == 'reasoning':
                if self.model.can_think and msg.summary:
                    ret_message.thoughts = '\n\n'.join(s.text for s in msg.summary)
            elif msg.type == 'function_call':
                if msg.name in self.tools:
                    arguments = json.loads(msg.arguments)
                    output = self.tools[msg.name].callback(arguments)
                    ret_message.tool_calls.append(ToolCall(msg.name, arguments, output))

        logger.debug(response)
        return Response(ret_message, usage)

    def get_tools(self):
        return [{
            "type": "function",
            "name": tool_name,
            "description": tool.desc,
            "parameters": {
                "type": "object",
                "properties": {
                    arg_name: {
                        "type": arg.kind,
                        "description": arg.desc
                    } for arg_name, arg in tool.args.items()
                },
                "required": list(tool.args.keys()),
                "additionalProperties": False
            }
        } for tool_name, tool in self.tools.items()]
