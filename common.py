import logging
from pathlib import Path

from lib import XML, JSON, GeoJSON, Boundaries, Coordinate
from llm import Tool, ToolArg
from tests import tests

PROMPT_DIR = Path('resources') / 'prompts'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


schema = XML.parse_file('resources/robot.xsd')
example = XML.parse_file('resources/example.xml')

if not example.validate():
    raise ValueError('Example XML file does not validate')

reza_medium_geojson = GeoJSON.parse_file('resources/reza_medium.geojson')
reza_medium_clean_geojson = GeoJSON.parse_file('resources/reza_medium_clean.geojson')

reza_medium_clean_json = JSON.parse_file('resources/reza_medium_clean.json')

boundaries = Boundaries(Coordinate(37.267089, -120.422088), Coordinate(37.267089, -120.420090),
                        Coordinate(37.265792, -120.420090), Coordinate(37.265792, -120.422088))

def send_xml(args):
    try:
        return args['xml']
    except (IndexError, KeyError, ValueError) as e:
        logger.error(f'send_xml failed: {e}')

class _Tools:
    @staticmethod
    def send_xml(cb=send_xml):
        return Tool(args={'xml': ToolArg(kind='string', desc='The XML string to send to the robot.')},
                    desc='Send an XML task plan directly to the robot to be executed.',
                    callback=cb)

tools = _Tools()

tests.disable_all()
tests.enable('test_lat_lon_swap')
tests.enable('test_inject_json')
tests.enable('test_emergency3')
tests.enable('test_new_boundaries1')
tests.enable('test_firmware_patch2')
tests.enable('test_mapping_error')
