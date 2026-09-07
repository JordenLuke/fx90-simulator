import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CERT_DIR = PROJECT_ROOT / "certs"


def _get_int(name: str, default: str, *, minimum: int | None = None) -> int:
    value = int(os.getenv(name, default))
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _get_float(name: str, default: str, *, minimum: float | None = None) -> float:
    value = float(os.getenv(name, default))
    if minimum is not None and value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value

HOST = os.getenv("FX90_HOST", "0.0.0.0")
HTTPS_PORT = int(os.getenv("FX90_HTTPS_PORT", "443"))
CERT_FILE = Path(os.getenv("FX90_CERT_FILE", str(CERT_DIR / "server.crt")))
KEY_FILE = Path(os.getenv("FX90_KEY_FILE", str(CERT_DIR / "server.key")))
TAGS_FILE = Path(os.getenv("FX90_TAGS_FILE", str(DATA_DIR / "tags.json")))

USERNAME = os.getenv("FX90_USERNAME", "admin")
PASSWORD = os.getenv("FX90_PASSWORD", "admin")
BEARER_TOKEN = os.getenv("FX90_BEARER_TOKEN", "fx90-simulator-token")

RUNNER_COUNT = _get_int("FX90_RUNNER_COUNT", "400", minimum=1)
NOISE_PERCENT = _get_float("FX90_NOISE_PERCENT", "5", minimum=0)
MAX_BURST_SIZE = _get_int("FX90_MAX_BURST_SIZE", "20", minimum=1)
MAX_BURST_SECONDS = _get_float("FX90_MAX_BURST_SECONDS", "0.8", minimum=0)
BETWEEN_BURSTS_MIN = _get_float("FX90_BETWEEN_BURSTS_MIN", "2", minimum=0)
BETWEEN_BURSTS_MAX = _get_float("FX90_BETWEEN_BURSTS_MAX", "8", minimum=0)
REPORT_EACH_TAG_ONCE = os.getenv("FX90_REPORT_EACH_TAG_ONCE", "true").lower() == "true"
NOISE_POOL_SIZE = _get_int("FX90_NOISE_POOL_SIZE", "50", minimum=1)
AUTO_START = os.getenv("FX90_AUTO_START", "false").lower() == "true"
CORS_ORIGINS = [origin.strip() for origin in os.getenv("FX90_CORS_ORIGINS", "").split(",") if origin.strip()]
