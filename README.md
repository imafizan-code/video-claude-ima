# Jom Naik! 🚆💖

Teman tren comel untuk pengguna pengangkutan awam Lembah Klang.

- **🧭 Rancang** — pilih stesen mula & destinasi (atau 📍 stesen terdekat), dapat laluan langkah demi langkah:
  naik apa, arah mana, tukar di mana, berapa stesen & anggaran masa. Ada pilihan *Paling cepat*, *Kurang tukar* & *Tanpa KTM*.
  Kalau laluan guna KTM, app cari **tren KTM sebenar seterusnya** ikut jadual rasmi.
- **🗺️ Peta** — semua laluan LRT (Ampang, Sri Petaling, Kelana Jaya, Shah Alam), MRT (Kajang, Putrajaya), Monorel, BRT Sunway
  & KTM Komuter (Pelabuhan Klang, Seremban) atas peta sebenar, dengan **tren KTM live** bergerak.
- **⏱️ KTM Live** — papan berlepas mana-mana stesen KTM (Komuter, ETS, Intercity) dengan status live,
  kedudukan tren semasa & anggaran lewat.
- **🚇 Laluan** — rajah setiap laluan, stesen pertukaran & kekerapan tren sekarang.

## Jalankan

Ini app web statik — tiada build. Buka melalui mana-mana server statik:

```bash
python3 -m http.server 8000
# buka http://localhost:8000
```

Boleh juga dihos di GitHub Pages / Netlify / Vercel terus dari folder ini.

## Data

| Data | Sumber |
|---|---|
| Stesen, laluan, bentuk landasan, kekerapan LRT/MRT/Monorel/BRT | GTFS Static Prasarana Rapid Rail KL — data.gov.my |
| Stesen & jadual KTM | GTFS Static KTMB — data.gov.my |
| Kedudukan tren KTM masa nyata | GTFS Realtime KTMB — `api.data.gov.my/gtfs-realtime/vehicle-position/ktmb` (dibaca terus dari browser setiap 30 saat) |

Kemas kini data statik (jadual KTM tamat tempoh berkala):

```bash
python3 scripts/build_data.py   # jana semula data/transit.js
```

### Nota
- Masa LRT/MRT ialah anggaran berdasarkan kekerapan (headway) GTFS — Prasarana tiada data live awam untuk rel.
- Anggaran lewat KTM dikira dengan membandingkan kedudukan GPS tren dengan jadual; sekadar panduan.
- Laluan pejalan kaki antara stesen berlainan nama (cth. KL Sentral ↔ Muzium Negara, Pasar Seni ↔ KTM Kuala Lumpur)
  ditetapkan dalam `scripts/build_data.py` (`WALK_LINKS`).
- Peta: © OpenStreetMap contributors.
