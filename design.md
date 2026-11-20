# HelioGrid V1 (Basic / Zero-Cache) — ISRO Data-Flow & API Design Doc

This is the stripped-down, stateless V1 flow: no database, no Redis, no caching. Every user click flows directly from the browser to the backend, hits ISRO's geospatial services live, runs the sizing math, and returns JSON.

---

## End-to-End Data Flow

```text
[User enters place + clicks 4 roof corners]
   │
   ├─► Step 1: GET Geocoder (Nominatim / Bhuvan) ──► { lat, lon }
   ├─► Step 2: GET Satellite Map Tiles ────────────► Zoom 19–20 Roof View
   ├─► Step 3: Browser Turf.js (Local) ────────────► { area_m2, centroid }
   │
   └─► Step 4: POST /api/v1/analyze (FastAPI — Stateless, No Cache)
                  │
                  ├─► Step 5: GET ISRO VEDAS API (WMS GetFeatureInfo / Temporal API)
                  │              └─► { ghi_kwh_m2_day, optimal_tilt_deg }
                  │
                  └─► Step 6: Solar Sizing + PM Surya Ghar Math
                                 └─► Step 7: 200 OK JSON ──► UI Result Cards
```

---

## Step 1: Place Name → Coordinates

- **Input:** User types an address or locality (e.g., `"Rohini Sector 17, New Delhi"`). *(If they paste raw `lat`, `lon`, skip to Step 2.)*
- **Hit API (Street/City Search):** OpenStreetMap Nominatim (free, no token needed):

```http
GET https://nominatim.openstreetmap.org/search?q=Rohini+Sector+17,+New+Delhi&format=jsonv2&limit=1
User-Agent: HelioGridBasic/1.0 (you@email.com)
```

> **(Optional ISRO Alternative for Rural/Village Lookups):** ISRO Bhuvan Village Geocoding API via [https://bhuvan-app1.nrsc.gov.in/api/](https://bhuvan-app1.nrsc.gov.in/api/) using your Bhuvan portal access token.

- **Get Back:**

```json
[
  {
    "lat": "28.74955",
    "lon": "77.11802",
    "display_name": "Sector 17, Rohini, New Delhi, India"
  }
]
```

- **Extract:** `lat = 28.74955`, `lon = 77.11802`.

---

## Step 2: Coordinates → High-Resolution Roof View

- **Trigger:** Map library (Leaflet or MapLibre GL JS) flies to `[28.74955, 77.11802]` at Zoom 19–20.
- **Hit API:** Load a sharp satellite basemap so the user can clearly see roof edges and water tanks:
  - **Option A (Easiest for Web Apps):** Esri World Imagery XYZ tiles:

```http
GET https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}
```

  - **Option B (ISRO Bhuvan WMS):** Add Bhuvan's high-resolution Cartosat imagery layer (50 cm / 1 m coverage on Bhuvan 2D) as an OGC WMS tile layer in Leaflet (`L.tileLayer.wms`).

- **Get Back:** Satellite image tiles rendered directly on the map canvas.

---

## Step 3: Roof Corners → Area in Square Meters (In-Browser)

- **Trigger:** User clicks 4 or more corners of their shadow-free terrace and inputs `monthly_bill_inr = 3500` and `tariff_inr_per_kwh = 7.5`.
- **Local Data Produced (GeoJSON Polygon):**

```json
{
  "type": "Polygon",
  "coordinates": [[
    [77.11790, 28.74960],
    [77.11810, 28.74960],
    [77.11810, 28.74950],
    [77.11790, 28.74950],
    [77.11790, 28.74960]
  ]]
}
```

- **Local Calculation (Turf.js, 0 API calls):**
  - `area_m2 = turf.area(polygon)` → `120.0`
  - `centroid = turf.centroid(polygon).geometry.coordinates` → `[77.11800, 28.74955]`

---

## Step 4: Browser → Backend Endpoint

- **Hit API (Your Single-File FastAPI Backend):**

```http
POST /api/v1/analyze
Content-Type: application/json
```

**Request Body:**

```json
{
  "lat": 28.74955,
  "lon": 77.11800,
  "area_m2": 120.0,
  "monthly_bill_inr": 3500,
  "tariff_inr_per_kwh": 7.5
}
```

- **Backend Behavior:** Zero cache lookup—immediately forwards `(lat, lon)` to Step 5.

---

## Step 5: Backend → ISRO VEDAS Solar Data API

ISRO SAC's VEDAS (Visualisation of Earth Observation Data and Archival System) computes India's solar potential ($\text{kWh/m}^2$) from Indian geostationary satellites (Kalpana / INSAT-3D) paired with Cartosat DEM terrain shadow data, and exposes programmatic access through the VEDAS API Centre ([https://vedas.sac.gov.in/vconsole/](https://vedas.sac.gov.in/vconsole/)) using GeoServer OGC WMS and Temporal APIs (free API key after registration).

- **How You Query a Single Point on OGC WMS (GetFeatureInfo):**  
  Construct a tiny bounding box around `(lon, lat)`—e.g., `[lon - 0.001, lat - 0.001, lon + 0.001, lat + 0.001]`—and request the pixel value at the center (`X=50, Y=50`) of a 101×101 virtual tile in JSON format:

```http
GET https://vedas.sac.gov.in/<vedas_solar_wms_endpoint>?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetFeatureInfo&LAYERS=<solar_insolation_layer>&QUERY_LAYERS=<solar_insolation_layer>&SRS=EPSG:4326&BBOX=77.1170,28.7485,77.1190,28.7505&WIDTH=101&HEIGHT=101&X=50&Y=50&INFO_FORMAT=application/json&API_KEY=<YOUR_VEDAS_KEY>
```

> *(You copy the exact WMS service path and layer name—such as INSAT GHI or WRF Solar Insolation—from the VEDAS API Centre's Samples / GetCapabilities page after signing up.)*

- **Get Back (Standard GeoServer GetFeatureInfo GeoJSON):**

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "GRAY_INDEX": 5.10
      }
    }
  ]
}
```

- **Extract:**
  - `ghi_daily = feature["properties"]["GRAY_INDEX"]` → `5.10` ($\text{kWh/m}^2/\text{day}$)
  - `optimal_tilt_deg = round(abs(lat), 1)` → `28.7°` (standard Northern Hemisphere rule matching latitude)

---

## Step 6: Deterministic Sizing & Subsidy Math (Inside FastAPI)

With `area_m2`, `monthly_bill_inr`, `tariff_inr_per_kwh`, and `ghi_daily` in hand, run 10 lines of pure arithmetic (`USABLE_RATIO = 0.65`, `SQM_PER_KW = 8.0`, `PANEL_KW = 0.545`, `PR = 0.78`, `COST_PER_KW = 55000`):

| Output Field | Formula | Worked Example (Delhi) |
| :--- | :--- | :--- |
| `usable_area_m2` | `area_m2 * 0.65` | 78.0 m² |
| `max_roof_kw` | `usable_area_m2 / 8.0` | 9.75 kW |
| `annual_usage_kwh` | `(monthly_bill_inr / tariff_inr_per_kwh) * 12` | 5,600 kWh/yr |
| `yield_per_kw_yr` | `ghi_daily * 365 * 0.78` | 1,452 kWh/kW/yr |
| `target_kw` | `annual_usage_kwh / yield_per_kw_yr` | 3.86 kW |
| `panel_count` | `max(1, round(min(max_roof_kw, target_kw) / 0.545))` | 7 panels |
| `installed_kw` | `panel_count * 0.545` | 3.815 kW |
| `annual_kwh` | `installed_kw * yield_per_kw_yr` | 5,539 kWh/yr |
| `gross_cost_inr` | `installed_kw * 55000` | ₹2,09,825 |
| `subsidy_inr` | PM Surya Ghar: ₹30k/kW up to 2 kW, ₹18k/kW up to 3 kW, max ₹78,000 | ₹78,000 |
| `net_cost_inr` | `gross_cost_inr - subsidy_inr` | ₹1,31,825 |
| `payback_years` | `net_cost_inr / (annual_kwh * tariff_inr_per_kwh)` | 3.17 years |

---

## Step 7: Backend → Frontend Response

- **HTTP Response (`200 OK`):**

```json
{
  "data_source": "ISRO VEDAS (INSAT/WRF Solar Layer)",
  "sizing": {
    "drawn_area_m2": 120.0,
    "usable_area_m2": 78.0,
    "panel_count": 7,
    "installed_kw": 3.82,
    "optimal_tilt_deg": 28.7,
    "facing": "Due South (180 deg)"
  },
  "energy": {
    "ghi_kwh_m2_day": 5.10,
    "annual_generation_kwh": 5539
  },
  "financials": {
    "gross_cost_inr": 209825,
    "pm_surya_ghar_subsidy_inr": 78000,
    "net_cost_inr": 131825,
    "annual_savings_inr": 41543,
    "payback_years": 3.17
  }
}
```

---

## Practical Implementation Notes for ISRO APIs

- **API Key / Token Expiry:** VEDAS API Centre issues a developer key on registration, whereas Bhuvan REST API access tokens expire every 24 hours—so keep Nominatim for geocoding in V1 to avoid regenerating tokens daily.
- **Isolate Step 5 in One Function:** Wrap the WMS `GetFeatureInfo` request inside a single `fetch_ghi(lat, lon)` Python function. If a specific VEDAS GeoServer layer is temporarily down for maintenance during a live demo, you can swap the URL inside that one function (or fall back to a static state-wise INSAT GHI lookup dictionary) without touching any other code.
