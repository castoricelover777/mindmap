# -*- coding: utf-8 -*-
"""
build_dqn_tech.py —— 生成「技术蜈蚣」独立页 dqn-tech.html（模板：index.html）

形态：复用 index.html 的 chain 视图（横向一排站卡 + 每站向下挂环节/细节），
把 DATA 一级分支做成 12 站数据流主干，每站的子节点做成「技术腿」，腿下再挂一句说明。
所以页面 = 一条真正的横线主干 + 垂直挂在下面的技术腿（蜈蚣状）。

与 dqn.html（讲解长链）互补：
  dqn.html      按叙事时间线走（七章 + 终章 + 技术蜈蚣附录）
  dqn-tech.html 按数据流走（144 维张量被哪些技术依次加工）
"""
import io, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_SRC = os.path.join(ROOT, "graph", "data", "dqn-tech.json")
TPL = os.path.join(ROOT, "index.html")
OUT = os.path.join(ROOT, "dqn-tech.html")

sc = json.load(io.open(DATA_SRC, encoding="utf-8"))
n_legs = sum(len(st["legs"]) for st in sc["stations"])
n_desc = sum(len(l["d"]) for st in sc["stations"] for l in st["legs"])

root = {
    "t": "魔方 DQN 技术蜈蚣：144 维数据的全链路技术地图",
    "c": [],
    "color": "#0F172A",
}
for st in sc["stations"]:
    snode = {"t": st["label"], "c": [], "color": st["color"]}
    for leg in st["legs"]:
        lnode = {"t": leg["t"], "c": [], "color": st["color"]}
        for d in leg["d"]:
            lnode["c"].append({"t": d, "c": [], "color": st["color"]})
        snode["c"].append(lnode)
    root["c"].append(snode)

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
    "<title>二阶魔方 DQN · 技术蜈蚣（144 维数据全链路）</title>", "title")
rep("<h1>前后端数据沟通全链路</h1>",
    "<h1>二阶魔方 DQN · 技术蜈蚣</h1>", "h1")

NAV = """<div class="seg">
      <a href="index.html">全链路图</a>
      <a href="graph.html?tab=mysql" title="MySQL 知识栏目">MySQL</a>
      <a href="https://castoricelover777.github.io/blog/" target="_blank" rel="noopener">博客源码</a>
      <a href="llm.html">数据分析</a>
      <a href="fastapi.html">FastAPI</a>
      <a href="ml.html">机器学习</a>
      <a href="dqn.html">魔方DQN</a>
      <a href="dqn-ref.html">细节版</a>
      <a class="on">蜈蚣图</a>
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
            if _esc:
                _esc = False
            elif ch == "\\":
                _esc = True
            elif ch == '"':
                _in_str = False
        else:
            if ch == '"':
                _in_str = True
            elif ch == "{":
                _depth += 1
            elif ch == "}":
                _depth -= 1
                if _depth == 0:
                    _k += 1
                    break
        _k += 1
    while _k < len(t) and t[_k] in "; \n\r\t":
        _k += 1
    t = t[:_i] + "const DATA = " + line + ";" + t[_k:]
    print("  OK DATA（%d 节点）" % (1 + len(sc["stations"]) + n_legs + n_desc))

# 存储键独立
rep('const LS_KEY = "mm-marks-v1";', 'const LS_KEY = "mm-marks-dqn-tech-v1";', "LS_KEY")
rep('const LS_SEEDED = "mm-marks-seeded-v1";',
    'const LS_SEEDED = "mm-marks-dqn-tech-seeded-v1";', "LS_SEEDED")
rep('const LS_MODE = "mm-mode-v1";', 'const LS_MODE = "mm-mode-dqn-tech-v1";', "LS_MODE")

# 内置标记清空（模板的 228 条是 index 的路径，对不上本页）
m2 = re.search(r"const MARK_DEFAULTS = \{.*?\};", t, re.S)
if not m2:
    print("  FAIL 找不到 MARK_DEFAULTS")
    ok = False
else:
    t = t[:m2.start()] + "const MARK_DEFAULTS = {};" + t[m2.end():]
    print("  OK MARK_DEFAULTS 清空")

# 默认打开长链模式
OLD_MODE = re.search(r'if \(q\.get\("mode"\) === "chain".*?catch\(e\)\{\}\s*\}', t, re.S)
OLD_MODE = OLD_MODE.group(0) if OLD_MODE else ""
NEW_MODE = '''if (q.get("mode") === "mind") m = "mind";
  else m = "chain";            /* 蜈蚣图默认横版长链，?mode=mind 可切回脑图 */'''
if OLD_MODE in t:
    t = t.replace(OLD_MODE, NEW_MODE, 1)
    print("  OK 默认打开长链模式")
else:
    print("  FAIL 找不到 mode 初始化块")
    ok = False

# 链视图取全部一级分支
rep("const CHAIN = DATA.c.slice(1, 7).map(", "const CHAIN = DATA.c.map(", "链视图取全部站点")

# 站与站之间的传递物标签（11 条，对应 12 站）
FLOW_JS = "const FLOW = " + json.dumps(sc["flow"], ensure_ascii=False) + ";"
t2, _n2 = re.subn(r"const FLOW = \[[^\]]*\];", FLOW_JS, t, count=1)
if _n2:
    t = t2
    print("  OK 站间传递物标签（%d 条）" % len(sc["flow"]))
else:
    print("  FAIL 找不到 FLOW")
    ok = False

# 底部回流箭头（模板里是「响应 JSON 回到前端」）：这里改成训练循环的语义
rep('"响应 JSON + 200 回到前端，渲染提示"',
    '"一次迭代完成 → 采下一个 batch，进入下一轮训练循环"', "回流箭头文案")

# 顶栏文案
rep('<span class="sub" id="brandsub">用户注册案例 · 六段式时序</span>',
    '<span class="sub" id="brandsub">12 站主干 · 61 条技术腿 · 每条腿挂术语毛</span>', "副标题(HTML)")
rep('$("brandsub").textContent = mind ? "用户注册案例 · 六段式时序" : "用户注册案例 · 一条链走完 6 个阶段";',
    '$("brandsub").textContent = mind ? "技术蜈蚣 · 脑图总览" : "12 站主干 · 61 条技术腿 · 每条腿挂术语毛";',
    "副标题(JS)")
rep('document.title = "前后端数据沟通全链路 · " + (mind ? "思维导图" : "长链图");',
    'document.title = "二阶魔方 DQN · 技术蜈蚣";', "document.title")
rep("<b>点阶段</b>收起/展开环节 · <b>点环节</b>看细节 · <b>滚轮</b>缩放 · <b>拖拽</b>平移",
    "<b>点站点</b>收起/展开技术腿 · <b>点技术腿</b>看详解与术语毛 · <b>滚轮</b>缩放 · <b>拖拽</b>平移",
    "操作提示")

# 本页不参与标记（无快照、chain 视角也没有标记入口）：隐藏标记按钮、统计圆点，保持顶栏干净
t = t.replace(
    "</style>",
    "\nsvg g.mk{display:none}\n"
    "#btn-author,#btn-export,#btn-import,#btn-reset,#file-import,#stats{display:none!important}\n"
    "</style>", 1)

# 初始视图：整条主干太长，默认按可读比例展示 A.1 起头，用户拖拽/滚轮看全链；「适应窗口」看全景
INIT = '''<script>
/* 初始视图：优先保证技术腿文字可读（点「适应窗口」可看整条主干全景） */
(function(){
  function readableInitial(){
    try{
      var st = ChainView.state;
      if (!st || typeof svg === "undefined" || !svg.clientWidth) return;
      var TARGET = 0.72;
      if (st.scale >= TARGET) return;
      st.scale = TARGET;
      st.tx = 46;
      st.ty = 112;
      ChainView.render(true);   /* 按目标缩放整页重绘一次，避免只改 transform 造成的文字重影 */
      var z = document.getElementById("zoomval");
      if (z) z.textContent = Math.round(TARGET*100) + "%";
    }catch(e){}
  }
  if (document.readyState === "complete") setTimeout(readableInitial, 220);
  else window.addEventListener("load", function(){ setTimeout(readableInitial, 220); });
})();
</script>
</body>'''
if "</body>" in t:
    t = t.replace("</body>", INIT, 1)
    print("  OK 初始可读视图")
else:
    print("  FAIL 找不到 </body>")
    ok = False

if not ok:
    print("  !! 有失败项，未写出")
    sys.exit(1)
io.open(OUT, "w", encoding="utf-8", newline=nl).write(t.replace("\n", nl))
print("  写出 %s（%.1f KB）" % (OUT, os.path.getsize(OUT) / 1024))
print("  %d 站 / %d 技术腿 / %d 条说明 / %d 个树节点"
      % (len(sc["stations"]), n_legs, n_desc,
         1 + len(sc["stations"]) + n_legs + n_desc))
