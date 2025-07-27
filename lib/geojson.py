import json
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from .json import JSON

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
