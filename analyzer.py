"""
Serial Signal Analyzer
======================
A real-time system monitor that simulates serial/sensor data streams,
detects anomalies, and logs events - mimicking embedded hardware debug workflows.

Author: Omran Shibli
"""

import psutil
import time
import random
import math
import logging
import os
import json
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)

# ── Logging Setup ─────────────────────────────────────────────────────────────
LOG_FILE = "signal_log.txt"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# ── Constants ─────────────────────────────────────────────────────────────────
SAMPLE_RATE_HZ = 2  # samples per second
ANOMALY_THRESHOLD = 85.0  # % threshold for CPU/RAM alerts
VOLTAGE_MIN = 3.0  # simulated voltage min (V)
VOLTAGE_MAX = 3.6  # simulated voltage max (V)
VOLTAGE_FAULT = 2.8  # fault threshold (V)
BAUD_RATE = 115200  # simulated UART baud rate (display only)

# ── Signal Simulation (mimics UART sensor stream) ────────────────────────────


def simulate_voltage_signal(t):


"""Simulate a noisy voltage signal with occasional faults."""
base = 3.3 + 0.1 * math.sin(2 * math.pi * 0.1 * t)
noise = random.gauss(0, 0.05)
fault = -0.8 if random.random() < 0.05 else 0  # 5% fault injection
return round(base + noise + fault, 3)


def simulate_current_signal(t):


"""Simulate current draw in mA."""
base = 120 + 20 * math.sin(2 * math.pi * 0.05 * t)
noise = random.gauss(0, 5)
return round(max(0, base + noise), 2)

# ── Anomaly Detection ─────────────────────────────────────────────────────────


def check_anomalies(cpu, ram, voltage, current, sample_id):


anomalies = []

if cpu > ANOMALY_THRESHOLD:
anomalies.append(f"HIGH CPU: {cpu}%")
logging.warning(f"Sample {sample_id} | HIGH CPU: {cpu}%")

if ram > ANOMALY_THRESHOLD:
anomalies.append(f"HIGH RAM: {ram}%")
logging.warning(f"Sample {sample_id} | HIGH RAM: {ram}%")

if voltage < VOLTAGE_FAULT:
anomalies.append(f"VOLTAGE FAULT: {voltage}V (below {VOLTAGE_FAULT}V)")
logging.error(f"Sample {sample_id} | VOLTAGE FAULT: {voltage}V")

if current > 160:
anomalies.append(f"OVERCURRENT: {current}mA")
logging.warning(f"Sample {sample_id} | OVERCURRENT: {current}mA")

return anomalies

# ── Display ───────────────────────────────────────────────────────────────────


def print_header():


os.system('cls' if os.name == 'nt' else 'clear')
print(Fore.CYAN + "=" * 65)
print(Fore.CYAN + " SERIAL SIGNAL ANALYZER | Omran Shibli")
print(Fore.CYAN +
      f" Simulated UART @ {BAUD_RATE} baud | Sample Rate: {SAMPLE_RATE_HZ} Hz")
print(Fore.CYAN + "=" * 65)


def color_value(value, warn, danger, unit=""):


if value >= danger:
return Fore.RED + f"{value}{unit}" + Style.RESET_ALL
elif value >= warn:
return Fore.YELLOW + f"{value}{unit}" + Style.RESET_ALL
else:
return Fore.GREEN + f"{value}{unit}" + Style.RESET_ALL


def print_sample(sample_id, ts, cpu, ram, voltage, current, anomalies):


print(f"\n{Fore.WHITE}[#{sample_id:04d}] {ts}")
print(f" CPU Usage : {color_value(cpu, 70, ANOMALY_THRESHOLD, '%')}")
print(f" RAM Usage : {color_value(ram, 70, ANOMALY_THRESHOLD, '%')}")

v_color = Fore.RED if voltage < VOLTAGE_FAULT else (
    Fore.YELLOW if voltage < VOLTAGE_MIN else Fore.GREEN)
print(f" Voltage : {v_color}{voltage}V{Style.RESET_ALL} (nominal: 3.3V)")

i_color = Fore.RED if current > 160 else (
    Fore.YELLOW if current > 140 else Fore.GREEN)
print(f" Current : {i_color}{current}mA{Style.RESET_ALL}")

if anomalies:
print(f"\n {Fore.RED}⚠ ANOMALY DETECTED:{Style.RESET_ALL}")
for a in anomalies:
print(f" {Fore.RED}→ {a}{Style.RESET_ALL}")
logging.error(f"Sample {sample_id} anomalies: {anomalies}")
else:
print(f" {Fore.GREEN}✓ All signals nominal{Style.RESET_ALL}")

print(Fore.CYAN + "-" * 65)

# ── Stats Summary ─────────────────────────────────────────────────────────────


def save_summary(stats):


with open("session_summary.json", "w") as f:
json.dump(stats, f, indent=2)
print(f"\n{Fore.CYAN}Session summary saved to session_summary.json")
print(f"Full log saved to {LOG_FILE}{Style.RESET_ALL}")

# ── Main Loop ─────────────────────────────────────────────────────────────────


def main():


print_header()
print(f"\n{Fore.YELLOW}Starting signal acquisition... Press Ctrl+C to stop.{Style.RESET_ALL}\n")
time.sleep(1)

sample_id = 0
total_anomalies = 0
session_start = datetime.now()
logging.info("=== Session Started ===")

cpu_history = []
voltage_history = []

try:
while True:
sample_id += 1
t = sample_id / SAMPLE_RATE_HZ
ts = datetime.now().strftime("%H:%M:%S.%f")[:-3]

# Read real system data
cpu = psutil.cpu_percent(interval=0)
ram = psutil.virtual_memory().percent

# Simulate hardware sensor signals
voltage = simulate_voltage_signal(t)
current = simulate_current_signal(t)

cpu_history.append(cpu)
voltage_history.append(voltage)

# Log every sample
logging.info(
    f"Sample {sample_id} | CPU={cpu}% RAM={ram}% "
    f"V={voltage}V I={current}mA"
)

# Detect anomalies
anomalies = check_anomalies(cpu, ram, voltage, current, sample_id)
total_anomalies += len(anomalies)

print_sample(sample_id, ts, cpu, ram, voltage, current, anomalies)

time.sleep(1.0 / SAMPLE_RATE_HZ)

except KeyboardInterrupt:
session_end = datetime.now()
duration = (session_end - session_start).seconds

print(f"\n\n{Fore.CYAN}{'='*65}")
print(f" SESSION COMPLETE")
print(f" Duration : {duration}s")
print(f" Total Samples: {sample_id}")
print(f" Anomalies : {total_anomalies}")
if cpu_history:
print(f" Avg CPU : {sum(cpu_history)/len(cpu_history):.1f}%")
if voltage_history:
print(f" Avg Voltage : {sum(voltage_history)/len(voltage_history):.3f}V")
print(f"{'='*65}{Style.RESET_ALL}")

save_summary({
    "duration_seconds": duration,
    "total_samples": sample_id,
    "total_anomalies": total_anomalies,
    "avg_cpu_percent": round(sum(cpu_history)/len(cpu_history), 2) if cpu_history else 0,
    "avg_voltage": round(sum(voltage_history)/len(voltage_history), 3) if voltage_history else 0,
    "session_start": str(session_start),
    "session_end": str(session_end)
})

logging.info(
    f"=== Session Ended | {sample_id} samples | {total_anomalies} anomalies ===")

if __name__ == "__main__":
