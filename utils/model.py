token_costs = {
  "o4-mini":          {"input": 1.10, "output":  4.40},
  "o3":               {"input": 2.00, "output":  8.00},
  "gpt-4.1":          {"input": 2.00, "output":  8.00},
  "gpt-4.1-mini":     {"input": 0.40, "output":  1.60},
  "gpt-4.1-nano":     {"input": 0.10, "output":  0.40},
  "gemini-2.5-pro":   {"input": 1.25, "output": 10.00},
  "gemini-2.5-flash": {"input": 0.30, "output":  2.50},
}

def model_costs(model, input_toks, output_toks):
  if model not in token_costs:
    return 0, 0
  input_cost = token_costs[model]["input"] * input_toks / 1_000_000
  output_cost = token_costs[model]["output"] * output_toks / 1_000_000
  return input_cost, output_cost

class Model:
  def __init__(self, name):
    self.provider = "openai"
    self.model = "gpt-4.1-nano"
    self.reasoning = None

    if name:
      parts = name.split('/')
      if len(parts) == 1:
        self.model = parts[0]
      elif len(parts) == 2:
        if parts[1].isdigit() or parts[1] in ["none", "low", "medium", "high"]:
          self.model = parts[0]
          self.reasoning = parts[1]
        else:
          self.provider = parts[0]
          self.model = parts[1]
      elif len(parts) == 3:
        self.provider = parts[0]
        self.model = parts[1]
        self.reasoning = parts[2]
      else:
        raise ValueError(f"Invalid model name '{name}'")

  def __str__(self) -> str:
    s = f"{self.provider}/{self.model}"
    if self.reasoning:
      s += f" ({self.reasoning})"
    return s
