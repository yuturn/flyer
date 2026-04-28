"""
auto_push.py
============
每 3 秒從本專案 GPS 模擬器讀取當前座標，
透過 Apple lockdownd 協定直接推送給 USB 連接的 iPhone，
效果等同於 3uTools 虛擬定位（但全自動、持續更新）。

使用前安裝額外套件：
    pip install pymobiledevice3 requests urllib3

使用方式：
    1. iPhone 用 USB 連接電腦，信任此電腦
    2. 確認 python app.py 已在另一個終端機執行中
    3. 執行本腳本：python auto_push.py
    4. 停止：Ctrl+C（會自動恢復真實 GPS）
"""

import time
import sys
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── 設定 ──────────────────────────────────────────────────
GPS_API      = "https://127.0.0.1:5443/api/position"  # 本機模擬器 API
PUSH_INTERVAL = 3          # 每幾秒推送一次（建議 2~5 秒）
# ─────────────────────────────────────────────────────────


def get_simulated_position():
    """從本專案模擬器取得目前座標"""
    try:
        resp = requests.get(GPS_API, verify=False, timeout=3)
        data = resp.json()
        return data["lat"], data["lon"]
    except Exception as e:
        print(f"[!] 無法取得模擬器座標：{e}")
        return None, None


def connect_iphone():
    """連接 USB iPhone，回傳 lockdown 物件"""
    try:
        from pymobiledevice3.lockdown import create_using_usbmux
        lockdown = create_using_usbmux()
        name = lockdown.display_name
        ios  = lockdown.product_version
        print(f"[✓] 已連接：{name}（iOS {ios}）")
        return lockdown
    except ImportError:
        print("[!] 請先安裝套件：pip install pymobiledevice3")
        sys.exit(1)
    except Exception as e:
        print(f"[!] 找不到 iPhone，請確認 USB 已連接並信任此電腦\n    錯誤：{e}")
        sys.exit(1)


def main():
    print("=" * 50)
    print("  GPS 自動推送腳本")
    print("=" * 50)
    print(f"  模擬器 API : {GPS_API}")
    print(f"  推送間隔   : {PUSH_INTERVAL} 秒")
    print("  停止方式   : Ctrl+C")
    print("=" * 50)

    # 確認模擬器是否執行中
    lat, lon = get_simulated_position()
    if lat is None:
        print("[!] 模擬器未執行，請先在另一個終端機執行：python app.py")
        sys.exit(1)
    print(f"[✓] 模擬器連線成功，起始座標：{lat}, {lon}")

    # 連接 iPhone
    lockdown = connect_iphone()

    # 開始推送
    try:
        from pymobiledevice3.services.simulate_location import SimulateLocationService
    except ImportError:
        # 舊版 pymobiledevice3 的路徑
        try:
            from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulationService as SimulateLocationService
        except ImportError:
            print("[!] pymobiledevice3 版本不支援，請升級：pip install --upgrade pymobiledevice3")
            sys.exit(1)

    print("\n[*] 開始推送座標到 iPhone，按 Ctrl+C 停止...\n")
    count = 0

    try:
        with SimulateLocationService(lockdown) as sim:
            while True:
                lat, lon = get_simulated_position()
                if lat is not None:
                    sim.set(lat, lon)
                    count += 1
                    print(f"[{count:04d}] 推送 → 緯度 {lat:.6f}  經度 {lon:.6f}")
                time.sleep(PUSH_INTERVAL)

    except KeyboardInterrupt:
        print("\n\n[*] 停止推送，正在恢復真實 GPS...")
        try:
            with SimulateLocationService(lockdown) as sim:
                sim.clear()
            print("[✓] 已恢復真實 GPS 定位")
        except Exception as e:
            print(f"[!] 恢復失敗（請在 3uTools 手動點「恢復真實定位」）：{e}")


if __name__ == "__main__":
    main()
