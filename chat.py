import sys
import time
import logging
from rich.console import Console
from dotenv import load_dotenv
from prompt_toolkit import prompt

import common as c
from lib import XML, XMLError, init_cost
from llm import make_llm, Message, Role

logging.basicConfig(filename=f'logs/chat/{int(time.time())}.log', filemode='a')
logger = logging.getLogger(__name__)

if len(sys.argv) < 2:
    exit(f'Usage: {sys.argv[0]} blue_model')

load_dotenv()
console = Console(force_terminal=True)
cost = init_cost()

variables = {
    'schema': c.schema.minify(),
    'field_spec': c.reza_medium_clean_json.minify(),
    'example': c.example.minify(),
}
tools = {'send_xml': c.tools.send_xml()}

blue = make_llm(sys.argv[1], Message(c.PROMPT_DIR / 'blue.txt', render=True, **variables), tools)

while True:
    try:
        user_input = prompt('> ')
        response = blue.run(user_input)
        blue.add_message(Role.USER, user_input)
        blue.add_message(Role.ASSISTANT, response.message)
        cost.add_usage(response.usage)
        console.print('\n', response, '\n', style='blue')

        tool_call = next(filter(lambda t: t.name == 'send_xml', response.message.tool_calls))
        xml = XML.parse(tool_call.output)
        xml.check_ok(geojson=c.reza_medium_clean_geojson)
    except StopIteration:
        logger.info('Blue did not call send_xml')
    except XMLError as err:
        logger.info('Instructions not ok: {err}')
    except (EOFError, KeyboardInterrupt):
        break
