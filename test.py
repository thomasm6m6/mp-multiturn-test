import logging
import sys
import time
from dotenv import load_dotenv
from rich.console import Console

import common as c
from lib import XML, XMLError, init_cost
from llm import make_llm, Message, Response
from tests import tests, Test

logging.basicConfig(filename=f'logs/auto/{int(time.time())}.log', filemode='a')
logger = logging.getLogger(__name__)

if len(sys.argv) < 2:
    exit(f'Usage: {sys.argv[0]} blue_model')

NUM_TRIES = 3
load_dotenv()
console = Console(force_terminal=True, highlight=False)
start_time = time.time()
cost = init_cost()

variables = {
    "schema": str(c.schema),
    "example": str(c.example),
    "boundaries": list(c.boundaries),
    "field_spec": str(c.reza_medium_clean_geojson),
}

tools = {'send_xml': c.tools.send_xml()}

blue = make_llm(sys.argv[1], Message(c.PROMPT_DIR / 'blue_no_geojson.txt', render=True, **variables), tools)

console.print(f"Blue is {blue.model}. Running {len(tests)} tests {NUM_TRIES} times each.")
logging.info(f"Blue's system prompt: {blue.system_prompt}")

def print_pass(test: Test, response: Response):
    console.print(f'  [green]PASS[/green]')
    logging.info(f'{blue.model} passed test {test.name}\nPROMPT: {test.text!r}\nOUTPUT: {response!r}')

def print_fail(test: Test, response: Response, problem):
    console.print(f'  [red]FAIL[/red]')
    logging.info(f'{blue.model} failed test {test.name}\nPROBLEM: {problem}\nPROMPT: {test.text!r}\nOUTPUT: {response!r}')

fails = 0
for i, test in enumerate(tests):
    console.print(f'\nRunning test {i+1}, {test.name}: {test.text!r}', no_wrap=True, overflow='ellipsis')
    for _ in range(NUM_TRIES):
        response = blue.run(test.text)
        cost.add_usage(response.usage)

        try:
            tool_call = next(filter(lambda t: t.name == 'send_xml', response.message.tool_calls))
            xml = XML.parse(tool_call.output)
            xml.check_ok(boundaries=c.boundaries)
            print_pass(test, response)
        except StopIteration:
            print_fail(test, response, 'No tool call')
            fails += 1
        except XMLError as err:
            print_fail(test, response, err)
            fails += 1

end_time = time.time()
time_delta = int(end_time - start_time)

if fails == 0:
    console.print(f"\n{blue.model} passed all tests! Finished in {time_delta}s.")
else:
    console.print(f"\n{blue.model} failed {fails}/{len(tests)*NUM_TRIES} tests. Finished in {time_delta}s.")
