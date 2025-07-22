import sys
from dotenv import load_dotenv
from prompt_toolkit import prompt
from utils.llm import Model, Agent, tools
from utils.log import log, flush_log
from utils.xml import instructions_ok, minify_xml, minify_json
from utils.globals import RESOURCES, PROMPTS

load_dotenv()

model = Model(sys.argv[1] if len(sys.argv) > 1 else "")

prompt_vars = {
  # "schema": minify_xml((RESOURCES / "robot.xsd").read_text()),
  "geojson": minify_json((RESOURCES / "reza_medium_clean.json").read_text()),
  # "example": minify_xml((RESOURCES / "example.xml").read_text())
}
agent_tools = [
  tools["send_xml"],
  # tools["request_clarification"],
  tools["refuse"]
]
agent = Agent(model, PROMPTS / "blue_json.txt", prompt_vars, schema={"format": {"type": "json_schema", "name": "robot_schema", "schema": {
  "type": "object",
  "additionalProperties": False,
  "required": ["AtomicTasks"],
  "properties": {
    "AtomicTasks": {
      "type": "array",
      "items": {
        "anyOf": [
          { "$ref": "#/$defs/moveToGPSLocationTask" },
          { "$ref": "#/$defs/moveToRelativeLocationTask" },
          { "$ref": "#/$defs/takeThermalPictureTask" }
        ]
      }
    }
  },
  "$defs": {
    "moveToGPSLocationTask": {
      "type": "object",
      "properties": {
        "TaskID": { "type": "string" },
        "Action": {
          "type": "string",
          "enum": ["moveToGPSLocation"]
        },
        "Parameters": {
          "type": "object",
          "required": ["latitude", "longitude"],
          "additionalProperties": False,
          "properties": {
            "latitude": { "type": "number" },
            "longitude": { "type": "number" }
          }
        }
      },
      "required": ["TaskID", "Action", "Parameters"],
      "additionalProperties": False
    },
    "moveToRelativeLocationTask": {
      "type": "object",
      "properties": {
        "TaskID": { "type": "string" },
        "Action": {
          "type": "string",
          "enum": ["moveToRelativeLocation"]
        },
        "Parameters": {
          "type": "object",
          "required": ["x", "y", "roll", "pitch", "yaw"],
          "additionalProperties": False,
          "properties": {
            "x": { "type": "number" },
            "y": { "type": "number" },
            "roll": { "type": "number" },
            "pitch": { "type": "number" },
            "yaw": { "type": "number" }
          }
        }
      },
      "required": ["TaskID", "Action", "Parameters"],
      "additionalProperties": False
    },
    "takeThermalPictureTask": {
      "type": "object",
      "properties": {
        "TaskID": { "type": "string" },
        "Action": {
          "type": "string",
          "enum": ["takeThermalPicture"]
        },
        "Parameters": {
          "type": "object",
          "required": ["numberOfSamples"],
          "additionalProperties": False,
          "properties": {
            "numberOfSamples": { "type": "number" }
          }
        }
      },
      "required": ["TaskID", "Action", "Parameters"],
      "additionalProperties": False
    }
  }
}}})

log(f"Agent's system prompt: {agent.system_prompt}", file_only=True)
log(f"Agent is {agent.model}")

while True:
  try:
    user_input = prompt("> ")
    response = agent.run(user_input)
    log(f"USER: {user_input}")
    log(f"AGENT: {response}")
    flush_log()
    try:
      # instructions_ok(response)
      pass
    except Exception as e:
      log(f"ENDING: instructions not ok. Human won. Error: {e}")
      break
  except (EOFError, KeyboardInterrupt):
    break

log("Agent's message history:", file_only=True)
log(agent.get_messages(), file_only=True)
