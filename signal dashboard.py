"""
Serial Signal Analyzer - Live Dashboard
========================================
Real-time oscilloscope-style visualization of hardware signals.
Simulates UART sensor stream with live plotting, anomaly detection,
and automatic PDF report generation.

Author: Omran Shibli
"""

import psutil
import time
import random
import math
import logging
import json
import threading
from datetime import datetime
from collections import deque
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
import numpy as np

# ── Constants ─────────────────────────────────────────────────────────────────
SAMPLE_RATE_HZ    = 4
WINDOW_SIZE       = 100
VOLTAGE_NOMINAL   = 3.3
VOLTAGE_FAULT     = 2.8
CURRENT_MAX       = 160.0
CPU_THRESHOLD     = 80.0
RAM_THRESHOLD     = 85.0
LOG_FILE          = "signal_log.txt"

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ── Shared Data Buffers ───────────────────────────────────────────────────────
timestamps   = deque(maxlen=WINDOW_SIZE)
voltage_buf  = deque(maxlen=WINDOW_SIZE)
current_buf  = deque(maxlen=WINDOW_SIZE)
cpu_buf      = deque(maxlen=WINDOW_SIZE)
ram_buf      = deque(maxlen=WINDOW_SIZE)
anomaly_buf  = deque(maxlen=WINDOW_SIZE)

session_data = {
    "samples": [],
    "anomalies": 0,
    "start": str(datetime.now())
}

sample_counter = [0]
running = [True]

# ── Signal Simulation ─────────────────────────────────────────────────────────
def simulate_voltage(t):
    base  = VOLTAGE_NOMINAL + 0.08 * math.sin(2 * math.pi * 0.2 * t)
    noise = random.gauss(0, 0.03)
    fault = -0.7 if random.random() < 0.04 else 0
    return round(base + noise + fault, 4)

def simulate_current(t):
    base  = 115 + 18 * math.sin(2 * math.pi * 0.08 * t)
    noise = random.gauss(0, 4)
    spike = 55 if random.random() < 0.03 else 0
    return round(max(0, base + noise + spike), 2)

# ── Data Acquisition Thread ───────────────────────────────────────────────────
def acquire_data():
    t = 0
    while running[0]:
        sample_counter[0] += 1
        t += 1.0 / SAMPLE_RATE_HZ

        cpu     = psutil.cpu_percent(interval=0)
        ram     = psutil.virtual_memory().percent
        voltage = simulate_voltage(t)
        current = simulate_current(t)
        ts      = datetime.now().strftime("%H:%M:%S.%f")[:-3]

        anomaly = []
        if voltage < VOLTAGE_FAULT:
            anomaly.append("VOLT_FAULT")
        if current > CURRENT_MAX:
            anomaly.append("OVERCURRENT")
        if cpu > CPU_THRESHOLD:
            anomaly.append("HIGH_CPU")
        if ram > RAM_THRESHOLD:
            anomaly.append("HIGH_RAM")

        timestamps.append(t)
        voltage_buf.append(voltage)
        current_buf.append(current)
        cpu_buf.append(cpu)
        ram_buf.append(ram)
        anomaly_buf.append(1 if anomaly else 0)

        log_entry = {
            "t": t, "cpu": cpu, "ram": ram,
            "voltage": voltage, "current": current,
            "anomaly": anomaly
        }
        session_data["samples"].append(log_entry)
        if anomaly:
            session_data["anomalies"] += 1
            logging.warning(f"Sample {sample_counter[0]} | {anomaly}")
        else:
            logging.info(f"Sample {sample_counter[0]} | V={voltage} I={current} CPU={cpu} RAM={ram}")

        time.sleep(1.0 / SAMPLE_RATE_HZ)

# ── Plot Setup ────────────────────────────────────────────────────────────────
fig = plt.figure(figsize=(14, 8), facecolor='#0D1117')
fig.suptitle('SERIAL SIGNAL ANALYZER  |  Omran Shibli',
             color='#58A6FF', fontsize=14, fontweight='bold', y=0.98)

gs = gridspec.GridSpec(3, 2, figure=fig, hspace=0.45, wspace=0.35)

ax_volt  = fig.add_subplot(gs[0, :])
ax_curr  = fig.add_subplot(gs[1, 0])
ax_cpu   = fig.add_subplot(gs[1, 1])
ax_anom  = fig.add_subplot(gs[2, :])

for ax in [ax_volt, ax_curr, ax_cpu, ax_anom]:
    ax.set_facecolor('#161B22')
    ax.tick_params(colors='#8B949E', labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor('#30363D')

line_volt,  = ax_volt.plot([], [], color='#39D353', lw=1.5, label='Voltage (V)')
line_fault, = ax_volt.plot([], [], color='#FF4444', lw=0.8, linestyle='--', alpha=0.6)
ax_volt.axhline(y=VOLTAGE_FAULT, color='#FF6B6B', lw=0.8, linestyle=':', alpha=0.7)
ax_volt.axhline(y=VOLTAGE_NOMINAL, color='#58A6FF', lw=0.6, linestyle=':', alpha=0.5)
ax_volt.set_ylim(2.5, 3.7)
ax_volt.set_title('Voltage Signal  (UART Analog Channel)', color='#58A6FF', fontsize=9, pad=4)
ax_volt.set_ylabel('Volts', color='#8B949E', fontsize=8)
ax_volt.legend(fontsize=7, facecolor='#161B22', labelcolor='#8B949E')

line_curr, = ax_curr.plot([], [], color='#FFA657', lw=1.5)
ax_curr.axhline(y=CURRENT_MAX, color='#FF6B6B', lw=0.8, linestyle=':', alpha=0.7)
ax_curr.set_ylim(50, 200)
ax_curr.set_title('Current Draw (mA)', color='#FFA657', fontsize=9, pad=4)
ax_curr.set_ylabel('mA', color='#8B949E', fontsize=8)

line_cpu, = ax_cpu.plot([], [], color='#D2A8FF', lw=1.5, label='CPU')
line_ram, = ax_cpu.plot([], [], color='#79C0FF', lw=1.5, label='RAM')
ax_cpu.set_ylim(0, 100)
ax_cpu.set_title('OS Metrics (%)', color='#D2A8FF', fontsize=9, pad=4)
ax_cpu.legend(fontsize=7, facecolor='#161B22', labelcolor='#8B949E')

bar_container = ax_anom.bar([], [], color='#FF4444', width=0.05)
ax_anom.set_ylim(0, 1.5)
ax_anom.set_title('Anomaly Events', color='#FF6B6B', fontsize=9, pad=4)
ax_anom.set_yticks([])

status_text = fig.text(0.01, 0.01, '', color='#8B949E', fontsize=8)

# ── Animation Update ──────────────────────────────────────────────────────────
def update(frame):
    if len(timestamps) < 2:
        return

    t_arr  = list(timestamps)
    v_arr  = list(voltage_buf)
    i_arr  = list(current_buf)
    c_arr  = list(cpu_buf)
    r_arr  = list(ram_buf)
    a_arr  = list(anomaly_buf)

    line_volt.set_data(t_arr, v_arr)
    line_curr.set_data(t_arr, i_arr)
    line_cpu.set_data(t_arr, c_arr)
    line_ram.set_data(t_arr, r_arr)

    for ax, arr in [(ax_volt, t_arr), (ax_curr, t_arr), (ax_cpu, t_arr)]:
        ax.set_xlim(max(0, t_arr[-1] - WINDOW_SIZE / SAMPLE_RATE_HZ), t_arr[-1] + 1)

    # Anomaly bars
    ax_anom.cla()
    ax_anom.set_facecolor('#161B22')
    ax_anom.set_title('Anomaly Events', color='#FF6B6B', fontsize=9, pad=4)
    ax_anom.set_ylim(0, 1.5)
    ax_anom.set_yticks([])
    ax_anom.set_xlim(max(0, t_arr[-1] - WINDOW_SIZE / SAMPLE_RATE_HZ), t_arr[-1] + 1)
    for spine in ax_anom.spines.values():
        spine.set_edgecolor('#30363D')
    ax_anom.tick_params(colors='#8B949E', labelsize=8)

    for ti, ai in zip(t_arr, a_arr):
        if ai:
            ax_anom.bar(ti, 1, color='#FF4444', width=0.15, alpha=0.8)

    # Status
    n_anom = session_data["anomalies"]
    last_v = v_arr[-1] if v_arr else 0
    fault_str = "⚠ FAULT" if last_v < VOLTAGE_FAULT else "✓ OK"
    status_text.set_text(
        f"Samples: {sample_counter[0]}  |  Anomalies: {n_anom}  |  "
        f"Last V: {last_v:.3f}V  |  Status: {fault_str}"
    )

    return line_volt, line_curr, line_cpu, line_ram

# ── Save Report ───────────────────────────────────────────────────────────────
def save_report():
    session_data["end"] = str(datetime.now())
    session_data["total_samples"] = sample_counter[0]
    with open("session_summary.json", "w") as f:
        json.dump({
            "start": session_data["start"],
            "end": session_data["end"],
            "total_samples": session_data["total_samples"],
            "total_anomalies": session_data["anomalies"]
        }, f, indent=2)

    fig.savefig("signal_report.png", dpi=150, bbox_inches='tight',
                facecolor='#0D1117')
    print("\nReport saved: signal_report.png + session_summary.json")

def on_close(event):
    running[0] = False
    save_report()

# ── Main ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    thread = threading.Thread(target=acquire_data, daemon=True)
    thread.start()

    fig.canvas.mpl_connect('close_event', on_close)

    ani = FuncAnimation(fig, update, interval=250, cache_frame_data=False)

    print("Signal Analyzer running... Close the window to stop and save report.")
    plt.show()
