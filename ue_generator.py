from dataclasses import dataclass
from typing import Literal, List
from enum import Enum
import random
from config_parser import ProfileConfig, Burst  #  importing from config_parser.py
import pandas as pd

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

def generate_ue_profiles(profiles: List[ProfileConfig]) -> List[UEProfile]:
    ue_profiles = []
    ue_id = 0
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