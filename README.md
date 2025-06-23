# mp-multiturn-test

A simple program to facilitate conversation with an LLM, for redteaming the mission-planner system prompt.

```sh
pip install -r requirements.txt
python3 llm.py
```

You may use the environment variables `SYSTEM_PROMPT`, `ROBOT_XML`, and `FARM_GEOJSON` to specify alternative files to be used, other than the default ones in `resources/`. I.E.:

```sh
SYSTEM_PROMPT=my_prompt.txt ROBOT_XML=my_robot.xml FARM_GEOJSON=my_farm.geojson python3 llm.py
```
