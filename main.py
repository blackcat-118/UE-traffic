import threading
import random
import os
import time
from config_parser import parse_config
from ue_generator import generate_ue_profiles
from simulator import Simulator

import argparse

# === Argument parsing ===
parser = argparse.ArgumentParser(description="")
parser.add_argument("--config_path", type=str, help="Path to the configuration file containing simulation info.")

args = parser.parse_args()

# === Load parsed config ===
cfg = parse_config(path=args.config_path)
ue_profiles = generate_ue_profiles(cfg.profiles, cfg.simulation.ue_arrival_rate, cfg.simulation.duration_sec)

# === Create Simulator instance ===
sim = Simulator(
    ue_profiles = ue_profiles,
    cfg = cfg,
)

# === Run simulation and display ===

runnung_status = sim.run()             # start all UE threads

if runnung_status == False:
    exit(1)  # exit if validation failed

print("[INFO] Simulation started. Waiting for threads to start...")
sim.wait_for_completion()
