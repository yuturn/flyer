"""
產生 iOS 可識別的 .mobileconfig 憑證描述檔
"""
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime, ipaddress, socket, base64, uuid, os, textwrap

# ── 取得本機 IP ──────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.38.216.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

local_ip = get_local_ip()
print(f"本機 IP: {local_ip}")

# ── 產生 RSA 私鑰 ────────────────────────────
key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)

# ── 建立 CA 憑證 ─────────────────────────────
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COMMON_NAME,         "GPS Simulator CA"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME,   "GPS Simulator"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=825))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address(local_ip)),
        ]),
        critical=False,
    )
    .add_extension(
        x509.KeyUsage(
            digital_signature=True, key_cert_sign=True, crl_sign=True,
            content_commitment=False, key_encipherment=False,
            data_encipherment=False, key_agreement=False,
            encipher_only=False, decipher_only=False
        ),
        critical=True
    )
    .sign(key, hashes.SHA256(), default_backend())
)

# ── 輸出 PEM 給 Flask ─────────────────────────
cert_pem = cert.public_bytes(serialization.Encoding.PEM)
key_pem  = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.TraditionalOpenSSL,
    serialization.NoEncryption()
)
with open("cert.pem", "wb") as f: f.write(cert_pem)
with open("key.pem",  "wb") as f: f.write(key_pem)
print("✅ cert.pem / key.pem 已產生")

# ── 產生 iOS mobileconfig（base64 每 52 字換行）──
cert_der     = cert.public_bytes(serialization.Encoding.DER)
# iOS plist <data> 需要帶換行的 base64
cert_b64_raw = base64.b64encode(cert_der).decode()
cert_b64     = "\n        ".join(textwrap.wrap(cert_b64_raw, 52))

profile_uuid = str(uuid.uuid4()).upper()
payload_uuid = str(uuid.uuid4()).upper()

mobileconfig = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>PayloadContent</key>
\t<array>
\t\t<dict>
\t\t\t<key>PayloadCertificateFileName</key>
\t\t\t<string>gps-ca.cer</string>
\t\t\t<key>PayloadContent</key>
\t\t\t<data>
\t\t\t{cert_b64}
\t\t\t</data>
\t\t\t<key>PayloadDescription</key>
\t\t\t<string>Installs the GPS Simulator root CA certificate</string>
\t\t\t<key>PayloadDisplayName</key>
\t\t\t<string>GPS Simulator CA</string>
\t\t\t<key>PayloadIdentifier</key>
\t\t\t<string>com.gpssimulator.ca.{payload_uuid}</string>
\t\t\t<key>PayloadType</key>
\t\t\t<string>com.apple.security.root</string>
\t\t\t<key>PayloadUUID</key>
\t\t\t<string>{payload_uuid}</string>
\t\t\t<key>PayloadVersion</key>
\t\t\t<integer>1</integer>
\t\t</dict>
\t</array>
\t<key>PayloadDescription</key>
\t<string>GPS Simulator local HTTPS certificate</string>
\t<key>PayloadDisplayName</key>
\t<string>GPS Simulator</string>
\t<key>PayloadIdentifier</key>
\t<string>com.gpssimulator.profile.{profile_uuid}</string>
\t<key>PayloadOrganization</key>
\t<string>GPS Simulator</string>
\t<key>PayloadRemovalDisallowed</key>
\t<false/>
\t<key>PayloadType</key>
\t<string>Configuration</string>
\t<key>PayloadUUID</key>
\t<string>{profile_uuid}</string>
\t<key>PayloadVersion</key>
\t<integer>1</integer>
</dict>
</plist>"""

with open("gps-ca.mobileconfig", "w", encoding="utf-8", newline="\n") as f:
    f.write(mobileconfig)

os.makedirs("static", exist_ok=True)
with open("local_ip.txt", "w") as f:
    f.write(local_ip)

print("✅ gps-ca.mobileconfig 已產生")
print()
print("=" * 58)
print(f"  本機 IP: {local_ip}")
print(f"  📱 iPhone Safari 開啟安裝頁：")
print(f"  https://{local_ip}:5443/install")
print("=" * 58)

from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime, ipaddress, socket, base64, uuid, os

# ── 取得本機 IP ──────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.38.216.1", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)

local_ip = get_local_ip()
print(f"本機 IP: {local_ip}")

# ── 產生 RSA 私鑰 ────────────────────────────
key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)

# ── 建立 CA 憑證 ─────────────────────────────
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME,            "TW"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME,  "Taiwan"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME,       "GPS Simulator CA"),
    x509.NameAttribute(NameOID.COMMON_NAME,             "GPS Simulator CA"),
])

cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=825))
    .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address(local_ip)),
        ]),
        critical=False,
    )
    .add_extension(
        x509.KeyUsage(
            digital_signature=True, key_cert_sign=True, crl_sign=True,
            content_commitment=False, key_encipherment=False,
            data_encipherment=False, key_agreement=False,
            encipher_only=False, decipher_only=False
        ),
        critical=True
    )
    .sign(key, hashes.SHA256(), default_backend())
)

# ── 輸出 PEM 給 Flask ─────────────────────────
cert_pem = cert.public_bytes(serialization.Encoding.PEM)
key_pem  = key.private_bytes(
    serialization.Encoding.PEM,
    serialization.PrivateFormat.TraditionalOpenSSL,
    serialization.NoEncryption()
)
with open("cert.pem", "wb") as f: f.write(cert_pem)
with open("key.pem",  "wb") as f: f.write(key_pem)
print("✅ cert.pem / key.pem 已產生")

# ── 產生 iOS mobileconfig ─────────────────────
cert_der     = cert.public_bytes(serialization.Encoding.DER)
cert_b64     = base64.b64encode(cert_der).decode()
profile_uuid = str(uuid.uuid4()).upper()
payload_uuid = str(uuid.uuid4()).upper()

mobileconfig = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>PayloadContent</key>
  <array>
    <dict>
      <key>PayloadCertificateFileName</key>
      <string>gps-simulator.cer</string>
      <key>PayloadContent</key>
      <data>{cert_b64}</data>
      <key>PayloadDescription</key>
      <string>GPS Simulator 本機 HTTPS 憑證</string>
      <key>PayloadDisplayName</key>
      <string>GPS Simulator CA</string>
      <key>PayloadIdentifier</key>
      <string>com.gpssimulator.cert.{payload_uuid}</string>
      <key>PayloadType</key>
      <string>com.apple.security.root</string>
      <key>PayloadUUID</key>
      <string>{payload_uuid}</string>
      <key>PayloadVersion</key>
      <integer>1</integer>
    </dict>
  </array>
  <key>PayloadDescription</key>
  <string>安裝此描述檔以信任 GPS 模擬器的本機 HTTPS 伺服器</string>
  <key>PayloadDisplayName</key>
  <string>GPS 模擬器憑證</string>
  <key>PayloadIdentifier</key>
  <string>com.gpssimulator.profile.{profile_uuid}</string>
  <key>PayloadOrganization</key>
  <string>GPS Simulator</string>
  <key>PayloadRemovalDisallowed</key>
  <false/>
  <key>PayloadType</key>
  <string>Configuration</string>
  <key>PayloadUUID</key>
  <string>{profile_uuid}</string>
  <key>PayloadVersion</key>
  <integer>1</integer>
</dict>
</plist>"""

with open("gps-ca.mobileconfig", "w", encoding="utf-8") as f:
    f.write(mobileconfig)

# 同時寫一份給 static 目錄讓 Flask 提供
os.makedirs("static", exist_ok=True)

print("✅ gps-ca.mobileconfig 已產生（iOS 描述檔）")
print()
print("=" * 58)
print(f"  本機 IP: {local_ip}")
print("=" * 58)
print(f"  📱 iPhone Safari 開啟安裝頁：")
print(f"  https://{local_ip}:5443/install")
print("=" * 58)

# 把 IP 寫到檔案讓 app.py 讀取
with open("local_ip.txt", "w") as f:
    f.write(local_ip)

from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
import datetime, ipaddress, socket

# 取得本機 IP
hostname = socket.gethostname()
local_ip = socket.gethostbyname(hostname)
print(f"本機 IP: {local_ip}")

# 產生私鑰
key = rsa.generate_private_key(
    public_exponent=65537, key_size=2048, backend=default_backend()
)

# 憑證資訊
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, "TW"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, "GPS Simulator"),
    x509.NameAttribute(NameOID.COMMON_NAME, local_ip),
])

# 加入 SAN（Subject Alternative Name）- iOS 必須有這個才信任
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.datetime.utcnow())
    .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=825))
    .add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
            x509.IPAddress(ipaddress.IPv4Address(local_ip)),
        ]),
        critical=False,
    )
    .sign(key, hashes.SHA256(), default_backend())
)

# 寫出憑證與私鑰
with open("cert.pem", "wb") as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

with open("key.pem", "wb") as f:
    f.write(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    ))

print("✅ 憑證已產生: cert.pem / key.pem")
print(f"✅ 有效 IP: 127.0.0.1 / {local_ip}")
print()
print("=" * 55)
print("  📱 iOS 安裝憑證步驟：")
print("=" * 55)
print(f"  1. iPhone Safari 開啟: https://{local_ip}:5443/cert.pem")
print("  2. 點「允許」下載描述檔")
print("  3. 設定 → 一般 → VPN與裝置管理 → 安裝描述檔")
print("  4. 設定 → 一般 → 關於本機 → 憑證信任設定")
print(f"     → 開啟「GPS Simulator」的完全信任")
print(f"  5. Safari 開啟: https://{local_ip}:5443")
print("  6. 點分享鈕 → 加入主畫面 → 即可像 App 安裝！")
print("=" * 55)
