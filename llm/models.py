from typing import Tuple

MODELS = {
    "gpt-4.1":      {"provider": "openai", "thinking": False, "tools": True, "input_cost": 2.00, "output_cost": 8.00},
    "gpt-4.1-mini": {"provider": "openai", "thinking": False, "tools": True, "input_cost": 0.40, "output_cost": 1.60},
    "gpt-4.1-nano": {"provider": "openai", "thinking": False, "tools": True, "input_cost": 0.10, "output_cost": 0.40},
    "o4-mini":      {"provider": "openai", "thinking": True,  "tools": True, "input_cost": 1.10, "output_cost": 4.40},
    "o3":           {"provider": "openai", "thinking": True,  "tools": True, "input_cost": 2.00, "output_cost": 8.00},

    "gemini-2.5-flash": {"provider": "gemini", "thinking": True, "tools": True, "input_cost": 0.30, "output_cost":  2.50},
    "gemini-2.5-pro":   {"provider": "gemini", "thinking": True, "tools": True, "input_cost": 1.25, "output_cost": 10.00},

    "qwen3:4b":       {"provider": "ollama", "thinking": True,  "tools": True, "input_cost": 0.0, "output_cost": 0.0},
    "qwen3:8b":       {"provider": "ollama", "thinking": True,  "tools": True, "input_cost": 0.0, "output_cost": 0.0},
    "qwen3:8b-fp16":  {"provider": "ollama", "thinking": True,  "tools": True, "input_cost": 0.0, "output_cost": 0.0},
    "qwen3:14b":      {"provider": "ollama", "thinking": True,  "tools": True, "input_cost": 0.0, "output_cost": 0.0},
    "qwen3:32b":      {"provider": "ollama", "thinking": True,  "tools": True, "input_cost": 0.0, "output_cost": 0.0},
    "gemma3n:latest": {"provider": "ollama", "thinking": False, "tools": True, "input_cost": 0.0, "output_cost": 0.0},
}

PROVIDERS = ['openai', 'gemini', 'ollama']

thinking_models = list(filter(lambda model: MODELS[model]['thinking'], MODELS))

def can_think(model):
    return model in thinking_models

def get(model):
    return MODELS.get(model)

def get_cost(model: str, input_tokens: int, output_tokens: int) -> Tuple[float, float]:
    if model not in MODELS:
        raise ValueError("Unrecognized model '{model}'")
    return (
        MODELS[model]['input_cost'] * input_tokens / 1_000_000,
        MODELS[model]['output_cost'] * output_tokens / 1_000_000
    )
