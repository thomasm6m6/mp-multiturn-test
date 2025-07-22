from litellm import completion
from pydantic import BaseModel
from pathlib import Path
from utils import add_cost

class Message(BaseModel):
  role: str
  content: str

class LLM:
  def __init__(self, model, system_prompt, reasoning=None, multiturn=True):
    self.model = model  # format: provider/model-name
    self.reasoning = reasoning
    self.multiturn = multiturn
    self.system_prompt = system_prompt
    self.messages = [{"role": "system", "content": system_prompt}]

  def run(self, prompt):
    args = {}
    if self.reasoning:
      args["reasoning_effort"] = self.reasoning

    response = completion(
      model=self.model,
      messages=self.messages,
      **args
    )
    response_text = response.choices[0].message.content

    if "reasoning_content" in response.choices[0].message:
      print(response.choices[0].message.reasoning_content)

    # TODO add this to total_cost
    input_tokens = response.usage.prompt_tokens
    output_tokens = response.usage.completion_tokens
    add_cost(self.model, input_tokens, output_tokens)

    if self.multiturn:
      self.add_message("user", prompt)
      self.add_message("assistant", response_text)

    return response_text

  def add_message(self, role, content):
    self.messages.append({"role": role, "content": content})

  def get_messages(self):
    return '\n'.join(map(lambda m: f"{m['role']}: {m['content']}", self.messages[1:]))

  def clear_messages(self):
    self.messages = []
