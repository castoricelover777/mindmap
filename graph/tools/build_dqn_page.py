# -*- coding: utf-8 -*-
"""
build_dqn_page.py —— 生成独立的 dqn.html（二阶魔方 DQN 项目导图）

复用 llm.html 的双向导图实现，内容来自 graph/data/dqn-tree.json（content_dqn.py 生成）。
"""
import io, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "graph", "data", "dqn-tree.json")
TPL = os.path.join(ROOT, "llm.html")
MARKS = os.path.join(ROOT, "graph", "data", "dqn-marks.json")
OUT = os.path.join(ROOT, "dqn-ref.html")

sc = json.load(io.open(DATA, encoding="utf-8"))
n_det = sum(len(st["details"]) for st in sc["steps"])
_marks = {}
try:
    _mk = json.load(io.open(MARKS, encoding="utf-8"))
    _marks = _mk.get("marks", _mk) if isinstance(_mk, dict) else {}
except Exception:
    _marks = {}

root = {"t": "二阶魔方 DQN：从 3,674,160 个状态到 93.5% 端到端", "c": [], "color": "#0F172A"}
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
    "<title>二阶魔方 DQN · 技术细节版（10 层知识树）</title>", "title")
rep("<h1>Python 数据分析</h1>", "<h1>二阶魔方 DQN · 细节版</h1>", "h1")
rep('<span class="sub">第 1~20 节 · 概述 + NumPy</span>',
    '<span class="sub">%d 层 · %d 环节 · %d 细节 · 全数字可回溯原文</span>'
    % (len(sc["phases"]), len(sc["steps"]), n_det), "sub")

NAV = """<div class="seg">
      <a href="index.html">全链路图</a>
      <a href="graph.html?tab=mysql" title="MySQL 知识栏目">MySQL</a>
      <a href="https://castoricelover777.github.io/blog/" target="_blank" rel="noopener">博客源码</a>
      <a href="llm.html">数据分析</a>
      <a href="fastapi.html">FastAPI</a>
      <a href="ml.html">机器学习</a>
      <a href="dqn.html">魔方DQN</a>
      <a class="on">细节版</a>
      <a href="dqn-tech.html" title="技术蜈蚣（横向主干 + 垂直技术腿）">蜈蚣图</a>
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

rep('const LS_KEY = "mm-marks-llm-v1";', 'const LS_KEY = "mm-marks-dqn-v1";', "LS_KEY")
# 模板（llm.html）现在自带作者默认标记，播种键已升到 llm 专用 v2；这里按「任意旧值」替换
_m = re.search(r'^const LS_SEEDED = "[^"]+";$', t, re.M)
if _m:
    t = t[:_m.start()] + 'const LS_SEEDED = "mm-marks-dqn-seeded-v1";' + t[_m.end():]
    print("  OK LS_SEEDED")
else:
    print("  FAIL LS_SEEDED")
    ok = False
t = t.replace("mm-marks-llm-backup-v1", "mm-marks-dqn-backup-v1")

# 内置标记：把导出快照内联成 MARK_DEFAULTS
if _marks:
    _mk_line = json.dumps(_marks, ensure_ascii=False, separators=(",", ":"))
    _hit = re.search(r"^const MARK_DEFAULTS = .*;$", t, re.M)
    if _hit:
        t = t[:_hit.start()] + "const MARK_DEFAULTS = " + _mk_line + ";" + t[_hit.end():]
        print("  OK MARK_DEFAULTS（%d 条）" % len(_marks))
    else:
        print("  FAIL 找不到空的 MARK_DEFAULTS")
        ok = False

NEW_SEED = '''function seedAuthorMarks(){
  try{
    if (localStorage.getItem(LS_SEEDED)) return 0;
    const defaults = MARK_DEFAULTS || {};
    const keys = Object.keys(defaults);
    if (!keys.length){ localStorage.setItem(LS_SEEDED, "1"); return 0; }
    let n = 0;
    keys.forEach(k => {
      const v = defaults[k];
      if (!state.marks[k] && v >= 1 && v <= 3){ state.marks[k] = v; n++; }
    });
    if (n) saveMarks();
    localStorage.setItem(LS_SEEDED, "1");
    return n;
  }catch(e){ return 0; }
}'''
_i = t.find("function seedAuthorMarks(){")
if _i < 0:
    print("  FAIL 找不到 seedAuthorMarks")
    ok = False
else:
    _depth = 0
    _j = _i
    while _j < len(t):
        if t[_j] == "{":
            _depth += 1
        elif t[_j] == "}":
            _depth -= 1
            if _depth == 0:
                _j += 1
                break
        _j += 1
    t = t[:_i] + NEW_SEED + t[_j:]
    print("  OK seedAuthorMarks 改为补齐空缺")

rep('const LS_SEEDED = "mm-marks-dqn-seeded-v1";',
    'const LS_SEEDED = "mm-marks-dqn-seeded-v2";', "LS_SEEDED 升 v2")

if not ok:
    print("  !! 有失败项，未写出")
    sys.exit(1)
io.open(OUT, "w", encoding="utf-8", newline=nl).write(t.replace("\n", nl))
print("  写出 %s（%.1f KB）" % (OUT, os.path.getsize(OUT) / 1024))
