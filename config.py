from dataclasses import dataclass
from pathlib import Path
import os


PROJECT_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Settings:
    host: str = os.getenv("FX90_HOST", "0.0.0.0")
    https_port: int = int(os.getenv("FX90_HTTPS_PORT", "8443"))
    server_cert: str = os.getenv(
        "FX90_SERVER_CERT",
        str(PROJECT_ROOT / "certs" / "server.crt"),
    )
    server_key: str = os.getenv(
        "FX90_SERVER_KEY",
        str(PROJECT_ROOT / "certs" / "server.key"),
    )
    tags_file: str = os.getenv(
        "FX90_TAGS_FILE",
        str(PROJECT_ROOT / "data" / "tags.json"),
    )
    reload: bool = os.getenv("FX90_RELOAD", "false").lower() == "true"


settings = Settings()
