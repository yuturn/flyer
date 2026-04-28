"""
GPS 位置模擬器 - 研究用途
原理：模擬 GPS 座標的移動軌跡，展示 Location-Based 應用的定位機制
"""

import time
import math
import random
import json
from dataclasses import dataclass, asdict
from typing import List, Tuple


@dataclass
class GPSCoordinate:
    latitude: float   # 緯度
    longitude: float  # 經度
    altitude: float   # 海拔 (公尺)
    accuracy: float   # 精確度 (公尺)
    speed: float      # 速度 (m/s)
    timestamp: float  # Unix 時間戳

    def to_dict(self):
        return asdict(self)

    def __str__(self):
        return (f"緯度: {self.latitude:.6f}, 經度: {self.longitude:.6f} | "
                f"海拔: {self.altitude:.1f}m | 精確度: ±{self.accuracy:.1f}m | "
                f"速度: {self.speed:.2f} m/s")


class GPSSimulator:
    """
    GPS 位置模擬器
    
    模擬原理：
    1. 設定起始座標
    2. 根據移動方向與速度計算下一個座標
    3. 加入真實 GPS 的隨機誤差 (noise)
    4. 輸出模擬的定位資料流
    """

    # 地球半徑 (公尺)
    EARTH_RADIUS = 6_371_000

    def __init__(self, start_lat: float, start_lon: float, altitude: float = 10.0):
        self.current_lat = start_lat
        self.current_lon = start_lon
        self.altitude = altitude
        self.heading = 0.0      # 移動方向 (度，0=北)
        self.speed = 0.0        # 移動速度 (m/s)
        self.noise_level = 3.0  # GPS 誤差模擬 (公尺)
        self.history: List[GPSCoordinate] = []

    def set_movement(self, speed_ms: float, heading_deg: float):
        """
        設定移動參數
        :param speed_ms: 速度 (公尺/秒)，步行約 1.4 m/s，跑步約 3 m/s
        :param heading_deg: 方向角 (0=北, 90=東, 180=南, 270=西)
        """
        self.speed = speed_ms
        self.heading = heading_deg
        print(f"[設定] 速度: {speed_ms} m/s ({speed_ms * 3.6:.1f} km/h), 方向: {heading_deg}°")

    def _add_gps_noise(self, value: float, scale: float) -> float:
        """模擬真實 GPS 的隨機誤差"""
        noise = random.gauss(0, self.noise_level / scale)
        return value + noise

    def _move(self, delta_seconds: float) -> Tuple[float, float]:
        """
        根據速度與方向計算新座標
        使用 Haversine 反推公式
        """
        distance = self.speed * delta_seconds  # 移動距離 (公尺)

        heading_rad = math.radians(self.heading)
        lat_rad = math.radians(self.current_lat)
        lon_rad = math.radians(self.current_lon)

        angular_dist = distance / self.EARTH_RADIUS

        new_lat_rad = math.asin(
            math.sin(lat_rad) * math.cos(angular_dist) +
            math.cos(lat_rad) * math.sin(angular_dist) * math.cos(heading_rad)
        )

        new_lon_rad = lon_rad + math.atan2(
            math.sin(heading_rad) * math.sin(angular_dist) * math.cos(lat_rad),
            math.cos(angular_dist) - math.sin(lat_rad) * math.sin(new_lat_rad)
        )

        return math.degrees(new_lat_rad), math.degrees(new_lon_rad)

    def get_current_position(self) -> GPSCoordinate:
        """取得當前模擬位置（含誤差）"""
        # 模擬 GPS 誤差
        noisy_lat = self._add_gps_noise(self.current_lat, 111_000)
        noisy_lon = self._add_gps_noise(self.current_lon, 111_000 * math.cos(math.radians(self.current_lat)))
        noisy_alt = self.altitude + random.gauss(0, 2)

        coord = GPSCoordinate(
            latitude=round(noisy_lat, 8),
            longitude=round(noisy_lon, 8),
            altitude=round(noisy_alt, 2),
            accuracy=round(abs(random.gauss(self.noise_level, 1)), 1),
            speed=round(self.speed + random.gauss(0, 0.1), 3),
            timestamp=time.time()
        )
        return coord

    def step(self, delta_seconds: float = 1.0) -> GPSCoordinate:
        """
        推進一步模擬
        :param delta_seconds: 時間步長 (秒)
        """
        if self.speed > 0:
            new_lat, new_lon = self._move(delta_seconds)
            self.current_lat = new_lat
            self.current_lon = new_lon

        coord = self.get_current_position()
        self.history.append(coord)
        return coord

    def teleport(self, lat: float, lon: float):
        """
        瞬間移動到指定座標（即「飛人」的核心概念）
        在真實 GPS 偽造中，這就是直接替換系統回傳的座標值
        """
        print(f"\n[瞬移] {self.current_lat:.6f},{self.current_lon:.6f} "
              f"→ {lat:.6f},{lon:.6f}")
        self.current_lat = lat
        self.current_lon = lon

    def run_simulation(self, duration_seconds: int = 30, interval: float = 1.0):
        """
        執行模擬，持續輸出定位資訊
        :param duration_seconds: 模擬時長 (秒)
        :param interval: 更新間隔 (秒)
        """
        print(f"\n{'='*60}")
        print(f"  GPS 模擬啟動 | 時長: {duration_seconds}s | 間隔: {interval}s")
        print(f"{'='*60}")

        steps = int(duration_seconds / interval)
        for i in range(steps):
            coord = self.step(interval)
            print(f"[{i+1:03d}] {coord}")
            time.sleep(interval)

        print(f"\n模擬結束，共記錄 {len(self.history)} 筆座標")

    def export_gpx(self, filename: str = "track.gpx"):
        """匯出 GPX 格式（可在 Google Maps / GPS 工具載入）"""
        gpx_content = ['<?xml version="1.0" encoding="UTF-8"?>',
                        '<gpx version="1.1" creator="GPS Simulator">',
                        '  <trk><name>Simulated Track</name><trkseg>']

        for coord in self.history:
            t = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(coord.timestamp))
            gpx_content.append(
                f'    <trkpt lat="{coord.latitude}" lon="{coord.longitude}">'
                f'<ele>{coord.altitude}</ele><time>{t}</time></trkpt>'
            )

        gpx_content += ['  </trkseg></trk>', '</gpx>']

        with open(filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(gpx_content))
        print(f"[匯出] GPX 檔案已儲存: {filename}")

    def export_json(self, filename: str = "track.json"):
        """匯出 JSON 格式"""
        data = [c.to_dict() for c in self.history]
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[匯出] JSON 檔案已儲存: {filename}")


# ──────────────────────────────────────────
# 工具函式
# ──────────────────────────────────────────

def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """計算兩點間的地表距離 (公尺)"""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing(lat1, lon1, lat2, lon2) -> float:
    """計算從 A 到 B 的方向角"""
    lat1, lat2 = math.radians(lat1), math.radians(lat2)
    dlon = math.radians(lon2 - lon1)
    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    return (math.degrees(math.atan2(x, y)) + 360) % 360


# ──────────────────────────────────────────
# 範例展示
# ──────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  GPS 位置模擬器 - 研究展示")
    print("=" * 60)

    # 起始點：台北 101 附近
    START_LAT = 25.033964
    START_LON = 121.564468

    sim = GPSSimulator(START_LAT, START_LON, altitude=15.0)

    # ── 範例 1：靜止狀態（模擬室內 GPS 漂移）──
    print("\n【範例 1】靜止狀態 - 觀察 GPS 自然誤差")
    sim.set_movement(speed_ms=0, heading_deg=0)
    for i in range(5):
        print(f"  {sim.step()}")
        time.sleep(0.3)

    # ── 範例 2：步行向北 ──
    print("\n【範例 2】步行向北 (1.4 m/s)")
    sim.set_movement(speed_ms=1.4, heading_deg=0)
    for i in range(5):
        coord = sim.step(1.0)
        print(f"  {coord}")
        time.sleep(0.3)

    # ── 範例 3：瞬移（飛人原理展示）──
    print("\n【範例 3】瞬間移動示範（飛人核心原理）")
    # 瞬移到高雄
    sim.teleport(22.627621, 120.301647)
    print(f"  新位置: {sim.get_current_position()}")

    dist = haversine_distance(START_LAT, START_LON, 22.627621, 120.301647)
    print(f"  瞬移距離: {dist/1000:.1f} 公里")
    print("  ⚠ 真實 GPS 系統中，這種瞬間位移會被伺服器端偵測")

    # ── 範例 4：沿路徑移動 ──
    print("\n【範例 4】沿路徑自動移動")
    waypoints = [
        (25.040000, 121.570000),  # 點 A
        (25.045000, 121.575000),  # 點 B
        (25.050000, 121.565000),  # 點 C
    ]

    current = (sim.current_lat, sim.current_lon)
    for wp in waypoints:
        dist = haversine_distance(*current, *wp)
        hdg = bearing(*current, *wp)
        speed = 1.4
        travel_time = dist / speed

        print(f"\n  → 前往 {wp}, 距離: {dist:.1f}m, 方向: {hdg:.1f}°")
        sim.set_movement(speed, hdg)

        steps = max(1, int(travel_time))
        for _ in range(min(steps, 5)):  # 最多顯示 5 步
            print(f"    {sim.step(1.0)}")
            time.sleep(0.1)

        current = wp

    # ── 匯出資料 ──
    sim.export_json("simulated_track.json")
    sim.export_gpx("simulated_track.gpx")

    print(f"\n{'='*60}")
    print("  研究重點整理")
    print("='*60")
    print("  1. GPS 座標本身只是數字，系統信任 API 回傳值")
    print("  2. 真實 GPS 有自然誤差（約 3-15 公尺）")
    print("  3. 瞬間大距離位移是伺服器端偵測外掛的主要依據")
    print("  4. 正規反制方法：速度檢查、位移合理性驗證、加速度感測器比對")
    print("=" * 60)
