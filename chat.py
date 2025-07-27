import sys
import logging
from rich.console import Console
from dotenv import load_dotenv
from prompt_toolkit import prompt

from lib import JSON, GeoJSON, XML, XMLError, read_file, init_cost
from llm import make_llm, Message, Role

if len(sys.argv) < 2:
    exit(f'Usage: {sys.argv[0]} blue_model')

load_dotenv()
console = Console(force_terminal=True)
cost = init_cost()
logger = logging.getLogger(__name__)

logging.basicConfig(filename='logs/chat.log', filemode='a',
    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

schema = XML.parse_file('resources/robot.xsd')
field_spec = JSON.parse_file('resources/reza_medium_clean.json')
geojson = GeoJSON.parse_file('resources/reza_medium_clean.geojson')
example = XML.parse_file('resources/example.xml')

if not example.validate():
    raise ValueError('Example XML file does not validate')

variables = {
    'schema': schema.minify(),
    'field_spec': field_spec.minify(),
    'example': example.minify(),
}
blue = make_llm(sys.argv[1], Message(read_file('resources/prompts/blue.txt'), render=True, **variables))

while True:
    try:
        user_input = prompt('> ')
        response = blue.run(user_input)
        blue.add_message(Role.USER, user_input)
        blue.add_message(Role.ASSISTANT, response.message)
        cost.add_usage(response.usage)
        console.print('\n', response, '\n', style='blue')
        try:
            xml = XML.parse(response.message.text)
            xml.check_ok(geojson)
            xml.to_geojson(copy=True)
        except XMLError as e:
            print(f"Instructions NOT ok. Human won. Reason: {e}")
    except (EOFError, KeyboardInterrupt):
        break
