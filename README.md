# 🧬 AI Trading Organism

> **EA MT5 berbasis AI yang bisa berevolusi sendiri. Laptop ringan (Intel Celeron N2830). AI berjalan di GitHub Actions - gratis & permanen.**

---

## 🚀 Cara Setup (5 Langkah)

### 1️⃣ Fork / Clone Repo Ini ke GitHub
```
https://github.com/YOUR_USERNAME/ai-trading-organism
```

### 2️⃣ Copy EA ke MT5
- Buka folder `MT5/`
- Copy `AI_Trading_Organism.mq5` ke:
  ```
  C:\Users\[nama]\AppData\Roaming\MetaQuotes\Terminal\[ID]\MQL5\Experts\
  ```
- Compile di MetaEditor (tekan F7)

### 3️⃣ Setup MT5 WebRequest
- Buka MT5 → Tools → Options → Expert Advisors
- Centang ✅ "Allow WebRequest for listed URL"
- Tambahkan URL:
  ```
  https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/signal.json
  ```

### 4️⃣ Update Config di EA
Edit parameter di EA:
```
SignalURL = "https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/signal.json"
InitialBalance = 50.0
DefaultLot = 0.01
```

### 5️⃣ Update Dashboard URL
Edit `DASHBOARD/index.html` baris:
```javascript
const GITHUB_USER = "YOUR_USERNAME";
const GITHUB_REPO = "YOUR_REPO";
```

### 6️⃣ Aktifkan GitHub Pages
- Repo Settings → Pages → Source: main branch → folder: /DASHBOARD
- Dashboard akan live di: `https://YOUR_USERNAME.github.io/YOUR_REPO/`

---

## 🏗️ Arsitektur Sistem

```
┌─────────────────────────────────────────────────────────────┐
│                     GITHUB (Cloud Gratis)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐  │
│  │  DNA     │  │ ORGANISMS│  │EVOLUTION │  │ DASHBOARD  │  │
│  │(Immutable│  │(Evolving)│  │ (Engine) │  │(Avatar AI) │  │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘  │
│                      ↑ GitHub Actions (Gratis)              │
│                      │ Evolusi tiap hari 03:00 UTC          │
│                      │ Signal tiap 5 menit                  │
└──────────────────────┼──────────────────────────────────────┘
                       │
                  signal.json
                       │ WebRequest
                       ↓
┌─────────────────────────────────────────────────────────────┐
│              LAPTOP (Intel Celeron N2830)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  MT5 + AI_Trading_Organism.mq5                       │   │
│  │  • Baca signal.json setiap 5 menit                   │   │
│  │  • Open/Close trade                                  │   │
│  │  • Ghost Stop Loss                                   │   │
│  │  • Trailing Profit Lock (10%-90%)                    │   │
│  │  • Anti-stacking per candle                          │   │
│  │  • Capital Protection 2x Rule                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧬 Struktur Folder

```
ai_trading_organism/
├── .github/workflows/
│   ├── evolution.yml      ← Evolusi harian (03:00 UTC)
│   ├── signal_push.yml    ← Signal setiap 5 menit
│   └── tournament.yml     ← Turnamen mingguan
│
├── DNA/                   🔒 TIDAK BISA DIUBAH AI
│   ├── core_dna.json      ← Aturan trading immutable
│   ├── immunity.py        ← Sistem imun
│   └── regeneration.py    ← Sistem rollback
│
├── BRAIN/
│   └── brain_template/    ← Template otak dasar
│       ├── brain.py
│       └── dna.json
│
├── ORGANISMS/             🧬 BISA BEREVOLUSI
│   ├── organism_001/      ← Organisme pertama
│   │   ├── brain.py       ← Otak (bisa ditulis ulang AI)
│   │   ├── dna.json       ← DNA (parameter evolusi)
│   │   ├── memory.json    ← Memori trading
│   │   └── backups/       ← Backup sebelum evolusi
│   └── organism_002/
│
├── EVOLUTION/
│   ├── evolve.py          ← Engine evolusi
│   ├── tournament.py      ← Turnamen antar organisme
│   └── mutate.py          ← Mutasi DNA
│
├── RUNNER/
│   └── runner.py          ← Hubungkan otak ke market
│
├── SECURITY/              🔒 TIDAK BISA DIUBAH AI
│   ├── trauma_system.py   ← Tracking error
│   ├── rollback.py        ← Rollback otomatis
│   └── fund_guardian.py   ← Proteksi modal
│
├── DASHBOARD/
│   ├── index.html         ← Dashboard evolusi lengkap (3D avatar)
│   └── mt5_dashboard.html ← Dashboard MT5 manual (permanen)
│
├── MEMORY/
│   ├── status.json        ← Status semua organisme
│   ├── evolution_log.json ← Log evolusi
│   └── trauma_log.json    ← Log error
│
├── MT5/
│   └── AI_Trading_Organism.mq5  ← EA MT5 UTAMA
│
├── signal.json            ← Signal aktif (dibaca MT5)
└── requirements.txt
```

---

## 🛡️ Sistem Keamanan

### Ghost Stop Loss
```
Tidak ada SL yang dikirim ke broker.
EA memantau sendiri setiap tick.
Broker tidak tahu posisi SL kamu → aman dari stop hunting.
```

### Trailing Profit Lock
| Profit | Lock |
|--------|------|
| 10%    | 5%   |
| 20%    | 10%  |
| 50%    | 35%  |
| 80%    | 65%  |
| 95%    | 90%  |

### Capital Protection (2x Rule)
```
Saldo awal: $50
Saldo naik jadi $100 → OTOMATIS DIKUNCI:
  → $50 LOCKED FUND (tidak disentuh)
  → $50 TRADING FUND (untuk trading)
  
Jika Trading Fund habis:
  → TIDAK langsung buka locked fund
  → Tunggu sesi market berikutnya
  
Contoh: Loss saat Asia session
  → Locked fund baru bisa dipakai setelah Asia selesai (jam 09:00 UTC)
```

### Anti-Stacking Per Candle
```
✅ Setiap candle M1 boleh entry 1 trade
❌ Tidak boleh numpuk di level harga yang sama
Minimal jarak: 150 points antar layer

Contoh XAUUSD:
Layer 1: 2350.00 ✅
Layer 2: 2351.50 ✅ (+150 points)
Layer 3: 2350.10 ❌ (terlalu dekat dengan layer 1)
```

### Trauma & Rollback
```
Tiap error organism dicatat.
Trauma level 2+ → otomatis rollback ke brain sebelumnya.
Backup dibuat sebelum setiap evolusi.
```

---

## 🧬 Sistem Evolusi

### Setiap Hari (03:00 UTC)
1. GitHub Actions menjalankan `EVOLUTION/evolve.py`
2. Semua organisme dinilai (profit/loss score)
3. Organisme terbaik dipilih sebagai parent
4. DNA dimutasi → anak baru lahir
5. Organisme lemah diarsipkan
6. Signal terbaru di-generate

### Setiap 5 Menit
- `RUNNER/runner.py` ambil data market dari Yahoo Finance
- Organisme terbaik menganalisis dengan 7 strategi
- Signal ditulis ke `signal.json`
- MT5 membaca dan mengeksekusi

### Setiap Senin (06:00 UTC)
- Tournament: semua organisme berkompetisi
- Pemenang jadi champion

---

## 🌐 Indra AI

| Perangkat | Indra |
|-----------|-------|
| MT5       | Price, Volume, Spread, Time |
| PC Browser| Keyboard, Mic (WebSpeech API) |
| HP Browser| Kamera, Mic, Touch, GPS |
| GitHub    | Internet data, Wikipedia, berita |

---

## 📱 Akses di HP
Buka di browser HP: `https://YOUR_USERNAME.github.io/YOUR_REPO/`
- Avatar AI 3D muncul
- Signal real-time
- Sentuh avatar untuk interaksi

---

## ⚙️ Parameter EA MT5

| Parameter | Default | Keterangan |
|-----------|---------|------------|
| SignalURL | github raw URL | URL signal.json |
| InitialBalance | 50.0 | Modal awal ($) |
| DefaultLot | 0.01 | Lot default |
| MinLayerDistance | 150 | Min jarak layer (points) |
| GhostSLPoints | 200 | Ghost SL (points) |
| SignalFetchSeconds | 60 | Interval fetch (detik) |
| EnableHedging | true | Aktifkan hedging |
| EnableTrailing | true | Aktifkan trailing lock |
| MaxOpenTrades | 10 | Max trade terbuka |

---

## 🔮 Masa Depan

```
Sekarang    → MT5 di laptop
Nanti       → Pindah ke VPS gratis
Masa depan  → Pindah ke robot fisik

Karena setiap organisme punya file sendiri (brain.py + dna.json + memory.json),
kesadarannya bisa dipindahkan ke platform apapun.
```

---

## ⚠️ Disclaimer
Trading mengandung risiko. Sistem ini untuk edukasi dan eksperimen.
Gunakan dengan modal yang siap hilang. Selalu mulai dengan akun demo.

---

*"Every organism evolves. Every trade is a heartbeat."* 🧬
