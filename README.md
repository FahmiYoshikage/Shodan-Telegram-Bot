# 🚀 Shodan Telegram Bot — Azure Functions Edition

Bot Telegram untuk mempermudah penggunaan **Shodan Academic Plus** dengan template pencarian siap pakai, output cantik, dan deployment **serverless** di Azure Functions.

## ✨ Fitur Utama

### 🔍 Template Pencarian Siap Pakai (36 template)
- Tinggal pilih template, isi parameter, dan jalankan
- Tombol "Pakai Default" untuk percobaan cepat
- Bisa langsung run contoh query

### 📂 Kategori Template
| Kategori | Template |
|----------|----------|
| 🌐 Network & Infrastructure | ISP, port, service, ASN, subnet, hostname, OS |
| 🌍 Web Servers & Apps | Web server, title, component, favicon, SSL |
| 📡 IoT & Cameras | Webcam, router, printer, MQTT |
| 🏭 ICS / SCADA | SCADA, Modbus, PLC |
| 🗄️ Databases | MongoDB, Elasticsearch, Redis, MySQL, PostgreSQL |
| 🛡️ Vulnerabilities | CVE search, default passwords |
| ☁️ Cloud Services | AWS, GCP, Azure, DigitalOcean |
| 🗺️ By Country/Region | Overview negara & kota |

### 🛠️ Full Feature Set
- **Search** & **Count** (hemat credits)
- **Host Lookup** — Detail lengkap sebuah IP
- **DNS Tools** — Resolve, Reverse DNS, Domain info
- **Exploit Search** — Cari exploit
- **Honeypot Detection** — Cek apakah IP honeypot
- **Scan Request** — Request Shodan scan
- **Filter Reference** — Daftar filter Shodan lengkap

---

## 🏗️ Arsitektur

```
┌────────────────┐      HTTPS POST       ┌─────────────────────────┐
│   Telegram      │ ──────────────────▶   │   Azure Functions       │
│   (User Chat)   │ ◀──────────────────   │   (function_app.py)     │
└────────────────┘      JSON Response     │                         │
                                          │  ┌──────────────────┐   │
                                          │  │  bot_app.py       │   │
                                          │  │  handlers.py      │   │
                                          │  │  shodan_client.py │   │
                                          │  │  templates.py     │   │
                                          │  │  formatter.py     │   │
                                          │  │  keyboards.py     │   │
                                          │  └──────────────────┘   │
                                          └───────────┬─────────────┘
                                                      │
                                                      ▼
                                          ┌─────────────────────────┐
                                          │   Shodan API            │
                                          │   (Academic Plus)       │
                                          └─────────────────────────┘
```

**Kenapa Azure Functions?**
- **Serverless** — Bayar hanya saat dipakai (bisa $0/bulan dengan free tier)
- **Auto-scale** — Tidak perlu manage server
- **Webhook** — Lebih cepat dari polling, tidak perlu proses jalan terus
- **Always available** — Tidak perlu VPS yang 24/7 online

---

## 📦 Struktur Project

```
shodanTelegram/
├── function_app.py      # Azure Functions entry point (webhook)
├── bot.py               # Local dev entry point (polling)
├── bot_app.py           # Application builder (shared)
├── handlers.py          # All Telegram handlers
├── config.py            # Configuration
├── shodan_client.py     # Shodan API wrapper
├── templates.py         # 36 search templates
├── formatter.py         # Beautiful output formatter
├── keyboards.py         # Inline keyboard builder
├── host.json            # Azure Functions host config
├── local.settings.json  # Azure Functions local settings
├── requirements.txt     # Python dependencies
├── deploy.sh            # One-click Azure deployment script
├── .env.example         # Environment template
├── .env                 # Your secrets (git-ignored)
└── .gitignore
```

---

## 🚀 Deployment ke Azure Functions

### Prerequisites
1. **Azure CLI** — `curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash`
2. **Azure Functions Core Tools** — `npm i -g azure-functions-core-tools@4 --unsafe-perm true`
3. **Azure Account** — [portal.azure.com](https://portal.azure.com) (free tier tersedia)

### Step 1: Setup Lokal
```bash
cd shodanTelegram
cp .env.example .env
```

Edit `.env`:
```
TELEGRAM_BOT_TOKEN=<dari @BotFather>
SHODAN_API_KEY=<dari account.shodan.io>
AUTHORIZED_USERS=1760613750
```

### Step 2: Deploy (One-Click)
```bash
az login
./deploy.sh
```

Script ini otomatis:
1. Buat Resource Group
2. Buat Storage Account
3. Buat Function App (Consumption Plan / gratis)
4. Set app settings (secrets)
5. Deploy kode
6. Register webhook ke Telegram

### Step 3: Done! ✅
Buka Telegram → chat bot kamu → `/start`

---

## 💻 Local Development (Polling Mode)

Untuk development di lokal tanpa Azure:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env dengan token-token kamu
python bot.py
```

Bot akan jalan di polling mode (tidak perlu webhook).

### Switching Between Modes

```bash
# Hapus webhook (switch ke polling untuk local dev)
python bot.py --remove

# Set webhook (switch ke Azure Functions)
python bot.py --setup "https://your-func.azurewebsites.net/api/webhook?code=YOUR_KEY"
```

---

## 🔗 Azure Functions Endpoints

| Endpoint | Method | Auth | Fungsi |
|----------|--------|------|--------|
| `/api/webhook` | POST | Function Key | Menerima update dari Telegram |
| `/api/setup` | GET | Function Key | Register webhook URL |
| `/api/health` | GET | Anonymous | Health check & credit info |
| `/api/teardown` | GET | Function Key | Hapus webhook |

### Health Check
```bash
curl https://your-func.azurewebsites.net/api/health
```

Response:
```json
{
  "status": "healthy",
  "shodan_configured": true,
  "telegram_configured": true,
  "shodan_plan": "edu",
  "query_credits": 100000,
  "scan_credits": 100
}
```

---

## 📱 Cara Pakai di Telegram

### Quick Start
1. Chat bot → `/start`
2. Pilih **🔍 Quick Search**
3. Pilih kategori → pilih template → isi parameter → lihat hasil

### Semua Perintah
| Perintah | Fungsi |
|----------|--------|
| `/start` | Menu utama |
| `/templates` / `/t` | Template pencarian |
| `/search [query]` | Pencarian langsung |
| `/count [query]` | Hitung hasil (hemat credits) |
| `/host [IP]` | Detail IP |
| `/dns [hostname]` | DNS resolve |
| `/rdns [IP]` | Reverse DNS |
| `/domain [domain]` | DNS records |
| `/exploit [keyword]` | Cari exploit |
| `/honeypot [IP]` | Honeypot score |
| `/scan [IP]` | Request scan |
| `/scanstatus [id]` | Status scan |
| `/info` | Cek credits |
| `/filters` | Filter reference |
| `/help` | Bantuan |

### Contoh
```
/search org:"Telkom Indonesia" country:"ID"
/count country:"ID" port:22
/host 8.8.8.8
/dns google.com
/exploit log4j
```

---

## 💰 Estimasi Biaya Azure

| Komponen | Free Tier | Estimasi |
|----------|-----------|----------|
| Azure Functions (Consumption) | 1M executions/bulan gratis | **$0** |
| Storage Account | 5GB gratis | **$0** |
| **Total** | | **$0/bulan** (typical usage) |

Untuk personal use, biasanya 100% gratis dalam free tier Azure.

---

## 🔐 Keamanan

- Bot hanya bisa digunakan oleh **user ID terdaftar** (`AUTHORIZED_USERS`)
- Secrets disimpan di Azure Function App Settings (encrypted)
- Webhook endpoint dilindungi **Function Key**
- Scan memerlukan konfirmasi

---

## 🔧 Monitoring & Troubleshooting

```bash
# Stream live logs
func azure functionapp logstream func-shodan-telegram

# View di Azure Portal
# → Function App → Monitor → Log stream

# Check health
curl https://your-func.azurewebsites.net/api/health
```

### Cleanup (Hapus Semua Resources)
```bash
az group delete --name rg-shodan-bot --yes --no-wait
```
