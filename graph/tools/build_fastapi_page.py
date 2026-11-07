# -*- coding: utf-8 -*-
"""
build_fastapi_page.py —— 生成独立的 fastapi.html（FastAPI 知识导图）

思路：复用 llm.html 那套「双向思维导图 + 标记 + 导出导入 + 手机竖排」的实现，
只替换标题 / 导航 / DATA / 存储键，内容来自 graph/data/scenario-fastapi.json。
这样 FastAPI 就不再是 graph.html 里的一个场景，而是和「数据分析」并列的独立页。

用法：python graph/tools/build_fastapi_page.py
"""
import io, json, os, re, sys
from collections import OrderedDict

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "graph", "data", "scenario-fastapi.json")
TPL = os.path.join(ROOT, "llm.html")
OUT = os.path.join(ROOT, "fastapi.html")

sc = json.load(io.open(DATA, encoding="utf-8"))

# ---------- 1) 组树：根 → 阶段 → 环节 → 细节 ----------
n_det = sum(len(st["details"]) for st in sc["steps"])
root = {
    "t": "FastAPI 后端（%d 阶段 / %d 环节）：对照 JavaWeb 学 Python Web"
         % (len(sc["phases"]), len(sc["steps"])),
    "c": [],
    "color": "#0F172A",
}
for pi, ph in enumerate(sc["phases"]):
    pnode = {"t": "%d. %s" % (pi + 1, ph["label"]), "c": [], "color": ph["color"]}
    for st in sc["steps"]:
        if st["phase"] != pi:
            continue
        snode = {"t": st["label"], "c": [], "color": ph["color"]}
        for d in st["details"]:
            snode["c"].append({"t": d, "c": [], "color": ph["color"]})
        pnode["c"].append(snode)
    root["c"].append(pnode)

# ---------- 2) 改模板 ----------
t = io.open(TPL, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in t else "\n"
t = t.replace("\r\n", "\n")
ok = True


def rep(old, new, label):
    global t, ok
    if old not in t:
        print("  FAIL", label)
        ok = False
        return
    t = t.replace(old, new, 1)
    print("  OK", label)


rep("<title>Python 数据分析（第 1~20 节）· 思维导图</title>",
    "<title>FastAPI 后端 · 对照 JavaWeb · 思维导图</title>", "title")
rep("<h1>Python 数据分析</h1>", "<h1>FastAPI 后端</h1>", "h1")
rep('<span class="sub">第 1~20 节 · 概述 + NumPy</span>',
    '<span class="sub">%d 阶段 · %d 环节 · %d 细节 · 每条标注 JavaWeb 对应物</span>'
    % (len(sc["phases"]), len(sc["steps"]), n_det), "sub")

# 导航：数据分析变成链接，FastAPI 高亮
seg_old = """<div class="seg">
      <a href="index.html">全链路图</a>
      <a href="graph.html?tab=mysql" title="MySQL 知识栏目">MySQL</a>
      <a href="https://castoricelover777.github.io/blog/" target="_blank" rel="noopener">博客源码</a>
      <a class="on">数据分析</a>
    </div>"""
seg_new = """<div class="seg">
      <a href="index.html">全链路图</a>
      <a href="graph.html?tab=mysql" title="MySQL 知识栏目">MySQL</a>
      <a href="https://castoricelover777.github.io/blog/" target="_blank" rel="noopener">博客源码</a>
      <a href="llm.html">数据分析</a>
      <a class="on">FastAPI</a>
    </div>"""
rep(seg_old, seg_new, "导航")

# DATA 整行替换
line = json.dumps(root, ensure_ascii=False, separators=(",", ":"))
m = re.search(r"^const DATA = .*;$", t, re.M)
if not m:
    print("  FAIL 找不到 DATA 行")
    ok = False
else:
    t = t[:m.start()] + "const DATA = " + line + ";" + t[m.end():]
    print("  OK DATA（%d 节点）" % (1 + len(sc["phases"]) + len(sc["steps"]) + n_det))

# 存储键独立，别和数据分析串号
rep('const LS_KEY = "mm-marks-llm-v1";', 'const LS_KEY = "mm-marks-fastapi-v1";', "LS_KEY")
rep('const LS_SEEDED = "mm-marks-seeded-v1";',
    'const LS_SEEDED = "mm-marks-fastapi-seeded-v1";', "LS_SEEDED")
t = t.replace("mm-marks-llm-backup-v1", "mm-marks-fastapi-backup-v1")

if not ok:
    print("  !! 有失败项，未写出")
    sys.exit(1)

io.open(OUT, "w", encoding="utf-8", newline=nl).write(t.replace("\n", nl))
print("  写出 %s（%.1f KB）" % (OUT, os.path.getsize(OUT) / 1024))
print("  阶段 %d / 环节 %d / 细节 %d / 树节点 %d"
      % (len(sc["phases"]), len(sc["steps"]), n_det,
         1 + len(sc["phases"]) + len(sc["steps"]) + n_det))
