# FX90 Simulator

A lightweight Zebra FXR90 stand-in specifically for testing Ultra Tracker's RFID interface.

This is **not** intended to be a complete FXR90 implementation. The goal is to reproduce the externally visible behavior that Ultra Tracker consumes so the RFID interface can be tested with normal race traffic, high-volume traffic, bursts, unknown tags, and controlled failure scenarios.

## Interface summary

The simulator intentionally matches the interface used by Ultra Tracker:

- HTTPS REST API on port **443**
- WebSocket Secure (WSS) on port **443**
- REST login with HTTP Basic authentication
- Bearer-authenticated `/cloud/*` endpoints
- Unauthenticated `/ws` WebSocket

```text
HTTPS REST:  https://<host>:443/cloud/...
WSS:         wss://<host>:443/ws
```

## FXR90 / Ultra Tracker contract

### REST

`GET /cloud/localRestLogin` uses HTTP Basic authentication and returns:

```json
{"code":0,"message":"<bearer-token>"}
```

All other supported REST endpoints require `Authorization: Bearer <token>`.

Supported endpoints:

```text
GET /cloud/localRestLogin
GET /cloud/status
GET /cloud/mode
PUT /cloud/mode
PUT /cloud/start
PUT /cloud/stop
```

`PUT /cloud/start` accepts the request body used by Ultra Tracker (`{"doNotPersistState":true}`), starts tag generation, and returns HTTP 204. If already active it returns HTTP 422 with `start currently ongoing`.

`PUT /cloud/stop` stops tag generation and returns HTTP 204.

`GET /cloud/status` reports simulated reader state, including `radioActivity` and antenna state. `GET /cloud/mode` returns the simulated reader mode. `PUT /cloud/mode` accepts the request and returns HTTP 204.

### WebSocket

Ultra Tracker connects without a Bearer token:

```text
wss://<host>:443/ws
```

Tag events use the observed FXR90 format:

```json
{"data":{"eventNum":1,"format":"epc","idHex":"000000000000000000001"},"timestamp":"2026-09-06T16:00:00.000-0600","type":"CUSTOM"}
```

The `idHex` format is compatible with Ultra Tracker's current parser: 20 leading zeroes followed by the decimal runner/tag number.

## Simulator behavior

The default configuration is designed around a typical ultra race with roughly 300–400 runners:

- **400 legitimate runner tags** by default
- Legitimate runner tags are generated from the configured bib range and reported **once per reader start**
- Runner reads can be sent in **sequential or randomized order**
- Runner reads are grouped into bursts of up to **20 events**
- A burst completes in approximately **one second or less**
- **5% unknown/noise tags** by default
- Noise tags use the same valid RFID format but use bib numbers outside the configured runner range
- Tag generation remains stopped until `/cloud/start` is called unless `FX90_AUTO_START=true`
- Periodic heartbeat logs report scan state, counts, remaining runners, and connected WebSocket clients

The simulator is intended to support controlled failure modes, including WebSocket disconnects, so Ultra Tracker reconnect and health-check behavior can be tested deliberately rather than relying only on failures from a physical reader.

## Project layout

```text
fx90-simulator/
├── src/fx90_simulator/
│   ├── api/          # REST and WebSocket interfaces
│   ├── simulator/    # Simulated reader and tag generation
│   ├── config.py     # Environment-based configuration
│   └── main.py       # Application entry point
├── scripts/          # Developer utilities
├── certs/            # Local TLS certificates (not committed)
├── data/             # Captured tag data and runtime data
├── systemd/          # Native Linux service definition
├── .devcontainer/    # VS Code Dev Container configuration
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

## Configuration

Configuration is supplied through environment variables. Docker Compose loads credentials from a local `.secrets` file.

Create the local secrets file from the committed template:

```bash
cp secrets_example .secrets
```

Edit `.secrets` and set the username, password, and bearer token. Never commit `.secrets`.

Important settings include:

| Variable | Default | Purpose |
|---|---:|---|
| `FX90_HOST` | `0.0.0.0` | Listen address |
| `FX90_HTTPS_PORT` | `443` | REST and WSS port |
| `FX90_BIB_START` | `1` | First possible legitimate bib number |
| `FX90_BIB_END` | `429` | Last possible legitimate bib number |
| `FX90_RUNNER_COUNT` | `400` | Number of legitimate runner tags per reader start |
| `FX90_TAG_ORDER` | `random` | Legitimate tag order: `random` or `sequential` |
| `FX90_NOISE_PERCENT` | `5` | Percentage of generated events using noise tags |
| `FX90_MAX_BURST_SIZE` | `20` | Maximum events in one burst |
| `FX90_MAX_BURST_SECONDS` | `0.8` | Target maximum burst duration |
| `FX90_BETWEEN_BURSTS_MIN` | `2` | Minimum seconds between bursts |
| `FX90_BETWEEN_BURSTS_MAX` | `8` | Maximum seconds between bursts |
| `FX90_REPORT_EACH_TAG_ONCE` | `true` | Report each legitimate runner once per start |
| `FX90_NOISE_POOL_SIZE` | `50` | Number of reusable noise tags |
| `FX90_AUTO_START` | `false` | Start the simulated reader automatically |
| `FX90_HEARTBEAT_SECONDS` | `5` | Interval between diagnostic heartbeat logs |
| `FX90_CORS_ORIGINS` | _(unset)_ | Comma-separated browser origins allowed for CORS; leave unset to disable CORS |

Legitimate RFID values are derived directly from the bib number. For example:

```text
Bib 1   -> 000000000000000000001
Bib 10  -> 000000000000000000010
Bib 190 -> 000000000000000000190
Bib 429 -> 000000000000000000429
```

No runner/tag data file is required.

## TLS and certificate pinning

The simulator uses TLS because Ultra Tracker connects to the FXR90 over HTTPS and WSS. The certificate-generation script creates a local CA and server certificate.

Generate certificates on the target machine:

```bash
./scripts/generate-certs.sh
```

The script detects the machine's short hostname, FQDN, and primary IP and includes them in the server certificate's Subject Alternative Names. It also includes `localhost`, `fx90-simulator`, and `127.0.0.1`.

If the machine's hostname is not the name you intend to use from Ultra Tracker, set an explicit certificate hostname before generating the certificate:

```bash
FX90_CERT_HOSTNAME=pi3.local ./scripts/generate-certs.sh
```

The certificate hostname/SAN is separate from Ultra Tracker's `sslCert` pin. If Ultra Tracker's certificate field rejects a hostname as invalid input, use the server certificate's serial number instead:

```bash
openssl x509 -in certs/server.crt -noout -serial
```

Enter the hexadecimal value after `serial=` as the certificate pin.

Keep `ca.key` and `server.key` private. Do not commit private keys or generated certificates.

## Docker deployment

```bash
git clone https://github.com/JordenLuke/fx90-simulator.git
cd fx90-simulator
git checkout develop
cp secrets_example .secrets
# Edit .secrets with your desired credentials
./scripts/generate-certs.sh
docker compose up -d --build
```

The container publishes HTTPS/WSS on port **443**.

Check the service:

```bash
docker compose ps
docker compose logs -f
```

Test connectivity:

```bash
curl -k https://localhost:443/cloud/mode
```

An `Unauthorized` response without a Bearer token is expected and confirms that the simulator is reachable.

Stop the container:

```bash
docker compose down
```

Update the simulator:

```bash
git pull
docker compose up -d --build
```

## Native Raspberry Pi / Linux deployment

Native deployment is useful on a Raspberry Pi or another Linux host where Docker is not desired. The examples install the simulator under `/opt/fx90-simulator`.

### Install prerequisites

```bash
sudo apt update
sudo apt install -y git python3 python3-venv openssl
```

### Install the simulator

```bash
sudo mkdir -p /opt
sudo git clone https://github.com/JordenLuke/fx90-simulator.git /opt/fx90-simulator
sudo chown -R "$USER":"$USER" /opt/fx90-simulator
cd /opt/fx90-simulator
git checkout develop
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./scripts/generate-certs.sh
```

Create `/etc/fx90-simulator.env` with credentials and local configuration:

```text
FX90_USERNAME=admin
FX90_PASSWORD=change-me
FX90_BEARER_TOKEN=change-me
FX90_HOST=0.0.0.0
FX90_HTTPS_PORT=443
```

### Run manually

```bash
cd /opt/fx90-simulator
sudo env PYTHONPATH=/opt/fx90-simulator/src \
  /opt/fx90-simulator/.venv/bin/python -m fx90_simulator
```

For normal operation, use the systemd service instead of running the application as root.

## systemd service

The repository includes `systemd/fx90-simulator.service` for running the simulator as an unprivileged service account while retaining permission to bind port 443.

```bash
sudo useradd --system --home /opt/fx90-simulator --shell /usr/sbin/nologin fx90-simulator
sudo chown -R fx90-simulator:fx90-simulator /opt/fx90-simulator
sudo cp /opt/fx90-simulator/systemd/fx90-simulator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fx90-simulator
```

Check logs:

```bash
sudo systemctl status fx90-simulator
sudo journalctl -u fx90-simulator -f
```

The service uses `CAP_NET_BIND_SERVICE` so it does not need to run as root merely to listen on port 443.

### Update a native installation

```bash
cd /opt/fx90-simulator
sudo -u fx90-simulator git pull
sudo -u fx90-simulator .venv/bin/pip install -r requirements.txt
sudo systemctl restart fx90-simulator
```

## Development container

The repository includes a VS Code Dev Container configuration. Open the repository in VS Code and select **Reopen in Container**. The simulator is available on port `443`.

## Capture utility

`scripts/capture.py` connects to an FXR90-compatible WebSocket and records raw tag data for analysis or replay work. It can reconnect after reader-side WebSocket/TCP resets so longer captures can continue.

Run it from the repository root:

```bash
python3 scripts/capture.py
```

For self-signed simulator certificates, provide the generated CA certificate explicitly:

```bash
python3 scripts/capture.py --cafile certs/ca.crt
```

Captured data is stored under `data/`.

## Security notes

This simulator is intended for controlled test networks. The default credentials are development defaults and should be changed before exposing the simulator to an untrusted network.
