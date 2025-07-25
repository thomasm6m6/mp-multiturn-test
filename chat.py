import sys
from dotenv import load_dotenv
from prompt_toolkit import prompt
from llm import OpenAILLM
from lib import Logger, XML, JSON, GeoJSON, read_prompt

load_dotenv()
log = Logger("chat")

model = sys.argv[1] if len(sys.argv) > 1 else "gpt-4.1-nano"

schema = XML.parse_file("resources/robot.xsd")
geojson = GeoJSON.parse_file("resources/reza_medium_clean.geojson")
example = XML.parse_file("resources/example.xml")
if not example.validate():
  raise ValueError("Example XML file does not validate")
system_prompt = read_prompt("blue.txt", schema=schema.minify(), geojson=geojson.minify(), example=example.minify())
llm = OpenAILLM(model, system_prompt)

while True:
  try:
    user_input = prompt("> ")
    response = llm.run(user_input)
    log(response)
    try:
      xml = XML.parse(response)
      xml.check_ok(geojson)
      xml.to_geojson(copy=True)
    except Exception as e:
      log(f"Instructions NOT ok. Human won. Reason: {e}")
  except (EOFError, KeyboardInterrupt):
    break

log(f"{model}'s system prompt and message history:", quietly=True)
log(llm.get_system_prompt(), quietly=True)
log(llm.get_messages(), quietly=True)
