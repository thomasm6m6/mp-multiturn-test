import logging
import os
from ollama import Client
from typing import Optional

from llm import LLM, Message, Response, Usage, Model, Tool, ToolCall
from .. import models

logger = logging.getLogger(__name__)
client: Optional[Client] = None

class OllamaLLM(LLM):
    def __init__(self, model: Model, system_prompt: Message, tools: Optional[dict[str, Tool]] = None, host: str = '127.0.0.1:11434'):
        super().__init__(model, system_prompt, tools)
        self.client = client or Client(host=os.environ.get('OLLAMA_HOST', host))

    def run(self, prompt: Optional[Message | str] = None) -> Response:
        if isinstance(prompt, str):
            prompt = Message(prompt)

        messages = [{'role': 'system', 'content': str(self.system_prompt)}]
        messages += [{'role': msg.role, 'content': str(msg.message)} for msg in self.messages]
        response = self.client.chat(
            model = self.model.name,
            messages = messages,
            tools = self.get_tools(),
            think = self.model.can_think and self.model.think_budget != 'no_think',
        )
        logger.debug(response)

        ret_msg = Message(response.message.content or '', thoughts=response.message.thinking)

        in_toks = response.prompt_eval_count or 0
        out_toks = response.eval_count or 0
        in_cost, out_cost = models.get_cost(self.model.name, in_toks, out_toks)
        usage = Usage(in_toks, out_toks, in_cost, out_cost)

        if response.message.tool_calls:
            for tool in response.message.tool_calls:
                if tool.function.name in self.tools:
                    args = dict(tool.function.arguments)
                    output = self.tools[tool.function.name].callback(args)
                    ret_msg.tool_calls.append(ToolCall(tool.function.name, args, output))

        return Response(ret_msg, usage)

    def get_tools(self):
        return [{
            'type': 'function',
            'function': {
                'name': tool_name,
                'description': tool.desc,
                'parameters': {
                    'type': 'object',
                    'properties': {
                        arg_name: {
                            'type': arg.kind,
                            'description': arg.desc,
                        } for arg_name, arg in tool.args.items()
                    },
                },
                'required': list(tool.args.keys()),
            },
        } for tool_name, tool in self.tools.items()]
