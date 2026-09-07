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
src/fx90_simulator/
├── api/          # REST and WebSocket interfaces
├── simulator/    # Simulated reader and tag generation
├── config.py     # Environment-based configuration
└── main.py       # Application entry point

scripts/          # Developer utilities
certs/            # Local TLS certificates (not committed)
data/             # Runner tags and captured tag data
```

## Run locally

Generate a development certificate:

```bash
./scripts/generate-certs.sh
```

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run the simulator:

```bash
PYTHONPATH=src python3 -m fx90_simulator.main
```

The simulator listens on `https://0.0.0.0:443` by default.

## Run with Docker

Create the local secrets file from the committed template first:

```bash
cp secrets_example .secrets
```

Edit `.secrets` and replace the example credentials with your local values. **Do not commit `.secrets`.**

Then generate the development certificate and start the simulator:

```bash
./scripts/generate-certs.sh
docker compose up --build
```

Generated TLS certificate and key files under `certs/` are ignored by Git. The `certs/.gitkeep` file keeps the directory in the repository.

## Default behavior

- 400 legitimate runner tags
- Each legitimate tag is reported once per reader start
- Bursts contain up to 20 events
- Burst duration is approximately one second or less
- 5% unknown/noise tags
- Reader is stopped until `/cloud/start` is called unless `FX90_AUTO_START=true`

## Configuration

Credentials are loaded from the local `.secrets` file when using Docker Compose. The committed `secrets_example` file documents the required values.

Other runtime configuration is supplied through environment variables in `compose.yaml`.

Important settings include:

| Variable | Default | Purpose |
|---|---:|---|
| `FX90_HTTPS_PORT` | `443` | REST and WSS port |
| `FX90_RUNNER_COUNT` | `400` | Number of legitimate runner tags |
| `FX90_NOISE_PERCENT` | `5` | Percentage of generated events using noise tags |
| `FX90_MAX_BURST_SIZE` | `20` | Maximum events in one burst |
| `FX90_MAX_BURST_SECONDS` | `0.8` | Target burst duration |
| `FX90_REPORT_EACH_TAG_ONCE` | `true` | Report each legitimate runner once per start |
| `FX90_AUTO_START` | `false` | Start the simulated reader automatically |

## FXR90-compatible endpoints

```text
GET /cloud/localRestLogin
GET /cloud/status
GET /cloud/mode
PUT /cloud/mode
PUT /cloud/start
PUT /cloud/stop
WSS /ws
```
