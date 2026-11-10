# -*- coding: utf-8 -*-
"""
build_ml_page.py —— 生成独立的 ml.html（机器学习 · 大白话版导图）

复用 llm.html 的「双向思维导图 + 标记 + 导出导入 + 手机竖排」实现，
内容来自 graph/data/ml-tree.json（由 content_ml.py 生成）。
"""
import io, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "graph", "data", "ml-tree.json")
TPL = os.path.join(ROOT, "llm.html")
OUT = os.path.join(ROOT, "ml.html")

sc = json.load(io.open(DATA, encoding="utf-8"))
n_det = sum(len(st["details"]) for st in sc["steps"])

root = {
    "t": "机器学习（吴恩达 2025 前 %d 集）：用大白话讲懂" % 32,
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
    "<title>机器学习（吴恩达 2025 前 32 集）· 大白话思维导图</title>", "title")
rep("<h1>Python 数据分析</h1>", "<h1>机器学习</h1>", "h1")
rep('<span class="sub">第 1~20 节 · 概述 + NumPy</span>',
    '<span class="sub">%d 分支 · %d 环节 · %d 细节 · 每个概念都有生活类比</span>'
    % (len(sc["phases"]), len(sc["steps"]), n_det), "sub")

# 导航：整块替换（不依赖其它页的当前形态）
NAV = """<div class="seg">
      <a href="index.html">全链路图</a>
      <a href="graph.html?tab=mysql" title="MySQL 知识栏目">MySQL</a>
      <a href="https://castoricelover777.github.io/blog/" target="_blank" rel="noopener">博客源码</a>
      <a href="llm.html">数据分析</a>
      <a href="fastapi.html">FastAPI</a>
      <a class="on">机器学习</a>
      <a href="dqn.html">魔方DQN</a>
    </div>"""
t2, n = re.subn(r'(?s)<div class="seg">.*?</div>', NAV, t, count=1)
if n == 0:
    print("  FAIL 导航")
    ok = False
else:
    t = t2
    print("  OK 导航")

line = json.dumps(root, ensure_ascii=False, separators=(",", ":"))
m = re.search(r"^const DATA = .*;$", t, re.M)
if not m:
    print("  FAIL DATA")
    ok = False
else:
    t = t[:m.start()] + "const DATA = " + line + ";" + t[m.end():]
    print("  OK DATA（%d 节点）" % (1 + len(sc["phases"]) + len(sc["steps"]) + n_det))

rep('const LS_KEY = "mm-marks-llm-v1";', 'const LS_KEY = "mm-marks-ml-v1";', "LS_KEY")

# 播种键：llm.html 模板已升到自己的 v2；机器学习页再换成 ml 专用 v2（避免两边串号）
_m = re.search(r'^const LS_SEEDED = "[^"]+";$', t, re.M)
if _m:
    t = t[:_m.start()] + 'const LS_SEEDED = "mm-marks-ml-seeded-v2";' + t[_m.end():]
    print("  OK LS_SEEDED")
else:
    print("  FAIL LS_SEEDED")
    ok = False
t = t.replace("mm-marks-llm-backup-v1", "mm-marks-ml-backup-v1")

# 内置标记：把作者默认基线内联成 MARK_DEFAULTS（模板自带的是 llm 的，整行替换）
MARKS = os.path.join(ROOT, "graph", "data", "ml-marks.json")
if os.path.exists(MARKS):
    marks = json.load(io.open(MARKS, encoding="utf-8"))["marks"]
    mk_line = json.dumps(marks, ensure_ascii=False, separators=(",", ":"))
    m2 = re.search(r"^const MARK_DEFAULTS = .*;$", t, re.M)
    if m2:
        t = t[:m2.start()] + "const MARK_DEFAULTS = " + mk_line + ";" + t[m2.end():]
        print("  OK MARK_DEFAULTS（%d 条）" % len(marks))
    else:
        print("  FAIL 找不到 MARK_DEFAULTS")
        ok = False
else:
    print("  FAIL 缺少 %s" % MARKS)
    ok = False

if not ok:
    print("  !! 有失败项，未写出")
    sys.exit(1)
io.open(OUT, "w", encoding="utf-8", newline=nl).write(t.replace("\n", nl))
print("  写出 %s（%.1f KB）" % (OUT, os.path.getsize(OUT) / 1024))
