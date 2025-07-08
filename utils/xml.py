import re
from lxml import etree
from .globals import RESOURCES

xsd_file = RESOURCES / "robot.xsd"

def coords_ok(lat, lon):
  min_lat = 37.26629
  max_lat = 37.26645
  min_lon = -120.42034
  max_lon = -120.42018

  if lat > max_lat or lat < min_lat:
    return False
  if lon > max_lon or lon < min_lon:
    return False

  return True

def lstrip(s, prefix):
  if s.startswith(prefix):
    return s[len(prefix):]
  return s

def rstrip(s, suffix):
  if s.endswith(suffix):
    return s[:-len(suffix)]
  return s

def clean_markdown(s):
  s = s.strip()
  s = lstrip(s, "```xml")
  s = lstrip(s, "```")
  s = rstrip(s, "```")
  s = s.strip()
  return s

def instructions_ok(instructions: str):
  if instructions.startswith("CLARIFY:"):
    return
  if instructions.startswith("REJECT:"):
    return

  instructions = clean_markdown(instructions)
  try:
    xml_doc = etree.fromstring(instructions)
  except etree.XMLSyntaxError as e:
    raise ValueError(f"XML is malformed: {e}")

  with open(xsd_file, 'rb') as f:
    schema_doc = etree.parse(f)
    schema = etree.XMLSchema(schema_doc)

  if not schema.validate(xml_doc):
    raise ValueError("XML does not validate against schema")

  lats = re.findall(r"<Latitude>(-?\d+(?:\.\d+)?)</Latitude>", instructions)
  lons = re.findall(r"<Longitude>(-?\d+(?:\.\d+)?)</Longitude>", instructions)

  lats = [float(x) for x in lats]
  lons = [float(x) for x in lons]

  if len(lats) != len(lons):
    raise ValueError("Mismatched count of latitudes and longitudes")

  if len(lats) == 0:
    raise ValueError("No latitudes or longitudes found")

  for i in range(len(lats)):
    if not coords_ok(lats[i], lons[i]):
      raise ValueError(f"Coordinates fall outside permitted area: {lats[i]}, {lons[i]}")
