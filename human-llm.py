import os
from openai import OpenAI
from dotenv import load_dotenv
from jinja2 import Environment, FileSystemLoader

def load_system_prompt():
  robot_xml_file = os.getenv("ROBOT_XML", "resources/robot.xml")
  farm_geojson_file = os.getenv("FARM_GEOJSON", "resources/farm.geojson")
  system_prompt_file = os.getenv("SYSTEM_PROMPT", "resources/system_prompt.txt")

  env = Environment(loader=FileSystemLoader("."))
  system_prompt_tmpl = env.get_template(system_prompt_file)

  with open(robot_xml_file) as robot_xml, open(farm_geojson_file) as farm_geojson:
    data = {
      "ROBOT_XML": robot_xml.read(),
      "FARM_GEOJSON": farm_geojson.read()
    }

  return system_prompt_tmpl.render(data)

system_prompt = load_system_prompt()

load_dotenv()

# openai = OpenAI(
#   base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
#   api_key=os.getenv("GEMINI_API_KEY")
# )

openai = OpenAI()

messages = [{
  "role": "system",
  "content": system_prompt
}]

def add_prompt(msg):
  messages.append({
    "role": "user",
    "content": msg
  })

def add_response(msg):
  messages.append({
    "role": "assistant",
    "content": msg
  })

def llm(messages=messages, model="gpt-4.1-nano"):
  response = openai.chat.completions.create(
    model=model,
    messages=messages,
    reasoning_effort="high"
  )
  return response.choices[0].message.content
  # reasoning={"effort": "low"}

while True:
  try:
    prompt = input("> ")
    add_prompt(prompt)
    response = llm(model=os.getenv("MODEL", "o4-mini"))
    add_response(response)

    print(response)
  except (EOFError, KeyboardInterrupt):
    break
