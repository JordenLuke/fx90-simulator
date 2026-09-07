#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="$ROOT/certs"
mkdir -p "$CERT_DIR"

openssl req -x509 -newkey rsa:2048 -nodes \
  -keyout "$CERT_DIR/server.key" \
  -out "$CERT_DIR/server.crt" \
  -days 3650 \
  -subj "/CN=fx90-simulator" \
  -addext "subjectAltName=DNS:fx90-simulator,DNS:localhost,DNS:pi3.local,IP:127.0.0.1"

echo "Generated simulator certificate in $CERT_DIR"
