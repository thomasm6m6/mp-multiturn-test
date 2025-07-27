import logging
from dataclasses import dataclass
from typing import Optional
from types import FunctionType, MethodType
from jinja2 import Template
from enum import Enum

from . import models

logger = logging.getLogger(__name__)

class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"

@dataclass
class ToolArg:
    kind: str
    desc: str

class Tool:
    def __init__(self, args: dict[str, ToolArg], desc: str, callback: FunctionType | MethodType):
        self.args = args
        self.desc = desc
        self.callback = callback

    def __repr__(self):
        return f'Tool(args={self.args!r}, desc={self.desc!r}, callback={self.callback!r})'

class ToolCall:
    def __init__(self, name: str, args: dict, output: Optional[str] = None):
        self.name = name
        self.args = args
        self.output = output

    def __repr__(self):
        return f'ToolCall(name={self.name!r}, args={self.args!r}, output={self.output!r})'

    def __str__(self):
        return f'`{self.name}({self.args})`' + f' = {self.output}' if self.output else ''

    def __rich__(self):
        try:
            from rich.text import Text
            import json

            args_str = json.dumps(self.args)

            text = Text()
            text.append(self.name, style='bold')
            text.append('(')
            text.append(args_str, style='italic')
            text.append(')')

            if self.output:
                text.append(' = ', style='dim')
                text.append(self.output, style='dim')
            return text
        except ImportError:
            logger.warning('Failed to import rich; falling back to str')
            return str(self)

class Message:
    def __init__(self, text: str, *, thoughts: Optional[str] = None,
                 tool_calls: Optional[list[ToolCall]] = None,
                 render: bool = False, **kwargs):
        self._template = text
        self.thoughts = thoughts
        self.tool_calls = tool_calls or []
        self.render = render
        self.kwargs = kwargs
        self._render()

    def _render(self):
        if self.render:
            template = Template(self._template,
                trim_blocks=True, lstrip_blocks=True, autoescape=True)
            self.text = template.render(**self.kwargs)
        else:
            self.text = self._template

    def update(self, **kwargs):
        self.kwargs.update(**kwargs)
        self._render()

    def __repr__(self):
        return f'Message(text={self.text!r}, thoughts={self.thoughts!r}, tool_calls={self.tool_calls!r},' \
               f' _template={self._template!r}, render={self.render!r}, kwargs={self.kwargs!r})'

    def __str__(self):
        s = ""
        if self.thoughts:
            s += f"<thinking>\n{self.thoughts}\n</thinking>\n\n"
        s += self.text
        if self.tool_calls:
            s += '\n' + '\n\n'.join(str(tool_call) for tool_call in self.tool_calls)
        return s

    def __rich__(self):
        try:
            from rich.console import Group
            from rich.text import Text

            elements = []

            if self.thoughts:
                thoughts_text = Text(self.thoughts, style='dim italic')
                elements.extend([thoughts_text, Text()])

            main_text = Text()
            main_text.append(self.text, style='bold')
            elements.append(main_text)

            if self.tool_calls:
                elements.append(Text())
                for tool_call in self.tool_calls:
                    elements.append(tool_call.__rich__())

            return Group(*elements)
        except ImportError:
            logger.warning('Failed to import rich; falling back to str')
            return str(self)

class RoleMessage:
    def __init__(self, role: Role | str, message: Message):
        self.role = str(getattr(role, 'value', role))
        self.message = message

    def __repr__(self):
        return f'RoleMessage(role={self.role!r}, message={self.message!r})'

class Model:
    def __init__(self, model: str):
        if '/' in model:
            self.name, self.think_budget = model.split('/', maxsplit=1)
        else:
            self.name = model
            self.think_budget = None
        self.can_think = models.can_think(self.name)
        if self.think_budget and not self.can_think:
            raise ValueError(f"'think' was specified ({self.think_budget}) but model '{self.name}' is not a thinking model")

    def __repr__(self):
        return f'Model(name={self.name!r}, think_budget={self.think_budget!r})'

    def __str__(self):
        return f"{self.name}/{self.think_budget}"

@dataclass
class Usage:
    input_tokens: int
    output_tokens: float
    input_cost: float
    output_cost: float

@dataclass
class Response:
    message: Message
    usage: Usage

    def __str__(self):
        return str(self.message)

    def __rich__(self):
        return self.message.__rich__()
