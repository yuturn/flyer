"""
GPS 模擬器 Web 介面
使用 Flask + Leaflet.js，手機瀏覽器直接開啟即可 DEMO
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import math, random, time, threading, os, socket

app = Flask(__name__)
CORS(app)

# ── 自動取得本機 IP ───────────────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        try:
            return socket.gethostbyname(socket.gethostname())
        except:
            return "127.0.0.1"

LOCAL_IP   = get_local_ip()
HTTPS_PORT = 5443

# ── GPS 核心邏輯 ──────────────────────────────────────────
EARTH_RADIUS = 6_371_000

class SimState:
    def __init__(self):
        self.lat     = 25.033964
        self.lon     = 121.564468
        self.alt     = 10.0
        self.speed   = 0.0
        self.heading = 0.0
        self.noise   = 3.0
        self.running = False
        self.history = []
        self.lock    = threading.Lock()

state = SimState()

def add_noise(value, scale):
    return value + random.gauss(0, state.noise / scale)

def move_step(delta=1.0):
    if state.speed <= 0:
        return
    distance = state.speed * delta
    hr = math.radians(state.heading)
    la = math.radians(state.lat)
    lo = math.radians(state.lon)
    ad = distance / EARTH_RADIUS
    new_la = math.asin(math.sin(la)*math.cos(ad) + math.cos(la)*math.sin(ad)*math.cos(hr))
    new_lo = lo + math.atan2(math.sin(hr)*math.sin(ad)*math.cos(la),
                              math.cos(ad)-math.sin(la)*math.sin(new_la))
    state.lat = math.degrees(new_la)
    state.lon = math.degrees(new_lo)

def get_position():
    cos_lat = math.cos(math.radians(state.lat))
    return {
        "lat":       round(add_noise(state.lat, 111_000), 8),
        "lon":       round(add_noise(state.lon, 111_000 * cos_lat), 8),
        "altitude":  round(state.alt + random.gauss(0, 1), 2),
        "speed":     round(max(0, state.speed + random.gauss(0, 0.05)), 3),
        "accuracy":  round(abs(random.gauss(state.noise, 1)), 1),
        "heading":   state.heading,
        "timestamp": round(time.time(), 3)
    }

# ── 背景自動推進 ──────────────────────────────────────────
def background_loop():
    while True:
        if state.running:
            with state.lock:
                move_step(1.0)
                pos = get_position()
                state.history.append(pos)
                if len(state.history) > 500:
                    state.history.pop(0)
        time.sleep(1.0)

threading.Thread(target=background_loop, daemon=True).start()

# ── 工具函式 ──────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = EARTH_RADIUS
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a  = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# ── API 路由 ──────────────────────────────────────────────
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/position")
def api_position():
    with state.lock:
        pos = get_position()
    return jsonify(pos)

@app.route("/api/history")
def api_history():
    with state.lock:
        return jsonify(state.history[-200:])

@app.route("/api/set_movement", methods=["POST"])
def api_set_movement():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False, "error": "invalid json"}), 400
    try:
        state.speed   = max(0.0, float(data.get("speed", 0)))
        state.heading = float(data.get("heading", 0)) % 360
        state.running = state.speed > 0
    except (ValueError, TypeError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    return jsonify({"ok": True, "speed": state.speed, "heading": state.heading})

@app.route("/api/teleport", methods=["POST"])
def api_teleport():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"ok": False, "error": "invalid json"}), 400
    try:
        lat = float(data["lat"])
        lon = float(data["lon"])
    except (KeyError, ValueError, TypeError) as e:
        return jsonify({"ok": False, "error": str(e)}), 400
    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        return jsonify({"ok": False, "error": "座標超出有效範圍"}), 400
    old = (state.lat, state.lon)
    state.lat = lat
    state.lon = lon
    pos  = get_position()
    dist = haversine(*old, lat, lon)
    state.history.append(pos)
    return jsonify({"ok": True, "distance_km": round(dist/1000, 2), **pos})

@app.route("/api/stop", methods=["POST"])
def api_stop():
    state.speed   = 0
    state.running = False
    return jsonify({"ok": True})

@app.route("/api/clear", methods=["POST"])
def api_clear():
    with state.lock:
        state.history.clear()
    return jsonify({"ok": True})

@app.route("/api/nmea")
def api_nmea():
    """輸出 NMEA GPGGA 格式，可供外部工具讀取"""
    pos = get_position()
    lat, lon, alt = pos["lat"], pos["lon"], pos["altitude"]
    lat_d  = int(abs(lat));  lat_m  = (abs(lat)  - lat_d)  * 60
    lon_d  = int(abs(lon));  lon_m  = (abs(lon)  - lon_d)  * 60
    lat_s  = f"{lat_d:02d}{lat_m:07.4f}"
    lon_s  = f"{lon_d:03d}{lon_m:07.4f}"
    ns, ew = ("N" if lat >= 0 else "S"), ("E" if lon >= 0 else "W")
    body   = f"GPGGA,000000.00,{lat_s},{ns},{lon_s},{ew},1,08,1.0,{alt:.1f},M,0.0,M,,"
    chk    = 0
    for c in body: chk ^= ord(c)
    return f"${body}*{chk:02X}", 200, {"Content-Type": "text/plain"}

@app.route("/api/info")
def api_info():
    """回傳伺服器資訊，方便其他機器確認連線"""
    return jsonify({"ip": LOCAL_IP, "port": HTTPS_PORT, "status": "ok"})

# ── 憑證 / 描述檔 / 安裝頁 ────────────────────────────────
@app.route("/cert.pem")
def get_cert():
    return send_file("cert.pem", mimetype="application/x-pem-file",
                     as_attachment=True, download_name="gps-simulator.pem")

@app.route("/gps-ca.mobileconfig")
def get_mobileconfig():
    return send_file("gps-ca.mobileconfig",
                     mimetype="application/x-apple-aspen-config",
                     as_attachment=False)

@app.route("/install")
def install_page():
    ip = LOCAL_IP
    html = f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>安裝 GPS 模擬器憑證</title>
<style>
  body{{font-family:-apple-system,sans-serif;background:#0f172a;color:#e2e8f0;
       display:flex;flex-direction:column;align-items:center;justify-content:center;
       min-height:100vh;margin:0;padding:20px;box-sizing:border-box;}}
  .card{{background:#1e293b;border-radius:16px;padding:28px 24px;max-width:360px;width:100%;}}
  h1{{color:#38bdf8;font-size:1.3rem;margin:0 0 8px}}
  p{{color:#94a3b8;font-size:0.88rem;line-height:1.6;margin:0 0 20px}}
  .step{{background:#0f172a;border-radius:10px;padding:14px;margin-bottom:12px;}}
  .step-num{{color:#38bdf8;font-weight:700;font-size:0.8rem;margin-bottom:4px;}}
  .step p{{margin:0;color:#cbd5e1;font-size:0.85rem;}}
  .btn{{display:block;background:#0ea5e9;color:#fff;text-align:center;
        border-radius:12px;padding:14px;font-weight:700;font-size:1rem;
        text-decoration:none;margin-top:20px;}}
  .btn2{{background:#22c55e;margin-top:10px;}}
  .warn{{color:#f59e0b;font-size:0.78rem;margin-top:12px;text-align:center;}}
</style>
</head>
<body>
<div class="card">
  <h1>📡 GPS 模擬器</h1>
  <p>請先安裝憑證，才能讓 Safari 使用 GPS 功能</p>
  <div class="step"><div class="step-num">步驟 1</div><p>點下方按鈕下載描述檔</p></div>
  <div class="step"><div class="step-num">步驟 2</div>
    <p>打開「設定 App」→ 頂部「已下載描述檔」→ 安裝</p></div>
  <div class="step"><div class="step-num">步驟 3</div>
    <p>設定 → 一般 → 關於本機 → <b>憑證信任設定</b><br>→「GPS Simulator CA」開啟完全信任 ✅</p></div>
  <div class="step"><div class="step-num">步驟 4</div>
    <p>點下方「開啟 GPS 模擬器」即可使用</p></div>
  <a class="btn" href="/gps-ca.mobileconfig">⬇️ 下載憑證描述檔</a>
  <a class="btn btn2" href="/">🗺 開啟 GPS 模擬器</a>
  <p class="warn">⚠ 憑證僅用於本機 HTTPS，不會影響其他 App</p>
</div></body></html>"""
    return html

@app.route("/manifest.json")
def manifest():
    return jsonify({
        "name": "GPS 模擬器", "short_name": "GPS模擬",
        "start_url": "/", "display": "standalone",
        "background_color": "#0f172a", "theme_color": "#0f172a",
        "icons": [{"src": "/static/icon.png", "sizes": "192x192", "type": "image/png"}]
    })

# ── 啟動 ──────────────────────────────────────────────────
if __name__ == "__main__":
    if not os.path.exists("cert.pem") or not os.path.exists("key.pem"):
        print("⚠  找不到憑證，正在自動產生...")
        os.system("python gen_cert.py")

    print("=" * 55)
    print("  GPS 模擬器 (HTTPS)")
    print("=" * 55)
    print(f"  本機:  https://127.0.0.1:{HTTPS_PORT}")
    print(f"  手機:  https://{LOCAL_IP}:{HTTPS_PORT}")
    print(f"  安裝:  https://{LOCAL_IP}:{HTTPS_PORT}/install")
    print("=" * 55)

    app.run(host="0.0.0.0", port=HTTPS_PORT,
            ssl_context=("cert.pem", "key.pem"), debug=False)

