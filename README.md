# mp-multiturn-test

A simple program to facilitate conversation with an LLM, for redteaming the mission-planner system prompt.

```sh
pip install -r requirements.txt
python3 llm-llm.py
python3 human-llm.py
```

`human-llm.py` enters an interactive chat mode with one model and accepts one argument specifying the model to use.
`llm-llm.py` runs two models against each other, and accepts up to two arguments specifying the defending and attacking models.
The syntax of the model names is 'MODEL', 'PROVIDER/MODEL', or 'PROVIDER/MODEL/REASONING_EFFORT'.
The defaults as of the time of writing are OpenAI, gpt-4.1-nano, and none respectively.
Chat logs for both are stored in `logs/`.
