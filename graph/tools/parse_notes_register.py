# -*- coding: utf-8 -*-
"""1) 建立笔记日期索引（课件章节 → 学习日期）
2) 把现有注册导图（index.html 的嵌套 DATA）转成场景 JSON

输出：
  graph/data/notes-index.json
  graph/data/scenario-register.json
"""
import io, json, os, re

OUT_DIR = r"E:\mindmap\graph\data"
NOTES = r"F:\JavaBlog\src\main\webapp\data\notes.json"
INDEX_HTML = r"E:\mindmap-backup-20261023-133052\index.html"

os.makedirs(OUT_DIR, exist_ok=True)


# ---------------- 1. 笔记索引 ----------------
def parse_range(title):
    """从标题里抓集数范围，如（第80~84集）（第 70/200）（第1~10集）"""
    m = re.search(r"第\s*(\d+)\s*[~\-－]\s*(\d+)\s*集", title)
    if m:
        return int(m.group(1)), int(m.group(2))
    m = re.search(r"第\s*(\d+)\s*/\s*(\d+)", title)
    if m:
        return int(m.group(1)), int(m.group(1))
    m = re.search(r"第\s*(\d+)\s*集", title)
    if m:
        return int(m.group(1)), int(m.group(1))
    return None


def build_notes_index():
    data = json.load(io.open(NOTES, encoding="utf-8"))
    rows = []
    for n in data:
        rng = parse_range(n.get("title", ""))
        rows.append({
            "id": n.get("id"),
            "date": n.get("date"),
            "title": n.get("title"),
            "category": n.get("category"),
            "episodes": list(rng) if rng else None,
            "chars": len(n.get("content") or ""),
        })
    rows.sort(key=lambda r: (r["date"] or ""))
    return rows


# ---------------- 2. 注册导图 → 场景 ----------------
def extract_data(html_path):
    src = io.open(html_path, encoding="utf-8").read()
    i = src.index("const DATA = ") + len("const DATA = ")
    while src[i] != "{":
        i += 1
    start = i
    depth = 0
    in_str = False
    esc = False
    while i < len(src):
        ch = src[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(src[start:i + 1])
        i += 1
    raise ValueError("unbalanced")


STAGE_PHASE = re.compile(r"^阶段[〇一二三四五六七]")


def build_register_scene():
    DATA = extract_data(INDEX_HTML)
    phases, steps, extras = [], [], []
    for si, stage in enumerate(DATA["c"]):
        title = stage["t"]
        is_phase = bool(re.match(r"^阶段[一二三四五六]", title))
        kids = stage.get("c") or []
        if is_phase:
            pidx = len(phases)
            phases.append({"label": title, "color": stage.get("color", "#334155")})
            for ii, item in enumerate(kids):
                details = [c["t"] for c in (item.get("c") or [])]
                steps.append({
                    "id": "st.register.%d.%d" % (pidx + 1, ii),
                    "label": item["t"],
                    "phase": pidx,
                    "color": stage.get("color", "#334155"),
                    "path": "r-%d-%d" % (si, ii),
                    "details": details,
                })
        else:
            # 阶段〇 与 附录 A~D：作为参考资料单独存
            extras.append({
                "id": "ex.register.%d" % si,
                "label": title,
                "color": stage.get("color", "#475569"),
                "items": [
                    {"t": it["t"], "details": [c["t"] for c in (it.get("c") or [])]}
                    for it in kids
                ],
            })
    return {
        "id": "s.register",
        "label": "用户注册全链路",
        "sub": "前端点击 → 落库 → 响应",
        "color": "#2563EB",
        "source": "source.md / 原思维导图",
        "phases": phases,
        "steps": steps,
        "extras": extras,
    }


def main():
    notes = build_notes_index()
    with io.open(os.path.join(OUT_DIR, "notes-index.json"), "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=1)
    print("notes-index: %d 篇" % len(notes))
    for r in notes:
        print("   %s  %-22s 集数=%s" % (r["date"], r["title"][:22], r["episodes"]))

    reg = build_register_scene()
    with io.open(os.path.join(OUT_DIR, "scenario-register.json"), "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=1)
    print("\nscenario-register: %d 阶段 / %d 环节 / %d 细节 / %d 附录组" % (
        len(reg["phases"]), len(reg["steps"]),
        sum(len(s["details"]) for s in reg["steps"]), len(reg["extras"])))
    print("\n--- 44 个环节标题 ---")
    for s in reg["steps"]:
        print("  [P%d] %s  (细节 %d)" % (s["phase"], s["label"][:40], len(s["details"])))


if __name__ == "__main__":
    main()
