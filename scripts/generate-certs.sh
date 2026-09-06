#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CERT_DIR="$PROJECT_ROOT/certs"

mkdir -p "$CERT_DIR"

CA_KEY="$CERT_DIR/ca.key"
CA_CERT="$CERT_DIR/ca.crt"
SERVER_KEY="$CERT_DIR/server.key"
SERVER_CSR="$CERT_DIR/server.csr"
SERVER_CERT="$CERT_DIR/server.crt"
OPENSSL_CNF="$CERT_DIR/server.cnf"

echo "Generating FX90 Simulator certificates..."

openssl genrsa -out "$CA_KEY" 4096

openssl req -x509 \
    -new \
    -nodes \
    -key "$CA_KEY" \
    -sha256 \
    -days 3650 \
    -out "$CA_CERT" \
    -subj "/C=US/ST=Utah/O=FX90 Simulator/CN=FX90 Simulator CA"

openssl genrsa -out "$SERVER_KEY" 2048

cat > "$OPENSSL_CNF" <<EOF
[req]
prompt = no
distinguished_name = dn
req_extensions = req_ext

[dn]
C = US
ST = Utah
O = FX90 Simulator
CN = pie3.local

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = pie3.local
DNS.2 = localhost
IP.1 = 127.0.0.1
EOF

openssl req \
    -new \
    -key "$SERVER_KEY" \
    -out "$SERVER_CSR" \
    -config "$OPENSSL_CNF"

openssl x509 \
    -req \
    -in "$SERVER_CSR" \
    -CA "$CA_CERT" \
    -CAkey "$CA_KEY" \
    -CAcreateserial \
    -out "$SERVER_CERT" \
    -days 825 \
    -sha256 \
    -extensions req_ext \
    -extfile "$OPENSSL_CNF"

rm -f "$SERVER_CSR" "$OPENSSL_CNF" "$CERT_DIR/ca.srl"

chmod 600 "$CA_KEY" "$SERVER_KEY"

echo
echo "Certificates generated:"
echo "  CA certificate:     $CA_CERT"
echo "  Server certificate: $SERVER_CERT"
echo "  Server key:         $SERVER_KEY"
echo
echo "Keep ca.key and server.key private."
