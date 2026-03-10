import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date, timedelta
from config.manager import ConfigManager
from engines.simulation.loop import SimulationLoop
from engines.system.telemetry import monitor

def run_audit(config_path: str, ticker: str, start_str: str, end_str: str):
    print(f"--- Aegis Quality Audit: {ticker} ---")
    config = ConfigManager.load(config_path)
    # Ensure only one ticker for the audit to keep it focused
    config.asset_universe.tickers = [ticker]
    
    start_dt = date.fromisoformat(start_str)
    end_dt = date.fromisoformat(end_str)
    
    loop = SimulationLoop(config)
    print(f"Running backtest from {start_dt} to {end_dt}...")
    loop.run(start_dt, end_dt)
    
    print("\n" + monitor.get_summary())
    
    # Generate Analytics
    generate_charts(monitor.events)

def generate_charts(events):
    if not events:
        return
    
    df = pd.DataFrame(events)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Chart 1: Latency over time
    plt.figure(figsize=(12, 6))
    for node in df['node'].unique():
        node_df = df[df['node'] == node]
        plt.plot(node_df['date'], node_df['duration_sec'], marker='o', label=node)
    
    plt.title("Pipeline Node Latency (Seconds)")
    plt.xlabel("Backtest Date")
    plt.ylabel("Execution Time (s)")
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    chart_path = "debug/telemetry/latency_chart.png"
    plt.savefig(chart_path)
    print(f"Latency chart saved to {chart_path}")
    
    # Chart 2: Pipeline Bottlenecks (Avg Time per Node)
    plt.figure(figsize=(10, 6))
    avg_latency = df.groupby('node')['duration_sec'].mean().sort_values(ascending=False)
    avg_latency.plot(kind='bar', color='skyblue')
    plt.title("Average Latency per Pipeline Node")
    plt.ylabel("Time (s)")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    bottleneck_path = "debug/telemetry/bottleneck_chart.png"
    plt.savefig(bottleneck_path)
    print(f"Bottleneck chart saved to {bottleneck_path}")

if __name__ == "__main__":
    # Default to 1-month run for AAPL
    run_audit(
        config_path="config/templates/tech_breakout_v1.json",
        ticker="AAPL",
        start_str="2023-11-20",
        end_str="2023-12-01"
    )
