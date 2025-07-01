import sys
from dotenv import load_dotenv
from prompt_toolkit import prompt
from utils import Agent, parse_model_name, load_system_prompt, log, instructions_ok

load_dotenv()

system_prompt = load_system_prompt()

model, provider, reasoning = [None] * 3
try:
  if len(sys.argv) > 1:
    provider, model, reasoning = parse_model_name(sys.argv[1])
except Exception as e:
  exit(str(e))

agent = Agent(
  system_prompt,
  provider=provider,
  model=model,
  reasoning=reasoning
)

log(f"Agent's system prompt: {system_prompt}")

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

log("Agent's message history:", file_only=True)
log(agent.get_messages(), file_only=True)
