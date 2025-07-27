from typing import Optional

from .base import LLM
from .types import Model, Tool, Message
from .providers import OpenAILLM, GeminiLLM
from . import models

def make_llm(model: Model | str, system_prompt: Message | str, tools: Optional[dict[str, Tool]] = None) -> LLM:
    if isinstance(model, str):
        model = Model(model)
    if isinstance(system_prompt, str):
        system_prompt = Message(system_prompt, render=True)

    model_info = models.get(model.name)
    if not model_info:
        raise ValueError(f"Unrecognized model '{model}'")
    match model_info['provider']:
        case 'openai': return OpenAILLM(model, system_prompt, tools)
        case 'gemini': return GeminiLLM(model, system_prompt, tools)
        case unknown:  raise ValueError(f"Unknown provider '{unknown}' for model '{model}'")
