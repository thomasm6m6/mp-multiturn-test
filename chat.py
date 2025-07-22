import sys
from dotenv import load_dotenv
from prompt_toolkit import prompt
from llm import LLM
from utils import Logger, read_prompt, read_file, minify_xml

load_dotenv()
log = Logger("chat")

model = sys.argv[1] if len(sys.argv) > 1 else "openai/gpt-4.1-nano"
if model.count('/') > 1:
  model, reasoning = model.rsplit('/', maxsplit=1)
else:
  reasoning = None

schema = read_file("resources/robot.xsd")
geojson = read_file("resources/reza_medium_clean.json")
example = read_file("resources/example.xml")
system_prompt = read_prompt("blue.txt", schema=schema, geojson=geojson, example=example)
llm = LLM(model, system_prompt)

log(f"Agent's system prompt: {system_prompt}", quietly=True)
log(f"Agent is {model}", quietly=True)

while True:
  try:
    user_input = prompt("> ")
    response = llm.run(user_input)
    print(response)
    try:
      # instructions_ok(response)
      pass
    except Exception as e:
      log(f"ENDING: instructions not ok. Human won. Error: {e}")
      break
  except (EOFError, KeyboardInterrupt):
    break

log("Agent's message history:", quietly=True)
log(llm.get_messages(), quietly=True)
