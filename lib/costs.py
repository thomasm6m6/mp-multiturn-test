import atexit
import signal
import sys

from llm import Usage

cost = None

class Cost:
    def __init__(self):
        self.total = 0

    def add(self, input_cost, output_cost):
        self.total += input_cost + output_cost

    def add_usage(self, usage: Usage):
        self.total += usage.input_cost + usage.output_cost

    def __str__(self):
        return str(round(self.total, 3))

    def __int__(self):
        return int(self.total)

def init_cost():
    global cost
    if cost is not None:
        return cost

    cost = Cost()

    def print_cost():
        print(f'Total cost: ${cost}')

    def signal_handler(sig, frame):
        # print_cost()
        sys.exit(str(cost or 0)) # HACK

    atexit.register(print_cost)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    return cost
