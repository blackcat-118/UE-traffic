import socket
import pandas as pd
from datetime import datetime
import time
import random
import os
from typing import Optional

class TrafficReplayer:
    def __init__(self, iface: str):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.iface = iface
        try:
            self.sock.setsockopt(socket.SOL_SOCKET, 25, iface.encode())
        except PermissionError:
            print(f"[WARN] Need root to bind socket to interface {iface}")
        except OSError as e:
            print(f"[ERROR] Cannot bind to {iface}: {e}")

    
    def _parse_time(self, s: str) -> float:
        """
            將時間字串轉換為秒數
            例如 "2022-10-05 15:59:09.860208" → 57549.860208 秒
        """
        try:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
            return dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
        except Exception as e:
            print(f"[WARN] Failed to parse time '{s}': {e}")
            return 0.0
        
    def _random_split(self, total: int, parts: int) -> list:
        """
        隨機將 total 拆成 parts 個整數，其總和等於 total
        """
        if parts == 1:
            return [total]
        # 隨機選擇 (parts - 1) 個切點
        cuts = sorted(random.sample(range(1, total), parts - 1))
        return [a - b for a, b in zip(cuts + [total], [0] + cuts)]

    def replay(self, csv_path: str, num_of_ue: int, destination: str):
        """
        重播流量
        從 CSV 檔案讀取流量資料，並將其分配給多個 UE
        """

        result = self.get_packet_size_per_second(csv_path=csv_path)
        print("Packet size per second:")
        print(result)

        for _, row in result.iterrows():
            second = row["Second"]
            total_bytes = int(row["TotalBytes"])

            # 隨機分配 total_bytes 給 num_of_ue 個 UE
            splits = self._random_split(total_bytes, num_of_ue)

            # 傳送給每個 UE 對應的 interface
            for i, size in enumerate(splits, start=0):
                iface = f"uesimtun{i}"

                # 嘗試綁定 interface（Linux only, root required）
                try:
                    self.sock.setsockopt(socket.SOL_SOCKET, 25, iface.encode())
                except PermissionError:
                    print(f"[WARN] Need root to bind socket to interface {iface}")
                except OSError as e:
                    print(f"[ERROR] Cannot bind to {iface}: {e}")

                payload = bytes(random.getrandbits(8) for _ in range(size))
                try:
                    self.sock.sendto(payload, (self.destination, 9000))
                    print(f"[SEND] {size} bytes from {iface} to {self.destination}")
                except Exception as e:
                    print(f"[ERROR] Failed to send from {iface} to {self.destination}: {e}")

            time.sleep(1)  # 模擬每秒發送


    def get_packet_size_per_second(self, csv_path: str) -> pd.DataFrame:
        """
        計算每秒的封包大小總和
        回傳 DataFrame: second, total_bytes
        """
        df = pd.read_csv(csv_path)

        # if statistics_only:
        #     # 只保留統計資訊，不需要實際的流量重播
        #     df.drop(columns=["No.", "Source", "Destination", "Protocol", "Info"], inplace=True, errors='ignore')

        if df["Time"].dtype != float:
            df["Time"] = df["Time"].apply(self._parse_time)

        df["Second"] = df["Time"].astype(int)

        result = df.groupby("Second")["Length"].sum().reset_index()
        result.rename(columns={"Length": "TotalBytes"}, inplace=True)

        return result
    
    def send_packet(self, *, target_ip: str, payload_size: int, target_port: Optional[int] = None):
        """
        Call by external simulator to send packets.
        """
        try:
            payload = bytes(random.getrandbits(8) for _ in range(payload_size))
            self.sock.sendto(payload, (target_ip, target_port))
            # print(f"[{self.iface}] Sent {payload_size} bytes to {target_ip}:{target_port}")
        except Exception as e:
            print(f"[{self.iface}] UDP send failed: {e}")

if __name__ == "__main__":
    """
    Testing for replaying traffic from a CSV file
    """
    import argparse

    parser = argparse.ArgumentParser(description="Replay network traffic from a CSV file.")
    parser.add_argument("--csv_path", type=str, help="Path to the CSV file containing traffic data.")
    parser.add_argument("--iface", type=str, help="Network interface to bind to (optional).")

    args = parser.parse_args()

    replayer = TrafficReplayer()
    replayer.replay(args.csv_path, num_of_ue=30, destination="192.168.1.222")