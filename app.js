/* Jom Naik! — teman tren Lembah Klang
 * Data statik: window.TRANSIT (scripts/build_data.py, GTFS data.gov.my)
 * Data live  : GTFS Realtime kedudukan tren KTMB (api.data.gov.my)
 */
(() => {
  "use strict";
  const T = window.TRANSIT;
  const RT_URL = "https://api.data.gov.my/gtfs-realtime/vehicle-position/ktmb/";
  const $ = (s, el = document) => el.querySelector(s);
  const $$ = (s, el = document) => [...el.querySelectorAll(s)];
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const store = {
    get(k, d) { try { const v = localStorage.getItem("jomnaik:" + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
    set(k, v) { try { localStorage.setItem("jomnaik:" + k, JSON.stringify(v)); } catch { /* abaikan */ } },
  };

  // ---------------------------------------------------------------- indeks
  const lineById = Object.fromEntries(T.lines.map((l) => [l.id, l]));
  const placeById = Object.fromEntries(T.places.map((p) => [p.id, p]));
  const nodes = T.nodes;
  const nodePos = {}; // nodeId -> index dalam laluan
  T.lines.forEach((l) => l.stations.forEach((n, i) => (nodePos[n] = i)));
  const placeLines = (p) => [...new Set(p.nodes.map((n) => nodes[n].line))];
  const ktmStopPlace = {}; // stop_id KTM -> place
  Object.values(nodes).forEach((n) => { if (n.ktm) ktmStopPlace[n.ktm] = n.place; });

  // ---------------------------------------------------------------- masa Malaysia
  const fmtParts = new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Kuala_Lumpur", year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", second: "2-digit", weekday: "short", hour12: false,
  });
  function myNow(d = new Date()) {
    const p = Object.fromEntries(fmtParts.formatToParts(d).map((x) => [x.type, x.value]));
    const h = +p.hour % 24;
    return {
      sec: h * 3600 + +p.minute * 60 + +p.second,
      date: `${p.year}${p.month}${p.day}`,
      dow: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(p.weekday), // 0 = Isnin
    };
  }
  function shiftDate(yyyymmdd, days) {
    const d = new Date(Date.UTC(+yyyymmdd.slice(0, 4), +yyyymmdd.slice(4, 6) - 1, +yyyymmdd.slice(6, 8)));
    d.setUTCDate(d.getUTCDate() + days);
    return d.toISOString().slice(0, 10).replace(/-/g, "");
  }
  const hhmm = (sec) => {
    sec = ((Math.round(sec / 60) * 60) % 86400 + 86400) % 86400;
    return `${String(Math.floor(sec / 3600)).padStart(2, "0")}:${String(Math.floor((sec % 3600) / 60)).padStart(2, "0")}`;
  };
  const mins = (sec) => Math.max(0, Math.round(sec / 60));
  const durTxt = (sec) => {
    const m = mins(sec);
    return m >= 60 ? `${Math.floor(m / 60)} jam ${m % 60} min` : `${m} min`;
  };

  // ---------------------------------------------------------------- UI kecil
  function toast(msg) {
    const t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toast._t);
    toast._t = setTimeout(() => t.classList.remove("show"), 2600);
  }
  const lineBadge = (lid) => {
    const l = lineById[lid];
    return `<span class="lb" style="background:${l.color};color:${l.text}" title="${esc(l.name)}">${l.id}</span>`;
  };
  const badgesFor = (place) => `<span class="badges">${placeLines(place).map(lineBadge).join("")}</span>`;

  function greet() {
    const { sec } = myNow();
    const h = sec / 3600;
    const g = h < 5 ? "Lewat malam ni 🌙 hati-hati balik!" : h < 12 ? "Selamat pagi! ☀️ Jom gerak!" : h < 15 ? "Selamat tengah hari! 🍱" : h < 19 ? "Selamat petang! 🌇" : "Selamat malam! 🌙";
    $("#greet").textContent = g;
    $("#clock").textContent = hhmm(sec);
  }
  greet();
  setInterval(greet, 15000);

  // ---------------------------------------------------------------- tabs
  let mapReady = false;
  function showView(v) {
    $$(".tab").forEach((b) => b.classList.toggle("active", b.dataset.view === v));
    $$(".view").forEach((s) => s.classList.toggle("active", s.id === "view-" + v));
    if (v === "map") { initMap(); setTimeout(() => map.invalidateSize(), 60); }
    if (v === "ktm") renderDepartures();
    if (v === "lines" && !$("#line-detail").innerHTML) renderLine(store.get("line", "KJ"));
    window.scrollTo({ top: 0 });
    history.replaceState(null, "", "#" + v);
  }
  $$(".tab").forEach((b) => b.addEventListener("click", () => showView(b.dataset.view)));

  // ---------------------------------------------------------------- picker (autolengkap)
  const norm = (s) => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^a-z0-9]/g, "");
  function makePicker(root, items, onPick) {
    const input = $("input", root);
    const box = $(".suggest", root);
    let hl = 0, shown = [];
    function render() {
      const q = norm(input.value);
      shown = items.filter((it) => !q || it.key.includes(q)).sort((a, b) => (b.key.startsWith(q) - a.key.startsWith(q))).slice(0, 40);
      box.innerHTML = shown.length
        ? shown.map((it, i) => `<button type="button" class="sug${i === hl ? " hl" : ""}" data-i="${i}"><span class="nm">${esc(it.label)}</span>${it.extra || ""}</button>`).join("")
        : `<div class="sug"><span class="empty">Tak jumpa stesen tu 🥲</span></div>`;
      box.classList.add("open");
    }
    function pick(i) {
      const it = shown[i];
      if (!it) return;
      input.value = it.label;
      box.classList.remove("open");
      input.blur();
      onPick(it);
    }
    input.addEventListener("focus", () => { input.select(); hl = 0; render(); });
    input.addEventListener("input", () => { hl = 0; render(); });
    input.addEventListener("keydown", (e) => {
      if (e.key === "ArrowDown") { hl = Math.min(hl + 1, shown.length - 1); render(); e.preventDefault(); }
      else if (e.key === "ArrowUp") { hl = Math.max(hl - 1, 0); render(); e.preventDefault(); }
      else if (e.key === "Enter") { pick(hl); e.preventDefault(); }
      else if (e.key === "Escape") box.classList.remove("open");
    });
    box.addEventListener("mousedown", (e) => e.preventDefault());
    box.addEventListener("click", (e) => { const b = e.target.closest(".sug[data-i]"); if (b) pick(+b.dataset.i); });
    input.addEventListener("blur", () => setTimeout(() => box.classList.remove("open"), 120));
    return { set(label) { input.value = label; } };
  }

  const distM = (a, b) => Math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * Math.cos(3.1 * Math.PI / 180));
  function nearestPlace(lat, lon) {
    let best = null, bd = Infinity;
    T.places.forEach((p) => { const d = distM([lat, lon], [p.lat, p.lon]); if (d < bd) { bd = d; best = p; } });
    return { place: best, dist: bd };
  }
  function locate(cb) {
    if (!navigator.geolocation) return toast("Peranti ni tak sokong lokasi 😢");
    toast("Mencari lokasi anda… 🛰️");
    navigator.geolocation.getCurrentPosition(
      (pos) => cb(pos.coords.latitude, pos.coords.longitude),
      () => toast("Tak dapat akses lokasi. Benarkan lokasi dalam browser ya 📍"),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  }
  // ---- kekerapan
  function headway(lid, sec, dow) {
    const l = lineById[lid];
    if (!l.headway) return { hw: 30 * 60, open: true, ktm: true };
    const svc = dow <= 4 ? "MonFri" : dow === 5 ? "Sat" : "Sun";
    const rows = l.headway[svc] || l.headway.MonFri;
    for (const [a, b, h] of rows) if (sec >= a && sec < b) return { hw: h, open: true };
    // di luar waktu operasi
    const first = rows.length ? rows[0][0] : 6 * 3600;
    return { hw: rows.length ? rows[0][2] : 600, open: false, opensAt: first };
  }

  // ---- graf
  const XFER_MIN = 3 * 60;
  function walkSecs(a, b) {
    const d = distM([nodes[a].lat, nodes[a].lon], [nodes[b].lat, nodes[b].lon]);
    return Math.max(XFER_MIN, Math.round(120 + d / 1.1));
  }
  const adj = {};
  Object.keys(nodes).forEach((n) => (adj[n] = []));
  T.lines.forEach((l) => {
    for (let i = 0; i + 1 < l.stations.length; i++) {
      const a = l.stations[i], b = l.stations[i + 1], s = l.secs[i];
      adj[a].push({ to: b, kind: "ride", secs: s, line: l.id });
      adj[b].push({ to: a, kind: "ride", secs: s, line: l.id });
    }
  });
  T.places.forEach((p) => {
    p.nodes.forEach((a) => p.nodes.forEach((b) => {
      if (a !== b && nodes[a].line !== nodes[b].line) adj[a].push({ to: b, kind: "xfer", secs: walkSecs(a, b) });
    }));
  });
  T.walks.forEach(([pa, pb, m, note]) => {
    placeById[pa].nodes.forEach((a) => placeById[pb].nodes.forEach((b) => {
      adj[a].push({ to: b, kind: "walk", secs: m * 60, note });
      adj[b].push({ to: a, kind: "walk", secs: m * 60, note });
    }));
  });

  // ---- jadual KTM
  const ktmTripsByStop = {};
  T.ktm.trips.forEach((t) => {
    t.idx = {};
    t.st.forEach((s, i) => { t.idx[s[0]] = i; (ktmTripsByStop[s[0]] ||= []).push(t); });
    t.num = (t.id.match(/(\d+)$/) || [, t.id])[1];
    t.headsign = T.ktm.stops[t.st[t.st.length - 1][0]][0];
  });
  function activeServices(date, dow) {
    const key = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][dow];
    let set = new Set(T.ktm.calendar.filter((c) => c[key] === "1" && c.start_date <= date && date <= c.end_date).map((c) => c.service_id));
    let stale = false;
    if (!set.size) { // jadual dah tamat tempoh: guna corak hari
      stale = true;
      set = new Set(T.ktm.calendar.filter((c) => c[key] === "1").map((c) => c.service_id));
    }
    T.ktm.calendarDates.forEach(([sid, d, ex]) => { if (d === date) ex === 1 ? set.add(sid) : set.delete(sid); });
    return { set, stale };
  }
  // senarai {trip, dep, arr(di 'toStop')} dengan masa relatif hari ini
  function ktmCandidates(stopId, now, toStop) {
    const today = activeServices(now.date, now.dow);
    const yest = activeServices(shiftDate(now.date, -1), (now.dow + 6) % 7);
    const out = [];
    for (const t of ktmTripsByStop[stopId] || []) {
      const i = t.idx[stopId];
      if (i === t.st.length - 1) continue; // tren tamat di sini
      let j = null;
      if (toStop != null) { j = t.idx[toStop]; if (j == null || j <= i) continue; }
      const dep = t.st[i][2], arr = j != null ? t.st[j][1] : null;
      if (today.set.has(t.s)) out.push({ trip: t, dep, arr });
      if (yest.set.has(t.s) && dep >= 86400) out.push({ trip: t, dep: dep - 86400, arr: arr != null ? arr - 86400 : null });
    }
    out.sort((a, b) => a.dep - b.dep);
    return { list: out, stale: today.stale };
  }

  // "now" yang dianjak ke hari lain (untuk masa > 24:00)
  function atTime(now, t) {
    const off = Math.floor(t / 86400);
    return { date: shiftDate(now.date, off), dow: ((now.dow + off) % 7 + 7) % 7, sec: t - off * 86400, off };
  }
  // cari tren KTM seterusnya dari masa t (boleh langkau ke esok)
  function nextKtm(fromStop, toStop, now, t) {
    for (let extra = 0; extra < 2; extra++) {
      const n2 = atTime(now, t);
      if (extra) { n2.date = shiftDate(n2.date, 1); n2.dow = (n2.dow + 1) % 7; n2.off += 1; n2.sec = 0; }
      const { list, stale } = ktmCandidates(fromStop, n2, toStop);
      const fut = list.filter((c) => c.dep >= n2.sec).map((c) => ({ ...c, dep: c.dep + n2.off * 86400, arr: c.arr + n2.off * 86400 }));
      if (fut.length) return { next: fut[0], after: fut.slice(1, 3), stale, tomorrow: n2.off > atTime(now, now.sec).off };
    }
    return { next: null, after: [], stale: false };
  }

  // ---- carian jadual KTM penuh (Komuter + ETS + Intercity, boleh tukar tren)
  const PSEUDO_LINES = {
    ETS: { id: "ETS", name: "KTM ETS", kind: "KTM", color: "#FFC72C", text: "#3b2a00" },
    IC: { id: "IC", name: "KTM Intercity", kind: "KTM", color: "#6E6E6E", text: "#fff" },
  };
  Object.values(PSEUDO_LINES).forEach((l) => (lineById[l.id] ||= l));
  const lineOfTrip = (t) => (t.r === "KA15_KD19" ? "KA" : t.r === "KC05_KB18" ? "KC" : t.r === "ETS" ? "ETS" : "IC");
  function ktmNode(lid, sid) {
    const id = `K:${lid}:${sid}`;
    if (!nodes[id]) {
      const st = T.ktm.stops[sid];
      nodes[id] = { id, line: lid, name: st[0], code: "", lat: st[1], lon: st[2], ktm: sid };
    }
    return id;
  }
  const connCache = {};
  function connsAround(now) {
    if (connCache[now.date]) return connCache[now.date];
    const out = [];
    let stale = false;
    for (const off of [-1, 0, 1]) {
      const date = shiftDate(now.date, off), dow = ((now.dow + off) % 7 + 7) % 7;
      const act = activeServices(date, dow);
      if (off === 0) stale = act.stale;
      for (const t of T.ktm.trips) {
        if (!act.set.has(t.s)) continue;
        for (let i = 0; i + 1 < t.st.length; i++) {
          const dep = t.st[i][2] + off * 86400, arr = t.st[i + 1][1] + off * 86400;
          if (arr < 0) continue;
          out.push({ trip: t, i, dep, arr, from: t.st[i][0], to: t.st[i + 1][0] });
        }
      }
    }
    out.sort((a, b) => a.dep - b.dep || a.arr - b.arr);
    return (connCache[now.date] = { conns: out, stale });
  }
  const KTM_CHANGE = 4 * 60;
  // Connection Scan berpusingan: tiba paling awal, dengan paling sedikit tukar tren
  function ktmJourney(from, to, now, t, opts = {}) {
    const { conns, stale } = connsAround(now);
    let lo = 0, hi = conns.length;
    while (lo < hi) { const m = (lo + hi) >> 1; if (conns[m].dep < t) lo = m + 1; else hi = m; }
    const horizon = t + 12 * 3600;
    let prevArr = { [from]: t - KTM_CHANGE };
    const rounds = [];
    const best = {};
    for (let k = 1; k <= 4; k++) {
      const arr = {}, ptr = {}, enter = {};
      for (let q = lo; q < conns.length; q++) {
        const c = conns[q];
        if (c.dep > horizon) break;
        const key = c.trip.id + "@" + Math.round((c.dep - c.trip.st[c.i][2]) / 86400);
        if (!enter[key]) {
          const a = prevArr[c.from];
          if (a == null || a + KTM_CHANGE > c.dep) continue;
          enter[key] = c;
        }
        if (arr[c.to] == null || c.arr < arr[c.to]) { arr[c.to] = c.arr; ptr[c.to] = { enter: enter[key], exit: c }; }
      }
      rounds.push({ arr, ptr, prev: prevArr });
      for (const x in arr) if (best[x] == null || arr[x] < best[x]) best[x] = arr[x];
      // round seterusnya boleh bermula dari mana-mana stesen yang dah dicapai
      const merged = { ...prevArr };
      for (const x in arr) if (merged[x] == null || arr[x] < merged[x]) merged[x] = arr[x];
      prevArr = merged;
    }
    if (opts.full) return { arr: best };
    if (best[to] == null) return null;
    // pilih round terkecil yang tiba ≤ 5 min daripada yang terbaik
    let k = rounds.findIndex((r) => r.arr[to] != null && r.arr[to] <= best[to] + 300);
    const legs = [];
    let x = to;
    while (x !== from && k >= 0) {
      const r = rounds[k];
      const p = r.ptr[x];
      if (!p) { k--; continue; } // dicapai dalam round lebih awal
      legs.unshift({ trip: p.enter.trip, i: p.enter.i, j: p.exit.i + 1, dep: p.enter.dep, arr: p.exit.arr });
      x = p.enter.from;
      k--;
      // cari round terkecil yang mencapai x sebelum naik tren
      while (k >= 0 && x !== from) {
        let kk = -1;
        for (let z = 0; z <= k; z++) if (rounds[z].arr[x] != null && rounds[z].arr[x] + KTM_CHANGE <= legs[0].dep) { kk = z; break; }
        k = kk;
        break;
      }
    }
    if (x !== from) return null;
    return { legs, stale };
  }

  // ================================================================ PERANCANG PINTU-KE-PINTU
  // Lokasi: { name, sub, lat, lon, kind: "gps"|"place"|"station"|"stop", pid? }
  const B = window.BUS || { stops: [], pats: [] };
  const WALK_MS = 1.2;          // kelajuan jalan kaki (m/s)
  const WALK_DETOUR = 1.3;      // jalan sebenar lebih panjang daripada garis lurus
  const walkSecsM = (m) => Math.round((m * WALK_DETOUR) / WALK_MS);
  const BUS_KIND = {
    rapid: { label: "Bas RapidKL", emoji: "🚌" },
    feeder: { label: "Bas Perantara MRT", emoji: "🚐" },
    gokl: { label: "Bas GoKL", emoji: "🚌" },
  };

  // ---- indeks hentian (rel + bas) dengan grid ruang
  const SK = []; // senarai hentian: {key, lat, lon, name, code, type:"rail"|"bus", node?, bi?}
  const skIndex = {};
  Object.values(nodes).forEach((n) => {
    if (n.id.startsWith("K:")) return;
    skIndex[n.id] = SK.length;
    SK.push({ key: n.id, lat: n.lat, lon: n.lon, name: n.name, code: n.code, type: "rail", node: n.id });
  });
  B.stops.forEach(([name, lat, lon, code], i) => {
    skIndex["B" + i] = SK.length;
    SK.push({ key: "B" + i, lat, lon, name, code, type: "bus", bi: i });
  });
  const GRID = 0.005; // ~550 m
  const grid = {};
  const gkey = (lat, lon) => `${Math.floor(lat / GRID)},${Math.floor(lon / GRID)}`;
  SK.forEach((s, i) => (grid[gkey(s.lat, s.lon)] ||= []).push(i));
  function stopsNear(lat, lon, radius) {
    const out = [];
    const r = Math.ceil(radius / 550);
    const gi = Math.floor(lat / GRID), gj = Math.floor(lon / GRID);
    for (let a = gi - r; a <= gi + r; a++) for (let b = gj - r; b <= gj + r; b++) {
      for (const i of grid[`${a},${b}`] || []) {
        const d = distM([lat, lon], [SK[i].lat, SK[i].lon]);
        if (d <= radius) out.push([i, d]);
      }
    }
    return out.sort((x, y) => x[1] - y[1]);
  }

  // ---- corak perjalanan (pattern): rel RapidKL (2 arah) + bas
  const PAT = []; // {mode:"rail"|"bus", line?, bus?, stops:[skIdx], cum:[sec]}
  const patsAt = SK.map(() => []); // skIdx -> [[patIdx, pos]]
  function addPat(p) {
    const id = PAT.length;
    PAT.push(p);
    p.stops.forEach((s, pos) => patsAt[s].push([id, pos]));
  }
  T.lines.forEach((l) => {
    if (l.kind === "KTM") return; // KTM guna jadual sebenar
    const cum = [0];
    l.secs.forEach((s) => cum.push(cum[cum.length - 1] + s));
    const fw = l.stations.map((n) => skIndex[n]);
    addPat({ mode: "rail", line: l.id, stops: fw, cum, towards: nodes[l.stations[l.stations.length - 1]].name });
    const total = cum[cum.length - 1];
    addPat({ mode: "rail", line: l.id, stops: [...fw].reverse(), cum: [...cum].reverse().map((c) => total - c), towards: nodes[l.stations[0]].name });
  });
  B.pats.forEach((bp, i) => {
    bp.hwArr = bp.hw.map((s) => s.split(",").map(Number));
    addPat({ mode: "bus", bus: i, stops: bp.s.map((x) => skIndex["B" + x]), cum: bp.t.map((x) => x * 10), towards: bp.h, loopHalf: bp.k === "gokl" ? Math.ceil(bp.s.length / 2) : null });
  });

  // ---- pautan jalan kaki antara hentian (≤ 350 m) + pertukaran rasmi stesen
  const WALK_LINK_M = 350;
  const walkAdj = SK.map(() => []);
  SK.forEach((s, i) => {
    for (const [j, d] of stopsNear(s.lat, s.lon, WALK_LINK_M)) if (j !== i) walkAdj[i].push([j, walkSecsM(d) + 30]);
  });
  Object.entries(adj).forEach(([n, es]) => es.forEach((e) => {
    if (e.kind === "ride" || skIndex[n] == null || skIndex[e.to] == null) return;
    walkAdj[skIndex[n]].push([skIndex[e.to], e.secs, e.note]);
  }));
  // KTM: stop_id -> skIdx (nod KA/KC)
  const ktmSk = {};
  Object.values(nodes).forEach((n) => { if (n.ktm && !n.id.startsWith("K:") && ktmSk[n.ktm] == null) ktmSk[n.ktm] = skIndex[n.id]; });

  // kekerapan bas (saat) pada masa t; null = tiada servis dalam 3 jam
  function busWait(bp, at) {
    const arr = bp.hwArr[at.dow <= 4 ? 0 : at.dow === 5 ? 1 : 2];
    const h = Math.floor(at.sec / 3600) % 24;
    if (arr[h]) return { wait: (arr[h] * 60) / 2, hw: arr[h] * 60 };
    for (let k = 1; k <= 3; k++) {
      const hh = (h + k) % 24;
      if (arr[hh]) return { wait: (Math.floor(at.sec / 3600) + k) * 3600 - at.sec + 5 * 60, hw: arr[hh] * 60, closed: true };
    }
    return null;
  }
  function railWait(lid, at) {
    const h = headway(lid, at.sec, at.dow);
    if (h.open) return { wait: h.hw / 2, hw: h.hw };
    const w = (h.opensAt - at.sec + 86400) % 86400 + 60;
    return w <= 6 * 3600 ? { wait: w, hw: h.hw, closed: true } : null;
  }

  // ---- binary heap kecil
  class Heap {
    constructor() { this.a = []; }
    push(x) { const a = this.a; a.push(x); let i = a.length - 1; while (i) { const p = (i - 1) >> 1; if (a[p][0] <= a[i][0]) break; [a[p], a[i]] = [a[i], a[p]]; i = p; } }
    pop() {
      const a = this.a, top = a[0], last = a.pop();
      if (a.length) { a[0] = last; let i = 0; for (;;) { const l = 2 * i + 1, r = l + 1; let m = i; if (l < a.length && a[l][0] < a[m][0]) m = l; if (r < a.length && a[r][0] < a[m][0]) m = r; if (m === i) break; [a[m], a[i]] = [a[i], a[m]]; i = m; } }
      return top;
    }
    get size() { return this.a.length; }
  }

  // ---- carian utama: Dijkstra bergantung masa, kos umum
  function route(from, to, now, prm) {
    const N = SK.length;
    const cost = new Float64Array(N).fill(Infinity), time = new Float64Array(N), prev = new Array(N), boards = new Uint8Array(N);
    const heap = new Heap();
    const t0 = now.sec;
    for (const [i, d] of stopsNear(from.lat, from.lon, prm.maxWalk)) {
      const w = walkSecsM(d);
      const c = w * prm.walkF;
      if (c < cost[i]) { cost[i] = c; time[i] = t0 + w; prev[i] = { kind: "walk", from: -1, secs: w, m: d }; heap.push([c, i]); }
    }
    const destStops = new Map(stopsNear(to.lat, to.lon, prm.maxWalk).map(([i, d]) => [i, d]));
    let best = { cost: Infinity };
    const done = new Uint8Array(N);
    while (heap.size) {
      const [c, u] = heap.pop();
      if (done[u] || c > cost[u]) continue;
      done[u] = 1;
      if (c >= best.cost) break;
      if (destStops.has(u)) {
        const d = destStops.get(u), w = walkSecsM(d), tc = c + w * prm.walkF;
        if (tc < best.cost) best = { cost: tc, stop: u, arr: time[u] + w, walk: w, m: d };
      }
      const tu = time[u];
      const relax = (v, nc, nt, p, nb) => {
        if (nc < cost[v]) { cost[v] = nc; time[v] = nt; prev[v] = p; boards[v] = nb; heap.push([nc, v]); }
      };
      // jalan kaki (tak benarkan dua jalan kaki berturut)
      if (!prev[u] || prev[u].kind !== "walk") {
        for (const [v, s, note] of walkAdj[u]) relax(v, c + s * prm.walkF, tu + s, { kind: "walk", from: u, secs: s, note }, boards[u]);
      }
      if (boards[u] >= prm.maxBoards) continue;
      const at = atTime(now, tu);
      // naik bas / rel RapidKL
      for (const [pi, pos] of patsAt[u]) {
        const p = PAT[pi];
        if (p.mode === "bus" && prm.noBus) continue;
        const bp = p.mode === "bus" ? B.pats[p.bus] : null;
        const w = bp ? busWait(bp, at) : railWait(p.line, at);
        if (!w) continue;
        const board = tu + w.wait;
        const maxPos = p.loopHalf ? Math.min(p.stops.length - 1, pos + p.loopHalf) : p.stops.length - 1;
        for (let k = pos + 1; k <= maxPos; k++) {
          const ride = p.cum[k] - p.cum[pos];
          const v = p.stops[k];
          relax(v, c + w.wait * prm.waitF + ride + prm.boardPen + (bp ? prm.busPen : 0), board + ride,
            { kind: "ride", from: u, pat: pi, i: pos, j: k, board, wait: w.wait, hw: w.hw, closed: w.closed }, boards[u] + 1);
        }
      }
      // KTM ikut jadual sebenar
      const sk = SK[u];
      if (sk.type === "rail" && nodes[sk.node].ktm) {
        const sid = nodes[sk.node].ktm;
        const seen = new Set();
        for (const k of [0, 1]) {
          const at2 = k ? { ...atTime(now, tu + 86400), sec: 0 } : at;
          const base = tu - at.sec + (k ? 86400 : 0);
          const { list } = ktmCandidates(sid, at2);
          for (const cnd of list) {
            const dep = base + cnd.dep;
            if (dep < tu + 60 || dep > tu + 4 * 3600) continue;
            const trip = cnd.trip, i0 = trip.idx[sid];
            if (seen.has(trip.id)) continue;
            seen.add(trip.id);
            for (let q = i0 + 1; q < trip.st.length; q++) {
              const v = ktmSk[trip.st[q][0]];
              if (v == null) continue;
              const arr = base + trip.st[q][1] + (cnd.dep - trip.st[i0][2]);
              relax(v, c + (dep - tu) * prm.waitF + (arr - dep) + prm.boardPen, arr,
                { kind: "ktm", from: u, trip, i: i0, j: q, board: dep, wait: dep - tu }, boards[u] + 1);
            }
          }
          if (seen.size) break;
        }
      }
    }
    // jalan kaki terus
    const direct = distM([from.lat, from.lon], [to.lat, to.lon]);
    const dw = walkSecsM(direct);
    if (direct <= 3000 && (best.stop == null || dw * prm.walkF <= best.cost)) {
      return { legs: [{ kind: "walk", secs: dw, m: direct, from: null, to: null, start: t0 }], start: t0, end: t0 + dw, directWalk: true };
    }
    if (best.stop == null) return null;
    // bina semula
    const legs = [];
    let x = best.stop;
    while (x !== -1 && x != null) {
      const p = prev[x];
      if (p.kind === "walk") legs.unshift({ kind: "walk", secs: p.secs, m: p.m, from: p.from === -1 ? null : p.from, to: x, note: p.note });
      else if (p.kind === "ride") {
        const P = PAT[p.pat];
        legs.unshift({ kind: P.mode, pat: p.pat, stops: P.stops.slice(p.i, p.j + 1), board: p.board, wait: p.wait, hw: p.hw, closed: p.closed, arrive: time[x], from: p.from, to: x });
      } else {
        legs.unshift({ kind: "ktm", trip: p.trip, i: p.i, j: p.j, board: p.board, wait: p.wait, arrive: time[x], from: p.from, to: x });
      }
      x = p.from;
    }
    legs.push({ kind: "walk", secs: best.walk, m: best.m, from: best.stop, to: null });
    // gabung jalan kaki berturut & isi jarak
    const out = [];
    for (const l of legs) {
      if (l.kind === "walk" && l.m == null && l.from != null && l.to != null) l.m = distM([SK[l.from].lat, SK[l.from].lon], [SK[l.to].lat, SK[l.to].lon]);
      const last = out[out.length - 1];
      if (l.kind === "walk" && last && last.kind === "walk") { last.secs += l.secs; last.m += l.m; last.to = l.to; last.note = last.note || l.note; }
      else out.push({ ...l });
    }
    // masa mula setiap langkah
    let t = t0;
    out.forEach((l) => {
      if (l.kind === "walk") { l.start = t; t += l.secs; }
      else { l.start = t; l.wait = l.board - t; t = l.arrive; }
    });
    // alternatif: naik pengangkutan awam separuh jalan, kemudian Grab
    let hybrid = null;
    const driveSecs = (km) => Math.round((km * 1.35) / 30 * 3600) + 8 * 60;
    for (let i = 0; i < N; i++) {
      if (!done[i] || boards[i] === 0) continue;
      const km = distM([SK[i].lat, SK[i].lon], [to.lat, to.lon]) / 1000;
      if (km > 30 || km < 1.5) continue;
      const eta = time[i] + driveSecs(km);
      if (!hybrid || eta < hybrid.eta) hybrid = { stop: i, at: time[i], km, eta };
    }
    const directKm = distM([from.lat, from.lon], [to.lat, to.lon]) / 1000;
    const res = { legs: out.filter((l) => !(l.kind === "walk" && l.m < 25)), start: t0, end: t, driveEta: t0 + driveSecs(directKm), directKm };
    if (hybrid && hybrid.eta < t - 30 * 60) res.hybrid = hybrid;
    return res;
  }

  // ---- lokasi & carian tempat (Photon / OpenStreetMap)
  const KV_BBOX = "101.2,2.65,102.0,3.55";
  const stopItems = SK.map((s, i) => ({ s, i, key: norm(s.name + " " + (s.code || "")) }));
  function localSuggest(q) {
    const nq = norm(q);
    if (!nq) return [];
    const places = T.places.filter((p) => norm(p.name + " " + p.nodes.map((n) => nodes[n].name).join(" ")).includes(nq))
      .sort((a, b) => norm(b.name).startsWith(nq) - norm(a.name).startsWith(nq)).slice(0, 5)
      .map((p) => ({ name: p.name, sub: "Stesen " + placeLines(p).map((l) => lineById[l].kind === "KTM" ? "KTM" : lineById[l].kind).filter((v, i, a) => a.indexOf(v) === i).join(" / "), lat: p.lat, lon: p.lon, kind: "station", pid: p.id, extra: badgesFor(p) }));
    const busStops = stopItems.filter((x) => x.s.type === "bus" && x.key.includes(nq)).slice(0, 4)
      .map(({ s }) => ({ name: s.name, sub: "🚏 Hentian bas" + (s.code ? " " + s.code : ""), lat: s.lat, lon: s.lon, kind: "stop" }));
    return [...places, ...busStops];
  }
  const isStation = (x) => x.kind === "station";
  const geoCache = {};
  async function geoSearch(q, near) {
    const k = q.trim().toLowerCase();
    if (geoCache[k]) return geoCache[k];
    const u = new URL("https://photon.komoot.io/api/");
    u.searchParams.set("q", q);
    u.searchParams.set("limit", "8");
    u.searchParams.set("bbox", KV_BBOX);
    u.searchParams.set("lat", near ? near.lat : 3.139);
    u.searchParams.set("lon", near ? near.lon : 101.687);
    let j;
    try {
      const r = await fetch(u);
      if (!r.ok) throw new Error(r.status);
      j = await r.json();
    } catch (e) {
      return (geoCache[k] = await nominatimSearch(q));
    }
    const out = j.features.map((f) => {
      const p = f.properties;
      const name = p.name || [p.housenumber, p.street].filter(Boolean).join(" ") || p.city || "Tempat";
      const sub = [p.street && p.name ? p.street : null, p.locality || p.district, p.city].filter(Boolean).filter((v, i, a) => a.indexOf(v) === i).join(", ");
      return { name, sub: sub || p.state || "", lat: f.geometry.coordinates[1], lon: f.geometry.coordinates[0], kind: "place", osm: p.osm_value };
    }).filter((x, i, a) => a.findIndex((y) => y.name === x.name && Math.abs(y.lat - x.lat) < 0.0005) === i);
    return (geoCache[k] = out);
  }
  async function nominatimSearch(q) {
    const u = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=8&countrycodes=my&viewbox=${KV_BBOX}&bounded=1&q=${encodeURIComponent(q)}`;
    const r = await fetch(u);
    if (!r.ok) throw new Error(r.status);
    return (await r.json()).map((x) => {
      const parts = x.display_name.split(", ");
      return { name: x.name || parts[0], sub: parts.slice(1, 3).join(", "), lat: +x.lat, lon: +x.lon, kind: "place" };
    });
  }
  async function reverseName(lat, lon) {
    try {
      const r = await fetch(`https://photon.komoot.io/reverse?lat=${lat}&lon=${lon}&limit=1`);
      const p = (await r.json()).features[0].properties;
      return [p.name, p.street, p.locality || p.district || p.city].filter(Boolean).slice(0, 2).join(", ");
    } catch { return null; }
  }

  function makeLocPicker(root, which) {
    const input = $("input", root), box = $(".suggest", root);
    let items = [], hl = 0, seq = 0, timer;
    const render = (loading) => {
      const q = input.value.trim();
      const head = !q ? [{ name: "📍 Lokasi saya sekarang", sub: "Guna GPS telefon", kind: "gps-req" }] : [];
      const recent = !q ? store.get("recent", []).slice(0, 5).map((r) => ({ ...r, sub: "🕘 " + (r.sub || "") })) : [];
      const all = [...head, ...recent, ...items];
      items._all = all;
      box.innerHTML = all.map((it, i) => `<button type="button" class="sug${i === hl ? " hl" : ""}" data-i="${i}"><span class="nm2"><span class="nm">${esc(it.name)}</span>${it.sub ? `<small>${esc(it.sub)}</small>` : ""}</span>${it.extra || ""}</button>`).join("")
        + (loading ? `<div class="sug"><span class="empty">🔎 Mencari tempat…</span></div>` : "")
        + (!all.length && !loading && q ? `<div class="sug"><span class="empty">Tak jumpa 🥲 Cuba nama lain / nama taman / jalan</span></div>` : "");
      box.classList.add("open");
    };
    const update = () => {
      const q = input.value.trim();
      items = localSuggest(q);
      hl = 0;
      render(q.length >= 3);
      clearTimeout(timer);
      if (q.length < 3) return;
      const my = ++seq;
      timer = setTimeout(async () => {
        try {
          const other = which === "from" ? plan.to : plan.from;
          const res = await geoSearch(q, other);
          if (my !== seq) return;
          const loc = localSuggest(q);
          items = [...loc.filter(isStation).slice(0, 3), ...res, ...loc.filter((x) => !isStation(x)).slice(0, 2)];
        } catch { if (my === seq) toast("Carian tempat gagal — periksa internet 📶"); }
        if (my === seq) render(false);
      }, 350);
    };
    const pick = (i) => {
      const it = (items._all || [])[i];
      if (!it) return;
      box.classList.remove("open");
      input.blur();
      if (it.kind === "gps-req") return useGps(which);
      setLoc(which, { name: it.name, sub: (it.sub || "").replace(/^🕘 /, ""), lat: it.lat, lon: it.lon, kind: it.kind, pid: it.pid });
    };
    input.addEventListener("focus", () => { input.select(); update(); });
    input.addEventListener("input", update);
    input.addEventListener("keydown", (e) => {
      const n = (items._all || []).length;
      if (e.key === "ArrowDown") { hl = Math.min(hl + 1, n - 1); render(false); e.preventDefault(); }
      else if (e.key === "ArrowUp") { hl = Math.max(hl - 1, 0); render(false); e.preventDefault(); }
      else if (e.key === "Enter") { pick(hl); e.preventDefault(); }
      else if (e.key === "Escape") box.classList.remove("open");
    });
    box.addEventListener("mousedown", (e) => e.preventDefault());
    box.addEventListener("click", (e) => { const b = e.target.closest(".sug[data-i]"); if (b) pick(+b.dataset.i); });
    input.addEventListener("blur", () => setTimeout(() => box.classList.remove("open"), 150));
    return { set(v) { input.value = v; } };
  }

  const plan = { from: store.get("fromLoc", null), to: store.get("toLoc", null) };
  const pickers = { from: makeLocPicker($('[data-picker="from"]'), "from"), to: makeLocPicker($('[data-picker="to"]'), "to") };
  if (plan.from) pickers.from.set(plan.from.name);
  if (plan.to) pickers.to.set(plan.to.name);
  function setLoc(which, loc, silent) {
    plan[which] = loc;
    store.set(which + "Loc", loc);
    pickers[which].set(loc ? loc.name : "");
    if (loc && loc.kind !== "gps") {
      const rec = store.get("recent", []).filter((r) => r.name !== loc.name);
      rec.unshift({ name: loc.name, sub: loc.sub, lat: loc.lat, lon: loc.lon, kind: loc.kind, pid: loc.pid });
      store.set("recent", rec.slice(0, 8));
    }
    if (!silent) maybePlan();
  }
  const placeLoc = (pid) => { const p = placeById[pid]; return { name: p.name, sub: "Stesen", lat: p.lat, lon: p.lon, kind: "station", pid }; };
  function setFrom(pid) { setLoc("from", placeLoc(pid), true); }
  function setTo(pid) { setLoc("to", placeLoc(pid), true); }
  function maybePlan() { if (plan.from && plan.to) runPlan(); }
  function useGps(which) {
    locate(async (lat, lon) => {
      setLoc(which, { name: "📍 Lokasi saya", sub: "", lat, lon, kind: "gps" }, true);
      maybePlan();
      const nm = await reverseName(lat, lon);
      if (nm && plan[which] && plan[which].kind === "gps") { plan[which].name = "📍 " + nm; pickers[which].set(plan[which].name); store.set(which + "Loc", plan[which]); }
    });
  }

  $("#swap").addEventListener("click", () => {
    const f = plan.from;
    setLoc("from", plan.to, true);
    setLoc("to", f, true);
    maybePlan();
  });
  $("#go-btn").addEventListener("click", () => {
    if (!plan.from || !plan.to) return toast("Isi tempat mula & destinasi dulu ya 🙏");
    runPlan();
  });
  $("#near-btn").addEventListener("click", () => useGps("from"));

  // ---- jalankan & papar
  let lastResult = null;
  const OPTS = [
    { id: "fast", boardPen: 180, walkF: 1.6, waitF: 1.2, busPen: 60, maxWalk: 1200, maxBoards: 5 },
    { id: "xfer", boardPen: 900, walkF: 1.6, waitF: 1.2, busPen: 60, maxWalk: 1200, maxBoards: 5 },
    { id: "walk", boardPen: 240, walkF: 3.5, waitF: 1.2, busPen: 60, maxWalk: 700, maxBoards: 5 },
    { id: "rail", boardPen: 240, walkF: 1.4, waitF: 1.2, busPen: 0, maxWalk: 2000, maxBoards: 5, noBus: true },
  ];
  function legSig(r) { return r.legs.map((l) => l.kind === "walk" ? "w" : l.kind === "ktm" ? "k" + l.trip.id : "p" + l.pat + ":" + l.stops[0]).join("|"); }
  function runPlan() {
    const out = $("#plan-result");
    if (!plan.from || !plan.to) return;
    const d = distM([plan.from.lat, plan.from.lon], [plan.to.lat, plan.to.lon]);
    if (d < 80) { out.innerHTML = `<div class="card empty-state"><span class="emo">😄</span>Eh, dah sampai pun! Tempat mula & destinasi sama.</div>`; return; }
    out.innerHTML = `<div class="card empty-state"><span class="emo">🧭</span>Sedang cari laluan terbaik…</div>`;
    setTimeout(() => {
      const now = myNow();
      const t0 = performance.now();
      let res = [];
      const seen = new Set();
      for (const prm of OPTS) {
        const r = route(plan.from, plan.to, now, prm);
        if (!r) continue;
        const sig = legSig(r);
        if (seen.has(sig)) continue;
        seen.add(sig);
        const rides = r.legs.filter((l) => l.kind !== "walk");
        r.boards = rides.length;
        r.walkM = r.legs.filter((l) => l.kind === "walk").reduce((a, l) => a + l.m, 0);
        r.prm = prm.id;
        res.push(r);
      }
      console.log("route ms", Math.round(performance.now() - t0));
      if (!res.length) {
        out.innerHTML = `<div class="card empty-state"><span class="emo">🥺</span>Alamak, tak jumpa laluan pengangkutan awam yang sesuai.<br><span class="small">Mungkin kawasan ni jauh dari bas/tren — cuba Grab/teksi.</span><div class="res-actions" style="justify-content:center;margin-top:10px">${gmapsBtn("driving")}</div></div>`;
        return;
      }
      res.sort((a, b) => a.end - b.end || a.boards - b.boards);
      const fastest = res[0];
      res = res.filter((r) => r === fastest || r.end - fastest.end < 45 * 60 || r.directWalk);
      const minB = Math.min(...res.map((r) => r.boards)), minW = Math.min(...res.map((r) => r.walkM));
      res.forEach((r, i) => {
        r.label = r.directWalk ? "🚶 Jalan kaki je" : i === 0 ? "⚡ Paling cepat" : r.boards === minB && r.boards < fastest.boards ? "🙌 Kurang tukar" : r.walkM === minW && r.walkM < fastest.walkM - 150 ? "🦶 Kurang jalan" : r.prm === "rail" ? "🚇 Tren je" : "✨ Pilihan lain";
      });
      lastResult = { opts: res.slice(0, 4), sel: 0, now };
      renderPlan();
      $("#plan-tips").style.display = "none";
    }, 30);
  }

  const fmtM = (m) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`);
  const gmapsUrl = (a, b, mode) => `https://www.google.com/maps/dir/?api=1&origin=${a.lat},${a.lon}&destination=${b.lat},${b.lon}&travelmode=${mode}`;
  function gmapsBtn(mode) {
    return `<a class="chip-btn small" target="_blank" rel="noopener" href="${gmapsUrl(plan.from, plan.to, mode)}">${mode === "driving" ? "🚗 Arah memandu / Grab" : "🗺️ Google Maps"}</a>`;
  }
  const skPt = (i) => (i == null || i < 0 ? null : { lat: SK[i].lat, lon: SK[i].lon });
  function legInfo(l) {
    if (l.kind === "rail") {
      const P = PAT[l.pat], L = lineById[P.line];
      return { color: L.color, text: L.text, badge: L.id, title: `Naik ${L.name}`, towards: P.towards, emoji: L.kind === "MRT" ? "🚇" : L.kind === "MRL" ? "🚝" : "🚈", n: l.stops.length - 1, unit: "stesen", names: l.stops.map((s) => SK[s].name), codes: l.stops.map((s) => SK[s].code) };
    }
    if (l.kind === "bus") {
      const P = PAT[l.pat], bp = B.pats[P.bus], K = BUS_KIND[bp.k];
      return { color: bp.c, text: "#fff", badge: bp.r, title: `Naik ${K.label} <b>${esc(bp.r)}</b>`, sub: bp.n, towards: bp.h, emoji: K.emoji, n: l.stops.length - 1, unit: "hentian", names: l.stops.map((s) => SK[s].name), codes: l.stops.map((s) => SK[s].code), bp };
    }
    const lid = lineOfTrip(l.trip), L = lineById[lid];
    const names = l.trip.st.slice(l.i, l.j + 1).map((x) => T.ktm.stops[x[0]][0]);
    return { color: L.color, text: L.text, badge: lid, title: `Naik ${L.name}`, towards: l.trip.headsign, emoji: lid === "ETS" ? "🚄" : "🚆", n: l.j - l.i, unit: "stesen", names, codes: names.map(() => ""), trip: l.trip };
  }

  function renderPlan() {
    const { opts, sel } = lastResult;
    const o = opts[sel];
    const total = o.end - o.start;
    const rides = o.legs.filter((l) => l.kind !== "walk");
    const walkM = o.legs.filter((l) => l.kind === "walk").reduce((a, l) => a + l.m, 0);
    const bar = o.legs.map((l) => {
      if (l.kind === "walk") return `<span style="background:#CFC3CB;flex:${Math.max(60, l.secs)}"></span>`;
      const I = legInfo(l);
      const w = l.wait > 120 ? `<span style="background:repeating-linear-gradient(90deg,#E6DAE1 0 4px,transparent 4px 7px);flex:${l.wait}"></span>` : "";
      return `${w}<span style="background:${I.color};flex:${Math.max(60, l.arrive - l.board)}"></span>`;
    }).join("");
    const modes = rides.map((l) => { const I = legInfo(l); return `<span class="lb" style="background:${I.color};color:${I.text}">${I.emoji} ${esc(I.badge)}</span>`; }).join(`<span class="muted small">›</span>`);

    let html = "";
    if (opts.length > 1) html += `<div class="opt-tabs">${opts.map((x, i) => `<button class="opt-tab${i === sel ? " active" : ""}" data-opt="${i}">${x.label} · ${durTxt(x.end - x.start)}</button>`).join("")}</div>`;
    html += `<div class="card">
      <div class="summary">
        <div class="big">${durTxt(total).replace(/(\d+) min$/, "$1<small> min</small>")}</div>
        <div class="meta">Bertolak <b>${hhmm(o.start)}</b> → tiba <b>~${hhmm(o.end)}</b><br>${o.directWalk ? "Dekat je, jalan kaki pun boleh 🚶" : `${rides.length <= 1 ? "Terus, tak payah tukar 🎉" : rides.length - 1 + " kali tukar"} · jalan ${fmtM(walkM)}`}</div>
      </div>
      ${modes ? `<div class="modes">${modes}</div>` : ""}
      <div class="linebar">${bar}</div>
      ${planNotes(o)}
      <div class="steps">`;
    const step = (time, color, cls, title, body) => `<div class="step ${cls}" style="--c:${color}"><div class="time">${time}</div><div class="rail"><span class="knob"></span></div><div class="body"><div class="st">${title}</div>${body || ""}</div></div>`;
    html += step(hhmm(o.start), "#FF8FA3", o.legs[0].kind === "walk" ? "walk" : "", `🟢 ${esc(plan.from.name)}`, plan.from.sub ? `<div class="small muted">${esc(plan.from.sub)}</div>` : "");
    o.legs.forEach((l, i) => {
      const next = o.legs[i + 1];
      if (l.kind === "walk") {
        const a = l.from == null ? plan.from : skPt(l.from), b = l.to == null ? plan.to : skPt(l.to);
        const target = l.to == null ? esc(plan.to.name) : (SK[l.to].type === "bus" ? `hentian bas <b>${esc(SK[l.to].name)}</b>${SK[l.to].code ? ` <span class="small muted">${esc(SK[l.to].code)}</span>` : ""}` : `stesen <b>${esc(SK[l.to].name)}</b>`);
        html += `<div class="step walk" style="--c:#C9B8C4"><div class="time"></div><div class="rail"></div><div class="body"><div class="what">🚶 Jalan kaki <b>${fmtM(l.m)}</b> (~${durTxt(l.secs)}) ke ${target}${l.note ? `<br><span class="small muted">${esc(l.note)}</span>` : ""}
          <div style="margin-top:6px"><a class="mini-link" target="_blank" rel="noopener" href="${gmapsUrl(a, b, "walking")}">🧭 Arah jalan kaki</a></div></div></div></div>`;
        return;
      }
      const I = legInfo(l);
      const first = I.names[0], last = I.names[I.names.length - 1];
      let extra = "";
      if (l.kind === "ktm") {
        extra = `<div class="ktm-next">🚂 Tren <b>${esc(l.trip.num)}</b> bertolak <b>${hhmm(l.board)}</b>${l.board >= 86400 ? " (esok)" : ""} · tiba ${hhmm(l.arrive)}${l.wait > 45 * 60 ? `<br><span class="small">⏳ Tren KTM jarang waktu ni — tunggu ${durTxt(l.wait)}</span>` : ""}</div>`;
      } else {
        const hwm = Math.round(l.hw / 60);
        extra = `<div class="small muted" style="margin-top:4px">${l.closed ? `🌙 Servis belum mula — anggaran bas/tren pertama ~${hhmm(l.board)}` : `${l.kind === "bus" ? "Bas" : "Tren"} setiap ~${hwm} min${I.bp && I.bp.est ? " (anggaran)" : ""} · tunggu ~${durTxt(l.wait)}`}</div>`;
        if (l.kind === "bus") extra += liveBusLine(I.bp);
      }
      const mid = I.names.slice(1, -1).map((n) => `<li>${esc(n)}</li>`).join("");
      html += step(hhmm(l.board), I.color, "", `${esc(first)} ${I.codes[0] ? `<span class="small muted">${esc(I.codes[0])}</span>` : ""}`,
        `<div class="what"><span class="lb" style="background:${I.color};color:${I.text}">${I.emoji} ${esc(I.badge)}</span> ${I.title} arah <b>${esc(I.towards)}</b>
          ${I.sub ? `<br><span class="small muted">${esc(I.sub)}</span>` : ""}
          <br><span class="muted">${I.n} ${I.unit} · ${durTxt(l.arrive - l.board)}</span>
          ${mid ? `<details><summary>Lalu ${I.names.length - 2} ${I.unit}</summary><ol>${mid}</ol></details>` : ""}
          ${extra}</div>`);
      html += step(hhmm(l.arrive), I.color, next ? "walk" : "", `Turun di ${esc(last)} ${I.codes[I.codes.length - 1] ? `<span class="small muted">${esc(I.codes[I.codes.length - 1])}</span>` : ""}`,
        l.kind === "bus" ? `<div class="small muted">💡 Tekan loceng bila nampak hentian sebelum ${esc(last)}</div>` : "");
    });
    html += step(hhmm(o.end), "#6CC1F5", "end", `🏁 Sampai ${esc(plan.to.name)}`, plan.to.sub ? `<div class="small muted">${esc(plan.to.sub)}</div>` : "");
    html += `</div>
      <div class="res-actions">
        <button class="chip-btn" id="show-on-map">🗺️ Lihat di peta</button>
        <button class="chip-btn" id="share-route">📤 Kongsi</button>
        ${gmapsBtn("driving")}
      </div>
      <div class="fare-tip">💳 Bayar dengan kad <b>Touch 'n Go</b> atau kad debit/kredit (tap) untuk bas RapidKL & tren.</div>
      <p class="small muted" style="margin:10px 0 0">Masa bas & LRT/MRT ialah anggaran ikut kekerapan GTFS. KTM ikut jadual rasmi. GoKL dari OpenStreetMap (anggaran).</p>
    </div>`;
    $("#plan-result").innerHTML = html;
    $$(".opt-tab").forEach((b) => b.addEventListener("click", () => { lastResult.sel = +b.dataset.opt; renderPlan(); }));
    $("#show-on-map").addEventListener("click", () => { showView("map"); drawRoute(o); });
    $("#share-route").addEventListener("click", () => shareRoute(o));
  }

  function planNotes(o) {
    const n = [];
    if (o.hybrid) n.push(`💡 Lebih cepat: naik sampai <b>${esc(SK[o.hybrid.stop].name)}</b> (tiba ~${hhmm(o.hybrid.at)}), kemudian Grab/teksi ~${o.hybrid.km.toFixed(0)} km — sampai ~${hhmm(o.hybrid.eta)}.`);
    if (o.legs.some((l) => l.kind === "ktm" && l.wait > 90 * 60 && ["KC", "ETS"].includes(lineOfTrip(l.trip)))) {
      n.push("ℹ️ KTMB sedang menstruktur semula jadual Lembah Klang (Apr–Dis 2026): tiada Komuter Mid Valley/BTS ↔ Pulau Sebang ~10 pagi–4 petang. Sebahagiannya diganti tren ETS.");
    }
    if (!o.directWalk && o.driveEta && o.end - o.start > 2.5 * (o.driveEta - o.start) && o.end - o.driveEta > 40 * 60) {
      n.push(`🚗 Kalau naik Grab/teksi terus (~${o.directKm.toFixed(0)} km), anggaran sampai ~${hhmm(o.driveEta)}.`);
    }
    return n.map((x) => `<div class="ktm-next warn">${x}</div>`).join("");
  }

  function shareRoute(o) {
    const lines = [`🧭 ${plan.from.name} → ${plan.to.name} (~${durTxt(o.end - o.start)})`];
    o.legs.forEach((l) => {
      if (l.kind === "walk") lines.push(`🚶 Jalan ${fmtM(l.m)}${l.to != null ? " ke " + SK[l.to].name : " ke destinasi"}`);
      else { const I = legInfo(l); lines.push(`${I.emoji} ${I.badge} arah ${I.towards}: ${I.names[0]} → ${I.names[I.names.length - 1]} (${I.n} ${I.unit})`); }
    });
    lines.push("— dirancang dengan Jom Naik! 💖 " + location.href.split("#")[0]);
    const text = lines.join("\n");
    if (navigator.share) navigator.share({ text }).catch(() => {});
    else navigator.clipboard?.writeText(text).then(() => toast("Laluan disalin 📋"), () => toast("Tak dapat salin 😅"));
  }

  // ---- bas live (GTFS Realtime Prasarana)
  const BUS_RT = [
    ["rapid", "https://api.data.gov.my/gtfs-realtime/vehicle-position/prasarana/?category=rapid-bus-kl"],
    ["feeder", "https://api.data.gov.my/gtfs-realtime/vehicle-position/prasarana/?category=rapid-bus-mrtfeeder"],
  ];
  let busLive = { at: 0, list: [], byRoute: {} };
  async function fetchBusLive() {
    const list = [];
    await Promise.all(BUS_RT.map(async ([k, url]) => {
      try {
        const r = await fetch(url, { cache: "no-store" });
        if (!r.ok) return;
        decodeFeed(await r.arrayBuffer()).forEach((v) => list.push({ ...v, k }));
      } catch { /* abaikan */ }
    }));
    const byRoute = {};
    list.forEach((v) => { const key = v.k + ":" + (v.routeId || ""); (byRoute[key] ||= []).push(v); });
    busLive = { at: Date.now(), list, byRoute };
    if (mapReady) drawBuses();
  }
  function liveBusLine(bp) {
    if (!bp || !busLive.at) return "";
    const key = bp.k === "rapid" ? "rapid:" + bp.rid : bp.k === "feeder" ? "feeder:" + bp.r : null;
    const n = key ? (busLive.byRoute[key] || []).length : 0;
    return n ? `<div class="small" style="margin-top:4px"><span class="tag live">● LIVE</span>${n} bas laluan ni sedang bergerak sekarang</div>` : "";
  }

  // ================================================================ PETA
  let map, lineLayers = {}, trainLayer, routeLayer;
  const hidden = new Set(store.get("hiddenLines", []));
  function initMap() {
    if (mapReady) return;
    if (!window.L) { $("#map").innerHTML = `<div class="empty-state"><span class="emo">🗺️</span>Peta tak dapat dimuat (tiada internet?)</div>`; return; }
    mapReady = true;
    map = L.map("map", { zoomControl: false, attributionControl: true, preferCanvas: false }).setView([3.135, 101.69], 12);
    L.control.zoom({ position: "bottomright" }).addTo(map);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> · Data: data.gov.my',
    }).addTo(map);
    map.createPane("lines").style.zIndex = 410;
    map.createPane("stations").style.zIndex = 420;
    map.createPane("route").style.zIndex = 430;
    map.createPane("trains").style.zIndex = 650;

    T.lines.forEach((l) => {
      const g = L.layerGroup();
      L.polyline(l.shape, { pane: "lines", color: "#fff", weight: 9, opacity: .9 }).addTo(g);
      L.polyline(l.shape, { pane: "lines", color: l.color, weight: 5, opacity: .95, dashArray: l.kind === "KTM" ? "1 0" : null }).addTo(g);
      lineLayers[l.id] = g;
      if (!hidden.has(l.id)) g.addTo(map);
    });
    const stLayer = L.layerGroup().addTo(map);
    T.places.forEach((p) => {
      const ls = placeLines(p);
      const big = ls.length > 1;
      const m = L.circleMarker([p.lat, p.lon], {
        pane: "stations", radius: big ? 7 : 4.5, weight: big ? 3 : 2.5,
        color: big ? "#3A2E39" : lineById[ls[0]].color, fillColor: "#fff", fillOpacity: 1,
      }).addTo(stLayer);
      m.placeId = p.id;
      m.bindTooltip(p.name, { className: "st-label", direction: "right", offset: [6, 0] });
      m.on("click", () => openStationPopup(p, m));
    });
    trainLayer = L.layerGroup().addTo(map);
    routeLayer = L.layerGroup().addTo(map);
    busRenderer = L.canvas({ padding: 0.3 });
    busStopLayer = L.layerGroup().addTo(map);
    busLiveLayer = L.layerGroup().addTo(map);
    map.on("moveend", () => { drawBusStops(); drawBuses(); });
    const lbl = () => {
      const z = map.getZoom();
      stLayer.eachLayer((m) => { const t = m.getTooltip(); if (!t) return; z >= 14 || (z >= 13 && placeLines(placeById[m.placeId]).length > 1) ? m.openTooltip() : m.closeTooltip(); });
    };
    map.on("zoomend", lbl);
    lbl();

    $("#map-chips").innerHTML = T.lines.map((l) => `<button class="mchip${hidden.has(l.id) ? " off" : ""}" data-l="${l.id}"><i style="background:${l.color}"></i>${esc(l.name.replace("KTM ", "KTM ").replace("Monorel KL", "Monorel"))}</button>`).join("")
      + `<button class="mchip${showBusLive ? "" : " off"}" id="bus-live-chip">🚌 Bas live</button><button class="mchip" id="locate-me">📍 Saya</button>`;
    $$(".mchip[data-l]").forEach((b) => b.addEventListener("click", () => {
      const id = b.dataset.l;
      if (hidden.has(id)) { hidden.delete(id); lineLayers[id].addTo(map); } else { hidden.add(id); map.removeLayer(lineLayers[id]); }
      b.classList.toggle("off", hidden.has(id));
      store.set("hiddenLines", [...hidden]);
    }));
    $("#bus-live-chip").addEventListener("click", (e) => {
      showBusLive = !showBusLive; store.set("busLive", showBusLive);
      e.currentTarget.classList.toggle("off", !showBusLive);
      drawBuses();
      if (showBusLive) fetchBusLive();
    });
    let meMarker;
    $("#locate-me").addEventListener("click", () => locate((lat, lon) => {
      if (meMarker) map.removeLayer(meMarker);
      meMarker = L.circleMarker([lat, lon], { radius: 9, color: "#fff", weight: 3, fillColor: "#3B82F6", fillOpacity: 1, pane: "trains" }).addTo(map).bindTooltip("Anda di sini 💙");
      map.setView([lat, lon], 15);
    }));
    drawTrains();
  }

  function openStationPopup(p, layer) {
    const ktmNode = p.nodes.map((n) => nodes[n]).find((n) => n.ktm);
    const html = `<div class="pop"><h4>${esc(p.name)}</h4>${badgesFor(p)}
      <div class="small muted" style="margin-top:4px">${p.nodes.map((n) => `${esc(nodes[n].name)}${nodes[n].code ? " (" + esc(nodes[n].code) + ")" : ""}`).filter((v, i, a) => a.indexOf(v) === i).join(" · ")}</div>
      <div class="btns"><button data-a="from">🟢 Dari sini</button><button data-a="to">🏁 Ke sini</button>${ktmNode ? `<button data-a="ktm">⏱️ Jadual KTM</button>` : ""}</div></div>`;
    const pop = L.popup({ offset: [0, -4] }).setLatLng([p.lat, p.lon]).setContent(html).openOn(map);
    const el = pop.getElement();
    $$("button", el).forEach((b) => b.addEventListener("click", () => {
      const a = b.dataset.a;
      if (a === "from") { setFrom(p.id); toast(`Dari: ${p.name}`); }
      if (a === "to") { setTo(p.id); toast(`Ke: ${p.name}`); }
      if (a === "ktm") { setKtmStop(ktmNode.ktm); showView("ktm"); return; }
      map.closePopup();
      if (plan.from && plan.to) { showView("plan"); runPlan(); }
    }));
  }

  function legPts(l) {
    if (l.kind === "ktm") return l.trip.st.slice(l.i, l.j + 1).map((x) => [T.ktm.stops[x[0]][1], T.ktm.stops[x[0]][2]]);
    return l.stops.map((i) => [SK[i].lat, SK[i].lon]);
  }
  const pinIcon = (emo, bg) => L.divIcon({ className: "", html: `<div class="pin" style="background:${bg}">${emo}</div>`, iconSize: [34, 34], iconAnchor: [17, 34] });
  function drawRoute(o) {
    if (!mapReady || !o) return;
    routeLayer.clearLayers();
    const all = [[plan.from.lat, plan.from.lon], [plan.to.lat, plan.to.lon]];
    o.legs.forEach((l) => {
      if (l.kind === "walk") {
        const a = l.from == null ? [plan.from.lat, plan.from.lon] : [SK[l.from].lat, SK[l.from].lon];
        const b = l.to == null ? [plan.to.lat, plan.to.lon] : [SK[l.to].lat, SK[l.to].lon];
        L.polyline([a, b], { pane: "route", color: "#3A2E39", weight: 4, dashArray: "2 8", lineCap: "round" }).addTo(routeLayer);
        return;
      }
      const I = legInfo(l), pts = legPts(l);
      all.push(...pts);
      L.polyline(pts, { pane: "route", color: "#3A2E39", weight: 12, opacity: .22 }).addTo(routeLayer);
      L.polyline(pts, { pane: "route", color: I.color, weight: 7 }).addTo(routeLayer);
      pts.forEach((pt, i) => {
        const end = i === 0 || i === pts.length - 1;
        const m = L.circleMarker(pt, { pane: "route", radius: end ? 6.5 : 3, color: "#3A2E39", weight: 2, fillColor: "#fff", fillOpacity: 1 }).addTo(routeLayer);
        if (end) m.bindTooltip(`${I.emoji} ${esc(I.names[i])}`, { className: "st-label", direction: "right", offset: [6, 0], permanent: i === 0 });
      });
    });
    L.marker([plan.from.lat, plan.from.lon], { icon: pinIcon("🟢", "#fff"), pane: "trains" }).addTo(routeLayer).bindTooltip(esc(plan.from.name));
    L.marker([plan.to.lat, plan.to.lon], { icon: pinIcon("🏁", "#fff"), pane: "trains" }).addTo(routeLayer).bindTooltip(esc(plan.to.name));
    map.fitBounds(all, { padding: [50, 60] });
    toast("Laluan anda ditunjukkan di peta 💖");
  }

  // ---- bas di peta: hentian (zum dekat) & bas live
  let busStopLayer, busLiveLayer, busRenderer, showBusLive = store.get("busLive", true);
  const stopRoutes = (bi) => {
    const sk = skIndex["B" + bi];
    return [...new Set(patsAt[sk].map(([pi]) => PAT[pi]).filter((p) => p.mode === "bus").map((p) => B.pats[p.bus].r))];
  };
  function drawBusStops() {
    if (!mapReady) return;
    busStopLayer.clearLayers();
    if (map.getZoom() < 16) return;
    const bd = map.getBounds();
    SK.forEach((s) => {
      if (s.type !== "bus" || !bd.contains([s.lat, s.lon])) return;
      const m = L.circleMarker([s.lat, s.lon], { pane: "stations", radius: 5, weight: 2, color: "#2B7BE4", fillColor: "#fff", fillOpacity: 1, renderer: busRenderer }).addTo(busStopLayer);
      m.on("click", () => {
        const routes = stopRoutes(s.bi);
        const html = `<div class="pop"><h4>🚏 ${esc(s.name)}</h4>${s.code ? `<div class="small muted">${esc(s.code)}</div>` : ""}
          <div style="margin-top:6px">${routes.map((r) => `<span class="lb" style="background:#2B7BE4;color:#fff;margin:2px">${esc(r)}</span>`).join("")}</div>
          <div class="btns"><button data-a="from">🟢 Dari sini</button><button data-a="to">🏁 Ke sini</button></div></div>`;
        const pop = L.popup().setLatLng([s.lat, s.lon]).setContent(html).openOn(map);
        $$("button", pop.getElement()).forEach((b) => b.addEventListener("click", () => {
          const loc = { name: s.name, sub: "🚏 Hentian bas" + (s.code ? " " + s.code : ""), lat: s.lat, lon: s.lon, kind: "stop" };
          setLoc(b.dataset.a, loc, true);
          toast((b.dataset.a === "from" ? "Dari: " : "Ke: ") + s.name);
          map.closePopup();
          if (plan.from && plan.to) { showView("plan"); runPlan(); }
        }));
      });
    });
  }
  function drawBuses() {
    if (!mapReady || !busLiveLayer) return;
    busLiveLayer.clearLayers();
    if (!showBusLive) return;
    const bd = map.getBounds().pad(0.3);
    const routeName = {};
    B.pats.forEach((bp) => { routeName[bp.k + ":" + (bp.k === "rapid" ? bp.rid : bp.r)] = bp; });
    busLive.list.forEach((v) => {
      if (!bd.contains([v.lat, v.lon])) return;
      const bp = routeName[v.k + ":" + v.routeId];
      const label = bp ? bp.r : v.routeId || "Bas";
      const icon = L.divIcon({ className: "", html: `<div class="bus-ico" style="background:${bp ? bp.c : "#2B7BE4"}">${esc(label)}</div>`, iconSize: [40, 20], iconAnchor: [20, 10] });
      L.marker([v.lat, v.lon], { icon, pane: "trains" }).addTo(busLiveLayer)
        .bindPopup(`<div class="pop"><h4>🚌 ${esc(label)}</h4>${bp ? `<div>${esc(bp.n)}</div>` : ""}<div class="small muted">${esc(v.label || v.vid || "")}</div></div>`);
    });
  }

  // ================================================================ GTFS REALTIME (protobuf mini)
  function pbRead(buf) {
    const dv = new DataView(buf.buffer, buf.byteOffset, buf.byteLength);
    let i = 0;
    const varint = () => {
      let r = 0, s = 0, b;
      do { b = buf[i++]; r += (b & 0x7f) * 2 ** s; s += 7; } while (b & 0x80);
      return r;
    };
    const fields = [];
    while (i < buf.length) {
      const key = varint(), f = Math.floor(key / 8), w = key & 7;
      if (w === 0) fields.push([f, varint()]);
      else if (w === 1) { fields.push([f, dv.getFloat64(i, true)]); i += 8; }
      else if (w === 5) { fields.push([f, dv.getFloat32(i, true)]); i += 4; }
      else if (w === 2) { const n = varint(); fields.push([f, buf.subarray(i, i + n)]); i += n; }
      else throw new Error("wire type " + w);
    }
    return fields;
  }
  const td = new TextDecoder();
  const str = (b) => (b instanceof Uint8Array ? td.decode(b) : String(b));
  function decodeFeed(ab) {
    const out = [];
    for (const [f, v] of pbRead(new Uint8Array(ab))) {
      if (f !== 2) continue; // entity
      const ent = { id: "" };
      for (const [ef, ev] of pbRead(v)) {
        if (ef === 1) ent.id = str(ev);
        if (ef !== 4) continue; // vehicle
        for (const [vf, vv] of pbRead(ev)) {
          if (vf === 1) for (const [tf, tv] of pbRead(vv)) { if (tf === 1) ent.tripId = str(tv); if (tf === 5) ent.routeId = str(tv); }
          if (vf === 2) for (const [pf, pv] of pbRead(vv)) { if (pf === 1) ent.lat = pv; if (pf === 2) ent.lon = pv; if (pf === 3) ent.bearing = pv; if (pf === 5) ent.speed = pv; }
          if (vf === 5) ent.ts = vv;
          if (vf === 7) ent.stopId = str(vv);
          if (vf === 8) for (const [df, dvv] of pbRead(vv)) { if (df === 1) ent.vid = str(dvv); if (df === 2) ent.label = str(dvv); }
        }
      }
      if (ent.lat != null && ent.lon != null) out.push(ent);
    }
    return out;
  }

  const tripsByNum = {};
  T.ktm.trips.forEach((t) => (tripsByNum[t.num] ||= []).push(t));
  function matchTrip(v, now) {
    const today = activeServices(now.date, now.dow).set;
    const cands = [];
    for (const key of [v.tripId, v.label, v.vid]) {
      if (!key) continue;
      const exact = T.ktm.trips.find((t) => t.id === key);
      if (exact) return exact;
      const num = (String(key).match(/(\d{3,5})\s*$/) || [])[1];
      if (num && tripsByNum[num]) cands.push(...tripsByNum[num]);
    }
    return cands.find((t) => today.has(t.s)) || cands[0] || null;
  }

  // anggar lewat: unjur kedudukan tren ke segmen jadual
  function estimate(v, trip, now) {
    const S = T.ktm.stops;
    let best = null;
    for (let i = 0; i + 1 < trip.st.length; i++) {
      const A = S[trip.st[i][0]], B = S[trip.st[i + 1][0]];
      if (!A || !B) continue;
      const ax = A[2] * 110000, ay = A[1] * 110600, bx = B[2] * 110000, by = B[1] * 110600, px = v.lon * 110000, py = v.lat * 110600;
      const dx = bx - ax, dy = by - ay, L2 = dx * dx + dy * dy || 1;
      const f = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / L2));
      const d = Math.hypot(ax + f * dx - px, ay + f * dy - py);
      if (!best || d < best.d) best = { d, i, f };
    }
    if (!best) return {};
    const { i, f, d } = best;
    const a = trip.st[i], b = trip.st[i + 1];
    const near = f < 0.5 ? a[0] : b[0];
    const nextStop = f > 0.95 ? trip.st[Math.min(i + 2, trip.st.length - 1)][0] : b[0];
    if (d > 2000) return { near, nextStop };
    let sched = a[2] + f * (b[1] - a[2]);
    let tod = v.ts ? myNow(new Date(v.ts * 1000)).sec : now.sec;
    if (sched >= 86400 && tod < 43200) tod += 86400;
    if (sched < 43200 && tod > 72000 && trip.st[0][2] > 72000) sched += 86400;
    let delay = tod - sched;
    if (delay > 12 * 3600 || delay < -12 * 3600) return { near, nextStop };
    return { near, nextStop, delay: Math.max(0, delay) };
  }

  let live = { vehicles: [], at: 0, ok: null, byTrip: {} };
  async function fetchLive() {
    try {
      const r = await fetch(RT_URL, { cache: "no-store" });
      if (!r.ok) throw new Error(r.status);
      const vs = decodeFeed(await r.arrayBuffer());
      const now = myNow();
      live = { vehicles: [], at: Date.now(), ok: true, byTrip: {} };
      vs.forEach((v) => {
        const trip = matchTrip(v, now);
        const est = trip ? estimate(v, trip, now) : {};
        const item = { ...v, trip, ...est };
        live.vehicles.push(item);
        if (trip) live.byTrip[trip.id] = item;
      });
    } catch (e) {
      live.ok = false;
      live.at = live.at || 0;
      console.warn("GTFS-R gagal", e);
    }
    updateLiveUI();
  }

  function routeStyle(rid) {
    const r = T.ktm.routes[rid] || { color: "#666", text: "#fff", name: rid };
    return r;
  }
  const trainEmoji = (rid) => (rid === "ETS" ? "🚄" : rid && rid.length > 3 ? "🚆" : "🚂");

  function drawTrains() {
    if (!mapReady) return;
    trainLayer.clearLayers();
    live.vehicles.forEach((v) => {
      const rs = routeStyle(v.trip ? v.trip.r : null);
      const icon = L.divIcon({ className: "", html: `<div class="train-ico" style="background:${rs.color}">${trainEmoji(v.trip && v.trip.r)}</div>`, iconSize: [30, 30], iconAnchor: [15, 15] });
      const m = L.marker([v.lat, v.lon], { icon, pane: "trains" }).addTo(trainLayer);
      m.bindPopup(trainPopup(v));
      m.vehicleKey = v.id;
    });
    $("#map-live-text").textContent = live.ok === false ? "Data live tak dapat dicapai" : `${live.vehicles.length} tren KTM live`;
  }
  function trainPopup(v) {
    const rs = routeStyle(v.trip ? v.trip.r : null);
    const S = T.ktm.stops;
    return `<div class="pop"><h4>${trainEmoji(v.trip && v.trip.r)} ${esc(v.label || v.trip?.num || v.id)}</h4>
      <span class="lb" style="background:${rs.color};color:${rs.text}">${esc(rs.name)}</span>
      ${v.trip ? `<div style="margin-top:6px">→ <b>${esc(v.trip.headsign)}</b></div>` : ""}
      ${v.near && S[v.near] ? `<div class="small muted">Dekat ${esc(S[v.near][0])}${v.nextStop && S[v.nextStop] && v.nextStop !== v.near ? ` · seterusnya ${esc(S[v.nextStop][0])}` : ""}</div>` : ""}
      ${v.delay != null ? `<div style="margin-top:4px">${delayTag(v.delay)}</div>` : ""}
      ${v.speed != null ? `<div class="small muted">${Math.round(v.speed * 3.6)} km/j</div>` : ""}</div>`;
  }
  const delayTag = (d) => (d >= 180 ? `<span class="tag late">lewat ~${mins(d)} min</span>` : `<span class="tag live">ikut jadual</span>`);

  function updateLiveUI() {
    const pill = $("#live-pill");
    pill.classList.toggle("off", live.ok !== true);
    const age = live.at ? Math.round((Date.now() - live.at) / 1000) : null;
    $("#feed-status").textContent = live.ok === false ? "⚠️ Data live tak dapat dicapai — papar jadual sahaja" : live.ok ? `Live · dikemas kini ${age < 5 ? "baru tadi" : age + "s lalu"}` : "Memuat…";
    drawTrains();
    renderDepartures();
    renderLiveList();
  }

  function renderLiveList() {
    const el = $("#live-list");
    if (live.ok === false) { el.innerHTML = `<div class="empty-state"><span class="emo">📡</span>Tak dapat sambung ke data live. Cuba lagi sekejap.</div>`; return; }
    if (live.ok == null) { el.innerHTML = `<div class="empty-state"><span class="emo">⏳</span>Memuat data live…</div>`; return; }
    if (!live.vehicles.length) { el.innerHTML = `<div class="empty-state"><span class="emo">😴</span>Tiada tren KTM yang sedang bergerak sekarang.<br><span class="small">(Biasanya Komuter beroperasi ~5:30 pagi – 12 tengah malam)</span></div>`; return; }
    const S = T.ktm.stops;
    const sorted = [...live.vehicles].sort((a, b) => (a.trip?.r || "zz").localeCompare(b.trip?.r || "zz"));
    el.innerHTML = sorted.map((v, i) => {
      const rs = routeStyle(v.trip ? v.trip.r : null);
      return `<button class="livecard" data-i="${i}">
        <span class="ic" style="background:${rs.color}">${trainEmoji(v.trip && v.trip.r)}</span>
        <span class="mid"><div class="hs">${esc(v.trip ? "→ " + v.trip.headsign : v.label || v.id)}</div>
          <div class="sub">${esc(rs.name)} · ${esc(v.label || v.trip?.num || "")}${v.near && S[v.near] ? " · dekat " + esc(S[v.near][0]) : ""}</div></span>
        ${v.delay != null ? delayTag(v.delay) : ""}
      </button>`;
    }).join("");
    $$(".livecard", el).forEach((b) => b.addEventListener("click", () => {
      const v = sorted[+b.dataset.i];
      showView("map");
      setTimeout(() => {
        map.setView([v.lat, v.lon], 14);
        trainLayer.eachLayer((m) => { if (m.vehicleKey === v.id) m.openPopup(); });
      }, 120);
    }));
  }

  // ================================================================ KTM: papan berlepas
  const ktmItems = Object.entries(T.ktm.stops)
    .filter(([sid]) => ktmTripsByStop[sid])
    .map(([sid, [name]]) => {
      const routes = [...new Set(ktmTripsByStop[sid].map((t) => t.r))];
      return {
        id: sid, label: name, key: norm(name + " " + sid),
        extra: `<span class="badges">${routes.slice(0, 4).map((r) => { const rs = routeStyle(r); return `<span class="lb" style="background:${rs.color};color:${rs.text}">${esc(r.length > 4 ? rs.name.split(" ")[0] : r)}</span>`; }).join("")}</span>`,
        kv: !!ktmStopPlace[sid],
      };
    })
    .sort((a, b) => (b.kv - a.kv) || a.label.localeCompare(b.label));
  let ktmStop = store.get("ktmStop", "19100");
  if (!T.ktm.stops[ktmStop]) ktmStop = "19100";
  const ktmPicker = makePicker($('[data-picker="ktm"]'), ktmItems, (it) => setKtmStop(it.id));
  function setKtmStop(sid) {
    ktmStop = sid; store.set("ktmStop", sid);
    ktmPicker.set(T.ktm.stops[sid][0]);
    renderDepartures();
  }
  ktmPicker.set(T.ktm.stops[ktmStop][0]);
  $("#ktm-quick").innerHTML = ["19100", "19000", "19600", "53700", "18500", "20400", "50600", "54700"]
    .filter((s) => T.ktm.stops[s])
    .map((s) => `<button class="chip-btn small" data-s="${s}">${esc(T.ktm.stops[s][0])}</button>`).join("");
  $$("#ktm-quick button").forEach((b) => b.addEventListener("click", () => setKtmStop(b.dataset.s)));
  $("#refresh-live").addEventListener("click", () => { toast("Muat semula data live… 🔄"); fetchLive(); });

  function renderDepartures() {
    const el = $("#dep-list");
    if (!el) return;
    const now = myNow();
    const { list, stale } = ktmCandidates(ktmStop, now);
    $("#dep-title").textContent = `Berlepas dari ${T.ktm.stops[ktmStop][0]}`;
    const rows = [];
    for (const c of list) {
      const lv = live.byTrip[c.trip.id];
      const delay = lv && lv.delay != null ? lv.delay : 0;
      const eta = c.dep + delay;
      if (eta < now.sec - 60) continue;
      // tren live yang dah lepas stesen ni → langkau
      if (lv && lv.near && c.trip.idx[lv.near] != null && c.trip.idx[lv.near] > c.trip.idx[ktmStop] + 0) continue;
      rows.push({ ...c, lv, delay, eta });
      if (rows.length >= 16) break;
    }
    rows.sort((a, b) => a.eta - b.eta);
    rows.length = Math.min(rows.length, 12);
    if (!rows.length) {
      const tm = atTime(now, 86400);
      const first = ktmCandidates(ktmStop, { ...tm, sec: 0 }).list.filter((c) => c.dep >= 0).slice(0, 5);
      el.innerHTML = `<div class="empty-state"><span class="emo">🌙</span>Tiada lagi tren dari stesen ni untuk hari ini.<br><span class="small">Jumpa esok pagi ya!</span></div>`
        + (first.length ? `<h3 style="margin:4px 0 8px;font-size:.95rem">Tren terawal esok ☀️</h3>` + first.map((c) => {
          const rs = routeStyle(c.trip.r);
          return `<div class="dep" style="--c:${rs.color}"><div class="t">${hhmm(c.dep)}</div><div class="mid"><div class="hs">→ ${esc(c.trip.headsign)}</div><div class="sub"><span class="tag sch">jadual</span>${esc(rs.name)} · ${esc(c.trip.num)}</div></div><div class="cd">esok</div></div>`;
        }).join("") : "");
      return;
    }
    el.innerHTML = (stale ? `<div class="ktm-next warn small">⚠️ Tempoh jadual GTFS dah tamat — jadual dipapar ikut corak hari biasa.</div>` : "") + rows.map((r) => {
      const rs = routeStyle(r.trip.r);
      const left = r.eta - now.sec;
      const cd = left <= 60 ? "Sekarang!" : left < 3600 ? `${mins(left)} min` : hhmm(r.eta);
      const status = r.lv ? (r.lv.delay != null ? `<span class="tag live">● LIVE</span>${r.delay >= 180 ? `<span class="tag late">+${mins(r.delay)} min</span>` : ""}` : `<span class="tag live">● LIVE</span>`) : `<span class="tag sch">jadual</span>`;
      const where = r.lv && r.lv.near && T.ktm.stops[r.lv.near] ? ` · kini dekat ${esc(T.ktm.stops[r.lv.near][0])}` : "";
      return `<div class="dep" style="--c:${rs.color}">
        <div class="t">${hhmm(r.eta)}${r.delay >= 180 ? `<s>${hhmm(r.dep)}</s>` : ""}</div>
        <div class="mid"><div class="hs">→ ${esc(r.trip.headsign)}</div>
          <div class="sub">${status}${esc(rs.name)} · ${esc(r.trip.num)}${where}</div></div>
        <div class="cd">${cd}<small class="muted">${left <= 60 ? "🏃" : left < 3600 ? "lagi" : "jadual"}</small></div>
      </div>`;
    }).join("");
  }
  setInterval(() => { if ($("#view-ktm").classList.contains("active")) renderDepartures(); }, 20000);

  // ================================================================ LALUAN
  $("#line-grid").innerHTML = T.lines.map((l) => {
    const a = nodes[l.stations[0]].name, b = nodes[l.stations[l.stations.length - 1]].name;
    return `<button class="lcard" data-l="${l.id}" style="background:${l.color};color:${l.text}"><div class="k">${l.kind} · ${l.id}</div><div class="n">${esc(l.name)}</div><div class="c">${esc(a)} ⇄ ${esc(b)}</div></button>`;
  }).join("");
  $$(".lcard").forEach((b) => b.addEventListener("click", () => renderLine(b.dataset.l)));

  function renderLine(lid) {
    const l = lineById[lid] || T.lines[0];
    store.set("line", l.id);
    $$(".lcard").forEach((b) => b.classList.toggle("sel", b.dataset.l === l.id));
    const now = myNow();
    const h = headway(l.id, now.sec, now.dow);
    const hwTxt = l.kind === "KTM" ? "🚂 Lihat jadual tepat di tab KTM Live" : h.open ? `⏱️ Tren setiap ~${Math.round(h.hw / 60)} min sekarang` : `🌙 Tutup sekarang · buka ~${hhmm(h.opensAt)}`;
    const total = l.secs.reduce((a, b) => a + b, 0);
    const items = l.stations.map((n) => {
      const nd = nodes[n], p = placeById[nd.place];
      const others = placeLines(p).filter((x) => x !== l.id);
      const walk = T.walks.filter((w) => w[0] === p.id || w[1] === p.id).map((w) => placeById[w[0] === p.id ? w[1] : w[0]]);
      const walkLines = [...new Set(walk.flatMap((wp) => placeLines(wp)))].filter((x) => x !== l.id && !others.includes(x));
      return `<li class="${others.length ? "x" : ""}"><span class="k"></span><div class="nm"><b>${esc(nd.name)}</b>${nd.code ? `<span class="code">${esc(nd.code)}</span>` : ""}
        ${others.map(lineBadge).join("")}${walkLines.length ? `<span class="small muted">🚶</span>${walkLines.map(lineBadge).join("")}` : ""}
        ${nd.ktm ? `<button data-ktm="${nd.ktm}">⏱️ jadual</button>` : ""}<button data-from="${p.id}">dari sini</button></div></li>`;
    }).join("");
    $("#line-detail").innerHTML = `<div class="card" style="--c:${l.color}">
      <div class="ld-head"><div><h2 style="margin:0">${esc(l.name)}</h2><div class="small muted">${l.stations.length} stesen · hujung ke hujung ~${durTxt(total)}</div></div><div class="hw">${hwTxt}</div></div>
      <ul class="strip">${items}</ul></div>`;
    $$("#line-detail [data-ktm]").forEach((b) => b.addEventListener("click", () => { setKtmStop(b.dataset.ktm); showView("ktm"); }));
    $$("#line-detail [data-from]").forEach((b) => b.addEventListener("click", () => { setFrom(b.dataset.from); showView("plan"); toast(`Dari: ${placeById[b.dataset.from].name} — pilih destinasi pula 🏁`); $("#to-input").focus(); }));
  }

  // ================================================================ mula
  fetchLive();
  fetchBusLive();
  setInterval(() => { if (!document.hidden) fetchBusLive(); }, 30000);
  let liveTimer = setInterval(fetchLive, 30000);
  document.addEventListener("visibilitychange", () => {
    clearInterval(liveTimer);
    if (!document.hidden) { fetchLive(); liveTimer = setInterval(fetchLive, 30000); }
  });
  setInterval(() => { if (live.ok) $("#feed-status").textContent = `Live · dikemas kini ${Math.round((Date.now() - live.at) / 1000)}s lalu`; }, 5000);

  const start = (location.hash || "#plan").slice(1);
  showView(["plan", "map", "ktm", "lines"].includes(start) ? start : "plan");
  if (plan.from && plan.to && start === "plan") runPlan();
})();
