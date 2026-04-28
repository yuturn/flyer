# GPS Simulator - 使用說明

> 在瀏覽器上展示 GPS 模擬移動、真實 GPS 讀取、瞬間移動（飛人）原理的 Web 工具。
> 支援 iPhone Safari，搭配 3uTools 可讓所有 App 收到模擬座標。

---

## 專案檔案說明

```
flyer/
├── app.py                 <- 主程式（Flask HTTPS 伺服器）
├── gen_cert.py            <- 產生自簽 SSL 憑證 + iPhone 描述檔
├── requirements.txt       <- Python 套件清單
├── gps_simulator.py       <- 純命令列版 GPS 模擬（獨立使用）
├── templates/
│   └── index.html         <- 網頁介面（地圖 + 控制面板）
├── static/                <- 靜態資源
│
│   -- 以下為執行後自動產生，搬到新電腦不需複製 --
├── cert.pem               <- HTTPS 憑證（gen_cert.py 產生）
├── key.pem                <- HTTPS 私鑰（gen_cert.py 產生）
├── gps-ca.mobileconfig    <- iPhone 信任描述檔（gen_cert.py 產生）
└── local_ip.txt           <- 本機 IP 記錄（gen_cert.py 產生）
```

注意：cert.pem、key.pem、gps-ca.mobileconfig 綁定電腦 IP，
      換電腦後必須重新用 gen_cert.py 產生，不能直接複製舊的。

---

## 電腦端設定（每台電腦只做一次）

### 前置條件

- Windows 10 / 11
- Python 3.9 以上 ( https://www.python.org/downloads/ )
  安裝時務必勾選「Add Python to PATH」

---

### 步驟 1：把專案複製到新電腦

將整個 flyer 資料夾複製到新電腦（USB、雲端硬碟、壓縮包皆可）。
打開 PowerShell，進入資料夾：

    cd C:\你的路徑\flyer

---

### 步驟 2：安裝 Python 套件

    pip install -r requirements.txt

成功後會顯示 Successfully installed flask flask-cors cryptography ...

如果 pip 找不到，改用：
    python -m pip install -r requirements.txt

---

### 步驟 3：產生 HTTPS 憑證（綁定本機 IP）

    python gen_cert.py

成功後顯示：
    cert.pem / key.pem  已產生
    gps-ca.mobileconfig 已產生
    本機 IP: 192.168.x.x

注意：每換一台電腦、或電腦 IP 改變後，都要重新執行這個步驟。

---

### 步驟 4：開放防火牆（讓手機能連進來）

用「系統管理員」身分開啟 PowerShell，貼上以下指令：

    netsh advfirewall firewall add rule name="GPS Simulator" dir=in action=allow protocol=TCP localport=5443

出現「確定。」代表成功。（只需做一次，重開機後依然有效）

如何用系統管理員開 PowerShell：
    開始 → 搜尋 PowerShell → 右鍵 → 以系統管理員身分執行

---

### 步驟 5：啟動伺服器

    python app.py

啟動後終端機會顯示：

    =======================================================
      GPS 模擬器 (HTTPS)
    =======================================================
      本機:  https://127.0.0.1:5443
      手機:  https://192.168.1.100:5443    <- 記住這個 IP
      安裝:  https://192.168.1.100:5443/install
    =======================================================

伺服器在終端機開著就會持續執行，關掉視窗即停止。

---

## iPhone 端設定（換電腦後必須重做）

前提：iPhone 和電腦必須連到同一個 Wi-Fi

### 步驟 A：安裝信任憑證

1. iPhone 打開 Safari（必須用 Safari，Chrome / Firefox 不行）

2. 輸入網址：https://192.168.x.x:5443/install
   （把 192.168.x.x 換成終端機顯示的「手機」那行 IP）

3. 點「下載憑證描述檔」
   → 跳出「已下載描述檔」提示 → 點「允許」

4. 打開 iPhone「設定 App」
   → 最頂部出現「已下載描述檔」→ 點進去
   → 右上角「安裝」→ 輸入手機解鎖密碼 → 再點「安裝」

5. 回到設定 App 主畫面
   → 一般 → 關於本機 → 最底部「憑證信任設定」
   → 找到「GPS Simulator CA」→ 把開關打開 → 繼續

   注意：步驟 4（安裝描述檔）和步驟 5（開啟信任）是兩個獨立動作，
         兩個都要做，少一個都不能用。

### 步驟 B：開啟使用

Safari 輸入：https://192.168.x.x:5443

建議加入 iPhone 主畫面（像 App 一樣使用）：
    Safari 底部點「分享」按鈕 → 加入主畫面 → 新增

---

## 功能使用說明

| 功能       | 說明                                         |
|------------|----------------------------------------------|
| 真實 GPS   | 讀取 iPhone 目前真實位置，顯示在地圖上       |
| 模擬模式   | 設定速度（km/h）與方向，讓虛擬點在地圖移動  |
| 瞬間移動   | 在地圖點任意位置立即跳過去（展示飛人原理）  |
| 複製座標   | 複製目前座標，可貼到 3uTools 虛擬定位使用   |
| NMEA 輸出  | 顯示標準 GPGGA 格式，可供外部工具讀取       |

---

## 讓所有 App 都收到模擬座標（含速度移動）

本程式的模擬座標只在 Safari 瀏覽器中可見。
若要讓 Pikmin Bloom、Google Maps 等所有 App 都收到假座標，
使用內建的 auto_push.py 腳本即可，不需要額外安裝其他軟體。

### 方式 A：自動連續推送（推薦，支援速度移動）

使用 auto_push.py，每 3 秒自動把模擬器目前座標推送給 iPhone，
搭配網頁設定 20 km/h 移動，所有 App 就會看到持續移動的效果。

步驟：

1. iPhone 用 USB 線連接電腦，跳出「信任此電腦？」→ 點信任

2. 開啟第一個 PowerShell，啟動模擬器：
       cd C:\你的路徑\flyer
       python app.py

3. 開啟第二個 PowerShell，啟動自動推送：
       cd C:\你的路徑\flyer
       python auto_push.py

4. 用瀏覽器或手機開啟模擬器網頁，切換到「模擬模式」
   設定速度（例如 20 km/h）和方向 → 點「開始」

5. 此時 iPhone 所有 App 的 GPS 每 3 秒更新一次，
   會看到位置沿著設定方向以 20 km/h 持續移動

6. 停止：在第二個 PowerShell 按 Ctrl+C
   腳本會自動恢復 iPhone 真實 GPS 定位

調整推送間隔：
   編輯 auto_push.py 第 17 行的 PUSH_INTERVAL = 3
   數字越小更新越頻繁（建議 2~5 秒）

---

### 方式 B：手動推送單一座標（靜止定位）

適合只需要把 iPhone 定位到某個固定地點的情況，
仍可搭配 3uTools 使用。

1. 電腦安裝 3uTools：https://www.3u.com/

2. iPhone 用 USB 線連接電腦，3uTools 應顯示裝置資訊

3. 3uTools 選「工具箱」→「虛擬定位」

4. 在模擬器網頁移動到目標位置後，點「複製座標」

5. 貼到 3uTools 地圖搜尋框 → 點「修改虛擬定位」

停止虛擬定位：3uTools → 虛擬定位 → 恢復真實定位

---

## 常見問題

Q: Safari 顯示「此連線不是私人連線」
A: 憑證還沒信任。回到步驟 A，確認步驟 A-5 的「憑證信任設定」
   有把「GPS Simulator CA」的開關打開。

Q: 手機打不開網頁（連線逾時 / 無法連線）
A: 依序確認：
   1. iPhone 和電腦是否連到同一個 Wi-Fi
   2. 步驟 4 防火牆指令是否以系統管理員執行過
   3. python app.py 是否還在終端機執行中（視窗沒關）

Q: 換了地點 / 換了 Wi-Fi 之後連不上
A: 電腦 IP 可能已改變。重新執行 python gen_cert.py，
   再讓 iPhone 重新安裝新的描述檔（步驟 A 全部重做）。

Q: pip install 出現錯誤
A: 先升級 pip 再裝：
       python -m pip install --upgrade pip
       pip install -r requirements.txt

Q: python 指令找不到 / 不是內部命令
A: Python 安裝時沒有勾選「Add Python to PATH」。
   重新安裝 Python，安裝頁面最底部勾選「Add Python to PATH」。

Q: 憑證安裝後 Safari 還是顯示不安全
A: 進入「設定 → 一般 → 關於本機 → 憑證信任設定」，
   確認「GPS Simulator CA」旁邊的開關是綠色（開啟）狀態。

Q: auto_push.py 顯示「找不到 iPhone」
A: 確認 ① USB 線有確實連接 ② iPhone 跳出「信任此電腦？」有點信任
   ③ 試著重新插拔 USB 再執行。

Q: auto_push.py 推送後 App 的位置沒有更新
A: 部分 App（如地圖）需要幾秒才反應。
   若完全沒反應，確認 iPhone 已拔除 3uTools 的虛擬定位（若有開的話）。

Q: 按 Ctrl+C 後 GPS 沒有恢復真實位置
A: 手動在終端機執行：
       python -c "from pymobiledevice3.lockdown import create_using_usbmux; from pymobiledevice3.services.simulate_location import SimulateLocationService; SimulateLocationService(create_using_usbmux()).clear()"
