import json
from .file import read_file

class JSON:
    def __init__(self, json):
        self.json = json

    def __str__(self):
        return json.dumps(self.json, indent=2)

    @classmethod
    def parse(cls, json_str):
        return cls(json.loads(json_str))

    @classmethod
    def parse_file(cls, filename):
        return cls.parse(read_file(filename))

    def minify(self):
        return json.dumps(self.json, separators=(",", ":"))
