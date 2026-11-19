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

  // ================================================================ PERANCANG
  const placeItems = T.places
    .map((p) => ({ id: p.id, label: p.name, key: norm(p.name + " " + p.nodes.map((n) => nodes[n].name + " " + nodes[n].code).join(" ")), extra: badgesFor(p) }))
    .sort((a, b) => a.label.localeCompare(b.label));
  const plan = { from: store.get("from", null), to: store.get("to", null) };
  const fromPicker = makePicker($('[data-picker="from"]'), placeItems, (it) => { plan.from = it.id; store.set("from", it.id); maybePlan(); });
  const toPicker = makePicker($('[data-picker="to"]'), placeItems, (it) => { plan.to = it.id; store.set("to", it.id); maybePlan(); });
  if (plan.from && placeById[plan.from]) fromPicker.set(placeById[plan.from].name); else plan.from = null;
  if (plan.to && placeById[plan.to]) toPicker.set(placeById[plan.to].name); else plan.to = null;
  function maybePlan() { if (plan.from && plan.to) runPlan(); }

  function setFrom(pid) { plan.from = pid; store.set("from", pid); fromPicker.set(placeById[pid].name); }
  function setTo(pid) { plan.to = pid; store.set("to", pid); toPicker.set(placeById[pid].name); }

  $("#swap").addEventListener("click", () => {
    const f = plan.from, t = plan.to;
    plan.from = t; plan.to = f;
    fromPicker.set(t ? placeById[t].name : ""); toPicker.set(f ? placeById[f].name : "");
    store.set("from", plan.from); store.set("to", plan.to);
    maybePlan();
  });
  $("#go-btn").addEventListener("click", () => {
    if (!plan.from || !plan.to) return toast("Pilih stesen mula & destinasi dulu ya 🙏");
    runPlan();
  });

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
  $("#near-btn").addEventListener("click", () => locate((lat, lon) => {
    const { place, dist } = nearestPlace(lat, lon);
    setFrom(place.id);
    toast(`Stesen terdekat: ${place.name} (${dist < 1000 ? Math.round(dist) + " m" : (dist / 1000).toFixed(1) + " km"}) 🎉`);
    maybePlan();
  }));

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

  function dijkstra(fromPid, toPid, xferPenalty, now, ktmPenalty = 0) {
    const dist = {}, prev = {}, done = new Set();
    const targets = new Set(placeById[toPid].nodes);
    const waitOf = (lid) => headway(lid, now.sec, now.dow).hw / 2 + (lineById[lid].kind === "KTM" ? ktmPenalty : 0);
    Object.keys(nodes).forEach((n) => (dist[n] = Infinity));
    placeById[fromPid].nodes.forEach((n) => { dist[n] = waitOf(nodes[n].line); prev[n] = null; });
    for (;;) {
      let u = null, best = Infinity;
      for (const n in dist) if (!done.has(n) && dist[n] < best) { best = dist[n]; u = n; }
      if (u === null) return null;
      if (targets.has(u)) {
        const path = [];
        for (let x = u; x != null; x = prev[x] && prev[x].from) path.unshift({ node: x, via: prev[x] ? prev[x].edge : null });
        return path;
      }
      done.add(u);
      for (const e of adj[u]) {
        let c = e.secs;
        if (e.kind !== "ride") c += waitOf(nodes[e.to].line) + xferPenalty;
        if (dist[u] + c < dist[e.to]) { dist[e.to] = dist[u] + c; prev[e.to] = { from: u, edge: e }; }
      }
    }
  }

  // Tukar laluan nod → langkah
  function toLegs(path) {
    const legs = [];
    for (let i = 1; i < path.length; i++) {
      const { node, via } = path[i];
      const from = path[i - 1].node;
      if (via.kind === "ride") {
        const last = legs[legs.length - 1];
        if (last && last.kind === "ride" && last.line === via.line) { last.stops.push(node); last.secs += via.secs; }
        else legs.push({ kind: "ride", line: via.line, stops: [from, node], secs: via.secs });
      } else {
        legs.push({ kind: via.kind, from, to: node, secs: via.secs, note: via.note });
      }
    }
    // buang pertukaran di hujung (jika ada)
    while (legs.length && legs[legs.length - 1].kind !== "ride") legs.pop();
    while (legs.length && legs[0].kind !== "ride") legs.shift();
    return legs;
  }

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

  // ---- jalankan perancangan
  let lastResult = null;
  function runPlan() {
    const out = $("#plan-result");
    if (plan.from === plan.to) {
      out.innerHTML = `<div class="card empty-state"><span class="emo">😄</span>Eh, dah sampai pun! Stesen mula & destinasi sama.</div>`;
      return;
    }
    const now = myNow();
    let opts = [];
    const seen = new Set();
    for (const [pen, kp] of [[60, 0], [15 * 60, 0], [60, 3 * 3600], [15 * 60, 3 * 3600]]) {
      const path = dijkstra(plan.from, plan.to, pen, now, kp);
      if (!path) continue;
      const legs = toLegs(path);
      if (!legs.length) continue;
      const sig = legs.map((l) => (l.kind === "ride" ? l.line + l.stops[0] + l.stops[l.stops.length - 1] : l.kind)).join("|");
      if (seen.has(sig)) continue;
      seen.add(sig);
      const rides = legs.filter((l) => l.kind === "ride");
      opts.push({ legs, timeline: buildTimeline(legs, now), xfers: rides.length - 1, ktm: rides.some((l) => lineById[l.line].kind === "KTM") });
    }
    // susun ikut masa tiba sebenar (termasuk tunggu KTM ikut jadual)
    opts.sort((a, b) => a.timeline.end - b.timeline.end || a.xfers - b.xfers);
    opts.forEach((o, i) => {
      const fewest = Math.min(...opts.map((x) => x.xfers));
      o.label = i === 0 ? "⚡ Paling cepat" : o.xfers === fewest && o.xfers < opts[0].xfers ? "🙌 Kurang tukar" : !o.ktm && opts[0].ktm ? "🚇 Tanpa KTM" : "✨ Pilihan lain";
    });
    opts = opts.slice(0, 3);
    if (!opts.length) {
      out.innerHTML = `<div class="card empty-state"><span class="emo">🥺</span>Alamak, tak jumpa laluan antara stesen ni.</div>`;
      return;
    }
    lastResult = { opts, sel: 0 };
    renderPlan();
    $("#plan-tips").style.display = "none";
  }

  function buildTimeline(legs, now) {
    let t = now.sec;
    const steps = [];
    const notes = [];
    const isKtmRide = (l) => l && l.kind === "ride" && lineById[l.line].kind === "KTM";
    for (let k = 0; k < legs.length; k++) {
      const leg = legs[k];
      if (isKtmRide(leg)) {
        // gabung segmen KTM berturut-turut (cth. KA → tukar di KL Sentral → KC)
        let j = k;
        while (legs[j + 1] && legs[j + 1].kind !== "ride" && isKtmRide(legs[j + 2])) j += 2;
        const last = legs[j];
        const fromS = nodes[leg.stops[0]].ktm, toS = nodes[last.stops[last.stops.length - 1]].ktm;
        const tSeg = t;
        const jr = ktmJourney(fromS, toS, now, t);
        if (jr && jr.legs.length) {
          jr.legs.forEach((jl, q) => {
            const lid = lineOfTrip(jl.trip);
            const stops = jl.trip.st.slice(jl.i, jl.j + 1).map((x) => ktmNode(lid, x[0]));
            if (q > 0) {
              const prev = steps[steps.length - 1];
              steps.push({ kind: "xfer", from: prev.stops[prev.stops.length - 1], to: stops[0], secs: Math.min(KTM_CHANGE, jl.dep - t), start: t });
              t += Math.min(KTM_CHANGE, jl.dep - t);
            }
            const later = q === 0 && jr.legs.length === 1 ? nextKtm(fromS, toS, now, jl.dep + 60).next : null;
            steps.push({
              kind: "ride", line: lid, stops, secs: jl.arr - jl.dep, towards: jl.trip.headsign,
              wait: jl.dep - t, board: jl.dep, arrive: jl.arr,
              ktm: { next: { trip: jl.trip, dep: jl.dep, arr: jl.arr }, after: later ? [later] : [], stale: jr.stale },
            });
            t = jl.arr;
          });
          // jika destinasi akhir & tren jarang: cadang turun di stesen berdekatan + e-hailing
          if (j === legs.length - 1) {
            const dst = T.ktm.stops[toS];
            const { arr } = ktmJourney(fromS, toS, now, tSeg, { full: true });
            let best = null;
            for (const sid in arr) {
              if (sid === toS || !T.ktm.stops[sid]) continue;
              const st = T.ktm.stops[sid];
              const km = distM([st[1], st[2]], [dst[1], dst[2]]) / 1000;
              if (km > 25) continue;
              const drive = Math.round((km * 1.35) / 35 * 3600) + 10 * 60; // ~35 km/j + 10 min tunggu kereta
              const eta = arr[sid] + drive;
              if (!best || eta < best.eta) best = { sid, km, eta, at: arr[sid] };
            }
            if (best && best.eta < t - 30 * 60) {
              notes.push(best.sid === fromS
                ? `💡 Tren ke ${dst[0]} jarang waktu ni. Lebih cepat naik Grab/teksi terus dari ${T.ktm.stops[fromS][0]} (~${best.km.toFixed(0)} km) — sampai ~${hhmm(best.eta)}.`
                : `💡 Tren ke ${dst[0]} jarang waktu ni. Alternatif: turun di ${T.ktm.stops[best.sid][0]} (tiba ~${hhmm(best.at)}), kemudian Grab/teksi ~${best.km.toFixed(0)} km — sampai ~${hhmm(best.eta)}.`);
            }
          }
          k = j;
          continue;
        }
      }
      if (leg.kind !== "ride") {
        steps.push({ ...leg, start: t });
        t += leg.secs;
        continue;
      }
      const l = lineById[leg.line];
      const a = leg.stops[0], b = leg.stops[leg.stops.length - 1];
      const dirTerm = nodePos[b] > nodePos[a] ? l.stations[l.stations.length - 1] : l.stations[0];
      const step = { ...leg, towards: nodes[dirTerm].name };
      if (l.kind === "KTM") {
        step.ktm = nextKtm(nodes[a].ktm, nodes[b].ktm, now, t);
        const nxt = step.ktm.next;
        if (nxt) {
          step.wait = nxt.dep - t; step.board = nxt.dep; step.arrive = nxt.arr;
          step.towards = nxt.trip.headsign;
          t = nxt.arr;
        } else {
          step.wait = 15 * 60; step.board = t + step.wait; step.arrive = step.board + leg.secs; t = step.arrive;
          notes.push("Tak jumpa tren KTM terus untuk segmen ni dalam jadual 😢 — anggaran masa sahaja.");
        }
      } else {
        const at = atTime(now, t);
        const h = headway(l.id, at.sec, at.dow);
        step.hw = h;
        let wait = h.hw / 2;
        if (!h.open) {
          wait = (h.opensAt - at.sec + 86400) % 86400 + 60;
          notes.push(`${l.name} tak beroperasi sekarang — buka semula ~${hhmm(h.opensAt)} 🌙`);
        }
        step.wait = wait; step.board = t + wait; step.arrive = step.board + leg.secs; t = step.arrive;
      }
      steps.push(step);
    }
    if (steps.some((x) => x.ktm && x.wait > 90 * 60 && (x.line === "KC" || x.line === "ETS"))) {
      notes.push("ℹ️ KTMB sedang menstruktur semula jadual Lembah Klang (Apr–Dis 2026): tiada Komuter Mid Valley/BTS ↔ Pulau Sebang dari ~10 pagi hingga 4 petang. Sebahagiannya diganti tren ETS.");
    }
    return { steps, start: now.sec, end: t, notes };
  }

  function renderPlan() {
    const { opts, sel } = lastResult;
    const o = opts[sel];
    const { steps, start, end, notes } = o.timeline;
    const rides = steps.filter((s) => s.kind === "ride");
    const nStops = rides.reduce((a, s) => a + s.stops.length - 1, 0);
    const transfers = rides.length - 1;
    const total = end - start;
    const bar = steps.map((s) => {
      const c = s.kind === "ride" ? lineById[s.line].color : "#D9CCD4";
      const w = s.wait > 120 ? `<span title="tunggu" style="background:repeating-linear-gradient(90deg,#E6DAE1 0 4px,transparent 4px 7px);flex:${s.wait}"></span>` : "";
      return `${w}<span style="background:${c};flex:${Math.max(60, s.secs || 60)}"></span>`;
    }).join("");

    let html = "";
    if (opts.length > 1) html += `<div class="opt-tabs">${opts.map((x, i) => `<button class="opt-tab${i === sel ? " active" : ""}" data-opt="${i}">${x.label} · ${durTxt(x.timeline.end - x.timeline.start)}</button>`).join("")}</div>`;
    html += `<div class="card">
      <div class="summary">
        <div class="big">${durTxt(total).replace(/(\d+) min$/, "$1<small> min</small>")}</div>
        <div class="meta">Bertolak <b>${hhmm(start)}</b> → tiba <b>~${hhmm(end)}</b><br>${nStops} stesen · ${transfers <= 0 ? "terus, tak payah tukar 🎉" : transfers + " kali tukar"}</div>
      </div>
      <div class="linebar">${bar}</div>
      ${notes.map((n) => `<div class="ktm-next warn">${esc(n)}</div>`).join("")}
      <div class="steps">`;

    steps.forEach((s, i) => {
      if (s.kind === "ride") {
        const l = lineById[s.line];
        const a = nodes[s.stops[0]], b = nodes[s.stops[s.stops.length - 1]];
        const mid = s.stops.slice(1, -1).map((n) => `<li>${esc(nodes[n].name)}</li>`).join("");
        let extra = "";
        if (s.ktm) {
          const n = s.ktm.next;
          if (n) {
            const w = n.dep - (s.board - s.wait);
            extra = `<div class="ktm-next">🚂 Tren <b>${esc(n.trip.num)}</b> bertolak <b>${hhmm(n.dep)}</b>${n.dep >= 86400 ? " (esok)" : ""} · tunggu ${w < 60 ? "sekejap je" : durTxt(w)} · tiba ${hhmm(n.arr)}`;
            if (w > 45 * 60) extra += `<br><span class="small">⏳ Tren KTM jarang waktu ni — boleh pertimbang pilihan lain di atas</span>`;
            if (s.ktm.after.length) extra += `<br><span class="small muted">Seterusnya: ${s.ktm.after.map((c) => hhmm(c.dep)).join(", ")}</span>`;
            if (s.ktm.stale) extra += `<br><span class="small muted">⚠️ Jadual GTFS mungkin dah lapuk</span>`;
            extra += `</div>`;
          }
        } else if (s.hw && s.hw.open) {
          extra = `<div class="small muted" style="margin-top:4px">Tren setiap ~${Math.round(s.hw.hw / 60)} min sekarang</div>`;
        }
        html += `<div class="step" style="--c:${l.color}">
          <div class="time">${hhmm(s.board)}</div><div class="rail"><span class="knob"></span></div>
          <div class="body"><div class="st">${esc(a.name)} ${a.code ? `<span class="small muted">${esc(a.code)}</span>` : ""}</div>
            <div class="what"><span class="lb" style="background:${l.color};color:${l.text}">${l.id}</span>
              Naik <span class="ln">${esc(l.name)}</span> arah <b>${esc(s.towards)}</b><br>
              <span class="muted">${s.stops.length - 1} stesen · ${durTxt(s.secs)}</span>
              ${mid ? `<details><summary>Lalu ${s.stops.length - 2} stesen</summary><ol>${mid}</ol></details>` : ""}
              ${extra}
            </div></div></div>`;
        const nx = steps[i + 1];
        html += `<div class="step${nx ? " walk" : " end"}" style="--c:${l.color}">
          <div class="time">${hhmm(s.arrive)}</div><div class="rail"><span class="knob"></span></div>
          <div class="body"><div class="st">${nx ? "Turun di " : "🎉 Sampai "}${esc(b.name)} ${b.code ? `<span class="small muted">${esc(b.code)}</span>` : ""}</div>
          ${nx ? `<div class="what">🚶 ${nx.kind === "walk" ? esc(nx.note || "Jalan kaki") : "Tukar tren"} ke <b>${esc(nodes[nx.to].name)}</b> ${lineBadge(nodes[nx.to].line)} · ~${durTxt(nx.secs)}</div>` : ""}
          </div></div>`;
      }
    });
    html += `</div>
      <div class="res-actions">
        <button class="chip-btn" id="show-on-map">🗺️ Lihat di peta</button>
        <button class="chip-btn" id="share-route">📤 Kongsi</button>
      </div>
      <p class="small muted" style="margin:10px 0 0">Masa LRT/MRT ialah anggaran ikut kekerapan GTFS. Masa KTM ikut jadual rasmi.</p>
    </div>`;
    $("#plan-result").innerHTML = html;
    $$(".opt-tab").forEach((b) => b.addEventListener("click", () => { lastResult.sel = +b.dataset.opt; renderPlan(); }));
    $("#show-on-map").addEventListener("click", () => { showView("map"); drawRoute(o.timeline.steps); });
    $("#share-route").addEventListener("click", () => shareRoute(o));
  }

  function shareRoute(o) {
    const lines = [`🚆 ${placeById[plan.from].name} → ${placeById[plan.to].name} (~${durTxt(o.timeline.end - o.timeline.start)})`];
    o.timeline.steps.forEach((s) => {
      if (s.kind === "ride") lines.push(`• ${lineById[s.line].name} arah ${s.towards}: ${nodes[s.stops[0]].name} → ${nodes[s.stops[s.stops.length - 1]].name} (${s.stops.length - 1} stesen)`);
    });
    lines.push("— dirancang dengan Jom Naik! 💖");
    const text = lines.join("\n");
    if (navigator.share) navigator.share({ text }).catch(() => {});
    else navigator.clipboard?.writeText(text).then(() => toast("Laluan disalin 📋"), () => toast("Tak dapat salin 😅"));
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
    const lbl = () => {
      const z = map.getZoom();
      stLayer.eachLayer((m) => { const t = m.getTooltip(); if (!t) return; z >= 14 || (z >= 13 && placeLines(placeById[m.placeId]).length > 1) ? m.openTooltip() : m.closeTooltip(); });
    };
    map.on("zoomend", lbl);
    lbl();

    $("#map-chips").innerHTML = T.lines.map((l) => `<button class="mchip${hidden.has(l.id) ? " off" : ""}" data-l="${l.id}"><i style="background:${l.color}"></i>${esc(l.name.replace("KTM ", "KTM ").replace("Monorel KL", "Monorel"))}</button>`).join("")
      + `<button class="mchip" id="locate-me">📍 Saya</button>`;
    $$(".mchip[data-l]").forEach((b) => b.addEventListener("click", () => {
      const id = b.dataset.l;
      if (hidden.has(id)) { hidden.delete(id); lineLayers[id].addTo(map); } else { hidden.add(id); map.removeLayer(lineLayers[id]); }
      b.classList.toggle("off", hidden.has(id));
      store.set("hiddenLines", [...hidden]);
    }));
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

  function drawRoute(legs) {
    if (!mapReady) return;
    routeLayer.clearLayers();
    const all = [];
    legs.forEach((leg) => {
      if (leg.kind === "ride") {
        const pts = leg.stops.map((n) => [nodes[n].lat, nodes[n].lon]);
        all.push(...pts);
        L.polyline(pts, { pane: "route", color: "#3A2E39", weight: 13, opacity: .25 }).addTo(routeLayer);
        L.polyline(pts, { pane: "route", color: lineById[leg.line].color, weight: 8 }).addTo(routeLayer);
        leg.stops.forEach((n, i) => L.circleMarker([nodes[n].lat, nodes[n].lon], { pane: "route", radius: i === 0 || i === leg.stops.length - 1 ? 7 : 3.5, color: "#3A2E39", weight: 2, fillColor: "#fff", fillOpacity: 1 }).addTo(routeLayer));
      } else {
        L.polyline([[nodes[leg.from].lat, nodes[leg.from].lon], [nodes[leg.to].lat, nodes[leg.to].lon]], { pane: "route", color: "#3A2E39", weight: 4, dashArray: "4 8" }).addTo(routeLayer);
      }
    });
    if (all.length) map.fitBounds(all, { padding: [40, 60] });
    toast("Laluan anda ditunjukkan di peta 💖");
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
