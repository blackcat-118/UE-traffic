from dataclasses import dataclass
from typing import List, Literal, Optional
import yaml
from colorama import Fore, Style

@dataclass
class PacketSize:
    distribution: Literal["uniform", "normal"]
    min: int
    max: int

@dataclass
class BurstRange:
    min: float
    max: float

@dataclass
class Burst:
    enabled: bool
    burst_chance: Optional[float] = None
    burst_arrival_rate: Optional[float] = None
    burst_on_duration: Optional[BurstRange] = None
    burst_off_duration: Optional[BurstRange] = None

@dataclass
class ProfileConfig:
    name: str
    ue_count: int
    packet_arrival_rate: float
    packet_size: PacketSize
    burst: Burst

@dataclass
class SimulationConfig:
    record_csv_path: str
    duration_sec: int
    display_interval_sec: int
    ue_arrival_rate: float
    packet_type: str
    target_ips: List[str]

@dataclass
class ParsedConfig:
    simulation: SimulationConfig
    profiles: List[ProfileConfig]


def parse_config(path: str = "config/config.yaml") -> ParsedConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    sim = raw["simulation"]
    simulation = SimulationConfig(
        record_csv_path=sim["record_csv_path"],
        duration_sec=sim["duration_sec"],
        display_interval_sec=sim["display_interval_sec"],
        ue_arrival_rate=sim["poisson_arrival_rate"],
        packet_type=sim["packet_type"],
        target_ips=sim["target_ips"]
    )

    profiles = []
    for p in raw["ue"]["profiles"]:
        burst_config = p.get("burst", {})
        if burst_config.get("enable", False):
            burst = Burst(
                enabled=True,
                burst_chance=burst_config["burst_chance"],
                burst_arrival_rate=burst_config["burst_arrival_rate"],
                burst_on_duration=BurstRange(
                    min=burst_config["burst_on_duration"]["min"],
                    max=burst_config["burst_on_duration"]["max"]
                ),
                burst_off_duration=BurstRange(
                    min=burst_config["burst_off_duration"]["min"],
                    max=burst_config["burst_off_duration"]["max"]
                )
            )
        else:
            burst = Burst(enabled=False)

        profile = ProfileConfig(
            name=p["name"],
            ue_count=p["ue_count"],
            packet_arrival_rate=p["packet_arrival_rate"],
            packet_size=PacketSize(
                distribution=p["packet_size"]["distribution"],
                min=p["packet_size"]["min"],
                max=p["packet_size"]["max"]
            ),
            burst=burst
        )

        profiles.append(profile)


    return ParsedConfig(simulation=simulation, profiles=profiles)

if __name__ == "__main__":
    config = parse_config()
    # print the parsed configuration in a readable format
    print("Parsed Configuration:")
    print("Simulation Configuration:")
    print(f"  Duration (sec): {config.simulation.duration_sec}")
    print(f"  Display Interval (sec): {config.simulation.display_interval_sec}")
    print(f"  Packet Type: {config.simulation.packet_type}")
    print(f"  Target IPs: [{'],   ['.join(config.simulation.target_ips)}]")
    
    print("User Profiles:")
    for profile in config.profiles:
        print(f"  Profile Name: {profile.name}") 
        print(Fore.GREEN + f"    UE Count: {profile.ue_count}" + Style.RESET_ALL)
        print(f"    Packet Arrival Rate: {profile.packet_arrival_rate} /s")
        print(f"    Packet Size: {profile.packet_size.min} ~ {profile.packet_size.max} byets --- distribution: {profile.packet_size.distribution}")
        print(f"    Burst Enabled: {profile.burst.enabled}")
        if profile.burst.enabled:
            print(f"    Burst Chance: {profile.burst.burst_chance}")
            print(f"    Burst Arrival Rate: {profile.burst.burst_arrival_rate} /s")
            print(f"    Burst On Duration: {profile.burst.burst_on_duration.min} ~ {profile.burst.burst_on_duration.max} sec")
            print(f"    Burst Off Duration: {profile.burst.burst_off_duration.min} ~ {profile.burst.burst_off_duration.max} sec")
        else:
            print("    Burst: Disabled")
    print(Style.RESET_ALL)
    print("Configuration parsing completed successfully.")

