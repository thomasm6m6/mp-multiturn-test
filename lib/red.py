import logging

from llm import Tool, ToolArg

logger = logging.getLogger(__name__)

def set_scratchpad(args):
    try:
        pass
    except (IndexError, ValueError) as e:
        logger.error(f'set_scratchpad failed: {e}')

tools = {
    'set_scratchpad': Tool(
        args={'contents': ToolArg(kind='string', desc='Text to populate the scratchpad with.')},
        desc='Replace the contents of the scratchpad with the given text.',
        callback=set_scratchpad)
}
