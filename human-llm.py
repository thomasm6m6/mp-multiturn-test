import argparse
from dotenv import load_dotenv
from prompt_toolkit import prompt
from utils import load_system_prompt, log, make_agent, instructions_ok

load_dotenv()

system_prompt = load_system_prompt("resources/red_system_prompt.txt")
print(system_prompt)
exit()

parser = argparse.ArgumentParser()
parser.add_argument("-m", "--model")
parser.add_argument("-r", "--reasoning")
parser.add_argument("-p", "--provider")
args = parser.parse_args()

agent = make_agent(
  system_prompt,
  provider = args.provider or "openai",
  model = args.model or "gpt-4.1-nano",
  reasoning = args.reasoning
)

while True:
  try:
    user_input = prompt("> ")
    response = agent.run(user_input)
    log(f"AGENT: {response}")
    if not instructions_ok(response):
      log("ENDING: instructions not ok. Human won.")
      break
  except (EOFError, KeyboardInterrupt):
    break
