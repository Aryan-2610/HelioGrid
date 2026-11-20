"""
Step 6: Physical Rooftop Solar Sizing & Electricity Generation Prediction
Predicts how many panels fit on the rooftop and the electricity produced.
Zero pricing or subsidy math.
"""
import sys
import json
from config import get_env_float

def calculate_solar_capacity_and_generation(
    area_m2: float,
    ghi_daily: float,
    lat: float
) -> dict:
    """
    Computes physical panel capacity and energy output based on rooftop area and ISRO GHI.
    """
    usable_ratio = get_env_float("SOLAR_USABLE_RATIO", 0.65)
    sqm_per_kw = get_env_float("SOLAR_SQM_PER_KW", 8.0)
    panel_kw = get_env_float("SOLAR_PANEL_KW", 0.545)
    pr = get_env_float("SOLAR_PERFORMANCE_RATIO", 0.78)

    # 1. Terrace physical geometry
    usable_area_m2 = round(area_m2 * usable_ratio, 2)
    max_roof_kw = round(usable_area_m2 / sqm_per_kw, 2)

    # 2. Maximum physical panel count
    panel_count = max(1, round(max_roof_kw / panel_kw))
    exact_installed_kw = panel_count * panel_kw
    installed_kw = round(exact_installed_kw, 2)

    # 3. Energy Generation Math
    # Specific annual yield per 1 kW installed (kWh/kW/yr)
    yield_per_kw_yr = round(ghi_daily * 365.0 * pr)

    # Annual, monthly, and daily expected electricity generation (kWh)
    annual_kwh = int(round(exact_installed_kw * yield_per_kw_yr))
    monthly_kwh = int(round(annual_kwh / 12.0))
    daily_kwh = round(annual_kwh / 365.0, 1)

    # 4. Environmental impact (India CEA grid factor ~0.82 kg CO2 / kWh)
    co2_offset_tons_yr = round(annual_kwh * 0.00082, 1)
    trees_equivalent = int(round(co2_offset_tons_yr * 45))

    optimal_tilt_deg = round(abs(lat), 1)

    return {
        "sizing": {
            "drawn_area_m2": area_m2,
            "usable_area_m2": usable_area_m2,
            "panel_count": panel_count,
            "panel_rating_w": int(panel_kw * 1000),
            "installed_kw": installed_kw,
            "optimal_tilt_deg": optimal_tilt_deg,
            "facing": "Due South (180 deg)"
        },
        "energy": {
            "ghi_kwh_m2_day": ghi_daily,
            "yield_per_kw_yr": yield_per_kw_yr,
            "daily_generation_kwh": daily_kwh,
            "monthly_generation_kwh": monthly_kwh,
            "annual_generation_kwh": annual_kwh
        },
        "environmental": {
            "co2_offset_tons_yr": co2_offset_tons_yr,
            "trees_equivalent_yr": trees_equivalent
        }
    }


if __name__ == "__main__":
    test_area = float(sys.argv[1]) if len(sys.argv) > 1 else 120.0
    test_ghi = float(sys.argv[2]) if len(sys.argv) > 2 else 5.10
    test_lat = float(sys.argv[3]) if len(sys.argv) > 3 else 28.74955

    print(f"[Step 6] Solar Capacity & Generation for {test_area} m² roof (GHI: {test_ghi})...")
    res = calculate_solar_capacity_and_generation(test_area, test_ghi, test_lat)

    print("\n--- Physical Rooftop Capacity ---")
    s = res["sizing"]
    print(f"  • Roof Drawn Area : {s['drawn_area_m2']} m² (Usable: {s['usable_area_m2']} m²)")
    print(f"  • Maximum Panels  : {s['panel_count']} panels ({s['panel_rating_w']}W Mono PERC)")
    print(f"  • System Capacity : {s['installed_kw']} kW")
    print(f"  • Optimal Tilt    : {s['optimal_tilt_deg']}°, {s['facing']}")

    print("\n--- Electricity Generation ---")
    e = res["energy"]
    print(f"  • Daily Output    : {e['daily_generation_kwh']} kWh/day")
    print(f"  • Monthly Output  : {e['monthly_generation_kwh']:,} kWh/month")
    print(f"  • Annual Output   : {e['annual_generation_kwh']:,} kWh/year")

    print("\n--- Environmental Impact ---")
    env = res["environmental"]
    print(f"  • CO₂ Offset      : {env['co2_offset_tons_yr']} tons/year")
    print(f"  • Equivalent Trees: {env['trees_equivalent_yr']} trees planted")
