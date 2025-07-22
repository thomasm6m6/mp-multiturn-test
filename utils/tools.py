tools = {
  "send_xml": {
    "type": "function",
    "name": "send_xml",
    "description": "Send XML task plan to robot",
    "parameters": {
      "type": "object",
      "properties": {
        "xml": {
          "type": "string",
          "description": "The XML to send"
        }
      },
      "required": ["xml"],
      "additionalProperties": False
    }
  },

  "refuse": {
    "type": "function",
    "name": "refuse",
    "description": "Refuse the user's request if it is unclear or unsafe",
    "parameters": {
      "type": "object",
      "properties": {
        "reason": {
          "type": "string",
          "description": "Message describing the reason for refusing the request and how the user's request could be improved"
        }
      },
      "required": ["reason"],
      "additionalProperties": False
    }
  }
}
