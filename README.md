## Professional dashboard and built-in guide

Launch the browser dashboard by double-clicking `Launch_Dashboard.command`, or run:

```bash
source .venv/bin/activate
streamlit run dashboard/app.py
```

The dashboard has five workspaces: **Overview**, **Run experiments**, **Results**,
**How to use**, and **Service manager**. The built-in guide explains the MQTT
publish/subscribe echo flow, CoAP Confirmable POST echo flow, QoS levels,
benchmark settings, result interpretation, CSV location, fair comparison
methodology, limitations, and troubleshooting.

Use Service manager to start the MQTT echo responder and CoAP server. An MQTT
broker already listening on `127.0.0.1:1883` is detected automatically. The
dashboard does not claim to control a broker started externally.

# NEW: Visual dashboard (recommended way to use the project)

After the one-time setup, open the project folder in Finder and double-click
`Launch_Dashboard.command`. Alternatively, from the project folder run:

```bash
source .venv/bin/activate
streamlit run dashboard/app.py
```

The dashboard opens in your browser. Use **Service Manager** to start the local
MQTT broker, MQTT echo service, and CoAP server. Then use **Experiment Control**
to run MQTT QoS 0/1/2 and CoAP tests with buttons. **Results & Comparison**
shows charts, summary metrics, raw records, and a CSV download. The Service
Manager also displays service logs.

The dashboard-managed Mosquitto configuration binds to `127.0.0.1` only.
If you previously started Mosquitto manually, stop that foreground process
with Ctrl+C first, or the dashboard will report that port 1883 is already in use.
The dashboard can use an already-running local broker, but it can only stop
processes it started itself.

# IoT Protocol Testbed — MQTT vs CoAP

A software-only testbed for implementing and comparing **real MQTT and CoAP communication**. The project is designed for macOS (including Apple Silicon) and does not require Arduino boards, sensors, or other physical IoT hardware.

> **Measurement integrity:** The MQTT and CoAP packets are real protocol traffic sent over the host's network stack. Round-trip time and delivery measurements are collected from those exchanges. The optional virtual sensor publisher generates clearly labelled `SYNTHETIC_TEST_DATA`; do not describe those generated temperatures/humidity values as physical sensor readings. Localhost benchmarks measure the Mac and local services, not Wi-Fi radio performance or a microcontroller's power consumption.

## What is included

- **MQTT broker:** Eclipse Mosquitto, started through Docker Compose.
- **MQTT clients:** Paho-based echo service, round-trip benchmark, telemetry publisher, and subscriber.
- **CoAP server and clients:** `aiocoap` server exposing `/sensor` and `/echo`, resource client, and round-trip benchmark.
- **Experiment logging:** each benchmark attempt is appended to `results/metrics.csv`, including failures/timeouts.
- **Dashboard:** Streamlit app for RTT, delivery success, message-size summaries, raw rows, and MQTT telemetry.
- **Packet analysis:** instructions for capturing MQTT and CoAP traffic with Wireshark.

## Requirements

- macOS 13 or newer is recommended (Apple Silicon or Intel).
- Python **3.11 or 3.12**. The project dependencies currently require Python 3.11+; `aiocoap` supports Python 3.11+ and Streamlit's current supported range includes Python 3.11+.
- Docker Desktop with Docker Compose (recommended for Mosquitto), **or** Mosquitto installed locally with Homebrew.
- Wireshark is optional, but recommended for packet-level analysis.

## 1. Create the Python environment

Open Terminal and move into this project folder:

```bash
cd iot_protocol_testbed
python3 --version
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Use the `.venv` interpreter for all commands in the rest of this README. If `python3 --version` is below 3.11, install a supported version first (for example, with Homebrew: `brew install python@3.12`).

## 2. Start the MQTT broker

### Option A — Docker (recommended)

Make sure Docker Desktop is running, then execute:

```bash
docker compose up -d
```

Check that the broker container is running:

```bash
docker compose ps
docker compose logs mosquitto
```

The broker listens on `127.0.0.1:1883` by default. The included Mosquitto configuration allows anonymous connections for a local classroom testbed only.

### Option B — Homebrew Mosquitto

In a separate Terminal window:

```bash
brew install mosquitto
mosquitto -c mosquitto/mosquitto.conf -v
```

Do not run both options on the same port at the same time.

## 3. Run the MQTT echo service

Keep the broker running. Open another Terminal in the project folder, activate the environment, and start the echo service:

```bash
source .venv/bin/activate
python -m mqtt.echo_service
```

The service subscribes to `testbed/mqtt/echo/request/+` and echoes each request to a run-specific response topic. Leave this terminal open while benchmarking.

## 4. Run an MQTT benchmark

Open a third Terminal:

```bash
source .venv/bin/activate
python -m mqtt.benchmark --count 50 --size 64 --qos 1
```

Try the three MQTT QoS levels separately:

```bash
python -m mqtt.benchmark --count 50 --size 64 --qos 0
python -m mqtt.benchmark --count 50 --size 64 --qos 1
python -m mqtt.benchmark --count 50 --size 64 --qos 2
```

Change the payload size to repeat the experiment at different application message sizes:

```bash
python -m mqtt.benchmark --count 50 --size 16 --qos 1
python -m mqtt.benchmark --count 50 --size 256 --qos 1
python -m mqtt.benchmark --count 50 --size 1024 --qos 1
```

The client performs a request/echo exchange and measures elapsed time on the client. Each attempt—including timeouts—is appended to `results/metrics.csv`.

## 5. Run the CoAP server and benchmark

Open another Terminal and start the CoAP resource server:

```bash
source .venv/bin/activate
python -m coap.server
```

The server listens on UDP port `5683` and exposes:

- `coap://127.0.0.1:5683/sensor` — GET, POST, PUT, DELETE
- `coap://127.0.0.1:5683/echo` — GET and POST

In a separate Terminal, run the CoAP round-trip benchmark:

```bash
source .venv/bin/activate
python -m coap.benchmark --count 50 --size 64
```

Repeat at the same message sizes used for MQTT:

```bash
python -m coap.benchmark --count 50 --size 16
python -m coap.benchmark --count 50 --size 256
python -m coap.benchmark --count 50 --size 1024
```

## 6. Try CoAP resource methods

With the CoAP server running, open another Terminal:

```bash
# Read current resource state
python -m coap.client GET

# Update the resource (example data are synthetic test values)
python -m coap.client POST --data '{"device_id":"coap-device-01","data_origin":"SYNTHETIC_TEST_DATA","temperature_c":26.2,"humidity_percent":48.0}'

# Replace resource state
python -m coap.client PUT --data '{"device_id":"coap-device-01","data_origin":"SYNTHETIC_TEST_DATA","temperature_c":27.0,"humidity_percent":46.5}'

# Read it again
python -m coap.client GET

# Reset the resource
python -m coap.client DELETE
```

## 7. Optional: publish MQTT virtual-device telemetry

Start the subscriber in one Terminal:

```bash
python -m mqtt.subscriber
```

In another Terminal, publish ten synthetic readings:

```bash
python -m mqtt.device --device-id room-01 --count 10 --interval 1 --qos 1
```

The messages are real MQTT publications, but the sensor values are generated for testing and carry `data_origin: SYNTHETIC_TEST_DATA`. Received messages are saved to `data/telemetry.jsonl`.

## 8. Open the dashboard

After running one or more benchmarks:

```bash
streamlit run dashboard/app.py
```

Streamlit prints a local URL (normally `http://localhost:8501`). Open it in your browser. Use **Refresh data** after a benchmark completes. You can filter by protocol and experiment, compare delivery and RTT summaries, inspect raw rows, and download the filtered CSV.

## 9. Capture packets with Wireshark

1. Install and open Wireshark.
2. For localhost experiments, select the loopback capture interface (`lo0` on macOS, where available). For a second-computer experiment, select the Wi-Fi interface.
3. Start a capture before running a benchmark.
4. Use these display filters:

```text
mqtt
coap
```

5. For the local testbed, MQTT uses TCP port `1883`; CoAP uses UDP port `5683`.
6. Save the capture as a `.pcapng` file in your lab records.

The CSV records **application message bytes** and measured client-side RTT. It does not claim to be the complete on-wire frame size. Use Wireshark packet details and frame lengths to analyse actual protocol headers and network-layer overhead.

## 10. Optional: test from a second device on the same Wi-Fi

Localhost is the best first check, but it does not measure Wi-Fi transmission. For a LAN experiment, keep the broker and CoAP server on the Mac and run clients on a second computer.

1. Find the Mac's Wi-Fi IP address in **System Settings → Wi-Fi → Details**, or with `ipconfig getifaddr en0`.
2. Edit `docker-compose.yml` and change the MQTT port mapping from:

   ```yaml
   - "127.0.0.1:1883:1883"
   ```

   to:

   ```yaml
   - "1883:1883"
   ```

3. Restart the broker with `docker compose down && docker compose up -d`.
4. Allow inbound TCP `1883` and UDP `5683` through the macOS firewall only on the trusted private network.
5. On the second device, install this project's Python dependencies and run the benchmark clients with `--host <MAC_WIFI_IP>`.

**Security warning:** the included broker is anonymous and has no TLS. It is deliberately bound to localhost by default. Do not expose this development broker to a public network or an untrusted Wi-Fi network. For LAN experiments, use a trusted private network and close the ports when finished. A production deployment needs authentication, access control lists, TLS, and a hardened configuration.

## 11. Understanding the measurements

- **RTT:** elapsed time from the benchmark client's send operation until the echoed response is received. It includes protocol handling and endpoint processing, not just propagation delay.
- **Delivery success:** successful echo exchanges divided by attempted exchanges.
- **Application message size:** byte count logged by the benchmark client. Both MQTT and CoAP benchmark clients use the same compact JSON envelope (`request_id` plus `payload`), so the logged application-message byte counts are comparable for a given payload size.
- **On-wire overhead:** analyse this separately in Wireshark using captured packet/frame lengths and header details.
- **QoS:** MQTT benchmark supports QoS 0, 1 and 2. CoAP benchmark uses the library's default Confirmable request behaviour.

For a fair comparison, run both protocols on the same host/network, use matching payload sizes, repeat each run several times, record the environment, and compare distributions (median and range), not a single measurement. The local echo service introduces endpoint processing time, so describe the result as application-level round-trip time rather than pure network propagation delay.

## Project layout

```text
iot_protocol_testbed/
├── common/                  # Shared paths, MQTT helpers, CSV/JSONL logging
├── mqtt/                    # MQTT echo service, benchmark, publisher, subscriber
├── coap/                    # CoAP resource server, client, benchmark
├── dashboard/               # Streamlit results dashboard
├── experiments/             # Space for later controlled experiment scripts
├── mosquitto/               # Local broker configuration
├── data/                    # Received telemetry JSONL (created at runtime)
├── results/                 # Measured results/metrics.csv (created at runtime)
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Troubleshooting

- **`docker compose` cannot connect:** open Docker Desktop and wait until its engine is running.
- **MQTT connection refused:** check `docker compose ps`, broker logs, and that port `1883` is not occupied by another Mosquitto instance.
- **CoAP address already in use:** stop another process using UDP port `5683`, or choose another port using `python -m coap.server --port 5684` and pass `--port 5684` to the client/benchmark.
- **Missing package:** make sure `.venv` is activated and run `python -m pip install -r requirements.txt`.
- **No dashboard data:** run at least one benchmark; ensure `results/metrics.csv` exists; click **Refresh data**.

## Suggested next experiments

1. Compare MQTT QoS 0/1/2 at fixed payload sizes.
2. Compare MQTT and CoAP with matching payload sizes and repetitions.
3. Repeat from localhost and from a second device over Wi-Fi.
4. Capture packets and compare on-wire overhead.
5. Introduce controlled delay/loss/bandwidth limits in a later network-emulation phase and document the exact tool/configuration used.

Do not claim constrained-hardware power consumption, radio range, or physical sensor accuracy from this software testbed. Those require hardware or a separately validated measurement setup.
