import json
from jinja2 import Template
from lxml import etree
from log import Logger
from pathlib import Path
from litellm.cost_calculator import cost_per_token

log = Logger()
_total_cost = 0
EXE_DIR = Path(__file__).resolve().parent

def add_cost(model, input_tokens, output_tokens):
  input_cost, output_cost = cost_per_token(model=model,
    prompt_tokens=input_tokens, completion_tokens=output_tokens)
  global _total_cost
  _total_cost += input_cost + output_cost

log.later(lambda: f"Total cost used: ${round(_total_cost, 3)}")

def read_prompt(fname, **kwargs):
  body = read_file(EXE_DIR / "resources" / "prompts" / fname)
  template = Template(body, trim_blocks=True, lstrip_blocks=True, autoescape=False)
  return template.render(**kwargs)

def read_file(fname):
  with open(fname) as f:
    return f.read()

def minify_xml(xml_str):
  parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
  root = etree.fromstring(xml_str.encode(), parser)
  return etree.tostring(root, encoding='unicode', pretty_print=False)

def minify_json(json_str):
  data = json.loads(json_str)
  return json.dumps(data, separators=(",", ":"))
