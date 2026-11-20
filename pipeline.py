"""
HelioGrid V1 - End-to-End Orchestrating Pipeline
Physical Rooftop Solar Capacity & Generation Prediction
(Zero pricing or subsidies).

Run directly:
    python3 pipeline.py
Or with address and area:
    python3 pipeline.py "Rohini, New Delhi" 150.0
"""
import sys
import json

from step1_geocoder import geocode_address
from step2_map_tiles import get_map_tile_info
from step3_roof_area import calculate_roof_geometry, SAMPLE_ROOF_POLYGON
from step4_request import validate_and_create_payload
from step5_vedas_solar import fetch_solar_data
from step6_solar_sizing import calculate_solar_capacity_and_generation
from step7_response import format_api_response, print_result_cards

def run_heliogrid_pipeline(
    address_query: str = "Sector 17, Rohini, New Delhi",
    roof_polygon_coords: list = None,
    area_override_m2: float = 120.0
) -> dict:
    """
    Executes the complete physical HelioGrid V1 flow:
    Address -> Lat/Lon -> Satellite Tiles -> Roof Area -> VEDAS GHI -> Physical Panels & kWh Output
    """
    print("\n" + "#" * 60)
    print("   🚀 HELIOGRID SOLAR PREDICTION PIPELINE (PHYSICAL SIZING)")
    print("#" * 60)

    # 1. Geocode
    print(f"\n[Step 1/7] Geocoding place: '{address_query}'...")
    geo_res = geocode_address(address_query)
    if geo_res.get("success"):
        lat, lon = geo_res["lat"], geo_res["lon"]
        print(f"  ✓ Found location: {geo_res['display_name']}")
    else:
        lat, lon = 28.74955, 77.11802
        print(f"  ℹ Using default coordinates: lat = {lat}, lon = {lon}")

    # 2. Satellite Tiles
    print(f"\n[Step 2/7] Fetching satellite basemap tiles at Zoom 19...")
    tile_info = get_map_tile_info(lat, lon, zoom=19)
    print(f"  ✓ Tile Coordinates : X={tile_info['tile_x']}, Y={tile_info['tile_y']}")
    print(f"  ✓ Basemap Tile URL : {tile_info['esri_tile_url']}")

    # 3. Geometry
    print(f"\n[Step 3/7] Calculating roof polygon area and centroid...")
    if roof_polygon_coords is None:
        roof_polygon_coords = SAMPLE_ROOF_POLYGON["coordinates"][0]

    roof_geom = calculate_roof_geometry(roof_polygon_coords)
    area_m2 = area_override_m2 if area_override_m2 else roof_geom["area_m2"]
    print(f"  ✓ Roof Area : {area_m2} m² (Centroid: {roof_geom['centroid']})")

    # 4. Payload Validation
    print(f"\n[Step 4/7] Packaging and validating request payload...")
    val_res = validate_and_create_payload(lat=lat, lon=lon, area_m2=area_m2)
    if not val_res["valid"]:
        raise ValueError(f"Payload validation failed: {val_res['errors']}")
    print(f"  ✓ Valid Payload: {json.dumps(val_res['payload'])}")

    # 5. ISRO VEDAS Solar GHI
    print(f"\n[Step 5/7] Querying ISRO VEDAS Solar Insolation (GHI)...")
    solar_data = fetch_solar_data(lat, lon)
    ghi_daily = solar_data["ghi_kwh_m2_day"]
    optimal_tilt_deg = solar_data["optimal_tilt_deg"]
    data_source = solar_data["data_source"]
    print(f"  ✓ Solar GHI    : {ghi_daily} kWh/m²/day")
    print(f"  ✓ Optimal Tilt : {optimal_tilt_deg}°")

    # 6. Physical Capacity & Generation
    print(f"\n[Step 6/7] Calculating maximum rooftop panel capacity and generation...")
    sizing_res = calculate_solar_capacity_and_generation(
        area_m2=area_m2,
        ghi_daily=ghi_daily,
        lat=lat
    )
    s = sizing_res["sizing"]
    e = sizing_res["energy"]
    print(f"  ✓ Usable Roof Space  : {s['usable_area_m2']} m² (65%)")
    print(f"  ✓ Maximum Panels Fit : {s['panel_count']} panels ({s['installed_kw']} kW)")
    print(f"  ✓ Annual Generation  : {e['annual_generation_kwh']:,} kWh/year")

    # 7. Response Format & Cards
    print(f"\n[Step 7/7] Formatting report cards...")
    final_response = format_api_response(
        data_source=data_source,
        sizing_data=sizing_res["sizing"],
        energy_data=sizing_res["energy"],
        environmental_data=sizing_res["environmental"]
    )

    print_result_cards(final_response)
    return final_response


if __name__ == "__main__":
    address = sys.argv[1] if len(sys.argv) > 1 else "Rohini, New Delhi"
    area = float(sys.argv[2]) if len(sys.argv) > 2 else 120.0

    run_heliogrid_pipeline(
        address_query=address,
        area_override_m2=area
    )
