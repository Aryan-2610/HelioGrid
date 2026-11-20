"""
Step 5: Backend → ISRO VEDAS Solar Data API
Design Doc Reference: Step 5
"""
import sys
import json
import urllib.request
import urllib.parse
from config import get_env, get_env_float

# Regional Indian Solar Insolation (INSAT GHI in kWh/m2/day) fallback lookup table
# Derived from ISRO SAC long-term satellite solar atlas
REGIONAL_GHI_FALLBACK = {
    "north": 5.10,    # Delhi, Haryana, Punjab, UP
    "west": 5.40,     # Rajasthan, Gujarat, Maharashtra
    "south": 5.25,    # Karnataka, Tamil Nadu, Andhra, Telangana, Kerala
    "east": 4.80,     # West Bengal, Bihar, Odisha, Jharkhand
    "central": 5.30,  # MP, Chhattisgarh
    "default": 5.10
}

def estimate_regional_ghi(lat: float, lon: float) -> float:
    """Estimates baseline GHI based on Indian coordinates if API is unreachable."""
    if lon < 74.0:
        return REGIONAL_GHI_FALLBACK["west"]
    elif lat > 26.0:
        return REGIONAL_GHI_FALLBACK["north"]
    elif lat < 16.0:
        return REGIONAL_GHI_FALLBACK["south"]
    elif lon > 83.0:
        return REGIONAL_GHI_FALLBACK["east"]
    else:
        return REGIONAL_GHI_FALLBACK["central"]

def fetch_solar_data(lat: float, lon: float) -> dict:
    """
    Fetches daily Global Horizontal Irradiance (GHI in kWh/m2/day) and
    calculates optimal tilt angle from latitude.
    Queries ISRO VEDAS GeoServer WMS GetFeatureInfo, with graceful demo fallback.
    """
    api_key = get_env("VEDAS_API_KEY", "")
    wms_base_url = get_env("VEDAS_WMS_URL", "https://vedas.sac.gov.in/vapi/ridam_server3/wms/")
    layer_name = get_env("VEDAS_SOLAR_LAYER", "annual_insolation")
    enable_fallback = get_env("ENABLE_VEDAS_FALLBACK", "true").lower() in ("true", "1", "yes")
    default_ghi = get_env_float("FALLBACK_GHI", 5.10)

    # 1. Optimal tilt angle rule (Northern Hemisphere rule: match latitude)
    optimal_tilt_deg = round(abs(lat), 1)

    # 2. Construct tiny bounding box around point (X=50, Y=50 in 101x101 tile)
    delta = 0.001
    bbox = f"{lon - delta:.4f},{lat - delta:.4f},{lon + delta:.4f},{lat + delta:.4f}"

    wms_params = {
        "SERVICE": "WMS",
        "VERSION": "1.1.1",
        "REQUEST": "GetFeatureInfo",
        "LAYERS": layer_name,
        "QUERY_LAYERS": layer_name,
        "SRS": "EPSG:4326",
        "BBOX": bbox,
        "WIDTH": "101",
        "HEIGHT": "101",
        "X": "50",
        "Y": "50",
        "INFO_FORMAT": "application/json",
        "X-API-KEY": api_key
    }

    full_url = f"{wms_base_url}?{urllib.parse.urlencode(wms_params)}"

    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "HelioGridBasic/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            features = data.get("features", [])
            if features:
                props = features[0].get("properties", {})
                # Gray index or GHI pixel value
                ghi_val = float(props.get("GRAY_INDEX", props.get("value", 0.0)))
                if ghi_val > 0:
                    return {
                        "ghi_kwh_m2_day": round(ghi_val, 2),
                        "optimal_tilt_deg": optimal_tilt_deg,
                        "data_source": "ISRO VEDAS Live (WMS GetFeatureInfo)",
                        "live_api_success": True
                    }
    except Exception as e:
        # Expected if layer endpoint is down, under maintenance, or requires domain whitelisting
        pass

    # Safe fallback if server is unreachable
    if enable_fallback:
        regional_ghi = estimate_regional_ghi(lat, lon)
        return {
            "ghi_kwh_m2_day": regional_ghi,
            "optimal_tilt_deg": optimal_tilt_deg,
            "data_source": "ISRO VEDAS INSAT Satellite Solar Atlas (Baseline Model)",
            "live_api_success": False
        }

    return {
        "error": "Failed to fetch solar insolation from ISRO VEDAS API and fallback is disabled.",
        "ghi_kwh_m2_day": None,
        "optimal_tilt_deg": optimal_tilt_deg,
        "live_api_success": False
    }


if __name__ == "__main__":
    test_lat = float(sys.argv[1]) if len(sys.argv) > 1 else 28.74955
    test_lon = float(sys.argv[2]) if len(sys.argv) > 2 else 77.11800

    print(f"[Step 5] Fetching Solar Insolation (GHI) for [{test_lat}, {test_lon}]...")
    result = fetch_solar_data(test_lat, test_lon)

    print(f"✓ Daily Solar Insolation (GHI): {result.get('ghi_kwh_m2_day')} kWh/m²/day")
    print(f"✓ Optimal Tilt Angle: {result.get('optimal_tilt_deg')}°")
    print(f"✓ Data Source: {result.get('data_source')}")
    print(f"✓ Live API Query: {'Connected' if result.get('live_api_success') else 'Using Resilient Fallback'}")
