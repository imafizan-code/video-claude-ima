# Walls — Jolly Jelly V2.2 "Long Week? Treat Secured!" (PREVIEW)

23.35 s · 1080×1920 · 30 fps · 9 shot · **semua bunyi asal video dibuang** · tiada BGM.
Ikut storyline V2, storyboard 6 beat dan KOL brief (ITTIFY / Wall's Jolly Jelly Grape & Apple).
V1 disimpan di `archive/v1.html`. Klip-klip V2 dah dikodkan semula tanpa audio, jadi V1 perlu klip asal di-transcode semula kalau nak render balik.

## Beat → shot (V2.2)

| Beat | Masa | Shot | Teks / efek |
| --- | --- | --- | --- |
| 1 | 0–2.95 | 0290 (berdiri di taman, tangan di dada, hembus nafas / termenung) | Long week? + awan serabut atas kepala dengan ikon kerja (emel 99+, kalendar MON, jam berpusing, sticky "deadline!"). Semua pop jadi hati di 2.4 s. |
| 2 | 2.95–5.6 | 0234 (tarik dari beg) | I deserve a little treat + hati |
| 3 | 5.6–9.8 | 0268 reveal slow-mo → 0275 close-up gigitan | Wait... jelly inside?! + sticker |
| 4 | 9.8–13.3 | 0273 gigit → 0282 WOW (slow-mo, flash, punch-in, gegar, garis terkejut, kilauan) | Okay, this hits different |
| 5 | 13.3–16.8 | 0286 termenung santai | Little treat, better mood |
| 6 | 16.8–23.35 | 0228 hero pack → 0296 senyum hulur pack ke kamera | Treat to Glow → You happy, you glow! + CTA. Masa pack dihulur: punch-in, ring doodle di hujung pack, letupan kilauan. |

Perubahan V2.2 (ikut permintaan):
- **Pembuka 0–3 s:** 0230/0231 dibuang, diganti dengan 0290. Animasi "stres fikir kerja" diletak di ruang langit atas kepala (y 250–560). Muka di y 670–975, jadi tak tertutup.
- **Penutup:** 0296 senyum tunjuk aiskrim, dengan efek ketika pack dihulur. 0264 dan freeze-frame dibuang.
- **Beautify (light makeup):** dibuat pada 0290, 0273, 0282, 0286, 0296 dengan `tools/beautify.py`:
  - MediaPipe Face Mesh, landmark dilicinkan antara frame supaya tak berkelip
  - Kulit dilicinkan sikit dengan tekstur dikekalkan, lif +4 L
  - Lipstick rose-red (#C0394E) yang padan dengan cardigan merah, kekuatan 0.45; bahagian dalam mulut dikecualikan, jadi gigi tak terwarna
  - Blush halus pada pipi
  - Muka dikesan dalam 100% frame

## Ikut brief

- **Produk:** Pack dan logo jelas dalam beat 2 dan 6. Shot hero tak menutup logo.
- **Shot yang dielak:** tiada produk terbalik, cair, atau separuh dimakan. Satu shot gigitan kecil (0275) dikekalkan sebab storyboard minta "bitten open showing jelly".
- **Warna:** Klip iPhone sebenarnya HDR (HLG). Klip ditukar ke SDR Rec.709 (tone-map hable), lepas tu grading ringan: exposure +0.06, shadows +0.08, highlights −0.05, vibrance +0.12. Hasilnya cerah dan bersih ikut brief.
- **Fakta produk:** Teks lapisan (chewy grape jelly, nata de coco) diambil dari slide Product Details dalam brief.
- **Bahasa:** Teks on-screen dalam English ikut storyboard.

## Look (beza dengan V1)

- **Font:** tulisan tangan Caveat Brush, isi putih dengan outline berry.
- **Doodle:** putih (hati, kilauan, titis peluh, anak panah, garis) yang "dilukis" atas skrin, ganti emoji dalam storyboard.
- **Sticker:** putih untuk label, guna font Nunito 900.
- **Transisi:** flash "glow" masuk ke payoff, dan fade cerah di hujung.

## Muka & safe zone

- **Jalur teks:** semua teks di jalur bawah dagu (y ≈ 1000–1440) atau atas kepala (y 236–520), dipilih ikut shot.
- **Kotak safe zone:** x 120–960, y 220–1440.
- **Semakan:** disemak pada 12 snapshot dengan kotak safe zone dilukis di atasnya.

## Audio

- **Bunyi asal:** semua video di-mute.
- **SFX:** cuma Kenney CC0 foley (wrapper, kain, glass ting, pluck, thud lembut, clack), setiap satu kena dengan aksi atas skrin.
- **BGM:** belum ada. Cadangan: tambah lagu trending terus dalam TikTok/IG.
- Bunyi diukur, **tidak didengar**.

## Warning yang dikekalkan

- **`contrast_aa_failure`** pada "Long week?" dan "you glow!": checker cuma kira warna isi tulisan berbanding latar. Outline berry 16px yang memberi kontras sebenar tak dikira. Atas skrin tulisan tu jelas.
- **Warning WebGL "GPU stall":** datang dari laluan grading. Tak jejaskan video.

## Perlu kau semak

1. **CTA:** Storyboard guna "Get your Wall's Jolly Jelly treat today!". Brief guna "Take a happy bite and Treat to Glow with Wall's Jolly Jelly!" dan minta elak hard selling. Pilih mana satu.
2. **Shot gigitan 0275:** Brief ada larangan "half-eaten shots". Gigitannya kecil, tapi kau tentukan sama ada okay.
3. **Beautify:** Kalau nak lipstick lebih pekat atau lebih natural, ubah `--lip` dalam `tools/beautify.py` (0.45 sekarang).

## Kredit

SFX: Kenney (kenney.nl), CC0.
