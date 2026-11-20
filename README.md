# HelioGrid V1 — Rooftop Solar Capacity & Generation Engine

This guide details each step module implemented for HelioGrid V1, how to test each one individually from the terminal, and how to run the full orchestrating pipeline.

---

## File Overview & Testing Commands

| Step File | What it does | How to test individually |
| :--- | :--- | :--- |
| **`config.py`** | Lightweight `.env` parser & config loader (no `python-dotenv` needed). | `python3 config.py` |
| **`step1_geocoder.py`** | **Step 1:** Geocodes place name to `(lat, lon)` using OpenStreetMap Nominatim. | `python3 step1_geocoder.py "Rohini, New Delhi"` |
| **`step2_map_tiles.py`** | **Step 2:** Converts `(lat, lon)` to XYZ tile indices & Esri/Bhuvan satellite basemap URLs. | `python3 step2_map_tiles.py 28.74955 77.11802` |
| **`step3_roof_area.py`** | **Step 3:** Computes geodesic roof area in $\text{m}^2$ and centroid from roof corners (Turf.js logic). | `python3 step3_roof_area.py` |
| **`step4_request.py`** | **Step 4:** Validates input parameters (`lat`, `lon`, `area_m2`) for `/api/v1/analyze`. | `python3 step4_request.py` |
| **`step5_vedas_solar.py`** | **Step 5:** Queries ISRO VEDAS Solar API for GHI ($\text{kWh/m}^2/\text{day}$) & optimal tilt with graceful fallback. | `python3 step5_vedas_solar.py 28.74955 77.11800` |
| **`step6_solar_sizing.py`** | **Step 6:** Computes maximum physical panel capacity and daily/monthly/annual electricity generation. | `python3 step6_solar_sizing.py 120.0 5.10 28.74955` |
| **`step7_response.py`** | **Step 7:** Formats the final HTTP 200 OK JSON payload and renders clean generation report cards. | `python3 step7_response.py` |
| **`verify_benchmark.py`** | **Verification:** Compares HelioGrid against **NASA POWER**, **European PVGIS**, and **Govt MNRE** sources of truth. | `python3 verify_benchmark.py 28.74955 77.11802 120.0` |

---

## Orchestrating Pipeline: `pipeline.py`

Stitches all 7 steps together in an automated flow:

```bash
# Run with default Delhi location (120 m² roof):
python3 pipeline.py

# Or pass custom place name and rooftop area:
python3 pipeline.py "Delhi, India" 250.0
```

### Pipeline Output Example

```text
=======================================================
      ☀️  HELIOGRID SOLAR GENERATION REPORT  ☀️     
=======================================================
Data Source: ISRO VEDAS INSAT Satellite Solar Atlas
-------------------------------------------------------
📐 ROOFTOP CAPACITY
  • Roof Drawn Area    : 150.0 m² (Usable: 97.5 m²)
  • Solar Panels       : 22 panels (545W Mono PERC)
  • Total Capacity     : 11.99 kW
  • Panel Orientation  : Due South (180 deg), Tilt: 28.6°
-------------------------------------------------------
⚡ ELECTRICITY PRODUCTION
  • Solar Insolation   : 5.1 kWh/m²/day
  • Daily Generation   : 47.7 kWh / day
  • Monthly Generation : 1,451 kWh / month
  • Annual Generation  : 17,409 kWh / year
-------------------------------------------------------
🌱 ENVIRONMENTAL IMPACT
  • CO₂ Offset         : 14.3 tons / year
  • Equivalent Trees   : 644 trees planted
=======================================================
```
