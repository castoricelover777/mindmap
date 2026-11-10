# -*- coding: utf-8 -*-
"""
build_dqn_chain.py —— 生成「讲解流程版」长链页 dqn.html（模板：index.html）

index.html 自带 mind / chain 两种模式，链视图正好把一级分支画成横向长链。
本脚本只替换：标题 / 导航 / DATA / 存储键 / 默认模式（默认 chain）。
"""
import io, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_SRC = os.path.join(ROOT, "graph", "data", "dqn-story.json")
TPL = os.path.join(ROOT, "index.html")
OUT = os.path.join(ROOT, "dqn.html")

sc = json.load(io.open(DATA_SRC, encoding="utf-8"))
n_det = sum(len(st["details"]) for st in sc["steps"])

root = {
    "t": "二阶魔方 DQN：从 2.4% 到 94.75% 的全流程复盘（八章）",
    "c": [],
    "color": "#0F172A",
}
for pi, ph in enumerate(sc["phases"]):
    pnode = {"t": ph["label"], "c": [], "color": ph["color"]}
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
t = re.sub(r"\n[ \t]*\n(?:[ \t]*\n)*", "\n", t)   # 压平 index.html 的空行
ok = True


def rep(old, new, label):
    global t, ok
    if old not in t:
        print("  FAIL", label)
        ok = False
        return
    t = t.replace(old, new, 1)
    print("  OK", label)


rep("<title>前后端数据沟通全链路 · 思维导图</title>",
    "<title>二阶魔方 DQN · 讲解流程长链图</title>", "title")
rep("<h1>前后端数据沟通全链路</h1>", "<h1>二阶魔方 DQN · 讲解流程</h1>", "h1")

NAV = """<div class="seg">
      <a href="index.html">全链路图</a>
      <a href="graph.html?tab=mysql" title="MySQL 知识栏目">MySQL</a>
      <a href="https://castoricelover777.github.io/blog/" target="_blank" rel="noopener">博客源码</a>
      <a href="llm.html">数据分析</a>
      <a href="fastapi.html">FastAPI</a>
      <a href="ml.html">机器学习</a>
      <a class="on">魔方DQN</a>
      <a href="dqn-ref.html" title="技术细节版（10 层知识树）">细节版</a>
    </div>"""
t2, _n = re.subn(r'(?s)<div class="seg">.*?</div>', NAV, t, count=1)
if _n == 0:
    print("  FAIL 导航")
    ok = False
else:
    t = t2
    print("  OK 导航")

line = json.dumps(root, ensure_ascii=False, separators=(",", ":"))
_i = t.find("const DATA = ")
if _i < 0:
    print("  FAIL 找不到 DATA")
    ok = False
else:
    _j = t.find("{", _i)
    _depth = 0
    _in_str = False
    _esc = False
    _k = _j
    while _k < len(t):
        ch = t[_k]
        if _in_str:
            if _esc: _esc = False
            elif ch == "\\": _esc = True
            elif ch == '"': _in_str = False
        else:
            if ch == '"': _in_str = True
            elif ch == "{": _depth += 1
            elif ch == "}":
                _depth -= 1
                if _depth == 0:
                    _k += 1
                    break
        _k += 1
    while _k < len(t) and t[_k] in "; \n\r\t":
        _k += 1
    t = t[:_i] + "const DATA = " + line + ";" + t[_k:]
    print("  OK DATA（%d 节点）" % (1 + len(sc["phases"]) + len(sc["steps"]) + n_det))

# 存储键独立（避免和 index.html / 细节版串号）
rep('const LS_KEY = "mm-marks-v1";', 'const LS_KEY = "mm-marks-dqn-story-v1";', "LS_KEY")
rep('const LS_SEEDED = "mm-marks-seeded-v1";',
    'const LS_SEEDED = "mm-marks-dqn-story-seeded-v1";', "LS_SEEDED")
rep('const LS_MODE = "mm-mode-v1";', 'const LS_MODE = "mm-mode-dqn-v1";', "LS_MODE")

# 内置标记清空（模板里的 228 条是 index 的路径，对不上本页）
m2 = re.search(r"const MARK_DEFAULTS = \{.*?\};", t, re.S)
if not m2:
    print("  FAIL 找不到 MARK_DEFAULTS")
    ok = False
else:
    t = t[:m2.start()] + "const MARK_DEFAULTS = {};" + t[m2.end():]
    print("  OK MARK_DEFAULTS 清空（讲解版从零标）")

# 默认打开长链模式：没有 ?mode=mind 就默认 chain
OLD_MODE = re.search(r'if \(q\.get\("mode"\) === "chain".*?catch\(e\)\{\}\s*\}', t, re.S)
OLD_MODE = OLD_MODE.group(0) if OLD_MODE else ""
NEW_MODE = '''if (q.get("mode") === "mind") m = "mind";
  else m = "chain";            /* 讲解版默认长链，?mode=mind 可切回脑图 */'''
if OLD_MODE in t:
    t = t.replace(OLD_MODE, NEW_MODE, 1)
    print("  OK 默认打开长链模式")
else:
    print("  FAIL 找不到 mode 初始化块")
    ok = False


# 链视图只取 DATA.c.slice(1,7)：改成全部章节（现在是 9 章）
rep("const CHAIN = DATA.c.slice(1, 7).map(", "const CHAIN = DATA.c.map(", "链视图取全部章节")

# 链上的传递物标签：换成 DQN 的讲解流向（8 条，对应 9 章之间的箭头）
t2, _n2 = re.subn(
    r"const FLOW = \[[^\]]*\];",
    'const FLOW = ["排雷 2.4%→87.5%", "底层能跑（课程学习）", "顶层 IL 热启动", '
    '"合体兜底 93.5%", "换标尺蒸馏 -46%", "负结果封存 94.75%", "宏观×微观融合", "面试话术"];',
    t, count=1)
if _n2:
    t = t2
    print("  OK 链视图传递物标签")
else:
    print("  FAIL 找不到 FLOW")
    ok = False

# 副标题
rep('<span class="sub" id="brandsub">用户注册案例 · 六段式时序</span>',
    '<span class="sub" id="brandsub">八章讲解 · 一条链从 2.4% 走到 94.75%</span>', "副标题(HTML)")
rep('$("brandsub").textContent = mind ? "用户注册案例 · 六段式时序" : "用户注册案例 · 一条链走完 6 个阶段";',
    '$("brandsub").textContent = mind ? "八章讲解 · 脑图总览" : "八章讲解 · 一条链从 2.4% 走到 94.75%";',
    "副标题(JS)")

if not ok:
    print("  !! 有失败项，未写出")
    sys.exit(1)
io.open(OUT, "w", encoding="utf-8", newline=nl).write(t.replace("\n", nl))
print("  写出 %s（%.1f KB）" % (OUT, os.path.getsize(OUT) / 1024))
print("  %d 章 / %d 环节 / %d 细节 / %d 树节点"
      % (len(sc["phases"]), len(sc["steps"]), n_det,
         1 + len(sc["phases"]) + len(sc["steps"]) + n_det))
