import logging
from typing import Optional

from llm import LLM, Message, Response, RoleMessage, Tool, ToolArg

logger = logging.getLogger(__name__)

prompt_template = r"""
{% if problem %}
<PROBLEM>
{{ problem }}
</PROBLEM>
{% endif %}

<SYSTEM PROMPT>
{{ system_prompt }}
</SYSTEM PROMPT>

<CONVERSATION>
{% for message in messages %}
{{ message }}
{% endfor %}
</CONVERSATION>
""".strip()

class Tuner:
    def __init__(self, llm: LLM, extra_instructions: list[str]):
        self.llm = llm
        self.tools = {
            'add_instruction': Tool(
                args={'instruction': ToolArg(kind='string', desc='This string will be appended to the system prompt.')},
                desc='Append an instruction to the system prompt.',
                callback=self.add_instruction),

            # 'delete_instruction': Tool(
            #     args={'index': ToolArg(kind='number', desc='The index (from 1) of the instruction to delete from the "ADDITIONAL INSTRUCTIONS" section of the system prompt.')},
            #     desc='Remove an instruction from the system prompt.',
            #     callback=self.delete_instruction),
        }
        self.llm.tools.update(self.tools)
        self.extra_instructions = extra_instructions

    def run(self, *, system_prompt: str, messages: list[RoleMessage], problem: Optional[str] = None) -> Response:
        variables = {'system_prompt': system_prompt, 'messages': messages, 'problem': problem}
        prompt = Message(prompt_template, render=True, **variables)
        return self.llm.run(prompt)

    def __getattr__(self, name):
        return getattr(self.llm, name)

    def add_instruction(self, args):
        logger.info(f"Calling add_instruction with args '{args}'")
        try:
            instruction = args['instruction']
            self.extra_instructions.append(instruction)
        except (IndexError, KeyError, ValueError) as e:
            logger.warning(f'add_instruction failed: {e}')

    # FIXME if the model produces multiple delete_instruction calls, this will fail
    # def delete_instruction(self, args):
    #     logger.info(f"Calling delete_instruction with args '{args}'")
    #     try:
    #         index = int(args['index'])
    #         self.extra_instructions.pop(index)
    #     except (IndexError, KeyError, ValueError) as e:
    #         logger.warning(f'delete_instruction failed: {e}')
