MODELS = {
    "gpt-4.1":      {"provider": "openai", "thinking": False, "input_cost": 2.00, "output_cost": 8.00},
    "gpt-4.1-mini": {"provider": "openai", "thinking": False, "input_cost": 0.40, "output_cost": 1.60},
    "gpt-4.1-nano": {"provider": "openai", "thinking": False, "input_cost": 0.10, "output_cost": 0.40},
    "o4-mini":      {"provider": "openai", "thinking": True,  "input_cost": 1.10, "output_cost": 4.40},
    "o3":           {"provider": "openai", "thinking": True,  "input_cost": 2.00, "output_cost": 8.00},

    "gemini-2.5-flash": {"provider": "gemini", "thinking": True, "input_cost": 0.30, "output_cost":  2.50},
    "gemini-2.5-pro":   {"provider": "gemini", "thinking": True, "input_cost": 1.25, "output_cost": 10.00},
}

thinking_models = list(filter(lambda model: MODELS[model]['thinking'], MODELS))

def can_think(model):
    return model in thinking_models

def get(model):
    return MODELS.get(model)

def get_cost(model, input_tokens, output_tokens):
    if model not in MODELS:
        raise ValueError("Unrecognized model '{model}'")
    return (
        MODELS[model]['input_cost'] * input_tokens / 1_000_000,
        MODELS[model]['output_cost'] * output_tokens / 1_000_000
    )
