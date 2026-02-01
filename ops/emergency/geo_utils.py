"""
Geospatial utilities for perimeter generation and spatial operations.

This module provides functions for:
- Generating perimeters from coordinates (radial, convex hull)
- Point-in-polygon checks
- Distance calculations
- GeoJSON manipulation
"""

import math
import json
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
import requests


@dataclass
class Coordinate:
    """Represents a geographic coordinate."""
    lat: float
    lon: float

    def to_point(self) -> Tuple[float, float]:
        """Convert to (lon, lat) tuple for GeoJSON."""
        return (self.lon, self.lat)


class GeoUtils:
    """Core geospatial utilities."""

    # Earth's radius in kilometers
    EARTH_RADIUS_KM = 6371.0

    @staticmethod
    def haversine_distance(coord1: Coordinate, coord2: Coordinate) -> float:
        """
        Calculate the great-circle distance between two points using the Haversine formula.
        
        Args:
            coord1: First coordinate
            coord2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        lat1, lon1 = math.radians(coord1.lat), math.radians(coord1.lon)
        lat2, lon2 = math.radians(coord2.lat), math.radians(coord2.lon)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        c = 2 * math.asin(math.sqrt(a))

        return GeoUtils.EARTH_RADIUS_KM * c

    @staticmethod
    def radial_perimeter(center: Coordinate, radius_km: float, num_points: int = 32) -> List[Tuple[float, float]]:
        """
        Generate a circular perimeter around a center point.
        
        Args:
            center: Center coordinate
            radius_km: Radius in kilometers
            num_points: Number of points to approximate the circle
            
        Returns:
            List of (lon, lat) tuples forming a closed polygon
        """
        # Approximate degrees per kilometer at this latitude
        lat_deg_per_km = 1 / 111.32
        lon_deg_per_km = 1 / (111.32 * math.cos(math.radians(center.lat)))

        points = []
        for i in range(num_points):
            angle = 2 * math.pi * i / num_points
            dx = radius_km * math.cos(angle) * lon_deg_per_km
            dy = radius_km * math.sin(angle) * lat_deg_per_km
            points.append((center.lon + dx, center.lat + dy))

        # Close the polygon
        points.append(points[0])
        return points

    @staticmethod
    def rectangular_perimeter(center: Coordinate, width_km: float, height_km: float) -> List[Tuple[float, float]]:
        """
        Generate a rectangular perimeter around a center point.
        
        Args:
            center: Center coordinate
            width_km: Width in kilometers (East-West)
            height_km: Height in kilometers (North-South)
            
        Returns:
            List of (lon, lat) tuples forming a closed rectangular polygon
        """
        # Approximate degrees per kilometer at this latitude
        lat_deg_per_km = 1 / 111.32
        lon_deg_per_km = 1 / (111.32 * math.cos(math.radians(center.lat)))

        half_w = (width_km / 2) * lon_deg_per_km
        half_h = (height_km / 2) * lat_deg_per_km

        # Corners: NW, NE, SE, SW
        points = [
            (center.lon - half_w, center.lat + half_h), # NW
            (center.lon + half_w, center.lat + half_h), # NE
            (center.lon + half_w, center.lat - half_h), # SE
            (center.lon - half_w, center.lat - half_h), # SW
        ]

        # Close the polygon
        points.append(points[0])
        return points

    @staticmethod
    def convex_hull(points: List[Coordinate]) -> List[Tuple[float, float]]:
        """
        Compute convex hull using Graham scan algorithm.
        
        Args:
            points: List of coordinates
            
        Returns:
            List of (lon, lat) tuples forming the convex hull
        """
        if len(points) < 3:
            return [p.to_point() for p in points]

        def cross_product(o: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        # Convert to (lon, lat) tuples and sort
        pts = sorted([p.to_point() for p in points])

        # Build lower hull
        lower = []
        for p in pts:
            while len(lower) >= 2 and cross_product(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)

        # Build upper hull
        upper = []
        for p in reversed(pts):
            while len(upper) >= 2 and cross_product(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)

        # Concatenate and remove duplicates
        hull = lower[:-1] + upper[:-1]
        # Close the polygon
        if hull:
            hull.append(hull[0])
        return hull

    @staticmethod
    def point_in_polygon(point: Coordinate, polygon: List[Tuple[float, float]]) -> bool:
        """
        Check if a point is inside a polygon using ray casting algorithm.
        
        Args:
            point: Point to check
            polygon: List of (lon, lat) tuples forming a closed polygon
            
        Returns:
            True if point is inside polygon
        """
        x, y = point.lon, point.lat
        n = len(polygon)
        inside = False

        p1x, p1y = polygon[0]
        for i in range(1, n + 1):
            p2x, p2y = polygon[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    @staticmethod
    def to_geojson_polygon(coordinates: List[Tuple[float, float]], properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert a list of coordinates to a GeoJSON Polygon feature.
        
        Args:
            coordinates: List of (lon, lat) tuples
            properties: Optional properties dictionary
            
        Returns:
            GeoJSON Feature dict
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            },
            "properties": properties or {}
        }

    @staticmethod
    def to_geojson_point(coord: Coordinate, properties: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert a coordinate to a GeoJSON Point feature.
        
        Args:
            coord: Coordinate
            properties: Optional properties dictionary
            
        Returns:
            GeoJSON Feature dict
        """
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [coord.lon, coord.lat]
            },
            "properties": properties or {}
        }


class GeocodingService:
    """Utilities for forward and reverse geocoding using Nominatim (OSM)."""

    BASE_URL = "https://nominatim.openstreetmap.org"
    USER_AGENT = "Pro-Harp-Security-Command/1.0"

    @staticmethod
    def geocode(query: str) -> Optional[Coordinate]:
        """
        Convert a location query (e.g. "City, State") to coordinates.
        """
        try:
            params = {
                "q": query,
                "format": "json",
                "limit": 1
            }
            headers = {"User-Agent": GeocodingService.USER_AGENT}
            response = requests.get(f"{GeocodingService.BASE_URL}/search", params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                if data:
                    return Coordinate(lat=float(data[0]["lat"]), lon=float(data[0]["lon"]))
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None

    @staticmethod
    def reverse_geocode(lat: float, lon: float) -> Optional[Dict[str, str]]:
        """
        Convert coordinates to physical address information.
        """
        try:
            params = {
                "lat": lat,
                "lon": lon,
                "format": "json"
            }
            headers = {"User-Agent": GeocodingService.USER_AGENT}
            response = requests.get(f"{GeocodingService.BASE_URL}/reverse", params=params, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                address = data.get("address", {})
                return {
                    "city": address.get("city") or address.get("town") or address.get("village") or "",
                    "state": address.get("state") or "",
                    "country": address.get("country") or ""
                }
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
        return None


class PerimeterGenerator:
    """High-level perimeter generation utilities."""

    @staticmethod
    def from_single_point(lat: float, lon: float, radius_km: float, properties: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a radial perimeter from a single point.
        
        Args:
            lat: Latitude
            lon: Longitude
            radius_km: Radius in kilometers
            properties: Optional extra properties
            
        Returns:
            GeoJSON Polygon feature
        """
        center = Coordinate(lat, lon)
        coords = GeoUtils.radial_perimeter(center, radius_km)
        base_props = {
            "type": "radial_buffer",
            "center": {"lat": lat, "lon": lon},
            "radius_km": radius_km
        }
        if properties:
            base_props.update(properties)
            
        return GeoUtils.to_geojson_polygon(coords, base_props)

    @staticmethod
    def from_rectangle(lat: float, lon: float, width_km: float, height_km: float, properties: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Generate a rectangular perimeter from center and dimensions.
        
        Args:
            lat: Center latitude
            lon: Center longitude
            width_km: Width in km
            height_km: Height in km
            properties: Optional extra properties
            
        Returns:
            GeoJSON Polygon feature
        """
        center = Coordinate(lat, lon)
        coords = GeoUtils.rectangular_perimeter(center, width_km, height_km)
        base_props = {
            "type": "rectangular_area",
            "center": {"lat": lat, "lon": lon},
            "width_km": width_km,
            "height_km": height_km
        }
        if properties:
            base_props.update(properties)
            
        return GeoUtils.to_geojson_polygon(coords, base_props)

    @staticmethod
    def from_multiple_points(coords: List[Tuple[float, float]]) -> Dict[str, Any]:
        """
        Generate a convex hull perimeter from multiple points.
        
        Args:
            coords: List of (lat, lon) tuples
            
        Returns:
            GeoJSON Polygon feature
        """
        points = [Coordinate(lat, lon) for lat, lon in coords]
        hull_coords = GeoUtils.convex_hull(points)
        return GeoUtils.to_geojson_polygon(hull_coords, {
            "type": "convex_hull",
            "num_input_points": len(coords)
        })

    @staticmethod
    def from_geojson_file(filepath: str) -> Dict[str, Any]:
        """
        Load a perimeter from a GeoJSON file.
        
        Args:
            filepath: Path to GeoJSON file
            
        Returns:
            GeoJSON feature
        """
        with open(filepath, 'r') as f:
            return json.load(f)

    @staticmethod
    def save_to_geojson(feature: Dict[str, Any], filepath: str) -> None:
        """
        Save a GeoJSON feature to a file.
        
        Args:
            feature: GeoJSON feature
            filepath: Output file path
        """
        with open(filepath, 'w') as f:
            json.dump(feature, f, indent=2)


def example_usage():
    """Example usage of the geo utilities."""
    
    # Example 1: Radial perimeter around a point
    print("Example 1: Radial perimeter (10 km radius)")
    perimeter = PerimeterGenerator.from_single_point(40.7128, -74.0060, 10)
    print(json.dumps(perimeter, indent=2))
    
    # Example 2: Convex hull from multiple points
    print("\nExample 2: Convex hull from waypoints")
    waypoints = [
        (40.7128, -74.0060),  # New York
        (40.7589, -73.9851),  # Times Square
        (40.6892, -74.0445),  # Statue of Liberty
    ]
    hull = PerimeterGenerator.from_multiple_points(waypoints)
    print(json.dumps(hull, indent=2))
    
    # Example 3: Point-in-polygon check
    print("\nExample 3: Point-in-polygon check")
    test_point = Coordinate(40.7300, -74.0100)
    polygon_coords = perimeter["geometry"]["coordinates"][0]
    is_inside = GeoUtils.point_in_polygon(test_point, polygon_coords)
    print(f"Point {test_point} is {'inside' if is_inside else 'outside'} the perimeter")


if __name__ == "__main__":
    example_usage()
