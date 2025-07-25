import json
import atexit
import time
import os
import subprocess
from jinja2 import Template
import lxml.etree as etree
from pathlib import Path
from litellm.cost_calculator import cost_per_token
from shapely.geometry import shape, Point
from shapely.ops import unary_union

EXE_DIR = Path(__file__).resolve().parent

class Logger:
  os.path.dirname(__file__)
  def __init__(self, name=None, cutoff=1024):
    fname = os.path.join(os.path.dirname(__file__), "x.log")
    self.file = open(fname, 'a', buffering=1)
    self.name = name
    self.cutoff = cutoff
    self.queue = []
    atexit.register(self._cleanup)

  def _log(self, msg, quietly=False):
    now = int(time.time())
    msg = msg.strip()
    line = f"{now} {self.name or ''} {msg}"
    print(line, file=self.file, flush=True)
    if not quietly:
      s = msg[:self.cutoff]
      if len(msg) > self.cutoff:
        s += "\n..."
      print(s, end="\n\n", flush=True)

  def __call__(self, msg, **kwargs):
    return self._log(msg, **kwargs)

  def later(self, fn_or_str, **kwargs):
    self.queue.append((fn_or_str, kwargs))

  def _cleanup(self):
    for (fn_or_str, kwargs) in self.queue:
      if callable(fn_or_str):
        msg = fn_or_str()
      else:
        msg = fn_or_str
      self._log(msg, **kwargs)
    self.file.close()

log = Logger()

class XML:
  def __init__(self, root):
    self.root = root

  @classmethod
  def parse(cls, xml_str):
    try:
      parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
      root = etree.fromstring(xml_str.encode(), parser)
      return cls(root)
    except etree.XMLSyntaxError as e:
      raise ValueError(f"XML is malformed: {e}")

  @classmethod
  def parse_file(cls, filename):
    return cls.parse(read_file(filename))

  def validate(self):
    xsi = "http://www.w3.org/2001/XMLSchema-instance"
    schema_location_attr = self.root.attrib.get(f"{{{xsi}}}schemaLocation")

    if not schema_location_attr:
      raise ValueError("No xsi:schemaLocation in XML")

    parts = schema_location_attr.strip().split()
    if len(parts) < 2:
      raise ValueError("xsi:schemaLocation must contain at least one namespace and schema path")

    schema_path = parts[1]

    with open(schema_path, "rb") as f:
      schema_doc = etree.parse(f)
      schema = etree.XMLSchema(schema_doc)

    return schema.validate(self.root)

  def find_coords(self):
    # returns [(lat, lon), ...]
    ns = {"ns": "https://robotics.ucmerced.edu/task"}
    lat_elems = self.root.findall(".//ns:latitude", namespaces=ns)
    lon_elems = self.root.findall(".//ns:longitude", namespaces=ns)

    if len(lat_elems) != len(lon_elems):
      raise ValueError(f"Mismatched lats/lons ({len(lat_elems)} lats, {len(lon_elems)} lons)")

    pairs = []
    for lat_el, lon_el in zip(lat_elems, lon_elems):
      try:
        lat = float(lat_el.text)
        lon = float(lon_el.text)
        pairs.append((lat, lon))
      except (TypeError, ValueError):
        raise ValueError(f"Invalid coordinate value in: {etree.tostring(lat_el)} or {etree.tostring(lon_el)}")

    return pairs

  def minify(self):
    return etree.tostring(self.root, encoding="unicode", pretty_print=False)

  def check_ok(self, geojson):
    ns = {"ns": "https://robotics.ucmerced.edu/task"}
    for tag in ["AtomicTasks", "ActionSequence"]:
      for el in self.root.findall(f".//ns:{tag}", namespaces=ns):
        if not el:
          raise ValueError(f"{tag} must not be empty")

    for lat, lon in self.find_coords():
      if not geojson.contains(lat, lon):
        raise ValueError(f"Coordinate ({lat,lon}) outside field boundary")

  def to_geojson(self, copy=False):
    coords = self.find_coords()
    if len(coords) == 0:
      raise ValueError("No coords found")
    if len(coords) == 1:
      feature_type = "Point"
      coords_list = [coords[0][1], coords[0][0]]
    else:
      feature_type = "LineString"
      coords_list = [[lon, lat] for lat, lon in coords]

    geojson = {
      "type": "FeatureCollection",
      "features": [{
        "type": "Feature",
        "properties": {},
        "geometry": {
          "type": feature_type,
          "coordinates": coords_list
        }
      }]
    }
    s = json.dumps(geojson)
    if copy:
      proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
      proc.communicate(input=s.encode("utf-8"))
      print("Wrote GEOJSON to clipboard")
    return s

class JSON:
  def __init__(self, json):
    self.json = json

  @classmethod
  def parse(cls, json_str):
    return cls(json.loads(json_str))

  @classmethod
  def parse_file(cls, filename):
    return cls.parse(read_file(filename))

  def minify(self):
    return json.dumps(self.json, separators=(",", ":"))

class GeoJSON(JSON):
  def __init__(self, geojson, geom):
    super().__init__(geojson)
    self.geom = geom

  @classmethod
  def parse(cls, json_str):
    gj = json.loads(json_str)
    if gj.get("type") == "FeatureCollection":
      geoms = [shape(feature["geometry"]) for feature in gj["features"]]
      geom = unary_union(geoms)
    elif gj.get("type") == "Feature":
      geom = shape(gj["geometry"])
    else:
      geom = shape(gj)

    return cls(gj, geom)

  def contains(self, lat, lon):
    pt = Point(lon, lat)
    return self.geom.contains(pt) or self.geom.touches(pt)

_total_cost = 0

def add_cost(model, input_tokens, output_tokens):
  input_cost, output_cost = cost_per_token(model=model,
    prompt_tokens=input_tokens, completion_tokens=output_tokens)
  global _total_cost
  _total_cost += input_cost + output_cost

def used_tokens(response):
  add_cost(response.model, response.usage.input_tokens, response.usage.output_tokens)

log.later(lambda: f"Total cost used: ${round(_total_cost, 3)}")

def read_prompt(fname, **kwargs):
  body = read_file(EXE_DIR / "resources" / "prompts" / fname)
  template = Template(body, trim_blocks=True, lstrip_blocks=True, autoescape=False)
  return template.render(**kwargs)

def render_system_prompt(prompt_template, data):
  template = Template(prompt_template, trim_blocks=True, lstrip_blocks=True, autoescape=False)
  return template.render(data)

def read_file(fname):
  with open(fname) as f:
    return f.read()
