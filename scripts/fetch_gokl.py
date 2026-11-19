#!/usr/bin/env python3
"""Muat turun laluan GoKL dari OpenStreetMap API (relation/full) → scripts/gokl_osm.json.
ID relation dijumpai dengan imbasan map.json sekitar KL (Overpass sering tak stabil)."""
import json, os, sys, urllib.request

IDS = [6479785, 6476228, 6477886, 6477887, 14757592, 20799361, 20799411, 20799414]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gokl_osm.json")
els = {}
for rid in IDS:
    with urllib.request.urlopen(f"https://api.openstreetmap.org/api/0.6/relation/{rid}/full.json", timeout=60) as r:
        d = json.loads(r.read())
    for e in d["elements"]:
        if e["type"] == "node" or (e["type"] == "relation" and e["id"] == rid):
            els[(e["type"], e["id"])] = e
    print("ok", rid, file=sys.stderr)
json.dump({"elements": list(els.values())}, open(OUT, "w"))
print("→", OUT, len(els), file=sys.stderr)
