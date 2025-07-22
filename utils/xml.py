import re
import json
import subprocess
from lxml import etree
from .globals import RESOURCES

xsd_file = RESOURCES / "robot.xsd"

# FIXME do not hardcode
def coords_ok(lat, lon):
  return True
  min_lat = 37.26629
  max_lat = 37.26645
  min_lon = -120.42034
  max_lon = -120.42018

  if lat > max_lat or lat < min_lat:
    return False
  if lon > max_lon or lon < min_lon:
    return False

  return True

# def lstrip(s, prefix):
#   if s.startswith(prefix):
#     return s[len(prefix):]
#   return s

# def rstrip(s, suffix):
#   if s.endswith(suffix):
#     return s[:-len(suffix)]
#   return s

# def clean_markdown(s):
#   s = s.strip()
#   s = lstrip(s, "```xml")
#   s = lstrip(s, "```")
#   s = rstrip(s, "```")
#   s = s.strip()
#   return s

def instructions_ok(instructions: str):
  try:
    xml_doc = etree.fromstring(instructions)
  except etree.XMLSyntaxError as e:
    raise ValueError(f"XML is malformed: {e}")

  with open(xsd_file, 'rb') as f:
    schema_doc = etree.parse(f)
    schema = etree.XMLSchema(schema_doc)

  if not schema.validate(xml_doc):
    raise ValueError("XML does not validate against schema")

  lats = re.findall(r"<latitude>(-?\d+(?:\.\d+)?)</latitude>", instructions)
  lons = re.findall(r"<longitude>(-?\d+(?:\.\d+)?)</longitude>", instructions)

  lats = [float(x) for x in lats]
  lons = [float(x) for x in lons]

  if len(lats) != len(lons):
    raise ValueError("Mismatched count of latitudes and longitudes")

  if len(lats) == 0:
    raise ValueError("No latitudes or longitudes found")

  for i in range(len(lats)):
    if not coords_ok(lats[i], lons[i]):
      raise ValueError(f"Coordinates fall outside permitted area: {lats[i]}, {lons[i]}")

  s = """{"type":"FeatureCollection","features": [{"type":"Feature","properties":{},"geometry":{"type":"LineString","coordinates":["""
  for i in range(len(lats)):
    if i > 0: s += ","
    s += f"[{lons[i]}, {lats[i]}]"
  s += "]}}]}"
  proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
  proc.communicate(input=s.encode("utf-8"))
  print("Wrote GEOJSON to clipboard")

def minify_xml(xml_str):
  parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
  root = etree.fromstring(xml_str.encode(), parser)
  return etree.tostring(root, encoding='unicode', pretty_print=False)

def minify_json(json_str):
  data = json.loads(json_str)
  return json.dumps(data, separators=(",", ":"))
