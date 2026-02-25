# 🚀 Shodan Telegram Bot

Bot Telegram untuk mempermudah penggunaan **Shodan Academic Plus** dengan template pencarian siap pakai dan output yang cantik.

## ✨ Fitur Utama

### 🔍 Template Pencarian Siap Pakai
- **30+ template** siap pakai untuk berbagai kategori
- Tinggal pilih template, isi parameter, dan jalankan
- Ada tombol "Pakai Default" untuk percobaan cepat
- Bisa juga langsung jalankan contoh query

### 📂 Kategori Template
| Kategori | Deskripsi |
|----------|-----------|
| 🌐 Network & Infrastructure | ISP, port, service, ASN, subnet, hostname, OS |
| 🌍 Web Servers & Apps | Web server, title, component, favicon, SSL |
| 📡 IoT & Cameras | Webcam, router, printer, MQTT |
| 🏭 ICS / SCADA | SCADA, Modbus, PLC |
| 🗄️ Databases | MongoDB, Elasticsearch, Redis, MySQL, PostgreSQL |
| 🛡️ Vulnerabilities | CVE search, default passwords |
| ☁️ Cloud Services | AWS, GCP, Azure, DigitalOcean |
| 🗺️ By Country/Region | Overview negara, overview kota |

### 🎨 Output Cantik
- Formatted dengan emoji dan box drawing
- Progress bar untuk statistik
- Facet breakdown (top org, port, product, dll)
- Pagination untuk navigasi hasil

### 🛠️ Fitur Lengkap
- **Host Lookup** — Detail lengkap sebuah IP
- **DNS Tools** — Resolve, Reverse DNS, Domain info
- **Exploit Search** — Cari exploit
- **Honeypot Detection** — Cek apakah IP honeypot
- **Scan Request** — Request Shodan scan
- **Count Query** — Hitung hasil tanpa pakai credits
- **Filter Reference** — Daftar filter Shodan lengkap

## 📦 Instalasi

### 1. Clone & Setup
```bash
cd shodanTelegram
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Konfigurasi
```bash
cp .env.example .env
```

Edit file `.env` dan isi:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
SHODAN_API_KEY=your_shodan_api_key_here
AUTHORIZED_USERS=your_telegram_user_id
```

**Cara mendapatkan:**
- **Telegram Bot Token**: Chat ke [@BotFather](https://t.me/BotFather) → `/newbot`
- **Shodan API Key**: Login di [account.shodan.io](https://account.shodan.io)
- **Telegram User ID**: Chat ke [@userinfobot](https://t.me/userinfobot)

### 3. Jalankan
```bash
python bot.py
```

## 📱 Cara Pakai

### Quick Start
1. Buka bot di Telegram
2. Ketik `/start`
3. Pilih **🔍 Quick Search** dari menu
4. Pilih kategori (misal: Network & Infrastructure)
5. Pilih template (misal: Cari Provider / ISP)
6. Isi parameter yang diminta atau tekan "Pakai Default"
7. Lihat hasilnya! 🎉

### Perintah Tersedia
| Perintah | Fungsi |
|----------|--------|
| `/start` | Mulai bot & tampilkan menu |
| `/templates` atau `/t` | Lihat template pencarian |
| `/search [query]` | Pencarian langsung |
| `/count [query]` | Hitung hasil (hemat credits) |
| `/host [IP]` | Lookup detail IP |
| `/dns [hostname]` | DNS resolve |
| `/rdns [IP]` | Reverse DNS |
| `/domain [domain]` | Info DNS domain |
| `/exploit [keyword]` | Cari exploit |
| `/honeypot [IP]` | Cek honeypot score |
| `/scan [IP]` | Request scan |
| `/scanstatus [id]` | Cek status scan |
| `/info` | Cek akun & credits |
| `/filters` | Referensi filter Shodan |
| `/help` | Bantuan |

### Contoh Penggunaan

**Cari semua Telkom di Indonesia:**
```
/search org:"Telkom Indonesia" country:"ID"
```

**Cari nginx di Jakarta:**
```
/search product:"nginx" city:"Jakarta" country:"ID"
```

**Count tanpa pakai credits:**
```
/count country:"ID" port:22
```

**Host lookup:**
```
/host 8.8.8.8
```

## 🏗️ Struktur Project

```
shodanTelegram/
├── bot.py              # Main bot & handlers
├── config.py           # Configuration & env vars
├── shodan_client.py    # Shodan API wrapper
├── templates.py        # Search templates
├── formatter.py        # Beautiful output formatter
├── keyboards.py        # Inline keyboard builder
├── requirements.txt    # Dependencies
├── .env.example        # Environment template
├── .gitignore
└── README.md
```

## 🔐 Keamanan

- Bot hanya bisa digunakan oleh **user ID yang terdaftar** di `AUTHORIZED_USERS`
- API key disimpan di `.env` (tidak di-commit ke git)
- Scan memerlukan konfirmasi sebelum dijalankan

## 📝 Tips

- Gunakan `/count` dulu untuk mengecek jumlah hasil sebelum `/search` (hemat query credits)
- Gunakan `/filters` sebagai referensi filter Shodan
- Template sudah didesain untuk use case umum, tapi kamu selalu bisa pakai **Raw Query** untuk query custom
