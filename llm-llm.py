import os
import time
from abc import ABC, abstractmethod
from openai import OpenAI
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

LOGFILE = open(f"logs/{int(time.time())}.txt", 'w')

def log(msg):
  print(msg)
  print(msg, file=LOGFILE)

def load_system_prompt(filename):
  robot_xml_file = os.getenv("ROBOT_XML", "resources/robot.xml")
  farm_geojson_file = os.getenv("FARM_GEOJSON", "resources/farm.geojson")

  env = Environment(loader=FileSystemLoader("."))
  system_prompt_tmpl = env.get_template(filename)

  with open(robot_xml_file) as robot_xml, open(farm_geojson_file) as farm_geojson:
    data = {
      "ROBOT_XML": robot_xml.read(),
      "FARM_GEOJSON": farm_geojson.read()
    }

  return system_prompt_tmpl.render(data)

defender_system_prompt = load_system_prompt("resources/defender_system_prompt.txt")
attacker_system_prompt = load_system_prompt("resources/attacker_system_prompt.txt")

load_dotenv()

openai = OpenAI()
response = openai.moderations.create(
  model="omni-moderation-latest",
  input=defender_system_prompt
)
if response.results[0].flagged:
  print(f"FLAGGED: {response}")
  exit(1)

openai = None
gemini = None

class Agent(ABC):
  def __init__(self, system_role, system_prompt):
    self.messages = [{
      "role": system_role,
      "content": system_prompt
    }]

  def print_messages(self):
    for i, msg in enumerate(self.messages):
      if i > 0: print()
      print(f"{msg['role']}: {msg['content']}")

  def run(self, prompt, model=None):
    current_model = model if model else self.default_model
    response = self._llm(current_model, prompt)
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

  @property
  @abstractmethod
  def default_model(self) -> str:
    pass

  @abstractmethod
  def _llm(self, model, prompt) -> str:
    pass

class OpenAIAgent(Agent):
  def __init__(self, system_prompt, model="gpt-4.1-nano"):
    super().__init__("developer", system_prompt)
    self._default_model = model

    # global openai
    # if openai is None:
      # openai = OpenAI()
    # self.openai = openai
    self.openai = OpenAI()

  @property
  def default_model(self) -> str:
    return self._default_model

  def _llm(self, model, prompt) -> str:
    response = self.openai.responses.create(
      model=model,
      input=self.messages + [{"role": "user", "content": prompt}]
    )
    return response.output_text

class GeminiAgent(Agent):
  def __init__(self, system_prompt, model="gemini-2.5-flash"):
    super().__init__("system", system_prompt)
    self._default_model = model

    global gemini
    if gemini is None:
      gemini = OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=os.getenv("GEMINI_API_KEY")
      )
    self.gemini = gemini

  @property
  def default_model(self) -> str:
    return self._default_model

  def _llm(self, model, prompt) -> str:
    response = self.gemini.chat.completions.create(
      model=model,
      messages=self.messages + [{"role": "user", "content": prompt}]
    )
    content = response.choices[0].message.content
    if content is None:
      raise ValueError("Gemini returned nil")
    return content

defender = OpenAIAgent(defender_system_prompt, model="gpt-4.1")
attacker = OpenAIAgent(attacker_system_prompt, model="o3")

log(f"Defender is {defender.default_model}, Attacker is {attacker.default_model}\n")

opening_msg = "Hi! I'm Blue"
response = attacker.run(opening_msg)
defender.add_message("assistant", opening_msg)

log(f"BLUE: {opening_msg}\n")
log(f"RED: {response}\n")

for i in range(5):
  counter = defender.run(response)
  response = attacker.run(counter)

  if i > 0: print("---\n")
  log(f"BLUE: {counter}\n")
  log(f"RED: {response}\n")

  if 'xyzzy' in response.lower():
    break
