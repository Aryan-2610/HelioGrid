"""
Step 3: Roof Corners → Area in Square Meters & Centroid (Turf.js Equivalent)
Design Doc Reference: Step 3
"""
import math
import json

def calculate_roof_geometry(coordinates: list[list[float]]) -> dict:
    """
    Computes the area (in square meters) and centroid of a GeoJSON Polygon.
    Coordinates format: [[lon, lat], [lon, lat], ...]
    Matches Turf.js (turf.area & turf.centroid) using geodesic projection.
    """
    if len(coordinates) < 4:
        raise ValueError("A polygon must have at least 4 coordinate pairs (first and last matching).")

    # Ensure closed polygon
    if coordinates[0] != coordinates[-1]:
        coordinates.append(coordinates[0])

    unique_coords = coordinates[:-1]
    n = len(unique_coords)

    # 1. Compute Centroid
    center_lon = sum(c[0] for c in unique_coords) / n
    center_lat = sum(c[1] for c in unique_coords) / n

    # 2. Project coordinates to local metric (x, y) plane around centroid
    # WGS84 mean earth radius = 6,378,137 meters
    R = 6378137.0
    rad = math.pi / 180.0
    cos_lat = math.cos(center_lat * rad)

    xy = [
        (
            (c[0] - center_lon) * rad * R * cos_lat,
            (c[1] - center_lat) * rad * R
        )
        for c in coordinates
    ]

    # 3. Shoelace formula for area
    area_m2 = 0.5 * abs(
        sum(xy[i][0] * xy[i + 1][1] - xy[i + 1][0] * xy[i][1] for i in range(len(xy) - 1))
    )

    return {
        "area_m2": round(area_m2, 2),
        "centroid": [round(center_lon, 5), round(center_lat, 5)],
        "vertex_count": n
    }


# Standard sample polygon from design doc Step 3
SAMPLE_ROOF_POLYGON = {
    "type": "Polygon",
    "coordinates": [[
        [77.11790, 28.74960],
        [77.11810, 28.74960],
        [77.11810, 28.74950],
        [77.11790, 28.74950],
        [77.11790, 28.74960]
    ]]
}

if __name__ == "__main__":
    coords = SAMPLE_ROOF_POLYGON["coordinates"][0]
    print(f"[Step 3] Calculating roof area for {len(coords)-1}-point polygon...")
    
    geom = calculate_roof_geometry(coords)
    print(f"✓ Roof Area: {geom['area_m2']} m²")
    print(f"✓ Centroid [lon, lat]: {geom['centroid']}")
    print(f"✓ Vertices: {geom['vertex_count']}")
