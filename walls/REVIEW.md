# Walls — Jolly Jelly V2.1 "Long Week? Treat Secured!" (PREVIEW)

23.3 s · 1080×1920 · 30 fps · 10 shot + 1 freeze-frame · **semua bunyi asal video dibuang** · tiada BGM.
Ikut storyline V2, storyboard 6 beat dan KOL brief (ITTIFY / Wall's Jolly Jelly Grape & Apple).
V1 disimpan di `archive/v1.html`. Klip-klip V2 dah dikodkan semula tanpa audio, jadi V1 perlu klip asal di-transcode semula kalau nak render balik.

## Beat → shot (V2.1)

| Beat | Masa | Shot | Teks on-screen |
| --- | --- | --- | --- |
| 1 | 0–2.95 | 0230 (penat) → 0231 (termenung) | Long week? + titis peluh |
| 2 | 2.95–5.6 | 0234 (tarik dari beg) | I deserve a little treat + hati |
| 3 | 5.6–9.8 | 0268 reveal slow-mo 0.75× → 0275 close-up gigitan | Wait... jelly inside?! + sticker |
| 4 | 9.8–13.3 | 0273 gigit → 0282 **WOW** | Okay, this hits different |
| 5 | 13.3–16.8 | 0286 termenung santai | Little treat, better mood |
| 6 | 16.8–23.3 | 0228 hero pack (flash glow) → 0264 senyum tunjuk aiskrim (slow-mo + freeze) | Treat to Glow → You happy, you glow! + CTA storyboard |

Perubahan dari V2 (ikut permintaan):
- Buang klip berulang: 0233 (close-up pack kedua) dan 0284 (senyum, sama dengan klip penutup).
- Buang 0294 (gelak tutup mata).
- Klip penutup: 0264, senyum tunjuk aiskrim. Dimainkan 0.5× lepas tu freeze-frame (`assets/stills/end_0264.jpg`) supaya CTA cukup masa dibaca.
- Reaction WOW:
  - Ramp slow-mo 0.5× masuk ke "wow"
  - Flash putih + punch-in 1.2× berpusat pada muka + gegaran kamera
  - Garis "terkejut" ala komik di atas dan sisi kepala, tanda "!!", letupan kilauan
  - Teks slam bergegar
  - SFX: punch + thud + glass ting + clack
- Close-up gigitan dan CTA storyboard dikekalkan.

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
3. **Beat 1:** Storyboard tunjuk main telefon. Footage yang ada cuma duduk termenung.

## Kredit

SFX: Kenney (kenney.nl), CC0.
