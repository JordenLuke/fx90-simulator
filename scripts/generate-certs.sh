#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/certs"
openssl req -x509 -newkey rsa:2048 -nodes -keyout "$ROOT/certs/server.key" -out "$ROOT/certs/server.crt" -days 3650 -subj "/CN=fx90-simulator" -addext "subjectAltName=DNS:fx90-simulator,DNS:localhost,IP:127.0.0.1"
echo "Generated simulator certificate."
