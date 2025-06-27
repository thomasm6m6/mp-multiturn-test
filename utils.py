import os
import re
import time
import atexit
import pystache
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

### LLMs

openai_client = None
gemini_client = None
claude_client = None
llamacpp_client = None

class Agent(ABC):
  def __init__(self, system_role, system_prompt, reasoning_effort):
    self.messages = [{
      "role": system_role,
      "content": system_prompt
    }]
    self.reasoning_effort = reasoning_effort

  def print_messages(self):
    for i, msg in enumerate(self.messages):
      if i > 0: print()
      print(f"{msg['role']}: {msg['content']}")

  def run(self, prompt, model=None):
    current_model = model if model else self.default_model
    response = self.llm(current_model, prompt)
    self.messages.extend([
      {"role": "user", "content": prompt},
      {"role": "assistant", "content": response}
    ])
    return response

  def add_message(self, role, msg):
    self.messages.append({
      "role": role,
      "content": msg
    })

  def get_name(self):
    s = self.default_model
    if self.reasoning_effort:
      s += f" ({self.reasoning_effort})"
    return s

  def llm(self, model, prompt) -> str:
    args = {"reasoning_effort": self.reasoning_effort} if self.reasoning_effort else {}
    response = self.client.chat.completions.create(
      model=model,
      messages=self.messages + [{"role": "user", "content": prompt}],
      **args
    )
    log_later(model_costs(model, response.usage.prompt_tokens,
      response.usage.completion_tokens), file_only=True)
    content = response.choices[0].message.content
    if content is None:
      raise ValueError("LLM returned nil")
    return content

  @property
  @abstractmethod
  def default_model(self) -> str:
    pass

  @property
  @abstractmethod
  def client(self) -> OpenAI:
    pass

class OpenAIAgent(Agent):
  def __init__(self, system_prompt, model, reasoning=None, api_key=None):
    super().__init__("developer", system_prompt, reasoning)
    self._default_model = model
    self.reasoning_effort = reasoning

    global openai_client
    if openai_client is None:
      args = {"api_key": api_key} if api_key else {}
      openai_client = OpenAI(**args)
    self._client = openai_client

  @property
  def default_model(self) -> str:
    return self._default_model

  @property
  def client(self) -> OpenAI:
    return self._client

class GeminiAgent(Agent):
  def __init__(self, system_prompt, model, reasoning=None, api_key=None):
    super().__init__("system", system_prompt, reasoning)
    self._default_model = model
    self.reasoning_effort = reasoning

    global gemini_client
    if gemini_client is None:
      args = {"api_key": api_key} if api_key else {}
      gemini_client = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        **args
      )
    self._client = gemini_client

  @property
  def default_model(self) -> str:
    return self._default_model

  @property
  def client(self) -> OpenAI:
    return self.client

# TODO: class ClaudeAgent(Agent):

def make_agent(system_prompt, provider="openai", api_key=None, model="gpt-4.1-nano", reasoning=None) -> Agent:
  match provider:
    case "openai":
      return OpenAIAgent(system_prompt, model, reasoning, api_key)
    case "gemini":
      return GeminiAgent(system_prompt, model, reasoning, api_key)
    # case "claude":
    #   return ClaudeAgent(system_prompt, model, reasoning, api_key)
    case _:
      raise ValueError(f"Unknown provider '{provider}'")

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
  missing_tags = "strict",
  search_dirs = "resources",
  file_extension = False
)

def load_system_prompt(filename):
  with open("resources/robot.xsd") as schema_file, \
      open("resources/farm.geojson") as geojson_file, \
      open(filename) as system_prompt_file:
    return renderer.render(system_prompt_file.read(), {
      "schema": schema_file.read(),
      "geojson": geojson_file.read()
    })

token_costs = {
  "o4-mini":      {"input": 1.1, "output": 4.4},
  "o3":           {"input": 2.0, "output": 8.0},
  "gpt-4.1":      {"input": 2.0, "output": 8.0},
  "gpt-4.1-mini": {"input": 0.4, "output": 1.6},
  "gpt-4.1-nano": {"input": 0.1, "output": 0.4},
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
