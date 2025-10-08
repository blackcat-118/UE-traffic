from .ping_sender import PingSender
from .udp_sender import UDPSender
from .base import PacketSender
from .traffic_replayer import TrafficReplayer
from typing import Optional


def get_packet_sender(packet_type: str, 
                      iface: str, 
                      destination_ip: Optional[str], 
                      destination_port: Optional[int], 
                      connection_type: Optional[str]) -> PacketSender:
    
    if packet_type == "ping":
        return PingSender(iface)
    elif packet_type == "udp":
        return UDPSender(iface)
    elif packet_type == "replay":
        return TrafficReplayer(iface, destination_ip=destination_ip, destination_port=destination_port, connection_type=connection_type)
    else:
        raise ValueError(f"Unsupported packet type: {packet_type}")
