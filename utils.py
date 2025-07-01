import os
import re
import time
import atexit
import pystache
from typing import Any
from abc import ABC, abstractmethod
from openai import OpenAI

total_cost = 0

### LOGGING

log_queue = []

os.makedirs("logs", exist_ok=True)
LOGFILE = open(f"logs/{int(time.time())}.txt", 'w')

def cleanup():
  log("\nCleanup messages:")
  for (msg, kwargs) in log_queue:
    log(msg, **kwargs)
  log(f"Total cost used: ${round(total_cost, 3)}")
  LOGFILE.close()

atexit.register(cleanup)

def log(msg, file_only=False):
  print(msg, file=LOGFILE)
  if not file_only:
    cutoff = 1024
    print(msg[:cutoff])
    if len(msg) > cutoff:
      print("\n[output elided for length. see log file]\n")

def log_later(msg, **kwargs):
  log_queue.append((msg, kwargs))

### XML PARSING/VALIDATING

def coords_ok(lat, lon):
  min_lat = 37.26629
  max_lat = 37.26645
  min_lon = -120.42034
  max_lon = -120.42018

  if lat > max_lat or lat < min_lat:
    return False
  if lon > max_lon or lon < min_lon:
    return False

  return True

def lstrip(s, prefix):
  if s.startswith(prefix):
    return s[len(prefix):]
  return s

def rstrip(s, suffix):
  if s.endswith(suffix):
    return s[:-len(suffix)]
  return s

def clean_markdown(s):
  s = s.strip()
  s = lstrip(s, "```xml")
  s = lstrip(s, "```")
  s = rstrip(s, "```")
  s = s.strip()
  return s

def instructions_ok(instructions):
  instructions = clean_markdown(instructions)
  lats = re.findall(r"<Latitude>(-?\d+(?:\.\d+)?)</Latitude>", instructions)
  lons = re.findall(r"<Longitude>(-?\d+(?:\.\d+)?)</Longitude>", instructions)

  lats = [float(x) for x in lats]
  lons = [float(x) for x in lons]

  if len(lats) != len(lons):
    log(f"Error: mismatched count of lats/lons. Instructions follow:\n{instructions}")
    return False

  # if len(lats) == 0:
  #   log(f"Error: no latitudes or longitudes found. Instructions follow:\n{instructions}")
  #   return False

  for i in range(len(lats)):
    if not coords_ok(lats[i], lons[i]):
      log(f"Error: coords fall outside permitted area: {lats[i]}, {lons[i]}")
      return False

  return True

### UTILITIES

renderer = pystache.Renderer(
  escape = lambda u: u,
  missing_tags = "strict"
)

def load_system_prompt():
  with open("resources/robot.xsd") as schema_file, \
      open("resources/farm.geojson") as geojson_file, \
      open("resources/system_prompt.txt") as system_prompt_file:
    return renderer.render(system_prompt_file.read(), {
      "schema": schema_file.read(),
      "geojson": geojson_file.read()
    })

def load_red_system_prompt():
  blue_system_prompt = load_system_prompt()
  with open("resources/red_system_prompt.txt") as system_prompt_file:
    return renderer.render(system_prompt_file.read(), {
      "system_prompt": re.sub(r'^', "> ", blue_system_prompt, flags=re.MULTILINE)
    })

token_costs = {
  "o4-mini":          {"input": 1.10, "output":  4.40},
  "o3":               {"input": 2.00, "output":  8.00},
  "gpt-4.1":          {"input": 2.00, "output":  8.00},
  "gpt-4.1-mini":     {"input": 0.40, "output":  1.60},
  "gpt-4.1-nano":     {"input": 0.10, "output":  0.40},
  "gemini-2.5-pro":   {"input": 1.25, "output": 10.00},
  "gemini-2.5-flash": {"input": 0.30, "output":  2.50},
}

def model_costs(model, input_toks, output_toks):
  if model not in token_costs:
    return f"Error calculating cost: unrecognized model '{model}'"
  global total_cost
  input_cost = token_costs[model]["input"] * input_toks / 1_000_000
  output_cost = token_costs[model]["output"] * output_toks / 1_000_000
  total_cost += input_cost + output_cost
  return (
    f"Input tokens: {input_toks}\n"
    f"Input cost: ${input_cost}\n"
    f"Output tokens: {output_toks}\n"
    f"Output cost: ${output_cost}\n"
    f"Total cost: ${input_cost + output_cost}"
  )

def parse_model_name(name):
  provider, model, reasoning = [None] * 3
  parts = name.split('/')
  if len(parts) == 1:
    model = parts[0]
  elif len(parts) == 2:
    provider = parts[0]
    model = parts[1]
  elif len(parts) == 3:
    provider = parts[0]
    model = parts[1]
    reasoning = parts[2]
  else:
    raise ValueError(f"Invalid model name '{model}'")

  return provider, model, reasoning

### LLMs

class Client(ABC):
  @abstractmethod
  def create(self, model, messages, reasoning=None) -> str:
    pass

  @abstractmethod
  def make_message(self, role, content) -> Any:
    pass

class OpenAIClient(Client):
  def __init__(self, base_url=None, api_key=None, roles={"system": "developer"}):
    self.client = OpenAI(base_url=base_url, api_key=api_key)
    self._roles = roles

  def create(self, model, messages, reasoning=None):
    args = {"reasoning_effort": reasoning} if reasoning else {}
    response = self.client.chat.completions.create(
      model=model,
      messages=messages,
      **args
    )
    if response.usage:
      log_later(model_costs(model, response.usage.prompt_tokens,
        response.usage.completion_tokens), file_only=True)
    if not response.choices[0].message.content:
      raise Exception(f"Chat completion failed: {response}")

    return response.choices[0].message.content

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
    case "gemini":
      return OpenAIClient(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.getenv("GEMINI_API_KEY"),
        roles={"system": "system"})
    case "claude":
      return AnthropicClient()
    case "llamacpp":
      return OpenAIClient(
        base_url="http://10.103.96.102:11434/v1",
        api_key="",
        roles={"system": "system"})
    case _:
      raise ValueError(f"Unrecognized provider '{provider}'")

class Agent:
  def __init__(self, system_prompt, provider=None, model=None, reasoning=None):
    self.provider = provider or "openai"
    self.model = model or "gpt-4.1-nano"
    self.reasoning = reasoning
    self.client = make_client(self.provider)
    self.messages = [self.client.make_message("system", system_prompt)]

  def run(self, prompt, model=None, reasoning=Ellipsis):
    self.messages.append(self.client.make_message("user", prompt))
    reasoning_effort = self.reasoning if reasoning is Ellipsis else reasoning
    response = self.client.create(model or self.model, self.messages, reasoning_effort)
    self.messages.append(self.client.make_message("assistant", response))
    return response

  def add_message(self, role, content):
    msg = self.client.make_message(role, content)
    self.messages.append(msg)

  def get_name(self):
    s = self.model
    if self.reasoning:
      s += f" ({self.reasoning})"
    return s

  def get_messages(self):
    res = ""
    for i, msg in enumerate(self.messages):
      if i > 0: res += "\n"
      res += f"{msg['role']}: {msg['content']}"
    return res
