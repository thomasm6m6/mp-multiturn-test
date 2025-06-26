from dotenv import load_dotenv
from utils import make_agent, load_system_prompt, log, instructions_ok

load_dotenv()

blue_system_prompt = load_system_prompt("resources/system_prompt.txt")
red_system_prompt = load_system_prompt("resources/red_system_prompt.txt")

blue = make_agent(blue_system_prompt, model="gpt-4.1")
red = make_agent(red_system_prompt, model="o4-mini", reasoning="low")

log(f"Blue is {blue.get_name()}, Red is {red.get_name()}\n")

log(f"Blue's system prompt follows:\n{blue_system_prompt}", file_only=True)
log(f"Red's system prompt follows:\n{red_system_prompt}\n", file_only=True)

blue_output = "I'm the Mission Planner Agent. Enter a mission plan description when ready."
blue.add_message("assistant", blue_output)

log(f"BLUE T0: {blue_output}\n")

for i in range(5):
  red_output = red.run(blue_output)
  log(f"RED T{i+1}: {red_output}\n")

  blue_output = blue.run(red_output)
  log(f"BLUE T{i+1}: {blue_output}\n")

  if not instructions_ok(blue_output):
    log(f"ENDING: instructions not ok. see reason above.\nRed won in {i+1} turns.")
    exit()

  if i > 0:
    print("---\n")

log("ENDING: all instructions valid.\nBlue won.")
