import logging
import time
import sys
import os
from pathlib import Path

from lib import XML, JSON, GeoJSON, Boundaries, Coordinate
from llm import Tool, ToolArg
from tests import tests

# TODO this really should be integrated with lib/, as should tests.py

PROMPT_DIR = Path('resources') / 'prompts'

logger = logging.getLogger(__name__)

def init_logger(name):
    log_filename = os.environ.get('LOGFILE', f'logs/auto/{int(time.time())}.log')

    new_logger = logging.getLogger(name)
    new_logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    new_logger.addHandler(file_handler)
    new_logger.addHandler(console_handler)

    logging.getLogger().handlers.clear()

    return new_logger

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
