# -*- coding: utf-8 -*-
"""把 content_login.py 的登录场景落成 scenario-login.json，并把新概念并入 concepts.json。
幂等：重复执行不会重复追加概念。
"""
import io, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
D = os.path.join(ROOT, "graph", "data")
sys.path.insert(0, os.path.join(ROOT, "graph", "tools"))

from content_login import LOGIN, EXTRA_CONCEPTS_LOGIN

# 1) 场景 JSON（不含 id，build_graph 统一编号）
out = os.path.join(D, "scenario-login.json")
json.dump(LOGIN, io.open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("写出", out, os.path.getsize(out), "bytes")
print("  阶段 %d / 环节 %d / 细节 %d" % (
    len(LOGIN["phases"]), len(LOGIN["steps"]), sum(len(s["details"]) for s in LOGIN["steps"])))

# 2) 概念合并
cp = os.path.join(D, "concepts.json")
data = json.load(io.open(cp, encoding="utf-8"))
have = {c["id"] for c in data["concepts"]}
added = []
for cid, label, aka, layer, gloss, learned, ep in EXTRA_CONCEPTS_LOGIN:
    if cid in have:
        continue
    data["concepts"].append({
        "id": cid, "label": label, "aka": aka, "layer": layer,
        "gloss": gloss, "learned": learned, "ep": ep,
    })
    added.append(cid)

json.dump(data, io.open(cp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("新增概念 %d 个: %s" % (len(added), ", ".join(added)))
print("concepts.json 现有 %d 个概念" % len(data["concepts"]))

# 3) 检查步骤引用的概念是否都存在
have = {c["id"] for c in data["concepts"]}
missing = sorted({cid for st in LOGIN["steps"] for cid in st["concepts"] if cid not in have})
print("缺失概念引用:", missing or "无")
