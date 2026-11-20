"""
Step 2: Coordinates → High-Resolution Roof Map Tiles
Design Doc Reference: Step 2
"""
import sys
import math
import urllib.request

def lat_lon_to_tile(lat: float, lon: float, zoom: int = 19) -> tuple[int, int]:
    """
    Converts latitude and longitude to standard slippy map tile coordinates (x, y).
    """
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return xtile, ytile

def get_map_tile_info(lat: float, lon: float, zoom: int = 19) -> dict:
    """
    Returns high-resolution satellite basemap URLs and Leaflet configuration
    for the given coordinates.
    """
    xtile, ytile = lat_lon_to_tile(lat, lon, zoom)

    # Esri World Imagery (Option A in design doc)
    esri_template = "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
    esri_tile_url = f"https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{zoom}/{ytile}/{xtile}"

    # Google Satellite / Hybrid (Sub-30cm HD Imagery)
    google_hybrid_url = f"https://mt1.google.com/vt/lyrs=y&x={xtile}&y={ytile}&z={zoom}"

    # Bhuvan WMS (Option B in design doc)
    bhuvan_wms_url = "https://bhuvan-app1.nrsc.gov.in/bhuvan2d/service/wms"

    # Leaflet quick snippet for frontend developers
    leaflet_snippet = f"""
    // Frontend (Leaflet JS) - Google HD Hybrid Basemap:
    const map = L.map('map').setView([{lat}, {lon}], {zoom});
    L.tileLayer('https://mt{{s}}.google.com/vt/lyrs=y&x={{x}}&y={{y}}&z={{z}}', {{
        subdomains: ['0', '1', '2', '3'],
        maxZoom: 22,
        attribution: 'Tiles &copy; Google Maps'
    }}).addTo(map);
    """

    return {
        "lat": lat,
        "lon": lon,
        "zoom": zoom,
        "tile_x": xtile,
        "tile_y": ytile,
        "esri_tile_url": esri_tile_url,
        "google_hybrid_url": google_hybrid_url,
        "bhuvan_wms_url": bhuvan_wms_url,
        "leaflet_snippet": leaflet_snippet.strip()
    }

def verify_tile_access(tile_url: str) -> bool:
    """Checks if the satellite tile endpoint is accessible."""
    try:
        req = urllib.request.Request(tile_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


if __name__ == "__main__":
    test_lat = float(sys.argv[1]) if len(sys.argv) > 1 else 28.74955
    test_lon = float(sys.argv[2]) if len(sys.argv) > 2 else 77.11802

    print(f"[Step 2] Generating satellite map tile info for [{test_lat}, {test_lon}] at Zoom 19...")
    info = get_map_tile_info(test_lat, test_lon, zoom=19)

    print(f"✓ Tile Coordinates: X={info['tile_x']}, Y={info['tile_y']}, Zoom={info['zoom']}")
    print(f"✓ Google HD Hybrid Tile: {info['google_hybrid_url']}")
    print(f"✓ Esri Maxar Tile: {info['esri_tile_url']}")

    is_online = verify_tile_access(info["google_hybrid_url"])
    print(f"✓ Google Tile Reachability: {'Online (HTTP 200 OK)' if is_online else 'Unreachable'}")
    print("\n--- Leaflet Code Snippet ---")
    print(info["leaflet_snippet"])
