"""
HelioGrid - Simple Environment & Config Loader
Zero external dependencies (pure standard library).
"""
import os
from pathlib import Path

def load_env(env_path: str = ".env") -> dict:
    """Reads .env into os.environ without requiring external packages."""
    env_file = Path(env_path)
    if not env_file.exists():
        # Fallback to search in parent or current working directory
        env_file = Path(__file__).resolve().parent / ".env"

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key and key not in os.environ:
                        os.environ[key] = val
    return dict(os.environ)

# Auto-load on import
load_env()

# Quick helper getters
def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)

def get_env_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default

def get_env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (ValueError, TypeError):
        return default


if __name__ == "__main__":
    print("--- Loaded Configuration ---")
    print(f"VEDAS_API_KEY: {get_env('VEDAS_API_KEY')[:6]}... (masked)")
    print(f"VEDAS_WMS_URL: {get_env('VEDAS_WMS_URL')}")
    print(f"NOMINATIM_EMAIL: {get_env('NOMINATIM_EMAIL')}")
    print(f"SOLAR_USABLE_RATIO: {get_env_float('SOLAR_USABLE_RATIO', 0.65)}")
    print(f"SOLAR_PANEL_KW: {get_env_float('SOLAR_PANEL_KW', 0.545)}")
    print(f"PORT: {get_env_int('PORT', 8000)}")
