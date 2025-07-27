import sys
import logging
from rich.console import Console
from dotenv import load_dotenv
from prompt_toolkit import prompt

from lib import JSON, GeoJSON, XML, XMLError, read_file, init_cost
from llm import make_llm, Message, Role, Tool, ToolArg

if len(sys.argv) < 2:
    exit(f'Usage: {sys.argv[0]} blue_model')

LOG_FILE = 'logs/chat.log'
load_dotenv()
console = Console(force_terminal=True)
cost = init_cost()
logger = logging.getLogger(__name__)

logging.basicConfig(filename=LOG_FILE, filemode='a',
    level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

schema = XML.parse_file('resources/robot.xsd')
field_spec = JSON.parse_file('resources/reza_medium_clean.json')
geojson = GeoJSON.parse_file('resources/reza_medium_clean.geojson')
example = XML.parse_file('resources/example.xml')

if not example.validate():
    raise ValueError('Example XML file does not validate')

def send_xml(args):
    try:
        return args['xml']
    except (IndexError, KeyError, ValueError) as e:
        logger.error(f'send_xml failed: {e}')

variables = {
    'schema': schema.minify(),
    'field_spec': field_spec.minify(),
    'example': example.minify(),
}
tools = {
    'send_xml': Tool(
        args={'xml': ToolArg(kind='string', desc='The XML string to send to the robot.')},
        desc='Send an XML task plan directly to the robot to be executed.',
        callback=send_xml)
}

blue = make_llm(sys.argv[1], Message(read_file('resources/prompts/blue.txt'), render=True, **variables), tools)

while True:
    try:
        user_input = prompt('> ')
        response = blue.run(user_input)
        blue.add_message(Role.USER, user_input)
        blue.add_message(Role.ASSISTANT, response.message)
        cost.add_usage(response.usage)
        console.print('\n', response, '\n', style='blue')

        xml_str = None
        for tool_call in response.message.tool_calls:
            if tool_call.name == 'send_xml':
                xml_str = tool_call.output
                break
        try:
            xml = XML.parse(xml_str)
            xml.check_ok(geojson)
            xml.to_geojson(copy=True)
        except XMLError as e:
            print(f"Instructions NOT ok. Human won. Reason: {e}")
    except (EOFError, KeyboardInterrupt):
        break
