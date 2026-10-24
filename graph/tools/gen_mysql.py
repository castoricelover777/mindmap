import io, re, json, os

SRC = r"E:\mindmap\graph\_src"
OUT = r"E:\mindmap\graph\data\mysql.json"
P = r"C:\Users\Admin1\AppData\Local\Temp\mm_graph\build_page.py"

H1 = re.compile(r"^(\d+)\.\s+(\S.{0,40})$")
H2 = re.compile(r"^(\d+\.\d+)\s+(\S.{0,40})$")
H3 = re.compile(r"^(\d+\.\d+\.\d+)\s+(\S.{0,40})$")
H4 = re.compile(r"^(\d+\.\d+\.\d+\.\d+)\s+(\S.{0,40})$")


def clean(t):
    t = t.replace("[[图片]]", "").replace("--- [1x1] ---", "")
    t = t.replace("点击图片可查看完整电子表格", "")
    t = re.sub(r"https?://\S+", "", t)
    return t.strip()


def split_code(line):
    if not line.startswith("SQL / "):
        return None
    parts = [p.strip() for p in line[len("SQL / "):].split(" / ")]
    parts = [p.strip() for p in parts if p and p.strip() != "SQL"]
    return "\n".join(parts)


def parse(fn, tag):
    lines = [clean(x) for x in io.open(os.path.join(SRC, fn), encoding="utf-8").read().split("\n")]
    chapters, cur_c, cur_g, cur_p = [], None, None, None

    def ensure_chapter(title):
        for c in chapters:
            if c["label"] == title:
                return c
        c = {"id": "c" + tag + str(len(chapters)), "label": title, "groups": []}
        chapters.append(c)
        return c

    for t in lines:
        if not t:
            continue
        m = H4.match(t) or H3.match(t) or H2.match(t) or H1.match(t)
        if m:
            num, title = m.group(1), m.group(2).strip()
            depth = num.count(".") + 1
            if depth == 1:
                cur_c = ensure_chapter(title)
                cur_g = None
                cur_p = None
            elif depth == 2:
                if cur_c is None:
                    cur_c = ensure_chapter("其他")
                cur_g = {"id": "g" + tag + num, "label": title, "points": []}
                cur_c["groups"].append(cur_g)
                cur_p = None
            elif depth >= 3 and cur_g is not None:
                cur_p = {"id": "p" + tag + num, "label": title, "text": [], "code": [], "tips": []}
                cur_g["points"].append(cur_p)
            continue
        if cur_p is None:
            continue
        code = split_code(t)
        if code:
            if len(code) > 3:
                cur_p["code"].append(code)
            continue
        if len(t) > 1 and any(t.startswith(k) for k in ("注意", "结论", "说明", "作用", "概念")):
            cur_p["tips"].append(t[:120])
            continue
        if len(t) > 8 and len(cur_p["text"]) < 3:
            cur_p["text"].append(t[:160])
    return chapters


chapters = parse("05-数据库.txt", "a") + parse("06-java操作数据库.txt", "b")

# 合并同名的「其他」章节，清理空组/空点
merged = []
for ch in chapters:
    hit = next((m for m in merged if m["label"] == ch["label"]), None)
    if hit:
        hit["groups"].extend(ch["groups"])
    else:
        merged.append(ch)
chapters = []
for ch in merged:
    ch["groups"] = [g for g in ch["groups"] if any(p["text"] or p["code"] or p["tips"] for p in g["points"])]
    if ch["groups"]:
        for g in ch["groups"]:
            g["points"] = [p for p in g["points"] if p["text"] or p["code"] or p["tips"]]
        chapters.append(ch)

groups_n = sum(len(c["groups"]) for c in chapters)
points_n = sum(len(g["points"]) for c in chapters for g in c["groups"])
code_n = sum(1 for c in chapters for g in c["groups"] for p in g["points"] if p["code"])
print("章节:", len(chapters), "组:", groups_n, "知识点:", points_n, "带代码:", code_n)
for c in chapters:
    print("  %-18s %d 组 / %d 点" % (c["label"][:16], len(c["groups"]),
                                    sum(len(g["points"]) for g in c["groups"])))

io.open(OUT, "w", encoding="utf-8").write(json.dumps({
    "meta": {"title": "MySQL", "chapters": len(chapters), "groups": groups_n,
             "points": points_n, "withCode": code_n,
             "source": "课件 05-数据库 / 06-java操作数据库 + 笔记 day6~7"},
    "chapters": chapters}, ensure_ascii=False, indent=1))
print("json:", os.path.getsize(OUT), "bytes")

# ---------------- 渲染器改成三级 ----------------
s = io.open(P, encoding="utf-8").read()
a = s.index("/* ================= MySQL 栏目 ================= */")
b = s.index("function openPanel(cid){")
NEW_JS = r'''/* ================= MySQL 栏目（章节 → 组 → 知识点，三级可折叠） ================= */
const MV_COLORS = ["#2563eb", "#0E7490", "#7c3aed", "#dc2626", "#059669", "#ea580c"];
let mysqlBuilt = false;
function mEsc(x){
  return String(x).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}
function buildMysql(){
  if (mysqlBuilt) return;
  mysqlBuilt = true;
  $("mv-body").innerHTML = MYSQL.chapters.map((ch, ci) => {
    const col = MV_COLORS[ci % MV_COLORS.length];
    const groups = ch.groups.map((g, gi) => {
      const pts = g.points.map(p => {
        const n = (p.code || []).length;
        const txt = (p.text || []).map(t => `<div class="ms">${mEsc(t)}</div>`).join("");
        const tip = (p.tips || []).slice(0, 1).map(t => `<div class="mo">⚠ ${mEsc(t)}</div>`).join("");
        const code = n ? `<details class="mcode"><summary>代码示例 · ${n} 段</summary>`
          + p.code.map(c => `<pre>${mEsc(c)}</pre>`).join("") + "</details>" : "";
        return `<details class="mpoint"><summary><span class="mt">${mEsc(p.label)}</span>`
          + (n ? `<i class="mc">${n}</i>` : "") + `</summary>`
          + `<div class="mpb">${txt}${tip}${code}</div></details>`;
      }).join("");
      const open = (ci === 0 && gi === 0) ? " open" : "";
      return `<details class="mgroup"${open}><summary><i class="dot" style="background:${col}"></i>`
        + `${mEsc(g.label)}<span>${g.points.length}</span></summary>`
        + `<div class="mgb">${pts}</div></details>`;
    }).join("");
    const n = ch.groups.reduce((a, g) => a + g.points.length, 0);
    return `<div class="mv-col"><h3 style="color:${col}"><i class="dot" style="background:${col}"></i>`
      + `${mEsc(ch.label)}<span>${ch.groups.length} 组 · ${n} 点</span></h3>${groups}</div>`;
  }).join("");
  $("mv-stat").textContent = MYSQL.meta.chapters + " 章 · " + MYSQL.meta.groups + " 组 · "
    + MYSQL.meta.points + " 个知识点 · " + MYSQL.meta.withCode + " 段代码 · 来源：" + MYSQL.meta.source;
}
function setMysqlView(on){
  $("mysqlview").classList.toggle("show", on);
  $("tab-mysql").classList.toggle("on", on);
  $("tab-graph").classList.toggle("on", !on);
  if (on) buildMysql();
}
'''
s = s[:a] + NEW_JS + s[b:]

# CSS：列宽 + 三级折叠样式
s = s.replace(".mv-col{flex:1 1 336px;max-width:420px;min-width:300px;",
              ".mv-col{flex:1 1 420px;max-width:560px;min-width:330px;")
extra = '''
  .mv-col h3 i.dot, .mgroup>summary i.dot{width:8px;height:8px;border-radius:50%;flex:0 0 8px}
  .mgroup{border:1px solid #eeeae2;border-radius:9px;margin-bottom:8px;background:#fcfbf9;overflow:hidden}
  .mgroup>summary{list-style:none;cursor:pointer;padding:9px 11px;font-size:12px;font-weight:800;
    color:#374151;display:flex;align-items:center;gap:7px;user-select:none}
  .mgroup>summary::-webkit-details-marker{display:none}
  .mgroup>summary span{margin-left:auto;font-size:10px;color:#9ca3af;font-weight:700}
  .mgroup>summary::after{content:"▸";font-size:9px;color:#b6b1a8;margin-left:6px;transition:transform .16s}
  .mgroup[open]>summary::after{transform:rotate(90deg)}
  .mgb{padding:0 9px 9px}
  .mpoint{border:1px solid #f1ede6;border-left:3px solid #cbd5e1;border-radius:7px;background:#fff;
    margin-bottom:6px;overflow:hidden}
  .mpoint>summary{list-style:none;cursor:pointer;padding:8px 10px;display:flex;align-items:center;gap:6px;
    user-select:none}
  .mpoint>summary::-webkit-details-marker{display:none}
  .mpoint>summary .mt{font-size:11.5px;font-weight:700;color:#111827;line-height:1.45}
  .mpoint>summary .mc{margin-left:auto;font-style:normal;font-size:9px;font-weight:800;color:#2563eb;
    background:#eff6ff;border-radius:4px;padding:1px 5px}
  .mpoint[open]>summary{border-bottom:1px solid #f3f0ea}
  .mpb{padding:8px 10px 9px}
  .mpb .mcode{font-size:10px;font-weight:700;color:#2563eb;cursor:pointer;margin-top:6px}
  .mpb .mcode>summary{list-style:none}
  .mpb .mcode>summary::-webkit-details-marker{display:none}
'''
if ".mgroup{" not in s:
    s = s.replace('"""\n\nBODY = r"""', extra + '"""\n\nBODY = r"""', 1)

io.open(P, "w", encoding="utf-8").write(s)
print("renderer patched")
