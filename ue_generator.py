from dataclasses import dataclass
from typing import Literal, List
from enum import Enum
import random
from config_parser import ProfileConfig, Burst  #  importing from config_parser.py
import pandas as pd
import numpy as np

class TrafficClass(Enum):
    HIGH = "high"
    MID = "mid"
    LOW = "low"
    REPLAY = "replay"
    NONE = "none"

@dataclass
class PacketSize:
    distribution: Literal["uniform", "normal", "replay"]
    min: int
    max: int
    series: List[int] = None  # For replay traffic, this will hold the actual packet sizes

@dataclass
class UEProfile:
    id: int
    profile_name: str
    traffic_class: TrafficClass
    packet_arrival_rate: float
    packet_size: PacketSize
    burst: Burst
    start_time: float = 0.0  # Start time for the UE, can be set later
    duration: float = 0.0  # Duration for which the UE is active, can be set later

def generate_service_times(num_users: int, sim_duration: float, tail_prob: float = 0.01):
    """
    Generate exponential service times for 'num_users' users.
    
    Parameters:
        num_users     : int   - Number of users
        sim_duration  : float - Simulation duration (max or near-max service time, in seconds)
        tail_prob     : float - Probability that service time exceeds sim_duration (default 1%)
    
    Returns:
        service_times : np.ndarray - Generated exponential service times
    """
    # Calculate lambda so that P(T > sim_duration) = tail_prob
    lam = -np.log(tail_prob) / sim_duration
    mean_service_time = 1 / lam

    print(f"λ (rate) = {lam:.6f} per second")
    print(f"Mean service time = {mean_service_time:.2f} seconds")
    print(f"≈ {100*(1-tail_prob):.1f}% of service times will be ≤ {sim_duration} seconds.\n")

    # Generate exponential service times
    service_times = np.random.exponential(scale=1/lam, size=num_users)
    return service_times

def generate_arrival_intervals(num_users: int, arrival_lambda: float):
    """
    Generate exponential inter-arrival times for 'num_users' arrivals.
    
    Parameters:
        num_users       : int   - Number of users (arrivals)
        arrival_lambda  : float - Arrival rate (users per second)
    
    Returns:
        inter_arrivals  : np.ndarray - Exponential inter-arrival times
        arrival_times   : np.ndarray - Cumulative arrival times
    """
    inter_arrivals = np.random.exponential(scale=1/arrival_lambda, size=num_users)
    arrival_times = np.cumsum(inter_arrivals)

    print(f"[Arrival Interval]")
    print(f"λ (rate) = {arrival_lambda:.6f} per second")
    print(f"Mean inter-arrival time = {1/arrival_lambda:.2f} seconds\n")

    return arrival_times

def generate_ue_profiles(profiles: List[ProfileConfig], ue_arrival_rate: float = 0.0, sim_duration: int = 600) -> List[UEProfile]:
    ue_profiles = []
    ue_id = 1
    for profile in profiles:
       # switch
        if profile.name == "high_traffic":
            traffic_class = TrafficClass.HIGH
        elif profile.name == "low_traffic":
            traffic_class = TrafficClass.LOW
        elif profile.name == "mid_traffic":
            traffic_class = TrafficClass.MID
        elif profile.name.endswith(".csv"):
            traffic_class = TrafficClass.REPLAY
        else:
            traffic_class = TrafficClass.NONE

        # generate service times for the UEs in this profile
        service_times = generate_service_times(num_users=profile.ue_count, sim_duration=sim_duration)  # assuming 1 hour max duration
        arrival_times = generate_arrival_intervals(num_users=profile.ue_count, arrival_lambda=ue_arrival_rate) if ue_arrival_rate > 0 else np.zeros(profile.ue_count)

        # Create UE profiles based on the profile configuration
        for i in range(profile.ue_count):
            if traffic_class == TrafficClass.REPLAY:
                # For replay traffic, we assume the packet size is a series of sizes from a CSV file
                df = pd.read_csv(profile.name)  # Assuming profile.name is the path to the CSV
                packet_size = PacketSize(
                    distribution="replay",
                    min=0,  # Min and max are not used for replay traffic
                    max=0,
                    series=df['TotalBytes'].values  # This should be a list of sizes from the CSV
                )
            else:
                packet_size = PacketSize(
                    min=profile.packet_size.min,
                    max=profile.packet_size.max,
                    distribution=profile.packet_size.distribution
                )

            ue_profile = UEProfile(
                id=ue_id,
                profile_name=profile.name,
                traffic_class=traffic_class,
                start_time=arrival_times[i],
                duration=service_times[i],
                packet_arrival_rate=profile.packet_arrival_rate,
                packet_size=packet_size,
                burst=profile.burst
            )
            ue_profiles.append(ue_profile)
            ue_id += 1

    # Shuffle the profiles to randomize UE IDs
    random.shuffle(ue_profiles)

    return ue_profiles

if __name__ == "__main__":
    from config_parser import BurstRange
    # Example usage
    profiles = [
        ProfileConfig(name="high_traffic", ue_count=3, packet_arrival_rate=2, 
                      packet_size=PacketSize(min=64, max=128, distribution="uniform"), 
                      burst=Burst(enabled=True, burst_chance=0.5, burst_arrival_rate=1.0, burst_on_duration=BurstRange(min=0.1, max=0.5), burst_off_duration=BurstRange(min=0.2, max=0.6))),
        ProfileConfig(name="mid_traffic", ue_count=1, packet_arrival_rate=0.3, 
                      packet_size=PacketSize(min=256, max=512, distribution="uniform"),
                      burst=Burst(enabled=False)),
        ProfileConfig(name="low_traffic", ue_count=3, packet_arrival_rate=0.1, 
                      packet_size=PacketSize(min=128, max=256, distribution="uniform"), 
                      burst=Burst(enabled=False)),
    ]

    ue_profiles = generate_ue_profiles(profiles)
    for profile in ue_profiles:
        print(profile)