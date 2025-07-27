# from jinja2 import Template
# from pathlib import Path
# from .file import read_file

# EXE_DIR = Path(__file__).resolve().parent

# def read_prompt(fname, **kwargs):
#     body = read_file(EXE_DIR / "resources" / "prompts" / fname)
#     template = Template(body, trim_blocks=True, lstrip_blocks=True, autoescape=False)
#     return template.render(**kwargs)
