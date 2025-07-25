from openai import OpenAI
from abc import ABC, abstractmethod
from pydantic import BaseModel
from lib import Logger, used_tokens, render_system_prompt

THINKING_MODELS = [
  "o4-mini", "o3", "o3-pro",
  "gemini-2.5-flash", "gemini-2.5-pro",
]

log = Logger("llm")
client = OpenAI()

class Message(BaseModel):
  role: str
  content: str

class Model:
  def __init__(self, model):
    if '/' in model:
      self.name, self.think_budget = model.split('/', maxsplit=1)
    else:
      self.name = model
      self.think_budget = None
    self.can_think = self.name in THINKING_MODELS
    if self.think_budget and not self.can_think:
      raise ValueError(f"'think' was specified ({self.think_budget}) but model '{self.name}' is not a recognized thinking model (known thinking models are {THINKING_MODELS})")

class LLM(ABC):
  def __init__(self, model: Model | str, system_prompt_template: str, system_prompt_vars={}, multiturn=True):
    if isinstance(model, str):
      model = Model(model)
    self.model = model
    self.multiturn = multiturn
    self.system_prompt_template = system_prompt_template
    self.system_prompt_vars = system_prompt_vars
    self.system_prompt = render_system_prompt(self.system_prompt_template, self.system_prompt_vars)
    self.messages = []

  @abstractmethod
  def run(self, prompt: str) -> str:
    pass

  def set_system_prompt(self, new_prompt: str) -> None:
    self.system_prompt_template = new_prompt
    self.system_prompt = render_system_prompt(self.system_prompt_template, self.system_prompt_vars)

  def set_system_prompt_vars(self, **kwargs):
    for key, val in kwargs.items():
      self.system_prompt_vars[key] = val
    self.system_prompt = render_system_prompt(self.system_prompt_template, self.system_prompt_vars)

  def get_system_prompt(self) -> str:
    return self.system_prompt_template

  def get_system_prompt_rendered(self) -> str:
    return self.system_prompt

  def add_message(self, role: str, content: str) -> None:
    self.messages.append({"role": role, "content": content})

  def get_messages(self, role_map={}) -> str:
    def msg_to_str(msg):
      role = role_map.get(msg["role"], msg["role"])
      return f"{role}: {msg['content']}"
    return '\n'.join(map(msg_to_str, self.messages))

  def clear_messages(self):
    self.messages = []

class OpenAILLM(LLM):
  def run(self, prompt: str) -> str:
    args = {}
    if self.model.can_think:
      args["reasoning"] = {"summary": "auto"}
      if self.model.think_budget:
        args["reasoning"]["effort"] = self.model.think_budget

    response = client.responses.create(
      model = self.model.name,
      instructions = self.system_prompt,
      input = self.messages + [{"role": "user", "content": prompt}],
      **args
    )
    log(f"Response:\n{response}", quietly=True)
    used_tokens(response)

    for msg in response.output:
      if msg.type == "reasoning":
        if msg.summary:
          summary = '\n'.join(s.text for s in msg.summary)
          log(f"Reasoning:\n{summary}")
        break

    if self.multiturn:
      self.add_message("user", prompt)
      self.add_message("assistant", response.output_text)

    return response.output_text

class GeminiLLM(LLM):
  def run(self, prompt: str) -> str:
    return ""
