from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATHS AND PAGE CONFIGURATION
# ============================================================

ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "results"
LOGS_DIR = ROOT / "logs"
METRICS_FILE = RESULTS_DIR / "metrics.csv"
MOSQUITTO_CONFIG = ROOT / "mosquitto" / "dashboard-local.conf"

RESULTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="IoT Protocol Laboratory",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# HTML RENDERING
# Use st.html instead of Markdown for HTML. This prevents
# indented HTML blocks from being displayed as code.
# ============================================================

def render_html(content: str) -> None:
    st.html(content)


# ============================================================
# PROFESSIONAL LIGHT THEME
# The matching .streamlit/config.toml is included separately.
# CSS below styles Streamlit components consistently on every
# page: alerts, cards, metrics, buttons, inputs, tables, etc.
# ============================================================

st.html("""
<style>
:root {
    color-scheme: light;
}

.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #F3F4F1 !important;
    color: #26343D !important;
}

[data-testid="stHeader"] {
    background: rgba(243, 244, 241, 0.96) !important;
}

.block-container {
    max-width: 1450px !important;
    padding-top: 1.65rem !important;
    padding-bottom: 3rem !important;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #DDE3DF !important;
}

section[data-testid="stSidebar"] > div {
    background: #FFFFFF !important;
}

section[data-testid="stSidebar"] .block-container {
    padding-top: 1.6rem !important;
}

section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: #354650 !important;
}

.brand-name {
    color: #294B59;
    font-size: 18px;
    font-weight: 760;
    letter-spacing: -0.45px;
    line-height: 1.2;
}

.brand-subtitle {
    color: #81908B;
    font-size: 9px;
    font-weight: 750;
    letter-spacing: 1.65px;
    margin-top: 5px;
}

/* Sidebar navigation */
section[data-testid="stSidebar"] div[role="radiogroup"] {
    gap: 5px !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label {
    border-radius: 5px !important;
    padding: 8px 10px !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {
    background: #F0F4F1 !important;
}

section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
    background: #E9F1ED !important;
    border-left: 3px solid #438477 !important;
}

/* Hero */
.hero {
    background: #263D4B;
    border: 1px solid #263D4B;
    border-radius: 7px;
    padding: 29px 33px;
    margin: 0 0 27px 0;
}

.hero-eyebrow {
    color: #B8D1C9;
    font-size: 10px;
    font-weight: 780;
    letter-spacing: 1.8px;
    text-transform: uppercase;
}

.hero-title {
    color: #FFFFFF;
    font-size: 34px;
    font-weight: 720;
    line-height: 1.15;
    letter-spacing: -0.8px;
    margin: 12px 0 8px;
}

.hero-description {
    color: #D6E0E3;
    font-size: 14px;
    line-height: 1.6;
    margin: 0;
    max-width: 900px;
}

/* Typography */
h1, h2, h3, h4 {
    color: #26343D !important;
    letter-spacing: -0.35px !important;
}

h2 {
    font-size: 25px !important;
    font-weight: 680 !important;
}

h3 {
    font-size: 19px !important;
    font-weight: 650 !important;
}

p, li {
    color: #394852;
}

[data-testid="stCaptionContainer"] p {
    color: #78858D !important;
    font-size: 12px !important;
}

.section-kicker {
    color: #668078;
    text-transform: uppercase;
    font-size: 10px;
    font-weight: 780;
    letter-spacing: 1.55px;
    margin-bottom: 5px;
}

.muted {
    color: #71808A;
    font-size: 13px;
    line-height: 1.55;
}

/* Content cards */
.panel {
    background: #FFFFFF;
    border: 1px solid #DCE2DE;
    border-radius: 7px;
    padding: 18px 19px;
    min-height: 118px;
    box-shadow: 0 1px 2px rgba(25, 40, 35, 0.035);
}

.panel-title {
    color: #294B59;
    font-size: 18px;
    font-weight: 690;
    margin: 7px 0 5px;
}

.panel-copy {
    color: #71808A;
    font-size: 12px;
    line-height: 1.55;
}

.panel-kicker {
    color: #668078;
    font-size: 10px;
    font-weight: 780;
    letter-spacing: 1.3px;
}

.workflow-card {
    background: #FFFFFF;
    border: 1px solid #DCE2DE;
    border-radius: 7px;
    padding: 17px;
    min-height: 145px;
}

.workflow-number {
    color: #438477;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}

.workflow-title {
    color: #263D4B;
    font-size: 16px;
    font-weight: 690;
    margin: 10px 0 7px;
}

.workflow-copy {
    color: #71808A;
    font-size: 12px;
    line-height: 1.55;
}

/* Metric cards - do not use Streamlit delta badges */
div[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #DCE2DE !important;
    border-radius: 7px !important;
    padding: 15px 17px !important;
    box-shadow: 0 1px 2px rgba(25, 40, 35, 0.035) !important;
}

div[data-testid="stMetricLabel"],
div[data-testid="stMetricLabel"] p {
    color: #71808A !important;
    font-size: 12px !important;
}

div[data-testid="stMetricValue"] {
    color: #294B59 !important;
    font-size: 28px !important;
    font-weight: 690 !important;
}

div[data-testid="stMetricDelta"] {
    background: transparent !important;
    color: #668078 !important;
}

/* Buttons */
div.stButton > button,
div.stDownloadButton > button {
    background: #FFFFFF !important;
    color: #294B59 !important;
    border: 1px solid #C9D5D0 !important;
    border-radius: 5px !important;
    min-height: 41px !important;
    font-weight: 630 !important;
    box-shadow: none !important;
}

div.stButton > button:hover,
div.stDownloadButton > button:hover {
    background: #EAF1EE !important;
    color: #294B59 !important;
    border-color: #438477 !important;
}

div.stButton > button[kind="primary"],
div.stDownloadButton > button[kind="primary"] {
    background: #294B59 !important;
    color: #FFFFFF !important;
    border: 1px solid #294B59 !important;
}

div.stButton > button[kind="primary"]:hover,
div.stDownloadButton > button[kind="primary"]:hover {
    background: #356473 !important;
    border-color: #356473 !important;
    color: #FFFFFF !important;
}

div.stButton > button:disabled {
    background: #EEF1EE !important;
    color: #A1AAA5 !important;
    border-color: #DDE3DF !important;
}

/* Inputs and select controls */
div[data-baseweb="input"] input,
div[data-baseweb="textarea"] textarea {
    background: #FFFFFF !important;
    color: #26343D !important;
    border-color: #CCD5D1 !important;
}

div[data-baseweb="select"] > div {
    background: #FFFFFF !important;
    color: #26343D !important;
    border-color: #CCD5D1 !important;
}

div[data-testid="stNumberInput"] button {
    background: #F2F5F2 !important;
    color: #294B59 !important;
    border-color: #D5DED9 !important;
}

div[data-testid="stSlider"] {
    color: #438477 !important;
}

/* Labels */
.stTextInput label,
.stNumberInput label,
.stSelectbox label,
.stMultiSelect label,
.stSlider label,
.stRadio label,
.stCheckbox label {
    color: #394852 !important;
    font-weight: 560 !important;
}

/* Alerts - explicitly override backgrounds and text */
div[data-testid="stAlert"] {
    background: #EAF1EE !important;
    border: 1px solid #D3E0D9 !important;
    border-left: 4px solid #438477 !important;
    border-radius: 6px !important;
    color: #294B59 !important;
}

div[data-testid="stAlert"] > div {
    background: transparent !important;
}

div[data-testid="stAlert"] p,
div[data-testid="stAlert"] span,
div[data-testid="stAlert"] li {
    color: #294B59 !important;
}

div[data-testid="stAlert"] svg {
    color: #438477 !important;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    background: #FFFFFF !important;
    border: 1px solid #DCE2DE !important;
    border-radius: 6px !important;
    overflow: hidden !important;
}

/* Code blocks - light terminal style, not raw HTML display */
div[data-testid="stCode"] {
    background: #EBEFEC !important;
    border: 1px solid #D8E0DB !important;
    border-radius: 6px !important;
}

div[data-testid="stCode"] pre,
div[data-testid="stCode"] code {
    background: #EBEFEC !important;
    color: #26343D !important;
}

/* Expanders */
div[data-testid="stExpander"] {
    background: #FFFFFF !important;
    border: 1px solid #DCE2DE !important;
    border-radius: 6px !important;
}

div[data-testid="stExpander"] summary {
    color: #294B59 !important;
    font-weight: 620 !important;
}

/* Links */
a {
    color: #36786D !important;
}

/* Dividers */
hr {
    border-color: #DCE2DE !important;
}

/* Footer */
.app-footer {
    border-top: 1px solid #DCE2DE;
    padding-top: 17px;
    margin-top: 35px;
    color: #81908B;
    font-size: 10px;
    letter-spacing: 0.45px;
    line-height: 1.7;
}

/* Responsive spacing */
@media (max-width: 800px) {
    .block-container {
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    .hero {
        padding: 22px;
    }
    .hero-title {
        font-size: 27px;
    }
}
</style>
""")


# ============================================================
# SHARED HELPERS
# ============================================================

def tcp_port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.4):
            return True
    except OSError:
        return False


def udp_port_in_use(port: int) -> bool:
    """Best-effort macOS/Linux check for a CoAP UDP listener."""
    try:
        result = subprocess.run(
            ["lsof", "-nP", f"-iUDP:{port}"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return bool(result.stdout.strip().splitlines()[1:])
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def service_running(key: str) -> bool:
    proc = st.session_state.get(key)
    return proc is not None and proc.poll() is None


def start_python_service(key: str, module: str) -> tuple[bool, str]:
    if service_running(key):
        return True, "This service is already running."

    log_path = LOGS_DIR / f"{key}.log"

    try:
        with log_path.open("a", encoding="utf-8") as log:
            proc = subprocess.Popen(
                [sys.executable, "-m", module],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                env=os.environ.copy(),
                start_new_session=True,
            )

        st.session_state[key] = proc
        time.sleep(0.7)

        if proc.poll() is not None:
            output = log_path.read_text(
                encoding="utf-8", errors="replace"
            )[-3000:]
            return False, output or "The process exited during startup."

        return True, f"{module} started successfully."

    except Exception as exc:
        return False, str(exc)


def stop_python_service(key: str) -> tuple[bool, str]:
    proc = st.session_state.get(key)

    if proc is None or proc.poll() is not None:
        return False, "No active dashboard-managed process was found."

    try:
        proc.terminate()
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    return True, "Service stopped."


def start_local_mosquitto() -> tuple[bool, str]:
    if tcp_port_open("127.0.0.1", 1883):
        return True, "An MQTT broker is already listening on port 1883."

    try:
        MOSQUITTO_CONFIG.parent.mkdir(exist_ok=True)
        MOSQUITTO_CONFIG.write_text(
            "listener 1883 127.0.0.1\n"
            "allow_anonymous true\n"
            "persistence false\n"
            "log_dest stdout\n",
            encoding="utf-8",
        )

        log_path = LOGS_DIR / "mosquitto.log"

        with log_path.open("a", encoding="utf-8") as log:
            proc = subprocess.Popen(
                [
                    "mosquitto",
                    "-c",
                    str(MOSQUITTO_CONFIG),
                    "-v",
                ],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,
            )

        st.session_state["mosquitto"] = proc
        time.sleep(0.8)

        if tcp_port_open("127.0.0.1", 1883):
            return True, "Mosquitto started successfully."

        return False, "Mosquitto did not open port 1883. Check its log."

    except Exception as exc:
        return False, str(exc)


def stop_local_mosquitto() -> tuple[bool, str]:
    proc = st.session_state.get("mosquitto")

    if proc is None or proc.poll() is not None:
        return False, "No dashboard-managed broker is running."

    proc.terminate()

    try:
        proc.wait(timeout=3)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()

    return True, "Dashboard-managed Mosquitto stopped."


def execute_benchmark(label: str, command: list[str]) -> tuple[int, str]:
    with st.spinner(f"Running {label}..."):
        try:
            result = subprocess.run(
                command,
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=240,
                env=os.environ.copy(),
            )

            output = (result.stdout or "") + (result.stderr or "")
            output = output.strip() or "Command completed without console output."

            st.session_state["last_run_label"] = label
            st.session_state["last_run_output"] = output[-14000:]

            return result.returncode, output

        except subprocess.TimeoutExpired:
            message = (
                "Experiment timed out. Check whether the required "
                "MQTT or CoAP service is running."
            )
            st.session_state["last_run_label"] = label
            st.session_state["last_run_output"] = message
            return 124, message

        except Exception as exc:
            st.session_state["last_run_label"] = label
            st.session_state["last_run_output"] = str(exc)
            return 1, str(exc)


def read_metrics() -> pd.DataFrame:
    if not METRICS_FILE.exists() or METRICS_FILE.stat().st_size == 0:
        return pd.DataFrame()

    try:
        frame = pd.read_csv(METRICS_FILE)

        if "rtt_ms" in frame.columns:
            frame["rtt_ms"] = pd.to_numeric(
                frame["rtt_ms"], errors="coerce"
            )

        if "message_size_bytes" in frame.columns:
            frame["message_size_bytes"] = pd.to_numeric(
                frame["message_size_bytes"], errors="coerce"
            )

        if "success" in frame.columns:
            frame["success"] = (
                frame["success"]
                .astype(str)
                .str.lower()
                .isin(["true", "1", "yes"])
            )

        if "timestamp_utc" in frame.columns:
            frame["timestamp_utc"] = pd.to_datetime(
                frame["timestamp_utc"],
                errors="coerce",
                utc=True,
            )

        return frame

    except (pd.errors.ParserError, OSError, ValueError):
        return pd.DataFrame()


def page_title(title: str, description: str) -> None:
    st.markdown(
        f'<div class="section-kicker">NETWORK LAB / {title.upper()}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f"## {title}")
    st.caption(description)


def status_card(title: str, value: str, detail: str) -> None:
    render_html(f"""
    <div class="panel">
        <div class="panel-kicker">{title}</div>
        <div class="panel-title">{value}</div>
        <div class="panel-copy">{detail}</div>
    </div>
    """)


# ============================================================
# SIDEBAR NAVIGATION
# ============================================================

with st.sidebar:
    render_html("""
    <div class="brand-name">📡 IoT PROTOCOL LAB</div>
    <div class="brand-subtitle">NETWORK ENGINEERING</div>
    """)

    st.divider()
    st.markdown("##### WORKSPACE")

    selected_page = st.radio(
        "Navigation",
        [
            "Overview",
            "Run Experiments",
            "Results & Analysis",
            "Project Guide",
            "Service Manager",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    st.markdown("##### LOCAL SERVICE STATUS")

    broker_online = tcp_port_open("127.0.0.1", 1883)
    echo_online = service_running("mqtt_echo")
    coap_online = service_running("coap_server") or udp_port_in_use(5683)

    st.markdown(
        f"{'🟢' if broker_online else '⚪'} MQTT broker · TCP 1883"
    )
    st.markdown(
        f"{'🟢' if echo_online else '⚪'} MQTT echo service"
    )
    st.markdown(
        f"{'🟢' if coap_online else '⚪'} CoAP server · UDP 5683"
    )

    st.divider()
    st.caption("UNIT 2 · LIGHTWEIGHT IoT PROTOCOLS")
    st.caption("Local development environment")


# ============================================================
# MAIN APPLICATION HEADER
# ============================================================

render_html("""
<div class="hero">
    <div class="hero-eyebrow">
        NETWORKING LAB / UNIT 2 / COMMUNICATION PROTOCOLS
    </div>
    <div class="hero-title">IoT Protocol Testbed</div>
    <p class="hero-description">
        Implementation and performance analysis of lightweight MQTT
        and CoAP communication protocols for constrained Internet
        of Things networks.
    </p>
</div>
""")


# ============================================================
# PAGE 1 — OVERVIEW
# ============================================================

if selected_page == "Overview":
    page_title(
        "Overview",
        "Monitor your local testbed and access the experiment workflow.",
    )

    broker_online = tcp_port_open("127.0.0.1", 1883)
    echo_online = service_running("mqtt_echo")
    coap_online = service_running("coap_server") or udp_port_in_use(5683)

    col_a, col_b, col_c = st.columns(3)

    with col_a:
        status_card(
            "MQTT BROKER",
            "Online" if broker_online else "Offline",
            "TCP · Port 1883",
        )

    with col_b:
        status_card(
            "MQTT ECHO SERVICE",
            "Running" if echo_online else "Stopped",
            "Request and response handler",
        )

    with col_c:
        status_card(
            "CoAP SERVER",
            "Running" if coap_online else "Stopped",
            "UDP · Port 5683",
        )

    st.markdown("### Experiment workflow")

    workflow = [
        (
            "01",
            "Start services",
            "Initialize the MQTT broker, MQTT echo responder and CoAP server.",
        ),
        (
            "02",
            "Configure tests",
            "Select QoS, message count and application payload size.",
        ),
        (
            "03",
            "Run experiments",
            "Execute real MQTT and CoAP request/response exchanges.",
        ),
        (
            "04",
            "Analyse results",
            "Compare latency, delivery success and recorded measurements.",
        ),
    ]

    workflow_columns = st.columns(4)

    for column, item in zip(workflow_columns, workflow):
        number, title, description = item
        with column:
            render_html(f"""
            <div class="workflow-card">
                <div class="workflow-number">{number}</div>
                <div class="workflow-title">{title}</div>
                <div class="workflow-copy">{description}</div>
            </div>
            """)

    st.markdown("### Experiment statistics")

    metrics = read_metrics()

    if metrics.empty:
        st.info(
            "No experiment records found. Start the required services "
            "and run your first benchmark."
        )
    else:
        successful = (
            metrics[metrics["success"]]
            if "success" in metrics.columns
            else metrics
        )

        average_rtt = (
            successful["rtt_ms"].mean()
            if "rtt_ms" in successful.columns
            else float("nan")
        )

        stat_a, stat_b, stat_c = st.columns(3)

        stat_a.metric("Recorded exchanges", f"{len(metrics):,}")
        stat_b.metric("Successful exchanges", f"{len(successful):,}")
        stat_c.metric(
            "Mean RTT",
            "—" if pd.isna(average_rtt) else f"{average_rtt:.3f} ms",
        )

        st.markdown("#### Recent measurements")
        st.dataframe(
            metrics.tail(10),
            use_container_width=True,
            hide_index=True,
        )

    st.info(
        "Recommended method: compare MQTT QoS 0, 1 and 2 using the same "
        "message count and payload size. Then run CoAP using equivalent "
        "application payload conditions."
    )


# ============================================================
# PAGE 2 — RUN EXPERIMENTS
# ============================================================

elif selected_page == "Run Experiments":
    page_title(
        "Run Experiments",
        "Configure protocol parameters and execute controlled benchmarks.",
    )

    mqtt_column, coap_column = st.columns(2, gap="large")

    # MQTT controls
    with mqtt_column:
        render_html("""
        <div class="panel">
            <div class="panel-kicker">PROTOCOL A</div>
            <div class="panel-title">MQTT</div>
            <div class="panel-copy">
                Publish/subscribe communication through a broker.
            </div>
        </div>
        """)

        st.markdown("#### MQTT configuration")

        qos = st.select_slider(
            "Quality of Service",
            options=[0, 1, 2],
            value=1,
            key="mqtt_qos",
        )

        qos_text = {
            0: "QoS 0 · At most once",
            1: "QoS 1 · At least once",
            2: "QoS 2 · Exactly once",
        }
        st.caption(qos_text[qos])

        mqtt_count = st.number_input(
            "Number of MQTT messages",
            min_value=1,
            max_value=5000,
            value=30,
            step=10,
            key="mqtt_count",
        )

        mqtt_size = st.number_input(
            "MQTT application payload (bytes)",
            min_value=0,
            max_value=4096,
            value=64,
            step=16,
            key="mqtt_size",
        )

        mqtt_timeout = st.number_input(
            "MQTT response timeout (seconds)",
            min_value=0.2,
            max_value=30.0,
            value=3.0,
            step=0.2,
            key="mqtt_timeout",
        )

        mqtt_ready = (
            tcp_port_open("127.0.0.1", 1883)
            and service_running("mqtt_echo")
        )

        if st.button(
            "Run MQTT Benchmark",
            type="primary",
            use_container_width=True,
        ):
            if not tcp_port_open("127.0.0.1", 1883):
                st.error("MQTT broker is offline. Start it in Service Manager.")
            elif not service_running("mqtt_echo"):
                st.error(
                    "MQTT echo service is not running. "
                    "Start it in Service Manager."
                )
            else:
                command = [
                    sys.executable,
                    "-m",
                    "mqtt.benchmark",
                    "--count",
                    str(mqtt_count),
                    "--size",
                    str(mqtt_size),
                    "--qos",
                    str(qos),
                    "--timeout",
                    str(mqtt_timeout),
                ]

                result_code, _ = execute_benchmark(
                    "MQTT benchmark", command
                )

                if result_code == 0:
                    st.success("MQTT benchmark completed successfully.")
                else:
                    st.error("MQTT benchmark failed. Review the output below.")

        st.caption(
            "Readiness: "
            + (
                "🟢 Broker and echo service ready"
                if mqtt_ready
                else "⚪ Start the required services"
            )
        )

    # CoAP controls
    with coap_column:
        render_html("""
        <div class="panel">
            <div class="panel-kicker">PROTOCOL B</div>
            <div class="panel-title">CoAP</div>
            <div class="panel-copy">
                Confirmable request/response communication over UDP.
            </div>
        </div>
        """)

        st.markdown("#### CoAP configuration")

        coap_count = st.number_input(
            "Number of CoAP messages",
            min_value=1,
            max_value=5000,
            value=30,
            step=10,
            key="coap_count",
        )

        coap_size = st.number_input(
            "CoAP application payload (bytes)",
            min_value=0,
            max_value=4096,
            value=64,
            step=16,
            key="coap_size",
        )

        coap_timeout = st.number_input(
            "CoAP response timeout (seconds)",
            min_value=0.2,
            max_value=30.0,
            value=3.0,
            step=0.2,
            key="coap_timeout",
        )

        coap_ready = service_running("coap_server") or udp_port_in_use(5683)

        if st.button(
            "Run CoAP Benchmark",
            type="primary",
            use_container_width=True,
        ):
            if not coap_ready:
                st.error("CoAP server is offline. Start it in Service Manager.")
            else:
                command = [
                    sys.executable,
                    "-m",
                    "coap.benchmark",
                    "--count",
                    str(coap_count),
                    "--size",
                    str(coap_size),
                    "--timeout",
                    str(coap_timeout),
                ]

                result_code, _ = execute_benchmark(
                    "CoAP benchmark", command
                )

                if result_code == 0:
                    st.success("CoAP benchmark completed successfully.")
                else:
                    st.error("CoAP benchmark failed. Review the output below.")

        st.caption(
            "Readiness: "
            + (
                "🟢 CoAP server detected"
                if coap_ready
                else "⚪ Start the CoAP server"
            )
        )

    st.divider()
    st.markdown("### Latest benchmark output")

    if st.session_state.get("last_run_output"):
        st.caption(st.session_state.get("last_run_label", "Last experiment"))
        st.code(
            st.session_state["last_run_output"],
            language="text",
        )
    else:
        st.info("The benchmark summary will appear here after your first run.")

    st.caption(
        "Localhost RTT measures a local client-to-service round trip. "
        "It is not a measurement of Wi-Fi or Internet latency."
    )


# ============================================================
# PAGE 3 — RESULTS AND ANALYSIS
# ============================================================

elif selected_page == "Results & Analysis":
    page_title(
        "Results & Analysis",
        "Review recorded measurements, compare protocol performance and export data.",
    )

    metrics = read_metrics()

    if metrics.empty:
        st.info(
            "No measurements are available yet. Run an MQTT or CoAP "
            "benchmark to populate this section."
        )
    else:
        protocols = sorted(
            metrics["protocol"].dropna().unique().tolist()
        ) if "protocol" in metrics.columns else []

        if not protocols:
            st.warning("No protocol labels were found in the metrics file.")
        else:
            selected_protocols = st.multiselect(
                "Protocols to include",
                protocols,
                default=protocols,
            )

            view = metrics[
                metrics["protocol"].isin(selected_protocols)
            ].copy()

            if view.empty:
                st.info("No records match the selected protocols.")
            else:
                valid = (
                    view[view["success"]]
                    if "success" in view.columns
                    else view
                )

                total = len(view)
                delivered = (
                    int(view["success"].sum())
                    if "success" in view.columns
                    else 0
                )

                success_rate = delivered / total * 100 if total else 0

                average_rtt = (
                    valid["rtt_ms"].mean()
                    if "rtt_ms" in valid.columns
                    else float("nan")
                )

                median_rtt = (
                    valid["rtt_ms"].median()
                    if "rtt_ms" in valid.columns
                    else float("nan")
                )

                metric_a, metric_b, metric_c, metric_d = st.columns(4)

                metric_a.metric("Total exchanges", f"{total:,}")
                metric_b.metric("Delivery success", f"{success_rate:.1f}%")
                metric_c.metric(
                    "Mean RTT",
                    "—" if pd.isna(average_rtt)
                    else f"{average_rtt:.3f} ms",
                )
                metric_d.metric(
                    "Median RTT",
                    "—" if pd.isna(median_rtt)
                    else f"{median_rtt:.3f} ms",
                )

                if not valid.empty and "rtt_ms" in valid.columns:
                    st.markdown("### Average RTT by protocol")

                    averages = (
                        valid.groupby("protocol")["rtt_ms"]
                        .mean()
                        .sort_values()
                    )

                    st.bar_chart(averages)

                    if (
                        "timestamp_utc" in valid.columns
                        and valid["timestamp_utc"].notna().any()
                    ):
                        st.markdown("### RTT across recorded exchanges")

                        chart_frame = (
                            valid.dropna(subset=["timestamp_utc"])
                            .sort_values("timestamp_utc")
                        )

                        st.line_chart(
                            chart_frame,
                            x="timestamp_utc",
                            y="rtt_ms",
                            color="protocol",
                        )

                st.markdown("### Measurement records")

                st.dataframe(
                    view,
                    use_container_width=True,
                    hide_index=True,
                )

                st.download_button(
                    "Download selected measurements",
                    data=view.to_csv(index=False).encode("utf-8"),
                    file_name="iot_protocol_measurements.csv",
                    mime="text/csv",
                    type="primary",
                )

                st.caption(
                    "For a fair comparison, use matching payload sizes, "
                    "exchange counts and network conditions."
                )


# ============================================================
# PAGE 4 — PROJECT GUIDE
# ============================================================

elif selected_page == "Project Guide":
    page_title(
        "Project Guide",
        "How the testbed works, how to perform experiments and how to interpret results.",
    )

    with st.expander("01 · Project overview", expanded=True):
        st.markdown("""
        This project implements two lightweight IoT communication protocols.

        **MQTT — Message Queuing Telemetry Transport**

        MQTT uses a publish/subscribe model. Clients exchange messages
        through a broker.

        **CoAP — Constrained Application Protocol**

        CoAP provides request/response communication designed for
        constrained devices and networks, typically over UDP.

        The testbed measures real protocol exchanges. Virtual sensor
        readings, where used, are synthetic application test inputs.
        """)

    with st.expander("02 · MQTT communication flow"):
        st.markdown("""
        1. The benchmark client publishes a uniquely identified request.
        2. The Mosquitto broker receives the publication.
        3. The MQTT echo service receives the request through its subscription.
        4. The echo service publishes a matching response.
        5. The benchmark client receives the response.
        6. The client records elapsed round-trip time and delivery status.

        **MQTT broker:** TCP port 1883 on localhost.
        """)

    with st.expander("03 · MQTT QoS levels"):
        st.markdown("""
        | QoS | Guarantee | Meaning |
        |---|---|---|
        | 0 | At most once | No delivery acknowledgement |
        | 1 | At least once | Acknowledgement; duplicates are possible |
        | 2 | Exactly once | Additional handshake for exactly-once delivery |

        Run each level separately while keeping payload size and message
        count constant.
        """)

    with st.expander("04 · CoAP communication flow"):
        st.markdown("""
        1. The CoAP client creates a request.
        2. It sends a Confirmable POST request to `/echo`.
        3. The CoAP server receives the request over UDP.
        4. The server returns the same payload.
        5. The client checks the response and records the round-trip time.

        **CoAP server:** UDP port 5683 on localhost.
        """)

    with st.expander("05 · Running the experiments"):
        st.markdown("""
        **MQTT**

        1. Open Service Manager.
        2. Ensure the broker is online.
        3. Start the MQTT echo service.
        4. Open Run Experiments.
        5. Select QoS, message count and payload size.
        6. Run the benchmark and inspect its output.

        **CoAP**

        1. Open Service Manager.
        2. Start the CoAP server.
        3. Open Run Experiments.
        4. Choose message count and payload size.
        5. Run the benchmark and inspect its output.
        """)

    with st.expander("06 · Understanding the measurements"):
        st.markdown("""
        **Round-trip time (RTT):** time between sending a request and
        receiving its matching response.

        **Delivery success:** successful responses divided by attempted
        exchanges.

        **Payload size:** application data size. It is not the complete
        on-the-wire packet size.

        **Packet overhead:** protocol headers and other network information.
        Use Wireshark to inspect actual packets and frames.

        **Mean and median RTT:** describe the centre of the measured
        latency distribution. Repeated experiments help reduce the
        influence of one-off scheduling effects.
        """)

    with st.expander("07 · Fair comparison methodology"):
        st.markdown("""
        - Use the same application payload size.
        - Use the same number of exchanges.
        - Repeat each experiment multiple times.
        - Run MQTT QoS 0, 1 and 2 as separate experiments.
        - Record delivery success, mean RTT and median RTT.
        - Document whether tests use localhost or a second device over Wi-Fi.
        """)

    with st.expander("08 · Project files and output"):
        st.markdown("""
        | Folder | Purpose |
        |---|---|
        | `mqtt/` | MQTT benchmark, publisher and echo responder |
        | `coap/` | CoAP client, server and benchmark |
        | `common/` | Shared paths and measurement logging |
        | `dashboard/` | Streamlit application |
        | `results/` | Recorded experiment CSV |
        | `logs/` | Service logs |
        | `mosquitto/` | Local broker configuration |

        Measurement records are appended to:

        `results/metrics.csv`
        """)

    with st.expander("09 · Limitations and future work"):
        st.markdown("""
        **Current limitations**

        - Localhost tests measure local software/protocol round trips,
          not Wi-Fi or Internet latency.
        - Virtual sensor values are not physical sensor readings.
        - RTT is not a measurement of radio energy consumption.
        - Application payload size is not full packet/frame size.

        **Future improvements**

        - Run clients on a second computer over the same Wi-Fi network.
        - Capture MQTT and CoAP packets using Wireshark.
        - Compare packet overhead and retransmission behaviour.
        - Test multiple payload sizes and network conditions.
        - Repeat trials and report statistical summaries.
        """)

    st.warning(
        "The network protocols are real implementations. Synthetic sensor "
        "values are only test inputs; localhost measurements do not establish "
        "physical-device power consumption or Wi-Fi performance."
    )


# ============================================================
# PAGE 5 — SERVICE MANAGER
# ============================================================

elif selected_page == "Service Manager":
    page_title(
        "Service Manager",
        "Start, stop and inspect the local services required by the testbed.",
    )

    broker_online = tcp_port_open("127.0.0.1", 1883)
    echo_online = service_running("mqtt_echo")
    coap_managed = service_running("coap_server")
    coap_detected = coap_managed or udp_port_in_use(5683)

    col_a, col_b, col_c = st.columns(3)

    col_a.metric(
        "MQTT Broker",
        "Online" if broker_online else "Offline",
        "TCP · 1883",
    )

    col_b.metric(
        "MQTT Echo",
        "Running" if echo_online else "Stopped",
    )

    col_c.metric(
        "CoAP Server",
        "Running" if coap_detected else "Stopped",
        "UDP · 5683",
    )

    st.divider()
    st.markdown("### 01 · MQTT broker")

    st.write(
        "The Mosquitto broker distributes MQTT publications to subscribed "
        "clients. If it is already running through Homebrew, the dashboard "
        "will detect it and will not start a duplicate broker."
    )

    broker_col_a, broker_col_b = st.columns(2)

    with broker_col_a:
        if st.button(
            "Start local Mosquitto",
            type="primary",
            use_container_width=True,
            disabled=broker_online,
        ):
            ok, message = start_local_mosquitto()
            (st.success if ok else st.error)(message)
            st.rerun()

    with broker_col_b:
        managed_broker = st.session_state.get("mosquitto")
        can_stop_broker = (
            managed_broker is not None
            and managed_broker.poll() is None
        )

        if st.button(
            "Stop dashboard-managed broker",
            use_container_width=True,
            disabled=not can_stop_broker,
        ):
            ok, message = stop_local_mosquitto()
            (st.success if ok else st.warning)(message)
            st.rerun()

    st.divider()
    st.markdown("### 02 · MQTT echo service")

    st.write(
        "The echo responder subscribes to the benchmark request topic "
        "and publishes a matching response."
    )

    echo_col_a, echo_col_b = st.columns(2)

    with echo_col_a:
        if st.button(
            "Start MQTT echo service",
            type="primary",
            use_container_width=True,
            disabled=echo_online or not broker_online,
        ):
            ok, message = start_python_service(
                "mqtt_echo", "mqtt.echo_service"
            )
            (st.success if ok else st.error)(message)
            st.rerun()

    with echo_col_b:
        if st.button(
            "Stop MQTT echo service",
            use_container_width=True,
            disabled=not echo_online,
        ):
            ok, message = stop_python_service("mqtt_echo")
            (st.success if ok else st.warning)(message)
            st.rerun()

    if not broker_online:
        st.caption("Start the MQTT broker before starting the echo service.")

    st.divider()
    st.markdown("### 03 · CoAP server")

    st.write(
        "The CoAP server hosts the `/sensor` and `/echo` resources "
        "and responds to CoAP client requests."
    )

    coap_col_a, coap_col_b = st.columns(2)

    with coap_col_a:
        if st.button(
            "Start CoAP server",
            type="primary",
            use_container_width=True,
            disabled=coap_detected,
        ):
            ok, message = start_python_service(
                "coap_server", "coap.server"
            )
            (st.success if ok else st.error)(message)
            st.rerun()

    with coap_col_b:
        if st.button(
            "Stop dashboard-managed CoAP server",
            use_container_width=True,
            disabled=not coap_managed,
        ):
            ok, message = stop_python_service("coap_server")
            (st.success if ok else st.warning)(message)
            st.rerun()

    st.caption(
        "The dashboard can stop only the CoAP process it started. "
        "An externally started server must be stopped from its original terminal."
    )

    st.divider()
    st.markdown("### Service logs")

    selected_log = st.selectbox(
        "Select a log file",
        [
            "mqtt_echo.log",
            "coap_server.log",
            "mosquitto.log",
        ],
    )

    log_path = LOGS_DIR / selected_log

    if log_path.exists():
        log_content = log_path.read_text(
            encoding="utf-8", errors="replace"
        )
        st.code(
            log_content[-10000:] or "Log file is empty.",
            language="text",
        )
    else:
        st.info("No log file has been created for this service yet.")


# ============================================================
# APPLICATION FOOTER
# ============================================================

render_html("""
<div class="app-footer">
    <strong>IoT PROTOCOL TESTBED</strong>
    &nbsp; · &nbsp; NETWORK ENGINEERING LABORATORY
    &nbsp; · &nbsp; MQTT / CoAP
    <br>
    Local development environment
    &nbsp; · &nbsp; Real protocol implementations
    &nbsp; · &nbsp; Experimental measurements
</div>
""")
