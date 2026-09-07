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

HOST_SHORT="$(hostname -s)"
HOST_FQDN="$(hostname -f 2>/dev/null || true)"
HOST_IP="$(hostname -I 2>/dev/null | awk '{print $1}')"
CERT_HOSTNAME="${FX90_CERT_HOSTNAME:-$HOST_FQDN}"
if [[ -z "$CERT_HOSTNAME" || "$CERT_HOSTNAME" == "localhost" ]]; then
    CERT_HOSTNAME="$HOST_SHORT"
fi
CERT_CN="$CERT_HOSTNAME"
if (( ${#CERT_CN} > 64 )); then
    CERT_CN="$HOST_SHORT"
fi
if [[ -z "$CERT_CN" || "$CERT_CN" == "localhost" || ${#CERT_CN} -gt 64 ]]; then
    CERT_CN="fx90-simulator"
fi

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
CN = ${CERT_CN}

[req_ext]
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
DNS.2 = fx90-simulator
DNS.3 = ${HOST_SHORT}
EOF

DNS_INDEX=4
if [[ -n "$CERT_HOSTNAME" && "$CERT_HOSTNAME" != "localhost" && "$CERT_HOSTNAME" != "fx90-simulator" && "$CERT_HOSTNAME" != "$HOST_SHORT" ]]; then
    printf 'DNS.%s = %s\n' "$DNS_INDEX" "$CERT_HOSTNAME" >> "$OPENSSL_CNF"
    DNS_INDEX=$((DNS_INDEX + 1))
fi
if [[ -n "$HOST_FQDN" && "$HOST_FQDN" != "$HOST_SHORT" && "$HOST_FQDN" != "localhost" && "$HOST_FQDN" != "fx90-simulator" && "$HOST_FQDN" != "$CERT_HOSTNAME" ]]; then
    printf 'DNS.%s = %s\n' "$DNS_INDEX" "$HOST_FQDN" >> "$OPENSSL_CNF"
fi

if [[ -n "$HOST_IP" ]]; then
    printf 'IP.1 = %s\n' "$HOST_IP" >> "$OPENSSL_CNF"
    printf 'IP.2 = 127.0.0.1\n' >> "$OPENSSL_CNF"
else
    printf 'IP.1 = 127.0.0.1\n' >> "$OPENSSL_CNF"
fi

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
echo "  Server hostname:    $CERT_HOSTNAME"
echo
echo "Certificate serial (for Ultra Tracker pinning):"
openssl x509 -in "$SERVER_CERT" -noout -serial

echo
echo "Keep ca.key and server.key private."
