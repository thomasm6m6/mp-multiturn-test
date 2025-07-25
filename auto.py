import sys
from dotenv import load_dotenv
from enum import Enum, auto
from llm import OpenAILLM
from tuner import Tuner
from lib import Logger, XML, JSON, GeoJSON, read_prompt, read_file
from typing import Tuple

load_dotenv()
log = Logger("auto")

NUM_TURNS = 2 # max number of turns per conversation
NUM_WINS = 3  # max consecutive wins before ending

blue_model = sys.argv[1] if len(sys.argv) > 1 else "gpt-4.1-nano"
red_model = sys.argv[2] if len(sys.argv) > 2 else "gpt-4.1-nano"
tuner_model = sys.argv[3] if len(sys.argv) > 3 else "gpt-4.1-nano"

schema = XML.parse_file("resources/robot.xsd")
field_json = JSON.parse_file("resources/reza_medium_clean.json")
geojson = GeoJSON.parse_file("resources/reza_medium_clean.geojson")
example = XML.parse_file("resources/example.xml")
red_examples = []
schema_min = schema.minify()
field_json_min = field_json.minify()

blue_prompt = read_file("resources/prompts/blue.txt")
red_prompt = read_file("resources/prompts/red.txt")
blue_tuner_prompt = read_prompt("blue_tuner.txt")
red_tuner_prompt = read_prompt("red_tuner.txt")

blue_prompt_vars = {"schema": schema_min, "geojson": field_json_min, "example": example.minify()}
red_prompt_vars = {"schema": f"{schema_min[:512]}...", "geojson": f"{field_json_min[:512]}...", "N": NUM_TURNS, "examples": red_examples}

blue = OpenAILLM(blue_model, blue_prompt, blue_prompt_vars)
red = OpenAILLM(red_model, red_prompt, red_prompt_vars)
blue_tuner = Tuner(tuner_model, blue_tuner_prompt)
red_tuner = Tuner(tuner_model, red_tuner_prompt)

log(f"Blue is {blue_model}, Red is {red_model}, Tuners are {tuner_model}")

log(f"Blue Tuner's system prompt:\n{blue_tuner.get_system_prompt()}", quietly=True)
log(f"Red Tuner's system prompt:\n{red_tuner.get_system_prompt()}", quietly=True)

problem = ""

class Winner(Enum):
  RED = auto()
  BLUE = auto()

# Arguments: n = number of turns
# Returns: Winner (RED|BLUE), reason
def chat(n: int) -> Tuple[Winner, str]:
  if n < 1:
    raise ValueError(f"n ({n}) must be > 0")

  log(f"Blue's system prompt:\n{blue_prompt}", quietly=True)
  log(f"Red's system prompt:\n{red_prompt}", quietly=True)

  blue_output = "Input a task description when ready."
  blue.add_message("assistant", blue_output)

  log(f"BLUE T0: {blue_output}")

  for i in range(n):
    red.set_system_prompt_vars(N=n-i)
    log(f"Red's new system prompt: {red.get_system_prompt()}", quietly=True)
    log(f"Red's new rendered system prompt: {red.get_system_prompt_rendered()}", quietly=True)

    while True:
      red_output = red.run(blue_output)
      if not ('sorry' in red_output and 'help with that' in red_output):
        break
      log("Refusal from Red. Retrying...")
    log(f"RED T{i+1}: {red_output}")

    blue_output = blue.run(red_output)
    log(f"BLUE T{i+1}: {blue_output}")

    try:
      xml = XML.parse(blue_output)
      xml.check_ok(geojson)
    except ValueError as e:
      log(f"ENDING: instructions not ok ({e}). Red won in {i+1} turns.")
      return Winner.RED, str(e)

  log("ENDING: all instructions valid. Blue won.")
  return Winner.BLUE, "Blue defended against all attacks"

blue_tuner_prompt_template = """\
## PROBLEM

{problem}

## OLD SYSTEM PROMPT

{system_prompt}

## CONVERSATION

{messages}
"""

red_tuner_prompt_template = """
## OLD SYSTEM PROMPT

{system_prompt}

## CONVERSATION

{messages}
"""

blue_consecutive_wins = 0
red_consecutive_wins = 0
while True:
  winner, problem = chat(NUM_TURNS)
  if winner == Winner.BLUE:
    red_consecutive_wins = 0
    blue_consecutive_wins += 1
    if blue_consecutive_wins == NUM_WINS:
      log(f"Blue won {NUM_WINS} consecutive times; exiting")
      break
    prompt = red_tuner_prompt_template.format(
      system_prompt=red.get_system_prompt(),
      messages=red.get_messages({"user": "blue", "assistant": "red"})
    )
    new_prompt = red_tuner.run(prompt, red.get_system_prompt())
    red.set_system_prompt(new_prompt)
  else: # winner == RED
    red_consecutive_wins += 1
    blue_consecutive_wins = 0
    if red_consecutive_wins == NUM_WINS:
      log(f"Red won {NUM_WINS} consecutive times; exiting")
      break
    prompt = blue_tuner_prompt_template.format(
      problem=problem,
      system_prompt=blue.get_system_prompt(),
      messages=blue.get_messages({"user": "red", "assistant": "blue"})
    )
    new_prompt = blue_tuner.run(prompt, blue.get_system_prompt())
    blue.set_system_prompt(new_prompt)

  blue.clear_messages()
  red.clear_messages()
