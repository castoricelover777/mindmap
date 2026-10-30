# -*- coding: utf-8 -*-
"""合并所有源数据 → graph/data/graph.json（渲染器唯一输入）。

输入：concepts.json / scenario-register.json / scenario-dept.json /
      map-register.json / edges.json / themes.json
输出：graph.json
"""
import io, json, os, re, datetime
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

D = os.path.join(ROOT, "graph", "data")
OUT = os.path.join(D, "graph.json")


def rd(name):
    return json.load(io.open(os.path.join(D, name), encoding="utf-8"))


def step_no(label):
    m = re.match(r"^(\d+(?:\.\d+)*)", label.strip())
    return m.group(1) if m else None


def main():
    base = rd("concepts.json")
    lay = base["layers"]
    concepts = base["concepts"]
    dept = rd("scenario-dept.json")
    reg = rd("scenario-register.json")
    rmap = rd("map-register.json")
    edges = rd("edges.json")
    themes = rd("themes.json")

    # ---- 注册场景：套上步骤→知识点映射 ----
    reg_steps = []
    unmapped = []
    for s in reg["steps"]:
        no = step_no(s["label"])
        cids = rmap.get(no, [])
        if not cids:
            unmapped.append(s["label"])
        reg_steps.append({
            "id": s["id"], "label": s["label"], "phase": s["phase"],
            "color": s["color"], "concepts": cids, "details": s["details"],
            # path 必须保留：旧标记 r-阶段-环节-细节 靠它映射到新 id
            "path": s.get("path"),
        })
    reg["steps"] = reg_steps

    # ---- 部门场景：补 id ----
    dept_steps = []
    for i, s in enumerate(dept["steps"]):
        dept_steps.append({
            "id": "st.dept.%d" % i, "label": s["label"], "phase": s["phase"],
            "color": dept["phases"][s["phase"]]["color"],
            "concepts": s["concepts"], "details": s["details"],
        })
    dept["steps"] = dept_steps

    scenarios = [reg, dept]

    # ---- 参考资料场景（阶段〇 + 附录 A~D）：不让任何叶子节点无处可达 ----
    refmap = rd("map-ref.json")
    ref_phases, ref_steps = [], []
    for e in reg.get("extras", []):
        si = int(str(e["id"]).split(".")[-1])
        pi = len(ref_phases)
        ref_phases.append({"label": e["label"], "color": e.get("color", "#475569")})
        for ii, item in enumerate(e["items"]):
            ref_steps.append({
                "id": "st.ref.%d.%d" % (si, ii),
                "label": item["t"],
                "phase": pi,
                "color": e.get("color", "#475569"),
                "path": "r-%d-%d" % (si, ii),
                "concepts": refmap.get("%d-%d" % (si, ii), []),
                "details": item["details"],
            })
    ref = {
        "id": "s.ref", "label": "参考与附录", "sub": "阶段〇 / 附录 A~D",
        "color": "#475569", "source": "原导图的阶段〇与附录",
        "phases": ref_phases, "steps": ref_steps,
        "flow": ["总览", "时序图", "错误对照", "面试追问", "使用方法"],
        "returnNote": "这些不是业务链路，是查漏补缺用的索引页",
    }
    # ---- 员工管理场景（课件 08 + 09）----
    emp = rd("scenario-emp.json")
    emp["steps"] = [{
        "id": "st.emp.%d" % i,
        "label": st["label"],
        "phase": st["phase"],
        "color": emp["phases"][st["phase"]]["color"],
        "concepts": st["concepts"],
        "details": st["details"],
    } for i, st in enumerate(emp["steps"])]

    # ---- 班级与学员管理场景（课件 11 + 接口文档）----
    clz = rd("scenario-clazz.json")
    clz["steps"] = [{
        "id": "st.clazz.%d" % i,
        "label": st["label"],
        "phase": st["phase"],
        "color": clz["phases"][st["phase"]]["color"],
        "concepts": st["concepts"],
        "details": st["details"],
    } for i, st in enumerate(clz["steps"])]

    scenarios = [reg, dept, emp, clz, ref]

    # 链视图的「传递物」标签与回流文案：每个场景各不相同，不能写死
    reg["flow"] = ["JSON 字符串", "HTTP 请求报文", "User 对象", "insert(user)", "受影响行数 int"]
    reg["returnNote"] = "响应 JSON + 200 回到前端，渲染提示"
    dept["flow"] = ["建好表与工程环境", "列表接口跑通", "简单参数打通", "JSON 参数打通", "增删改查完成"]
    dept["returnNote"] = "每个接口都统一返回 Result{code, msg, data}"

    # ---- 统计每个概念被哪些场景用到 ----
    by_id = {c["id"]: c for c in concepts}
    for c in concepts:
        c["scenarios"] = []
        c["themes"] = []
    for sc in scenarios:
        seen = set()
        for st in sc["steps"]:
            for cid in st["concepts"]:
                if cid not in seen:
                    seen.add(cid)
                    by_id[cid]["scenarios"].append(sc["id"])
    for t in themes:
        for cid in t["members"]:
            by_id[cid]["themes"].append(t["id"])
    for c in concepts:
        c["weight"] = len(c["scenarios"])

    # ---- 场景 → 知识点 的边（推导） ----
    auto_edges = []
    for sc in scenarios:
        seen = set()
        for st in sc["steps"]:
            for cid in st["concepts"]:
                k = (sc["id"], cid)
                if k in seen:
                    continue
                seen.add(k)
                auto_edges.append({"s": sc["id"], "t": cid, "type": "uses"})

    graph = {
        "meta": {
            "built": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "layers": len(lay),
            "concepts": len(concepts),
            "scenarios": len(scenarios),
            "steps": sum(len(s["steps"]) for s in scenarios),
            "details": sum(len(st["details"]) for s in scenarios for st in s["steps"]),
            "edges": len(edges) + len(auto_edges),
            "themes": len(themes),
            "shared": sum(1 for c in concepts if c["weight"] >= 2),
        },
        "layers": lay,
        "concepts": concepts,
        "scenarios": scenarios,
        "edges": edges,
        "uses": auto_edges,
        "themes": themes,
    }

    json.dump(graph, io.open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    m = graph["meta"]
    print("graph.json 写出:", os.path.getsize(OUT), "bytes")
    print("  概念 %d / 场景 %d / 步骤 %d / 细节 %d / 关系边 %d / 母题 %d" % (
        m["concepts"], m["scenarios"], m["steps"], m["details"], m["edges"], m["themes"]))
    print("  跨场景复用的概念: %d 个" % m["shared"])
    print("\n  ---- 复用最多（真正把两条逻辑连起来的知识点）----")
    for c in sorted(concepts, key=lambda x: -x["weight"])[:14]:
        if c["weight"] >= 2:
            print("   ×%d  %-22s %s" % (c["weight"], c["label"], [s.replace("s.", "") for s in c["scenarios"]]))
    shared = [c for c in concepts if c["weight"] >= 2]
    if len(shared) < 8:
        print("  ! 复用偏少，网状价值不足")
    if unmapped:
        print("\n  ! 注册场景有 %d 个环节没匹配到知识点: %s" % (len(unmapped), unmapped[:4]))


if __name__ == "__main__":
    main()
