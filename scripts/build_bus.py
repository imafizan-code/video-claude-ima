#!/usr/bin/env python3
"""Jana data/bus.js: bas RapidKL + bas perantara MRT (GTFS data.gov.my) + GoKL (OpenStreetMap).

Guna:  python3 scripts/build_bus.py
GoKL tiada GTFS rasmi; laluan & hentian diambil dari OpenStreetMap (scripts/gokl_osm.json,
muat turun semula dengan --refresh-gokl). Kekerapan GoKL dianggar.
"""
import csv, io, json, math, os, re, sys, urllib.request, urllib.parse, zipfile
from collections import defaultdict, Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "bus.js")
GOKL_CACHE = os.path.join(ROOT, "scripts", "gokl_osm.json")
FEEDS = {
    "rapid": "https://api.data.gov.my/gtfs-static/prasarana/?category=rapid-bus-kl",
    "feeder": "https://api.data.gov.my/gtfs-static/prasarana/?category=rapid-bus-mrtfeeder",
}
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.private.coffee/api/interpreter",
            "https://overpass.kumi.systems/api/interpreter"]
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def load_zip(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        z = zipfile.ZipFile(io.BytesIO(r.read()))
    out = {}
    for n in z.namelist():
        if n.startswith("__MACOSX") or not n.endswith(".txt"):
            continue
        out[os.path.basename(n)[:-4]] = list(csv.DictReader(io.StringIO(z.read(n).decode("utf-8-sig"))))
    return out


def hms(t):
    h, m, s = (int(x) for x in t.strip().split(":"))
    return h * 3600 + m * 60 + s


def dist_m(a, b):
    return math.hypot((a[0] - b[0]) * 111320, (a[1] - b[1]) * 111320 * math.cos(math.radians(3.1)))


SMALL = {"KL", "KLCC", "LRT", "MRT", "KTM", "BRT", "USJ", "SS", "PJ", "UM", "UIA", "UKM", "UPM", "UITM", "IOI", "SOGO",
         "TTDI", "PPR", "KLIA", "HKL", "PWTC", "TRX", "AEON", "MRR2", "LDP", "NPE", "JKR", "KWSP", "LHDN", "SMK", "SK", "SJK",
         "(C)", "(T)", "TNB", "MBPJ", "MPAJ", "MPSJ", "DBKL", "UTC", "IKEA", "PKNS", "BSN", "MPS", "NSK", "KFC", "GM"}


def nice(name):
    name = " ".join((name or "").replace("_", " ").split())
    out = []
    for w in name.split(" "):
        up = w.upper()
        if up in SMALL or (any(c.isdigit() for c in up) and len(up) <= 6):
            out.append(up)
        elif up.startswith("(") and up.endswith(")") and len(up) <= 8:
            out.append(up)
        else:
            out.append("-".join(p[:1].upper() + p[1:].lower() for p in w.split("-")))
    return " ".join(out)


def day_types(calendar):
    """service_id -> set of day types {wd, sa, su}"""
    m = {}
    for c in calendar:
        s = set()
        if any(c[d] == "1" for d in DAYS[:5]):
            s.add("wd")
        if c["saturday"] == "1":
            s.add("sa")
        if c["sunday"] == "1":
            s.add("su")
        m[c["service_id"]] = s
    return m


def hourly_from_departures(deps):
    """senarai masa bertolak (saat) -> 24 nilai kekerapan (minit, 0 = tiada)"""
    cnt = Counter(int(d // 3600) % 24 for d in deps)
    return [round(60 / cnt[h]) if cnt[h] else 0 for h in range(24)]


def hourly_from_windows(wins):
    hw = [0] * 24
    for a, b, h in wins:
        for hr in range(24):
            mid = hr * 3600 + 1800
            if a <= mid < b:
                v = max(1, round(h / 60))
                hw[hr] = min(hw[hr], v) if hw[hr] else v
    return hw


def build_gtfs(kind, g, stops_out, stop_index):
    routes = {r["route_id"]: r for r in g["routes"]}
    st = defaultdict(list)
    for r in g["stop_times"]:
        st[r["trip_id"]].append(r)
    for k in st:
        st[k].sort(key=lambda r: int(r["stop_sequence"]))
    freqs = defaultdict(list)
    for f in g.get("frequencies", []):
        freqs[f["trip_id"]].append((hms(f["start_time"]), hms(f["end_time"]), int(f["headway_secs"])))
    dts = day_types(g["calendar"])
    gstops = {s["stop_id"]: s for s in g["stops"]}

    pats = {}
    for t in g["trips"]:
        rows = st.get(t["trip_id"])
        if not rows or len(rows) < 2:
            continue
        r = routes[t["route_id"]]
        if kind == "rapid" and r["route_short_name"].upper().startswith("SUNWAY"):
            continue  # BRT dah ada sebagai rel
        seq = tuple(x["stop_id"] for x in rows)
        key = (t["route_id"], seq)
        p = pats.get(key)
        if not p:
            t0 = hms(rows[0]["departure_time"])
            cum = [max(0, hms(x["arrival_time"]) - t0) for x in rows]
            short = r["route_short_name"] or r["route_long_name"]
            head = t.get("trip_headsign") or ""
            if not head:
                last = gstops[seq[-1]]["stop_name"]
                head = last
            p = pats[key] = {"route": t["route_id"], "short": short.strip(),
                             "long": (r["route_long_name"] if r["route_short_name"] else head),
                             "head": head, "seq": seq, "cum": cum,
                             "color": "#" + (r.get("route_color") or ("8E44AD" if kind == "feeder" else "006CFF")),
                             "deps": {"wd": [], "sa": [], "su": []}, "wins": {"wd": [], "sa": [], "su": []}}
        types = dts.get(t["service_id"], set())
        if freqs.get(t["trip_id"]):
            for d in types:
                p["wins"][d].extend(freqs[t["trip_id"]])
        else:
            dep = hms(rows[0]["departure_time"])
            for d in types:
                p["deps"][d].append(dep)

    out = []
    for p in pats.values():
        hw = {}
        for d in ("wd", "sa", "su"):
            a = hourly_from_windows(p["wins"][d]) if p["wins"][d] else [0] * 24
            b = hourly_from_departures(p["deps"][d]) if p["deps"][d] else [0] * 24
            hw[d] = [min(x, y) if x and y else (x or y) for x, y in zip(a, b)]
        if not any(any(v) for v in hw.values()):
            continue
        idxs = []
        for sid in p["seq"]:
            k = (kind, sid)
            if k not in stop_index:
                s = gstops[sid]
                stop_index[k] = len(stops_out)
                nm, code = s["stop_name"].strip(), (s.get("stop_code") or "").strip()
                m = re.match(r"^([A-Z]{1,3}\d{2,5})\s+(.*)$", nm)
                if m:
                    code, nm = code or m.group(1), m.group(2)
                stops_out.append([nice(nm), round(float(s["stop_lat"]), 6), round(float(s["stop_lon"]), 6), code])
            idxs.append(stop_index[k])
        out.append({"k": kind, "r": p["short"], "rid": p["route"], "n": nice(p["long"]), "h": stops_out[idxs[-1]][0],
                    "c": p["color"], "s": idxs, "t": [round(c / 10) for c in p["cum"]],
                    "hw": [",".join(map(str, hw[d])) for d in ("wd", "sa", "su")]})
    return out


def fetch_gokl():
    q = ('[out:json][timeout:180];'
         'relation["type"="route"]["route"="bus"](2.95,101.55,3.3,101.85);'
         'relation._["network"~"GO ?KL",i]->.r;'
         '(.r;.r>;);out body;')
    last = None
    for u in OVERPASS:
        try:
            data = urllib.parse.urlencode({"data": q}).encode()
            with urllib.request.urlopen(urllib.request.Request(u, data=data, headers={"User-Agent": "jomnaik-build/1.0"}), timeout=200) as r:
                d = json.loads(r.read())
            if d.get("elements"):
                return d
        except Exception as e:  # noqa
            last = e
            print("  overpass gagal:", u, e, file=sys.stderr)
    raise RuntimeError(last)


def build_gokl(osm, stops_out):
    nodes = {e["id"]: e for e in osm["elements"] if e["type"] == "node"}
    rels = [e for e in osm["elements"] if e["type"] == "relation"]
    out = []
    gidx = {}
    for r in rels:
        tags = r.get("tags", {})
        stops = [m["ref"] for m in r["members"] if m["type"] == "node" and m.get("role", "").startswith(("stop", "platform"))
                 and m["ref"] in nodes]
        # buang pendua berturut (stop_position + platform)
        seq = []
        for nid in stops:
            n = nodes[nid]
            pt = (n["lat"], n["lon"])
            if seq and dist_m(pt, (nodes[seq[-1]]["lat"], nodes[seq[-1]]["lon"])) < 60:
                continue
            seq.append(nid)
        if len(seq) < 3:
            continue
        idxs, cum, tsec = [], [], 0
        for i, nid in enumerate(seq):
            n = nodes[nid]
            if i:
                p = nodes[seq[i - 1]]
                tsec += dist_m((p["lat"], p["lon"]), (n["lat"], n["lon"])) * 1.3 / (14 / 3.6) + 20
            if nid not in gidx:
                gidx[nid] = len(stops_out)
                nm = n.get("tags", {}).get("name") or "Hentian GoKL"
                stops_out.append([nice(nm), round(n["lat"], 6), round(n["lon"], 6), ""])
            idxs.append(gidx[nid])
            cum.append(tsec)
        ref = (tags.get("ref") or "GOKL").upper().replace("GOKL-", "GoKL ").replace("GOKL", "GoKL")
        name = tags.get("name") or ref
        short = name.split(":", 1)[-1].split("(")[0].strip()
        try:
            iv = int(tags.get("interval", "00:10").split(":")[1])
        except Exception:  # noqa
            iv = 10
        hw = ",".join(str(iv if 6 <= h < 23 else 0) for h in range(24))
        loop = "↺" in name or tags.get("roundtrip") == "yes"
        if loop:  # ulang sekali supaya boleh naik melepasi hentian pertama
            total = cum[-1] + 60
            idxs = idxs + idxs[1:]
            cum = cum + [total + c for c in cum[1:]]
        out.append({"k": "gokl", "r": ref, "rid": str(r["id"]), "n": short,
                    "h": "pusingan " + (tags.get("to") or short.split("↺")[0].strip()) if loop else (tags.get("to") or short),
                    "c": tags.get("colour") or "#7B2CBF", "s": idxs, "t": [round(c / 10) for c in cum],
                    "hw": [hw, hw, hw], "est": 1})
    return out


def main():
    stops, sidx, pats = [], {}, []
    for kind, url in FEEDS.items():
        print("Muat turun", kind, file=sys.stderr)
        pats += build_gtfs(kind, load_zip(url), stops, sidx)
    if "--refresh-gokl" in sys.argv:
        try:
            osm = fetch_gokl()
            with open(GOKL_CACHE, "w") as f:
                json.dump(osm, f)
        except Exception as e:  # noqa
            print("GoKL tidak dapat dimuat:", e, file=sys.stderr)
    if os.path.exists(GOKL_CACHE):
        pats += build_gokl(json.load(open(GOKL_CACHE)), stops)
    data = {"stops": stops, "pats": pats}
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("// Dijana oleh scripts/build_bus.py — jangan sunting manual\nwindow.BUS = ")
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    c = Counter(p["k"] for p in pats)
    print(f"OK: {len(stops)} hentian, {len(pats)} corak laluan {dict(c)} → {OUT} ({os.path.getsize(OUT)//1024} KB)", file=sys.stderr)


if __name__ == "__main__":
    main()
