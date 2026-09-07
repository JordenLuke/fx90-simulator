# FX90 Simulator

A lightweight Zebra FXR90 stand-in specifically for testing Ultra Tracker's RFID interface.

REST: `GET /cloud/localRestLogin`, `GET /cloud/status`, `GET /cloud/mode`, `PUT /cloud/mode`, `PUT /cloud/start`, `PUT /cloud/stop`.

WebSocket: `wss://<host>:<port>/ws` with no Bearer token, matching Ultra Tracker.

Observed tag event:

```json
{"data":{"eventNum":1,"format":"epc","idHex":"000000000000000000000001"},"timestamp":"2026-09-06T16:00:00.000-0600","type":"CUSTOM"}
```

Defaults: 400 legitimate runners, each reported once; up to 20 events per burst; burst duration under about one second; 5% unknown/noise tags.

Run locally:

```bash
./scripts/generate-certs.sh
python3 -m pip install -r requirements.txt
python3 app.py
```

Or with Docker:

```bash
./scripts/generate-certs.sh
docker compose up --build
```

Configuration is in `compose.yaml` environment variables.
