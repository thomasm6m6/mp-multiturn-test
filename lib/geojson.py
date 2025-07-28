import json
import math
from shapely.geometry import shape, Point
from shapely.ops import unary_union
from dataclasses import dataclass
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


# class Coordinate:
#     def __init__(self, latitude: float, longitude: float):
#         self.latitude = latitude
#         self.longitude = longitude

#     def between(self, c1: 'Coordinate', c2: 'Coordinate'):
#         if max(c1.latitude, c2.latitude) >= self.latitude >= min(c1.latitude, c2.latitude):
#             return True
#         return max(c1.longitude, c2.longitude) >= self.longitude >= min(c1.longitude, c2.longitude)

# class Boundaries:
#     def __init__(self, upper_left: Coordinate, upper_right: Coordinate, lower_right: Coordinate, lower_left: Coordinate):
#         self.upper_left = upper_left
#         self.upper_right = upper_right
#         self.lower_right = lower_right
#         self.lower_left = lower_left

#     def contains(self, c: Coordinate):
#         return c.between(self.upper_left, self.lower_left) and c.between(self.upper_left, self.upper_right)

class Coordinate:
    def __init__(self, latitude: float, longitude: float):
        self.latitude = latitude
        self.longitude = longitude

class Boundaries:
    def __init__(self, upper_left: Coordinate, upper_right: Coordinate,
                 lower_right: Coordinate, lower_left: Coordinate):
        self.upper_left = upper_left
        self.upper_right = upper_right
        self.lower_right = lower_right
        self.lower_left = lower_left

    def contains(self, c: Coordinate):
        lat_in_bounds = (self.lower_left.latitude <= c.latitude <= self.upper_left.latitude)
        lon_in_bounds = (self.upper_left.longitude <= c.longitude <= self.upper_right.longitude)

        return lat_in_bounds and lon_in_bounds

    def __iter__(self):
        return iter([
            (self.upper_left.latitude, self.upper_left.longitude),
            (self.upper_right.latitude, self.upper_right.longitude),
            (self.lower_right.latitude, self.lower_right.longitude),
            (self.lower_left.latitude, self.lower_left.longitude)
        ])
