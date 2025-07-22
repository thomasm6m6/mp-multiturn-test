import re
import json
import time
import pystache
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any
from openai import OpenAI
from .log import log
from .model import Model, model_costs
from .globals import shared_state
from .tools import tools

__all__ = ["Model", "tools"]

class Client(ABC):
  @abstractmethod
  def create(self, model, messages, reasoning=None) -> str | None:
    pass

  @abstractmethod
  def make_message(self, role, content) -> Any:
    pass

class OpenAIClient(Client):
  def __init__(self, base_url=None, api_key=None, roles={"system": "developer"}):
    self.client = OpenAI(base_url=base_url, api_key=api_key)
    self._roles = roles

  def create(self, model, messages, reasoning=None, tools=None, text_format=None, _recur=0):
    args = {}
    if model in ["o3", "o4-mini"]:
      args["reasoning"] = {"summary": "auto"}
    if reasoning:
      args["reasoning"]["effort"] = reasoning
    if tools:
      args["tools"] = tools
      args["tool_choice"] = "required"
    if text_format:
      args["text"] = text_format
    response = self.client.responses.parse(
      model=model,
      input=messages,
      **args
    )
    if response.usage:
      in_tokens = response.usage.input_tokens
      out_tokens = response.usage.output_tokens
      in_cost, out_cost = model_costs(model, in_tokens, out_tokens)
      shared_state["total_cost"] += in_cost + out_cost
    for output in response.output:
      if output.type == "reasoning":
        if output.summary:
          log(f"REASONING: {output.summary[0].text}")
      elif output.type == "function_call":
        name = output.name
        arg = json.loads(output.arguments)
        if name == "send_xml":
          return arg["xml"]
        elif name == "refuse":
          print(f"REFUSE: {arg}")
          return arg["reason"]
      elif output.type == "message":
        return output.content[0].text
      else:
        break

    # if we're here, response is bad
    if _recur < 3:
      log(f"RESPONSE: {response}")
      log(f"LLM call failed, retrying in {_recur * 10} seconds...")
      time.sleep(_recur * 10)
      return self.create(model, messages, reasoning, _recur=_recur+1)
    else:
      raise ValueError(f"Failed or empty response: {response}")

  def make_message(self, role, content):
    chosen_role = self._roles[role] if role in self._roles else role
    return {"role": chosen_role, "content": content}

def AnthropicClient(Client):
  def __init__(self):
    raise Exception("TODO")

  def create(self, model, messages, reasoning=None):
    raise Exception("TODO")

  def make_message(self, role, content):
    raise Exception("TODO")

def make_client(provider):
  match provider:
    case "openai":
      return OpenAIClient()
    # case "gemini":
    #   return OpenAIClient(
    #     base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    #     api_key=os.getenv("GEMINI_API_KEY"),
    #     roles={"system": "system"})
    # case "claude":
    #   return AnthropicClient()
    # case "llamacpp":
    #   return OpenAIClient(
    #     base_url="http://10.103.96.102:11434/v1",
    #     api_key="",
    #     roles={"system": "system"})
    case _:
      raise ValueError(f"Unrecognized provider '{provider}'")

class Agent:
  def __init__(self, model: Model, system_prompt_file: Path, system_prompt_vars={}, tools={}, schema={}, multiturn=True):
    self.model = model
    self.client = make_client(model.provider)
    self.multiturn = multiturn
    self.tools = tools
    self.system_prompt_file = system_prompt_file
    self.system_prompt_vars = system_prompt_vars
    self.load_system_prompt(system_prompt_file, system_prompt_vars)
    self.messages = [self.client.make_message("system", self.system_prompt)]
    self.schema = schema

  def load_system_prompt(self, prompt: str | Path, system_prompt_vars={}):
    renderer = pystache.Renderer(escape = lambda u: u, missing_tags = "strict")
    prompt_str = prompt.read_text() if isinstance(prompt, Path) else prompt
    full_prompt = renderer.render(prompt_str, system_prompt_vars or self.system_prompt_vars)
    flattened = re.sub(r'\n\s*\n+', "\n\n", full_prompt)
    self.system_prompt = flattened

  def run(self, prompt, model=None, reasoning=Ellipsis):
    if self.multiturn:
      self.messages.append(self.client.make_message("user", prompt))
    reasoning_effort = self.model.reasoning if reasoning is Ellipsis else reasoning
    response = self.client.create(
      model or self.model.model,
      self.messages,
      reasoning_effort,
      text_format=self.schema
      # self.tools
    )
    if self.multiturn:
      self.messages.append(self.client.make_message("assistant", response))
    return response

  def add_message(self, role, content):
    msg = self.client.make_message(role, content)
    self.messages.append(msg)

  def get_messages(self, role_map={}):
    def msg_to_str(msg):
      role = msg["role"]
      role_str = role_map[role] if role in role_map else role
      return f"{role_str}: {msg['content']}"

    return '\n'.join(map(msg_to_str, self.messages[1:]))

  def clear_messages(self):
    self.messages = []

class Tuner(Agent):
  def __init__(self, agent: Agent, team: str, model: Model, system_prompt_file: Path, prompt_vars={}):
    super().__init__(model, system_prompt_file, prompt_vars, multiturn=False)
    self.agent = agent
    self.team = team

  def tune(self, problem: str):
    system_prompt_tmpl = self.agent.system_prompt_file.read_text()
    if self.team == "red":
      messages = self.agent.get_messages({"user": "Blue", "assistant": "Red"})
    else:
      messages = self.agent.get_messages({"user": "Red", "assistant": "Blue"})
    prompt = f"PROBLEM:\n{problem}\n\nSYSTEM PROMPT:\n{system_prompt_tmpl}\n\nMESSAGES:\n{messages}"
    log(f"Calling `tune` with prompt: {prompt}")
    new_system_prompt = self.run(prompt)
    log(f"New system prompt (pre-rendered): {new_system_prompt}")
    self.agent.load_system_prompt(new_system_prompt)
