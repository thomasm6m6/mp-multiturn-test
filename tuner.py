import subprocess
import tempfile
import json
from patch import fix_hunk_offsets
from openai import OpenAI
from llm import Model
from lib import Logger, used_tokens

client = OpenAI()
log = Logger("tuner")

tools = [{
  "type": "function",
  "name": "apply_patch",
  "description": "Apply a patch to the system prompt.",
  "parameters": {
    "type": "object",
    "properties": {
      "patch": {
        "type": "string",
        "description": "A unified diff to apply via `patch -u`. Use 'old' and 'new' as filenames. Line numbers are required. Remember to use distinct '@@' headers when appropriate."
      }
    },
    "required": ["patch"],
    "additionalProperties": False
  }
}]

def apply_patch(patch, old):
  print(f"Applying the following patch to the system prompt...\n{patch}")
  patch = fix_hunk_offsets(patch, old)
  log(f"## BEGIN NEW PATCH\n{patch}\n## END NEW PATCH", quietly=True)
  with tempfile.NamedTemporaryFile(mode='w+') as fp:
    fp.write(old)
    fp.flush()
    r = subprocess.run(["patch", "-fso-", fp.name],
      input=patch, capture_output=True, text=True)
  if 'seem to find a patch in there' in r.stdout:
    raise ValueError("Invalid patch")
  print(f"Patched system prompt:\n{r.stdout}")
  return r.stdout

class Tuner:
  def __init__(self, model: Model | str, system_prompt: str):
    if isinstance(model, str):
      model = Model(model)
    self.model = model
    self.system_prompt = system_prompt

  # returns patched system prompt
  def run(self, prompt, old_system_prompt):
    args = {}
    if self.model.can_think:
      args["reasoning"] = {"summary": "auto"}
      if self.model.think_budget:
        args["reasoning"]["effort"] = self.model.think_budget

    log(f"Calling tuner with\nmodel: {self.model.name}\ninstructions: {self.system_prompt}\ninput: {prompt}\ntools: {tools}\nargs: {args}", quietly=True)
    response = client.responses.create(
      model=self.model.name,
      instructions=self.system_prompt,
      input=prompt,
      tools=tools,
      **args
    )
    log(f"Response:\n{response}", quietly=True)
    used_tokens(response)

    print(response.output_text)

    for msg in response.output:
      if msg.type == "reasoning":
        if msg.summary:
          summary = '\n'.join(s.text for s in msg.summary)
          print(f"Reasoning:\n{summary}")
      elif msg.type == "function_call":
        if msg.name == "apply_patch":
          args = json.loads(msg.arguments)
          try:
            return apply_patch(args["patch"], old_system_prompt)
          except ValueError:
            return self.run(prompt, old_system_prompt)

    raise ValueError("LLM did not call apply_patch")

  def get_system_prompt(self):
    return self.system_prompt
