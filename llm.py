from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

openai = OpenAI()

with open("system_prompt.txt") as f:
  system_prompt = f.read()

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
  return openai.responses.create(
    model=model,
    input=messages,
    # reasoning={"effort": "low"}
  ).output_text

while True:
  try:
    prompt = input("> ")
    add_prompt(prompt)
    response = llm()
    add_response(response)

    print(response)
  except (EOFError, KeyboardInterrupt):
    break
