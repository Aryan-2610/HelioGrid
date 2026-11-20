"""
Step 4: Request Payload Structuring & Validation (FastAPI /analyze schema)
Pure physical parameters: lat, lon, area_m2.
"""
import json

def validate_and_create_payload(
    lat: float,
    lon: float,
    area_m2: float
) -> dict:
    """
    Validates physical parameters and builds the payload for /api/v1/analyze.
    """
    errors = []

    # Latitude & Longitude validation (India bounding box roughly 6°-38°N, 68°-98°E)
    if not (6.0 <= lat <= 38.5):
        errors.append(f"Latitude {lat} is out of expected Indian subcontinent bounds (6.0 to 38.5).")
    if not (68.0 <= lon <= 98.5):
        errors.append(f"Longitude {lon} is out of expected Indian subcontinent bounds (68.0 to 98.5).")

    # Physical roof area validation
    if area_m2 <= 0:
        errors.append("Roof area must be greater than 0 m².")
    elif area_m2 < 5.0:
        errors.append(f"Roof area {area_m2} m² is too small to install solar panels (min 5 m²).")

    if errors:
        return {
            "valid": False,
            "errors": errors,
            "payload": None
        }

    payload = {
        "lat": round(lat, 5),
        "lon": round(lon, 5),
        "area_m2": round(area_m2, 2)
    }

    return {
        "valid": True,
        "errors": [],
        "payload": payload
    }


if __name__ == "__main__":
    print("[Step 4] Testing Physical Request Payload Validation...\n")

    sample = validate_and_create_payload(
        lat=28.74955,
        lon=77.11800,
        area_m2=120.0
    )
    print("✓ Valid Payload Case:")
    print(json.dumps(sample, indent=2))
