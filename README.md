# RFID Interface Test Harness

A lightweight RFID interface test harness for **Ultra Tracker**, with the **Zebra FXR90** as the first simulated reader implementation.

The project is intentionally **not** a complete Zebra FXR90 implementation. It reproduces the externally visible behavior that Ultra Tracker consumes so the RFID interface can be tested with normal race traffic, high-volume traffic, bursts, unknown tags, reconnects, and controlled failure scenarios.

## Test control panel

The harness includes a browser-based control panel:

```text
https://<host>:443/test/
```

Test behavior is organized as **scenario JSON files** under `scenarios/`. The control panel discovers those files automatically and places them in the **Test Scenario** drop-down.

Selecting a scenario loads its settings into the visible form fields so the user can see exactly what will be tested. The fields remain editable while the reader is stopped, so a scenario can be adjusted without creating another JSON file.

The initial scenarios are:

- **Start Line Test** — compact, high-volume runner traffic with bursts of up to 20 tags.
- **Finish Line Test** — 400 runners distributed across a 16-hour period, with compact groups at the finish line.

Adding another scenario is intended to be as simple as adding another JSON file. The simulator validates the settings when they are saved or when a scan starts.

The panel provides:

- **Scenario selection** loaded dynamically from JSON
- **Visible scenario settings** for runner count, bib range, tag order, noise, bursts, duration, and delivery delay
- **Live scan status** and counters
- **Custom noise tags** supplied as a JSON array
- **Failure injection** for WebSocket disconnects after a tag count or elapsed time
- **Start, stop, save, and reset controls**
- **Diagnostic JSON** containing the complete current test state

Settings are runtime-only and can only be changed while the simulated reader is stopped.

### Scenario format

A scenario file contains a display name, description, and a settings object. For example:

```json
{
  "name": "Finish Line Test",
  "description": "Simulates 400 runners finishing an ultra marathon over a 16-hour period.",
  "settings": {
    "simulation_mode": "finish-line",
    "duration_hours": 16,
    "runner_count": 400,
    "tag_order": "random",
    "noise_percent": 5,
    "max_burst_size": 20,
    "max_burst_seconds": 0.8,
    "between_bursts_min": 30,
    "between_bursts_max": 1800,
    "report_each_tag_once": true
  }
}
```

Scenario JSON describes the test; the simulator code remains responsible for executing the supported simulation modes. This keeps future scenarios easy to add without putting executable code in configuration files.

### Custom noise tags

Custom noise tags are treated as a one-shot queue. When a noise event occurs, the next supplied custom tag is sent in list order. Once the list is exhausted, the generated noise pool is used. This is useful for parser and error-handling tests because custom values are not required to look like valid RFID tags.

## Current reader implementation

The current implementation simulates the subset of the **Zebra FXR90** interface used by Ultra Tracker:

- HTTPS REST API on port **443**
- WebSocket Secure (WSS) on port **443**
- REST login with HTTP Basic authentication
- Bearer-authenticated `/cloud/*` endpoints
- Unauthenticated `/ws` WebSocket

```text
HTTPS REST:  https://<host>:443/cloud/...
WSS:         wss://<host>:443/ws
```

## Zebra FXR90 / Ultra Tracker contract

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

## Simulated traffic behavior

The **Start Line Test** is designed around a typical ultra race start with roughly 300–400 runners:

- **400 legitimate runner tags** by default
- Legitimate runner tags are generated from the configured bib range and reported **once per reader start**
- Runner reads can be sent in **sequential or randomized order**
- Runner reads are grouped into bursts of up to **20 events**
- A burst targets approximately **one second or less**
- **5% unknown/noise tags** by default
- Generated noise uses bib numbers outside the configured runner range
- Periodic heartbeat logs report scan state, counts, remaining runners, and connected WebSocket clients

The **Finish Line Test** keeps the same runner/tag contract but distributes legitimate runner reads across its configured duration. The default scenario represents 400 runners finishing over **16 hours**, with compact groups at the finish line rather than a single start-line burst.

The harness also supports deliberate WebSocket disconnects and artificial delivery delay so reconnect, health-check, timeout, and throughput behavior can be tested deliberately.

## Automated tests

Install dependencies and run the complete suite:

```bash
pytest
```

Useful subsets:

```bash
pytest -m unit
pytest -m integration
pytest -m websocket
pytest -m stress
```

## Project layout

```text
fx90-simulator/
├── scenarios/        # JSON-defined simulation scenarios
├── src/fx90_simulator/
│   ├── api/          # REST, WebSocket, and test-control interfaces
│   ├── simulator/    # Simulated reader, scenarios, test controls, and tag generation
│   ├── config.py     # Environment-based deployment configuration
│   └── main.py       # Application entry point
├── tests/            # Automated unit and integration tests
├── scripts/          # Developer utilities
├── certs/            # Local TLS certificates (not committed)
├── data/             # Runtime and captured data
├── systemd/          # Native Linux service definition
├── .devcontainer/    # VS Code Dev Container configuration
├── Dockerfile
├── compose.yaml
├── requirements.txt
└── README.md
```

## Deployment configuration

Environment variables continue to handle deployment and reader-interface configuration such as the HTTPS port, credentials, certificate paths, CORS, and heartbeat interval. Simulation behavior is now primarily selected through the scenario control panel rather than requiring environment-variable changes.

Important deployment settings include:

| Variable | Default | Purpose |
|---|---:|---|
| `FX90_HOST` | `0.0.0.0` | Listen address |
| `FX90_HTTPS_PORT` | `443` | REST and WSS port |
| `FX90_AUTO_START` | `false` | Start automatically |
| `FX90_HEARTBEAT_SECONDS` | `5` | Diagnostic heartbeat interval |
| `FX90_CORS_ORIGINS` | _(unset)_ | Comma-separated allowed browser origins |

The current environment variables for runner/tag defaults remain available as application defaults, but scenario JSON is the preferred way to select a repeatable test configuration.

## TLS and certificate pinning

The harness uses TLS because Ultra Tracker connects to the simulated FXR90 over HTTPS and WSS. Generate local certificates with:

```bash
./scripts/generate-certs.sh
```

If Ultra Tracker's `sslCert` field is being used for certificate pinning, obtain the server certificate serial with:

```bash
openssl x509 -in certs/server.crt -noout -serial
```

Enter the hexadecimal value after `serial=` as the certificate pin.

## Docker deployment

```bash
git clone https://github.com/JordenLuke/fx90-simulator.git
cd fx90-simulator
git checkout develop
cp secrets_example .secrets
./scripts/generate-certs.sh
docker compose up -d --build
```

The container publishes HTTPS/WSS on port **443**.

## Native Raspberry Pi / Linux deployment

Native deployment is useful on a Raspberry Pi or another Linux host where Docker is not desired. The examples install the harness under `/opt/fx90-simulator`.

```bash
sudo apt update
sudo apt install -y git python3 python3-venv openssl
sudo mkdir -p /opt
sudo git clone https://github.com/JordenLuke/fx90-simulator.git /opt/fx90-simulator
sudo chown -R "$USER":"$USER" /opt/fx90-simulator
cd /opt/fx90-simulator
git checkout develop
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
./scripts/generate-certs.sh
```

For normal operation, use the repository's systemd service rather than running the application as root.

## Development container

The repository includes a VS Code Dev Container configuration. Open the repository in VS Code and select **Reopen in Container**. The harness is available on port `443`.

## Capture utility

`scripts/capture.py` is a utility for the current Zebra FXR90-compatible WebSocket interface. It records raw tag data for analysis or replay work and can reconnect after reader-side WebSocket/TCP resets.

## Security notes

This harness is intended for controlled test networks. The default credentials are development defaults and should be changed before exposing the harness to an untrusted network.
