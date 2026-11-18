#!/usr/bin/env python3
"""Muat turun GTFS Static rasmi (data.gov.my) dan jana data/transit.js untuk app.

Guna:  python3 scripts/build_data.py
Sumber:
  - Prasarana Rapid Rail KL : https://api.data.gov.my/gtfs-static/prasarana?category=rapid-rail-kl
  - KTMB                    : https://api.data.gov.my/gtfs-static/ktmb
"""
import csv, io, json, math, os, sys, urllib.request, zipfile
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "transit.js")
URL_RAPID = "https://api.data.gov.my/gtfs-static/prasarana/?category=rapid-rail-kl"
URL_KTM = "https://api.data.gov.my/gtfs-static/ktmb/"


def load_zip(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    out = {}
    for n in z.namelist():
        if n.startswith("__MACOSX") or not n.endswith(".txt"):
            continue
        text = z.read(n).decode("utf-8-sig")
        out[os.path.basename(n)[:-4]] = list(csv.DictReader(io.StringIO(text)))
    return out


def hms(t):
    h, m, s = (int(x) for x in t.strip().split(":"))
    return h * 3600 + m * 60 + s


def dist_m(a, b):
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(3.1)))


# ---------- nama cantik ----------
SMALL = {"KL", "KLCC", "PWTC", "UOB", "USJ", "UPM", "UKM", "UITM", "TRX", "SS", "BK5", "CBP", "LRT", "MRT", "KTM", "II", "JB", "IOI", "SA"}
KTM_NAMES = {
    "PEL KLANG SEL": "Pelabuhan Klang", "JLN KASTAM": "Jalan Kastam", "KG RAJA UDA": "Kampung Raja Uda",
    "KG DATO HARUN": "Kampung Dato Harun", "BDR TASEK SELATAN": "Bandar Tasik Selatan",
    "BATU KENTOMENN": "Batu Kentonmen", "PERHENTIAN MIDVALLEY": "Mid Valley", "PULAU SEBANG/TAMPIN": "Pulau Sebang/Tampin",
    "TANJONG MALIM": "Tanjung Malim", "KUALA KUBU BHARU": "Kuala Kubu Bharu",
}


def nice(name):
    name = " ".join(name.strip().split())
    if name in KTM_NAMES:
        return KTM_NAMES[name]
    words = []
    for w in name.split(" "):
        parts = []
        for p in w.split("-"):
            up = p.upper()
            if up in SMALL or (len(up) <= 3 and any(c.isdigit() for c in up)):
                parts.append(up)
            elif up.startswith("SS") and up[2:].isdigit():
                parts.append(up)
            else:
                parts.append(p[:1].upper() + p[1:].lower())
        words.append("-".join(parts))
    s = " ".join(words).replace("Dato'", "Dato'").replace("Sunu", "SunU")
    for sponsor in (" - Redone", " - UOB", " - Bank Rakyat", " - Petworld", " - CBP Coopbank Pertama"):
        s = s.replace(sponsor, "")
    return s.replace("Usj7", "USJ 7").replace("USJ7", "USJ 7")


LINES_RAPID = {
    # route_id: (id, nama, jenis, warna, warna teks)
    "AG": ("AG", "LRT Ampang", "LRT", "#E57200", "#fff"),
    "PH": ("SP", "LRT Sri Petaling", "LRT", "#8A2432", "#fff"),
    "KJ": ("KJ", "LRT Kelana Jaya", "LRT", "#D50032", "#fff"),
    "SA": ("SA", "LRT Shah Alam", "LRT", "#C93ED6", "#fff"),
    "KGL": ("KG", "MRT Kajang", "MRT", "#047940", "#fff"),
    "PYL": ("PY", "MRT Putrajaya", "MRT", "#F2B705", "#3b2a00"),
    "MR": ("MR", "Monorel KL", "MRL", "#84BD00", "#fff"),
    "BRT": ("BRT", "BRT Sunway", "BRT", "#115740", "#fff"),
}
LINES_KTM = {
    "KA15_KD19": ("KA", "KTM Pelabuhan Klang", "KTM", "#DC2420", "#fff"),
    "KC05_KB18": ("KC", "KTM Seremban", "KTM", "#3C5A9F", "#fff"),
}
# Koordinat GTFS yang salah (Seri Setia sama dengan Setia Jaya)
COORD_FIX = {"53500": (3.08463, 101.62202)}
# Laluan pejalan kaki rasmi antara stesen berlainan nama (minit)
WALK_LINKS = [
    ("KJ15", "KG15", 7, "Laluan pejalan kaki NU Sentral"),
    ("KJ14", "KTM:19000", 7, "Jejantas ke Stesen KTM Kuala Lumpur"),
    ("AG4", "KTM:18800", 6, "Jejantas PWTC ↔ Putra"),
    ("KJ12", "MR8", 6, "Laluan pejalan kaki Dang Wangi ↔ Bukit Nanas"),
    ("PY14", "KTM:50300", 6, "Jalan kaki Kentonmen ↔ Batu Kentonmen"),
    ("KJ9", "PY20", 5, "Terowong Ampang Park"),
]


def main():
    print("Muat turun GTFS…", file=sys.stderr)
    rr = load_zip(URL_RAPID)
    ktm = load_zip(URL_KTM)

    lines, nodes = [], {}

    # ---- Rapid Rail ----
    rstops = {s["stop_id"]: s for s in rr["stops"]}
    rtimes = defaultdict(list)
    for r in rr["stop_times"]:
        rtimes[r["trip_id"]].append(r)
    freq = defaultdict(list)
    for f in rr["frequencies"]:
        freq[f["trip_id"]].append([hms(f["start_time"]), hms(f["end_time"]), int(f["headway_secs"])])
    shapes = defaultdict(list)
    for p in rr["shapes"]:
        shapes[p["shape_id"]].append((int(p["shape_pt_sequence"]), round(float(p["shape_pt_lat"]), 5), round(float(p["shape_pt_lon"]), 5)))
    trips_by_route = defaultdict(dict)
    for t in rr["trips"]:
        trips_by_route[t["route_id"]][(t["service_id"], t["direction_id"])] = t
    for rid, (lid, name, kind, color, tcolor) in LINES_RAPID.items():
        tr = trips_by_route[rid].get(("MonFri", "0"))
        if not tr:
            continue
        st = sorted(rtimes[tr["trip_id"]], key=lambda r: int(r["stop_sequence"]))
        seq, secs = [], []
        prev = None
        for r in st:
            sid = r["stop_id"]
            s = rstops[sid]
            nodes[sid] = {"id": sid, "line": lid, "name": nice(s["stop_name"]), "code": sid,
                          "lat": float(s["stop_lat"]), "lon": float(s["stop_lon"])}
            if prev is not None:
                secs.append(max(60, hms(r["arrival_time"]) - prev))
            prev = hms(r["departure_time"])
            seq.append(sid)
        shp = [[a, b] for _, a, b in sorted(shapes[tr["shape_id"]])]
        hw = {}
        for svc in ("MonFri", "Sat", "Sun"):
            t2 = trips_by_route[rid].get((svc, "0"))
            hw[svc] = sorted(freq[t2["trip_id"]]) if t2 else []
        lines.append({"id": lid, "name": name, "kind": kind, "color": color, "text": tcolor,
                      "stations": seq, "secs": secs, "shape": shp, "headway": hw})

    # ---- KTM ----
    kstops = {s["stop_id"]: s for s in ktm["stops"]}
    for sid, (la, lo) in COORD_FIX.items():
        kstops[sid]["stop_lat"], kstops[sid]["stop_lon"] = str(la), str(lo)
    ktimes = defaultdict(list)
    for r in ktm["stop_times"]:
        ktimes[r["trip_id"]].append(r)
    for k in ktimes:
        ktimes[k].sort(key=lambda r: int(r["stop_sequence"]))
    ktrips = {t["trip_id"]: t for t in ktm["trips"]}
    for rid, (lid, name, kind, color, tcolor) in LINES_KTM.items():
        best = max((t for t in ktrips.values() if t["route_id"] == rid and t["direction_id"] == "0"),
                   key=lambda t: len(ktimes[t["trip_id"]]))
        st = ktimes[best["trip_id"]]
        seq, secs, prev = [], [], None
        for r in st:
            s = kstops[r["stop_id"]]
            nid = f"KTM:{r['stop_id']}"
            nodes[f"{lid}:{r['stop_id']}"] = {"id": f"{lid}:{r['stop_id']}", "line": lid, "name": nice(s["stop_name"]),
                                               "code": "", "lat": float(s["stop_lat"]), "lon": float(s["stop_lon"]),
                                               "ktm": r["stop_id"]}
            if prev is not None:
                secs.append(max(60, hms(r["arrival_time"]) - prev))
            prev = hms(r["departure_time"])
            seq.append(f"{lid}:{r['stop_id']}")
        lines.append({"id": lid, "name": name, "kind": kind, "color": color, "text": tcolor,
                      "stations": seq, "secs": secs,
                      "shape": [[nodes[n]["lat"], nodes[n]["lon"]] for n in seq], "headway": None})

    # ---- Kelompok stesen (tempat pertukaran) ----
    ids = list(nodes)
    parent = {i: i for i in ids}
    members = {i: {nodes[i]["line"]} for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def norm(n):
        return n.lower().split(" - ")[0].replace("tasek", "tasik").replace(" ", "")

    pairs = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            A, B = nodes[a], nodes[b]
            if A["line"] == B["line"]:
                continue
            d = dist_m((A["lat"], A["lon"]), (B["lat"], B["lon"]))
            if d <= 250 or (d <= 500 and norm(A["name"]) == norm(B["name"])):
                pairs.append((d, a, b))
    for d, a, b in sorted(pairs):
        ra, rb = find(a), find(b)
        if ra == rb or members[ra] & members[rb]:
            continue
        parent[rb] = ra
        members[ra] |= members[rb]
    groups = defaultdict(list)
    for i in ids:
        groups[find(i)].append(i)

    places = []
    PREF = ["KJ", "KG", "AG", "PY", "SP", "MR", "SA", "BRT", "KA", "KC"]
    for root, mem in groups.items():
        mem.sort(key=lambda n: PREF.index(nodes[n]["line"]))
        names = []
        for n in mem:
            nm = nodes[n]["name"]
            if nm not in names:
                names.append(nm)
        # pilih nama utama; jika berbeza tunjuk gabungan
        base = []
        for nm in names:
            key = norm(nm)
            if not any(norm(x) == key for x in base):
                base.append(nm)
        pname = " / ".join(base[:2])
        pid = f"P{len(places)}"
        lat = sum(nodes[n]["lat"] for n in mem) / len(mem)
        lon = sum(nodes[n]["lon"] for n in mem) / len(mem)
        places.append({"id": pid, "name": pname, "nodes": mem, "lat": round(lat, 6), "lon": round(lon, 6)})
        for n in mem:
            nodes[n]["place"] = pid

    walks = []
    for a, b, mins, note in WALK_LINKS:
        def resolve(x):
            if x.startswith("KTM:"):
                sid = x[4:]
                for n in nodes.values():
                    if n.get("ktm") == sid:
                        return n["id"]
            return x if x in nodes else None
        ra, rb = resolve(a), resolve(b)
        if ra and rb and nodes[ra]["place"] != nodes[rb]["place"]:
            walks.append([nodes[ra]["place"], nodes[rb]["place"], mins, note])

    # ---- Jadual KTM (semua laluan, untuk papan berlepas & kereta api live) ----
    route_info = {}
    for r in ktm["routes"]:
        route_info[r["route_id"]] = {"name": r["route_short_name"], "long": r["route_long_name"],
                                     "color": "#" + (r["route_color"] or "666666"), "text": "#" + (r["route_text_color"] or "FFFFFF")}
    route_info["KA15_KD19"]["name"] = "Pelabuhan Klang"
    route_info["KC05_KB18"]["name"] = "Seremban"
    ktm_stops = {sid: [nice(s["stop_name"]), round(float(s["stop_lat"]), 6), round(float(s["stop_lon"]), 6)] for sid, s in kstops.items()}
    ktm_trips = []
    for tid, t in ktrips.items():
        st = ktimes[tid]
        if not st:
            continue
        ktm_trips.append({"id": tid, "r": t["route_id"], "s": t["service_id"], "d": int(t["direction_id"] or 0),
                          "st": [[r["stop_id"], hms(r["arrival_time"]), hms(r["departure_time"])] for r in st]})
    calendar = [{k: v for k, v in c.items()} for c in ktm["calendar"]]
    cal_dates = [[c["service_id"], c["date"], int(c["exception_type"])] for c in ktm.get("calendar_dates", [])]

    data = {
        "generated": __import__("datetime").datetime.now().strftime("%Y-%m-%d"),
        "lines": lines,
        "nodes": nodes,
        "places": places,
        "walks": walks,
        "ktm": {"routes": route_info, "stops": ktm_stops, "trips": ktm_trips,
                "calendar": calendar, "calendarDates": cal_dates},
    }
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("// Dijana oleh scripts/build_data.py daripada GTFS data.gov.my — jangan sunting manual\n")
        f.write("window.TRANSIT = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"OK: {len(lines)} laluan, {len(nodes)} nod, {len(places)} stesen, {len(walks)} laluan kaki, "
          f"{len(ktm_trips)} trip KTM → {OUT} ({os.path.getsize(OUT)//1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
