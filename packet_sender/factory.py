from .ping_sender import PingSender
from .udp_sender import UDPSender
from .base import PacketSender
from .traffic_replayer import TrafficReplayer


def get_packet_sender(packet_type: str, iface: str) -> PacketSender:
    if packet_type == "ping":
        return PingSender(iface)
    elif packet_type == "udp":
        return UDPSender(iface)
    elif packet_type == "replay":
        return TrafficReplayer(iface)
    else:
        raise ValueError(f"Unsupported packet type: {packet_type}")
