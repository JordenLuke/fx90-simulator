# FX90 Simulator

A lightweight Zebra FXR90 stand-in specifically for testing Ultra Tracker's RFID interface.

The simulator intentionally implements only the interfaces consumed by Ultra Tracker:

- HTTPS REST API on port **443**
- WebSocket Secure (WSS) on port **443**
- REST login with Basic authentication
- Bearer-authenticated `/cloud/*` endpoints
- Unauthenticated `/ws` WebSocket, matching Ultra Tracker

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
├── data/             # Runner tags and captured tag data
├── systemd/          # Native Linux service definition
├── .devcontainer/    # VS Code Dev Container configuration
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

## FXR90-compatible interface

### REST

All REST endpoints except `/cloud/localRestLogin` require:

```text
Authorization: Bearer <token>
```

Supported endpoints:

```text
GET /cloud/localRestLogin
GET /cloud/status
GET /cloud/mode
PUT /cloud/mode
PUT /cloud/start
PUT /cloud/stop
```

The login endpoint uses HTTP Basic authentication and returns the FXR90-style response:

```json
{"code":0,"message":"<bearer-token>"}
```

### WebSocket

Ultra Tracker connects without a Bearer token:

```text
wss://<host>:443/ws
```

Tag events use the observed FXR90 format:

```json
{"data":{"eventNum":1,"format":"epc","idHex":"000000000000000000000001"},"timestamp":"2026-09-06T16:00:00.000-0600","type":"CUSTOM"}
```

## Default behavior

- 400 legitimate runner tags
- Each legitimate tag is reported once per reader start
- Bursts contain up to 20 events
- Burst duration is approximately one second or less
- 5% unknown/noise tags
- Reader is stopped until `/cloud/start` is called unless `FX90_AUTO_START=true`

## TLS certificate

The simulator requires a certificate because both REST and WebSocket traffic use TLS.

Generate a development certificate:

```bash
./scripts/generate-certs.sh
```

The generated certificate includes `fx90-simulator`, `localhost`, and `pi3.local` as DNS names.

For Ultra Tracker certificate pinning, inspect the generated certificate serial with:

```bash
openssl x509 -in certs/server.crt -noout -serial
```

Do not commit `server.key` or `server.crt`.

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
| `FX90_HTTPS_PORT` | `443` | REST and WSS port |
| `FX90_RUNNER_COUNT` | `400` | Number of legitimate runner tags |
| `FX90_NOISE_PERCENT` | `5` | Percentage of generated events using noise tags |
| `FX90_MAX_BURST_SIZE` | `20` | Maximum events in one burst |
| `FX90_MAX_BURST_SECONDS` | `0.8` | Target burst duration |
| `FX90_BETWEEN_BURSTS_MIN` | `2` | Minimum seconds between bursts |
| `FX90_BETWEEN_BURSTS_MAX` | `8` | Maximum seconds between bursts |
| `FX90_REPORT_EACH_TAG_ONCE` | `true` | Report each legitimate runner once per start |
| `FX90_NOISE_POOL_SIZE` | `50` | Number of reusable noise tags |
| `FX90_AUTO_START` | `false` | Start the simulated reader automatically |

## Docker deployment

Docker is the recommended deployment method when the target Linux system already runs Docker.

### Install

```bash
git clone https://github.com/JordenLuke/fx90-simulator.git
cd fx90-simulator
git checkout develop

cp secrets_example .secrets
# Edit .secrets with your desired credentials

./scripts/generate-certs.sh
docker compose up -d --build
```

The container publishes HTTPS/WSS on port `443`.

Check the service:

```bash
docker compose ps
docker compose logs -f
```

Test connectivity from the Linux host:

```bash
curl -k https://localhost:443/cloud/mode
```

An `Unauthorized` response is expected without a Bearer token and confirms that the simulator is reachable.

### Stop the container

```bash
docker compose down
```

### Update the simulator

```bash
git pull
docker compose up -d --build
```

## Native Linux deployment

Native deployment is useful on a Raspberry Pi or another Linux host where Docker is not desired.

The examples below assume Debian, Ubuntu, or Raspberry Pi OS and install the simulator under `/opt/fx90-simulator`.

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

Create an environment file for credentials and local configuration:

```bash
sudo install -m 600 /dev/null /etc/fx90-simulator.env
sudo nano /etc/fx90-simulator.env
```

Example:

```text
FX90_USERNAME=admin
FX90_PASSWORD=change-me
FX90_BEARER_TOKEN=change-me
FX90_HOST=0.0.0.0
FX90_HTTPS_PORT=443
```

### Run manually

For a quick test, port 443 can be bound by running as root:

```bash
cd /opt/fx90-simulator
sudo env PYTHONPATH=/opt/fx90-simulator/src \
  /opt/fx90-simulator/.venv/bin/python -m fx90_simulator
```

For normal operation, use the systemd service below instead of running the application as root.

## systemd service

The repository includes `systemd/fx90-simulator.service` for running the simulator as a dedicated unprivileged service account while retaining permission to bind HTTPS port 443.

Create the service account:

```bash
sudo useradd --system --home /opt/fx90-simulator --shell /usr/sbin/nologin fx90-simulator
```

Give the service account ownership of the installation:

```bash
sudo chown -R fx90-simulator:fx90-simulator /opt/fx90-simulator
```

Install and enable the service:

```bash
sudo cp /opt/fx90-simulator/systemd/fx90-simulator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now fx90-simulator
```

Check the service:

```bash
sudo systemctl status fx90-simulator
```

View logs:

```bash
sudo journalctl -u fx90-simulator -f
```

The service uses `CAP_NET_BIND_SERVICE` so the application does not need to run as root merely to listen on port 443.

### Update a native installation

```bash
cd /opt/fx90-simulator
sudo -u fx90-simulator git pull
sudo -u fx90-simulator .venv/bin/pip install -r requirements.txt
sudo systemctl restart fx90-simulator
```

## Development container

The repository includes a VS Code Dev Container configuration using the Docker Compose service.

Open the repository in VS Code and select **Reopen in Container**. The simulator is available on port `443`.

## Capture utility

`scripts/capture.py` can connect to an FXR90-compatible WebSocket and record raw tag data for analysis or replay work.

Run it from the repository root:

```bash
python3 scripts/capture.py
```

Captured data is stored under `data/`.

## Security notes

This simulator is intended for controlled test networks. The default credentials are development defaults and should be changed before exposing the simulator to an untrusted network.
