import re
import subprocess
import lxml.etree as etree
import json
from io import StringIO
import xml.etree.ElementTree as ET
from .file import read_file

class XMLError(Exception):
    pass

class XMLMalformedError(XMLError):
    def __init__(self, message):
        self.message = message
        super().__init__(f"XML malformed: {message}")

class OutOfBoundsError(XMLError):
    def __init__(self, message):
        self.message = message
        super().__init__(message)

class XML:
    def __init__(self, root, xml_str):
        self.root = root
        self.xml_str = xml_str

    @classmethod
    def parse(cls, xml_str):
        dash_like_chars = [
            '\u2010',  # Hyphen
            '\u2011',  # Non-breaking hyphen
            '\u2012',  # Figure dash
            '\u2013',  # En dash
            '\u2014',  # Em dash
            '\u2015',  # Horizontal bar
            '\u2212',  # Minus sign
            '\u2E3A',  # Two-em dash
            '\u2E3B',  # Three-em dash
            '\uFE58',  # Small em dash
            '\uFE63',  # Small hyphen-minus
            '\uFF0D',  # Fullwidth hyphen-minus
        ]

        regex = '[' + ''.join(dash_like_chars) + ']'
        xml_str = re.sub(regex, '-', xml_str)

        try:
            parser = etree.XMLParser(remove_blank_text=True, remove_comments=True)
            root = etree.fromstring(xml_str.encode(), parser)
            return cls(root, xml_str)
        except etree.XMLSyntaxError as e:
            raise XMLMalformedError(e)

    @classmethod
    def parse_file(cls, filename):
        return cls.parse(read_file(filename))

    def validate(self):
        xsi = "http://www.w3.org/2001/XMLSchema-instance"
        schema_location_attr = self.root.attrib.get(f"{{{xsi}}}schemaLocation")

        if not schema_location_attr:
            raise XMLMalformedError("No xsi:schemaLocation in XML")

        parts = schema_location_attr.strip().split()
        if len(parts) < 2:
            raise XMLMalformedError("xsi:schemaLocation must contain at least one namespace and schema path")

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
            raise XMLMalformedError(f"Mismatched lats/lons ({len(lat_elems)} lats, {len(lon_elems)} lons)")

        pairs = []
        for lat_el, lon_el in zip(lat_elems, lon_elems):
            try:
                lat = float(lat_el.text)
                lon = float(lon_el.text)
                pairs.append((lat, lon))
            except (TypeError, ValueError):
                raise XMLMalformedError(f"Invalid coordinate value in: {etree.tostring(lat_el)} or {etree.tostring(lon_el)}")

        return pairs

    def minify(self):
        return etree.tostring(self.root, encoding="unicode", pretty_print=False)

    def check_ok(self, geojson):
        if not self.validate():
            raise XMLMalformedError('XML does not validate')

        ns = {"ns": "https://robotics.ucmerced.edu/task"}
        for tag in ["AtomicTasks", "ActionSequence"]:
            for el in self.root.findall(f".//ns:{tag}", namespaces=ns):
                if len(el) == 0:
                    raise XMLMalformedError(f"{tag} must not be empty")

        for lat, lon in self.find_coords():
            if not geojson.contains(lat, lon):
                raise OutOfBoundsError(f"Coordinate ({lat,lon}) outside field boundary")

    def to_geojson(self, copy=False):
        coords = self.find_coords()
        if len(coords) == 0:
            raise XMLMalformedError("No coords found")
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
