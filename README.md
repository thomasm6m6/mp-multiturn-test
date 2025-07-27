# mp-multiturn-test

A simple program to facilitate conversation with an LLM, for redteaming the mission-planner system prompt.

The main entrypoint to this code is the `./make` shell script; read it for usage info.
Herein, "Blue" refers to the defending LLM, and "Red" refers to the attacking LLM.
The syntax for model names is `model_name[/reasoning_effort]`, or `-` to disable.
