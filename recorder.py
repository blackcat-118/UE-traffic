import threading
from typing import Dict, List, Optional
from datetime import datetime
import csv

from ue_generator import UEProfile


class Recorder:
    def __init__(self, lock: threading.Lock, ueProfiles: List[UEProfile], csv_path: str = "log/packet_records.csv"):
        self.lock = lock
        self.csv_path = csv_path
        self.record_start_time = datetime.now().timestamp()

        # 紀錄每一個送出的封包資訊，用於畫圖 / 儲存 CSV / 時間分析
        # 每筆紀錄是一個字典，格式如下：
        # {
        #     "timestamp": float,    # 封包送出時間（timestamp in seconds）
        #     "ue_id": int,          # 發送封包的 UE ID（對應 UEProfile.id）
        #     "iface": str,          # Interface 名稱，例如 "uesimtun1"
        #     "size_bytes": int,     # 封包大小（byte）
        #     "latency_ms": float    # ping latency（毫秒），可為 None
        # }
        self.packet_records: List[Dict] = []

        # 每個 UE 已發送的封包總數，用於：
        # - 即時畫面（bar chart 條狀圖）
        # - 模擬後快速統計每個 UE 的發送強度
        # 結構範例如下：
        # {
        #     1: 47,   # UE 1 發了 47 個封包
        #     2: 58,   # UE 2 發了 58 個封包
        #     ...
        # }
        self.ue_packet_cnt: Dict[int, int] = {}

        # 每個 UE 所送封包的延遲（latency）記錄，用於：
        # - 延遲分析（平均 / 標準差 / 最大最小）
        # - 畫 latency boxplot（橫向比較各 UE）
        # 結構範例如下：
        # {
        #     1: [3.12, 2.95, 3.48, ...],
        #     2: [12.1, 11.8, 14.3, ...],
        #     ...
        # }
        self.ue_latency_ms: Dict[int, List[float]] = {}

        for ue in ueProfiles:
            self.ue_packet_cnt[ue.id] = 0
        
        print(f"[INFO] Recorder initialized with {len(self.ue_packet_cnt)} UEs.")

    def increment_ue_packet_cnt(self, ue_id: int):
        with self.lock:
            self.ue_packet_cnt[ue_id] += 1
            self.ue_latency_ms[ue_id] = []

    def record_packet(
        self,
        ue_id: int,
        iface: str,
        size_bytes: int,
        latency_ms: Optional[float] = None
    ):
        with self.lock:
            self.packet_records.append({
                "timestamp": datetime.now().timestamp() - self.record_start_time,
                "ue_id": ue_id,
                "iface": iface,
                "size_bytes": size_bytes,
                "latency_ms": latency_ms
            })

            # ue packet cnt (cache) record
            self.ue_packet_cnt[ue_id] += 1

            # ue latency ms (cache) record
            if latency_ms is not None:
                if ue_id not in self.ue_latency_ms:
                    self.ue_latency_ms[ue_id] = []
                self.ue_latency_ms[ue_id].append(latency_ms)
    
    def save_csv(self):
        if not self.packet_records:
            print("[ERROR] No packet records to save.")
            return
        with open(self.csv_path, "w", newline="") as csvfile:
            fieldnames = self.packet_records[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.packet_records:
                writer.writerow(record)

    def get_ue_packet_cnt(self):
        with self.lock:
            return self.ue_packet_cnt.copy()
        
    