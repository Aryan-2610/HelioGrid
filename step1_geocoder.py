"""
Step 1: Place Name → Coordinates (Nominatim Geocoding)
Design Doc Reference: Step 1
"""
import sys
import json
import urllib.request
import urllib.parse
from config import get_env

def geocode_address(query: str) -> dict:
    """
    Converts a place name or address into (lat, lon) coordinates using
    OpenStreetMap Nominatim API.
    """
    email = get_env("NOMINATIM_EMAIL", "helio_grid@example.com")
    user_agent = get_env("NOMINATIM_USER_AGENT", "HelioGridBasic/1.0")

    encoded_query = urllib.parse.quote(query)
    url = f"https://nominatim.openstreetmap.org/search?q={encoded_query}&format=jsonv2&limit=1&email={urllib.parse.quote(email)}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": f"{user_agent} ({email})",
            "Accept": "application/json"
        }
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if not data:
                # If hyper-specific address didn't match, return None or fallback
                return {
                    "success": False,
                    "error": f"No coordinates found for '{query}'. Try a broader locality."
                }
            
            first_match = data[0]
            return {
                "success": True,
                "lat": float(first_match["lat"]),
                "lon": float(first_match["lon"]),
                "display_name": first_match.get("display_name", query)
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Geocoding request failed: {str(e)}"
        }


if __name__ == "__main__":
    test_place = sys.argv[1] if len(sys.argv) > 1 else "DLF CAPITAL GREENS"
    print(f"[Step 1] Geocoding query: '{test_place}'...")
    result = geocode_address(test_place)
    
    if result["success"]:
        print(f"✓ Found: {result['display_name']}")
        print(f"  Latitude  (lat): {result['lat']}")
        print(f"  Longitude (lon): {result['lon']}")
    else:
        print(f"✗ Error: {result.get('error')}")
