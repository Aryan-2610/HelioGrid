"""
Step 7: Backend → Frontend Response (JSON Schema & Solar Production Cards)
Zero pricing or subsidy clutter.
"""
import json

def format_api_response(
    data_source: str,
    sizing_data: dict,
    energy_data: dict,
    environmental_data: dict = None
) -> dict:
    """
    Builds the clean JSON payload returned to the frontend (HTTP 200 OK).
    """
    resp = {
        "data_source": data_source,
        "sizing": {
            "drawn_area_m2": sizing_data.get("drawn_area_m2", 0.0),
            "usable_area_m2": sizing_data.get("usable_area_m2", 0.0),
            "panel_count": sizing_data.get("panel_count", 0),
            "panel_rating_w": sizing_data.get("panel_rating_w", 545),
            "installed_kw": sizing_data.get("installed_kw", 0.0),
            "optimal_tilt_deg": sizing_data.get("optimal_tilt_deg", 0.0),
            "facing": sizing_data.get("facing", "Due South (180 deg)")
        },
        "energy": {
            "ghi_kwh_m2_day": energy_data.get("ghi_kwh_m2_day", 0.0),
            "daily_generation_kwh": energy_data.get("daily_generation_kwh", 0.0),
            "monthly_generation_kwh": energy_data.get("monthly_generation_kwh", 0),
            "annual_generation_kwh": energy_data.get("annual_generation_kwh", 0)
        }
    }
    if environmental_data:
        resp["environmental"] = environmental_data

    return resp

def print_result_cards(response: dict):
    """Prints clean solar prediction cards in terminal."""
    s = response["sizing"]
    e = response["energy"]
    env = response.get("environmental", {})

    print("\n" + "=" * 55)
    print("      ☀️  HELIOGRID SOLAR GENERATION REPORT  ☀️     ")
    print("=" * 55)
    print(f"Data Source: {response['data_source']}")
    print("-" * 55)
    print("📐 ROOFTOP CAPACITY")
    print(f"  • Roof Drawn Area    : {s['drawn_area_m2']} m² (Usable: {s['usable_area_m2']} m²)")
    print(f"  • Solar Panels       : {s['panel_count']} panels ({s['panel_rating_w']}W Mono PERC)")
    print(f"  • Total Capacity     : {s['installed_kw']} kW")
    print(f"  • Panel Orientation  : {s['facing']}, Tilt: {s['optimal_tilt_deg']}°")
    print("-" * 55)
    print("⚡ ELECTRICITY PRODUCTION")
    print(f"  • Solar Insolation   : {e['ghi_kwh_m2_day']} kWh/m²/day")
    print(f"  • Daily Generation   : {e['daily_generation_kwh']} kWh / day")
    print(f"  • Monthly Generation : {e['monthly_generation_kwh']:,} kWh / month")
    print(f"  • Annual Generation  : {e['annual_generation_kwh']:,} kWh / year")
    if env:
        print("-" * 55)
        print("🌱 ENVIRONMENTAL IMPACT")
        print(f"  • CO₂ Offset         : {env.get('co2_offset_tons_yr', 0)} tons / year")
        print(f"  • Equivalent Trees   : {env.get('trees_equivalent_yr', 0)} trees planted")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    sample_response = {
        "data_source": "ISRO VEDAS INSAT Satellite Solar Atlas",
        "sizing": {
            "drawn_area_m2": 120.0,
            "usable_area_m2": 78.0,
            "panel_count": 18,
            "panel_rating_w": 545,
            "installed_kw": 9.81,
            "optimal_tilt_deg": 28.7,
            "facing": "Due South (180 deg)"
        },
        "energy": {
            "ghi_kwh_m2_day": 5.10,
            "daily_generation_kwh": 39.0,
            "monthly_generation_kwh": 1187,
            "annual_generation_kwh": 14244
        },
        "environmental": {
            "co2_offset_tons_yr": 11.7,
            "trees_equivalent_yr": 526
        }
    }

    print("[Step 7] Formatting Clean Physical Solar JSON...")
    print(json.dumps(sample_response, indent=2))
    print_result_cards(sample_response)
