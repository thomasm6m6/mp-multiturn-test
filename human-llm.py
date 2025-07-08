import sys
from dotenv import load_dotenv
from prompt_toolkit import prompt
from utils.model import Model
from utils.llm import Agent
from utils.log import log
from utils.xml import instructions_ok
from utils.globals import PROMPTS

load_dotenv()

model = Model(sys.argv[1] if len(sys.argv) > 1 else "")

agent = Agent(model, PROMPTS / "blue.txt")

log(f"Agent's system prompt: {agent.system_prompt}")
log(f"Agent is {agent.model}")

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
