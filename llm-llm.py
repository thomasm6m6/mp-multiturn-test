import sys
from dotenv import load_dotenv
from utils import Agent, parse_model_name, load_system_prompt, load_red_system_prompt, log, instructions_ok

load_dotenv()

blue_system_prompt = load_system_prompt()
red_system_prompt = load_red_system_prompt()

blue_provider, blue_model, blue_reasoning = [None] * 3
red_provider, red_model, red_reasoning = [None] * 3
try:
  if len(sys.argv) > 1:
    blue_provider, blue_model, blue_reasoning = parse_model_name(sys.argv[1])
  if len(sys.argv) > 2:
    red_provider, red_model, red_reasoning = parse_model_name(sys.argv[2])
except Exception as e:
  exit(str(e))

blue = Agent(blue_system_prompt, provider=blue_provider, model=blue_model, reasoning=blue_reasoning)
red = Agent(red_system_prompt, provider=red_provider, model=red_model, reasoning=red_reasoning)

log(f"Blue is {blue.get_name()}, Red is {red.get_name()}\n")

log(f"Blue's system prompt follows:\n{blue_system_prompt}", file_only=True)
log(f"Red's system prompt follows:\n{red_system_prompt}\n", file_only=True)

blue_output = "I'm the Mission Planner Agent. Enter a mission plan description when ready."
blue.add_message("assistant", blue_output)

log(f"BLUE T0: {blue_output}\n")

blue_won = True

for i in range(5):
  red_output = red.run(blue_output)
  log(f"RED T{i+1}: {red_output}\n")

  blue_output = blue.run(red_output)
  log(f"BLUE T{i+1}: {blue_output}\n")

  if not instructions_ok(blue_output):
    blue_won = False
    break

  print("---\n")

if blue_won:
  log("ENDING: all instructions valid. Blue won.")
else:
  log(f"ENDING: instructions not ok. Red won in {i+1} turns.")

log("\nBlue's message history:", file_only=True)
log(blue.get_messages(), file_only=True)
log("\nRed's message history:", file_only=True)
log(red.get_messages(), file_only=True)
