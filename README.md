# FX90 Simulator

A lightweight Python-based simulator for a Zebra FX90 RFID reader.

The simulator is intended to run on a Raspberry Pi and provide a network-based stand-in for a physical FX90 during development and testing.

The project will eventually reproduce the REST and WebSocket interfaces that the application under test expects from the real reader.

## Project Structure

```text
fx90-simulator/
├── app.py
├── config.py
├── reader.py
├── websocket.py
├── requirements.txt
├── README.md
├── .gitignore
├── scripts/
│   └── generate-certs.sh
├── certs/
│   └── .gitkeep
└── data/
    └── tags.json
```

### Files

- `app.py` - FastAPI application and REST/WebSocket routes.
- `config.py` - Application configuration and certificate paths.
- `reader.py` - Simulated reader state and tag data.
- `websocket.py` - WebSocket connection management.
- `data/tags.json` - Sample RFID tags used by the simulator.
- `scripts/generate-certs.sh` - Reproducibly creates the development CA and server certificate.

## Purpose

This is a test device, not an RFID reader. It allows application development and integration testing without having a physical FX90 connected.

Planned capabilities include:

- Start/stop the simulated reader
- Report reader status
- Generate simulated RFID tag reads
- Simulate multiple antennas
- Simulate reader errors
- Simulate disconnect/reconnect
- Expose FX90-compatible REST endpoints
- Expose FX90-compatible WebSocket events

The actual FX90-compatible endpoint paths and JSON formats will be added as they are documented.

## Raspberry Pi Setup

### 1. Install prerequisites

On Raspberry Pi OS/Debian:

```bash
sudo apt update
sudo apt install -y git python3 python3-venv openssl
```

Verify:

```bash
python3 --version
openssl version
```

### 2. Clone the repository

```bash
git clone <repository-url>
cd fx90-simulator
```

### 3. Create a Python virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` in your shell prompt.

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Generate the Development Certificate

The simulator uses HTTPS and WSS so applications can be tested against TLS rather than plain HTTP.

Run:

```bash
chmod +x scripts/generate-certs.sh
./scripts/generate-certs.sh
```

This creates:

```text
certs/
├── ca.crt
├── ca.key
├── server.crt
└── server.key
```

The server certificate is currently valid for:

- `pie3.local`
- `localhost`
- `127.0.0.1`

If the simulator will be accessed through another hostname or IP address, update the SAN entries in `scripts/generate-certs.sh` before generating the certificate.

### Important

`ca.key` and `server.key` are private keys. Do not commit them to Git.

Generated certificates and private keys are ignored by `.gitignore`.

## Start the Simulator

With the virtual environment activated:

```bash
python app.py
```

The default HTTPS endpoint is:

```text
https://pie3.local:8443
```

The server listens on all network interfaces (`0.0.0.0`).

You can also start it with Uvicorn:

```bash
uvicorn app:app \
  --host 0.0.0.0 \
  --port 8443 \
  --ssl-keyfile certs/server.key \
  --ssl-certfile certs/server.crt
```

## Test the REST API

Because the certificate is self-signed, `curl` will not trust it until the CA is installed.

For a quick development test, certificate verification can temporarily be disabled:

```bash
curl -k https://pie3.local:8443/reader/status
```

Start the reader:

```bash
curl -k -X POST https://pie3.local:8443/reader/start
```

Stop the reader:

```bash
curl -k -X POST https://pie3.local:8443/reader/stop
```

## WebSocket

The initial WebSocket endpoint is:

```text
wss://pie3.local:8443/ws
```

When a client connects, the simulator sends an initial status message.

The WebSocket implementation is intentionally minimal at this stage. RFID tag events and the exact FX90 WebSocket protocol will be added after the real reader messages are documented.

## Configuration

Settings can be changed with environment variables.

For example:

```bash
export FX90_HTTPS_PORT=8443
export FX90_HOST=0.0.0.0
python app.py
```

Available settings:

| Variable | Default | Purpose |
|---|---|---|
| `FX90_HOST` | `0.0.0.0` | Listen address |
| `FX90_HTTPS_PORT` | `8443` | HTTPS/WebSocket port |
| `FX90_SERVER_CERT` | `certs/server.crt` | Server certificate |
| `FX90_SERVER_KEY` | `certs/server.key` | Server private key |
| `FX90_TAGS_FILE` | `data/tags.json` | Simulated tag file |
| `FX90_RELOAD` | `false` | Enable development reload |

## Trusting the CA

For normal TLS validation, install `certs/ca.crt` as a trusted development CA on the machine running the application under test.

Do not disable certificate validation in the application as the permanent solution. Using the local CA allows TLS behavior to be tested normally.

The exact trust-store procedure depends on the operating system and application.

## Current REST API

The initial simulator provides:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/reader/status` | Get simulated reader status |
| `POST` | `/reader/start` | Start simulated reader |
| `POST` | `/reader/stop` | Stop simulated reader |

These are temporary simulator endpoints. They will be changed to match the actual FX90 API once the real request/response examples are provided.

## Current WebSocket API

Initial endpoint:

```text
wss://pie3.local:8443/ws
```

On connection:

```json
{
  "type": "status",
  "data": {
    "state": "STOPPED",
    "timestamp": "..."
  }
}
```

The final WebSocket message format will be based on the actual FX90 messages.

## Development Workflow

A typical development session:

```bash
cd fx90-simulator
source .venv/bin/activate
python app.py
```

Then use the application under test to connect to:

```text
https://pie3.local:8443
```

and:

```text
wss://pie3.local:8443/ws
```

As FX90 API examples become available, update the simulator to reproduce the real interface.

## Design Goal

Keep the simulator intentionally simple.

The goal is not to reproduce the internal implementation of a Zebra FX90. The goal is to reproduce the externally visible behavior that our application depends on.

That makes this project useful as a repeatable development and integration-test device.
