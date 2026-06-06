Serial Signal Analyzer
A real-time hardware signal monitoring and anomaly detection system built in Python.
What It Does
This tool simulates an embedded hardware debug workflow:
• Reads real CPU and RAM data from the operating system
• Simulates analog sensor signals (voltage and current) mimicking a UART serial stream
• Detects anomalies in real-time (voltage faults, overcurrent, high CPU/RAM)
• Logs all samples and events to structured files for post-analysis
• Displays a color-coded live dashboard in the terminal
Why I Built This
As an Electrical & Electronics Engineering student, I wanted to build a tool that reflects real embedded systems work — monitoring hardware signals, detecting faults, and logging data — similar to what engineers do when debugging hardware platforms.
Technical Stack
• Language: Python 3
• Libraries: psutil (system metrics), colorama (terminal UI), json, logging
• Concepts: Real-time data acquisition, signal simulation, anomaly detection, structured logging
Signal Parameters
