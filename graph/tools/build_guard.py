# -*- coding: utf-8 -*-
"""把 content_guard.py 的守卫场景落成 scenario-guard.json，并把新概念并入 concepts.json。幂等。"""
import io, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "graph", "data")
sys.path.insert(0, os.path.join(ROOT, "graph", "tools"))

from content_guard import GUARD, EXTRA_CONCEPTS_GUARD

out = os.path.join(D, "scenario-guard.json")
json.dump(GUARD, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("写出", out, os.path.getsize(out), "bytes")
print("  阶段 %d / 环节 %d / 细节 %d" % (
    len(GUARD["phases"]), len(GUARD["steps"]), sum(len(s["details"]) for s in GUARD["steps"])))

cp = os.path.join(D, "concepts.json")
data = json.load(io.open(cp, encoding="utf-8"))
have = {c["id"] for c in data["concepts"]}
added = []
for cid, label, aka, layer, gloss, learned, ep in EXTRA_CONCEPTS_GUARD:
    if cid in have:
        continue
    data["concepts"].append({"id": cid, "label": label, "aka": aka, "layer": layer,
                             "gloss": gloss, "learned": learned, "ep": ep})
    added.append(cid)
json.dump(data, io.open(cp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("新增概念 %d: %s" % (len(added), ", ".join(added)))
print("concepts.json 共 %d" % len(data["concepts"]))

have = {c["id"] for c in data["concepts"]}
missing = sorted({cid for st in GUARD["steps"] for cid in st["concepts"] if cid not in have})
print("缺失概念引用:", missing or "无")
