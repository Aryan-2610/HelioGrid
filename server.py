"""
HelioGrid V1 - Lightweight API & Web Server
Physical Solar Prediction (Zero Pricing/Subsidies)
"""
import os
import json
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler

from config import get_env, get_env_int
from step1_geocoder import geocode_address
from step4_request import validate_and_create_payload
from step5_vedas_solar import fetch_solar_data
from step6_solar_sizing import calculate_solar_capacity_and_generation
from step7_response import format_api_response

class HelioGridHandler(SimpleHTTPRequestHandler):
    """Handles HTTP requests for HelioGrid static files and API endpoints."""

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-API-KEY")

    def _send_json_response(self, status_code: int, data: dict):
        response_bytes = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(response_bytes)

    def do_OPTIONS(self):
        """Handle pre-flight CORS requests."""
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # API: Geocode
        if path == "/api/v1/geocode":
            query_params = urllib.parse.parse_qs(parsed.query)
            q = query_params.get("q", [""])[0]
            if not q:
                self._send_json_response(400, {"success": False, "error": "Missing 'q' query parameter."})
                return
            result = geocode_address(q)
            status_code = 200 if result.get("success") else 404
            self._send_json_response(status_code, result)
            return

        # Serve index.html by default
        if path == "/" or path == "/index.html":
            self.path = "/index.html"
            return super().do_GET()

        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # API: Analyze Rooftop Solar (Physical sizing & kWh prediction)
        if path == "/api/v1/analyze":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length == 0:
                self._send_json_response(400, {"error": "Missing JSON request body."})
                return

            body_str = self.rfile.read(content_length).decode("utf-8")
            try:
                body = json.loads(body_str)
            except Exception:
                self._send_json_response(400, {"error": "Invalid JSON format."})
                return

            lat = float(body.get("lat", 0.0))
            lon = float(body.get("lon", 0.0))
            area_m2 = float(body.get("area_m2", 0.0))

            # Step 4: Validate
            val = validate_and_create_payload(lat, lon, area_m2)
            if not val["valid"]:
                self._send_json_response(422, {"errors": val["errors"]})
                return

            # Step 5: Solar insolation
            solar = fetch_solar_data(lat, lon)
            ghi = solar["ghi_kwh_m2_day"]
            data_source = solar["data_source"]

            # Step 6: Physical sizing & energy prediction
            res = calculate_solar_capacity_and_generation(area_m2, ghi, lat)

            # Step 7: Formatted response
            resp = format_api_response(
                data_source=data_source,
                sizing_data=res["sizing"],
                energy_data=res["energy"],
                environmental_data=res["environmental"]
            )
            self._send_json_response(200, resp)
            return

        self._send_json_response(404, {"error": f"Endpoint '{path}' not found."})


def run_server():
    port = get_env_int("PORT", 8000)
    host = get_env("HOST", "0.0.0.0")
    server_address = (host, port)
    httpd = HTTPServer(server_address, HelioGridHandler)
    print("=" * 60)
    print(f"☀️ HelioGrid V1 Server running at http://localhost:{port}/")
    print(f"• Frontend UI : http://localhost:{port}/index.html")
    print(f"• API Endpoint: http://localhost:{port}/api/v1/analyze")
    print("=" * 60)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")

if __name__ == "__main__":
    run_server()
