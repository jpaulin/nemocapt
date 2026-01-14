#!/usr/bin/env python3
"""
Standalone iptraf-style network monitor for Windows 11
Requirements: pip install textual rich psutil
"""

# © 2026 Alan Vaihto – Kaikki oikeudet vaihdettu, paitsi huumori!

# Before running with "python", install libraries:
#  pip install psutil textual rich
# Then run:
#  python ./nemocapt.py
#
# Please report bugs in the github! 

import psutil
import time
from collections import deque

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer, Static
from textual.reactive import reactive
from rich.text import Text
from rich.panel import Panel
from rich.console import Group

# -------------------------------
# Traffic sampler
# -------------------------------

class TrafficSampler:
    def __init__(self):
        self.prev = psutil.net_io_counters()
        self.prev_time = time.time()

    def sample(self):
        now = time.time()
        cur = psutil.net_io_counters()
        dt = now - self.prev_time
        print("The time slice dt="+str(dt))
        rx = (cur.bytes_recv - self.prev.bytes_recv) / dt
        tx = (cur.bytes_sent - self.prev.bytes_sent) / dt
        self.prev = cur
        self.prev_time = now
        return rx, tx  # bytes/sec

# -------------------------------
# Traffic state buffer
# -------------------------------

class TrafficState:
    def __init__(self, size=60):
        self.rx = deque(maxlen=size)
        self.tx = deque(maxlen=size)

    def push(self, rx, tx):
        self.rx.append(rx)
        self.tx.append(tx)

# -------------------------------
# ASCII graph helpers
# -------------------------------

def fmt_mbps(v):
    return f"{v * 8 / 1_000_000:6.2f} Mbps"

def traffic_panel(rx_data, tx_data):
    max_len = 30
    rx_len = int((len(rx_data) / max_len) * max_len) if rx_data else 0
    tx_len = int((len(tx_data) / max_len) * max_len) if tx_data else 0

    rx_bar = Text("RX ") + Text("█" * rx_len, style="green")
    tx_bar = Text("TX ") + Text("█" * tx_len, style="red")

    return Panel(
        Group(
            Text("Live Traffic", style="bold cyan"),
            rx_bar,
            tx_bar,
            Text(f"RX: {fmt_mbps(rx_data[-1]) if rx_data else '0'}"),
            Text(f"TX: {fmt_mbps(tx_data[-1]) if tx_data else '0'}"),
        ),
        title="Network",
        border_style="cyan"
    )

# -------------------------------
# UI view widget
# -------------------------------

class TrafficView(Static):
    rx = reactive([])
    tx = reactive([])

    def render(self):
        return traffic_panel(self.rx, self.tx)

# -------------------------------
# Main App
# -------------------------------

class NetMonApp(App):
    CSS = """
    Screen {
        background: black;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Horizontal():
            with Vertical(id="sidebar"):
                yield Static("Interfaces\n──────────\nEthernet\nWi-Fi\nLoopback", expand=True)
            with Vertical(id="main"):
                self.view = TrafficView()
                yield self.view
        yield Footer()

    def on_mount(self):
        self.sampler = TrafficSampler()
        self.state = TrafficState()
        self.set_interval(1.0, self.update_traffic)

    def update_traffic(self):
        rx, tx = self.sampler.sample()
        self.state.push(rx, tx)
        self.view.rx = list(self.state.rx)
        self.view.tx = list(self.state.tx)

# -------------------------------
# Entry point
# -------------------------------

if __name__ == "__main__":
    NetMonApp().run()
