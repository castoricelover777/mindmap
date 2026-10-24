# -*- coding: utf-8 -*-
"""Build merged index.html: mindmap + chain in one page, one bottom-right mode switch."""
import io, re, sys

BASE = r"E:\mindmap"
SRC = r"E:\mindmap\graph\_src\_orig"   # 原始未合并版（构建源，勿改）
def read(p):
    with io.open(p, encoding="utf-8") as f:
        return f.read()

idx = read(SRC + r"\index.html")
chn = read(SRC + r"\chain.html")

def script_of(html):
    return re.search(r"<script>(.*)</script>", html, re.S).group(1)

IS = script_of(idx)
CS = script_of(chn)

# ---------- helpers ----------
def literal_after(src, marker):
    """Return the balanced {...} literal text (inclusive) that follows marker."""
    i = src.index(marker) + len(marker)
    while src[i] != '{':
        i += 1
    start = i
    depth = 0; in_str = False; esc = False; tick = False
    while i < len(src):
        ch = src[i]
        if in_str:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': in_str = False
        elif tick:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '`': tick = False
        else:
            if ch == '"': in_str = True
            elif ch == '`': tick = True
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return src[start:i+1]
        i += 1
    raise ValueError("unbalanced literal")

def func(src, name):
    m = re.search(r"(?m)^function " + re.escape(name) + r"\s*\(", src)
    if not m:
        raise KeyError("function not found: " + name)
    start = m.start()
    i = src.index('{', m.start())
    depth = 0; in_str = False; esc = False; tick = False
    while i < len(src):
        ch = src[i]
        if in_str:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '"': in_str = False
        elif tick:
            if esc: esc = False
            elif ch == '\\': esc = True
            elif ch == '`': tick = False
        else:
            if ch == '"': in_str = True
            elif ch == '`': tick = True
            elif ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    return src[start:i+1]
        i += 1
    raise ValueError("unbalanced function " + name)

def line_of(src, pattern):
    m = re.search(pattern, src, re.S)
    if not m:
        raise KeyError("line not found: " + pattern)
    return m.group(0)

# ---------- pull pieces from index.html ----------
DATA_LIT = literal_after(IS, "const DATA = ")
MARK_LIT = literal_after(IS, "const MARK_DEFAULTS = ")

IDX_CONSTS = line_of(IS, r"const FS\s+= \{0:17.*?const MAXL = [^\n]*\n")

mind_names = ["measure", "layoutSide", "collect",
              "assignPaths", "build", "render", "renderKeepNode", "fit",
              "buildLegend", "setAll"]
mind_code = IDX_CONSTS + "\n"
for n in mind_names:
    mind_code += func(IS, n) + "\n\n"

# 导图这边的 wrap 改成调用共享的 wrap2（字重与 render 里的 font-weight 对齐）
mind_code += """const WEIGHT = {0:800, 1:700, 2:600, 3:400};   // 与 render 里的 font-weight 保持一致
function wrap(text, level){
  return wrap2(text, FS[level], MAXW[level], MAXL[level], WEIGHT[level]);
}

"""

# rename pass for the mind engine (must run on the whole mind section)
def rename_mind(s):
    s = re.sub(r"(?<![\w.])render\(", "renderMind(", s)
    s = re.sub(r"(?<![\w.])fit\(\)", "fitMind()", s)
    s = re.sub(r"(?<![\w.])apply\(\)", "applyZoom()", s)
    s = s.replace("markOf(n)", "markGet(n._path)")
    s = s.replace("cycleMark(n)", "markCyclePath(n._path)")
    s = s.replace("setAll", "mindSetAll")
    s = s.replace("state.", "mindState.")
    s = s.replace("const state = {collapsed:new Set(), scale:1, tx:0, ty:0};", "")
    return s

# build() references `state.collapsed` -> handled; the mind state object is declared in glue
mind_code = rename_mind(mind_code)
# 宽度用实测（带上字重），并防空行时 Math.max() 得到 -Infinity
mind_code = mind_code.replace(
    "node._w = Math.max(...node._lines.map(l => textW(l, FS[level]))) + PADX[level]*2;",
    "node._w = Math.max(0, ...node._lines.map(l => textW(l, FS[level], WEIGHT[level]))) + PADX[level]*2;")
# `measure` was collected before rename; ensure no `state` token remains
if re.search(r"(?<![\w.$])state\b", mind_code):
    leftovers = [l for l in mind_code.splitlines() if re.search(r"(?<![\w.$])state\b", l)]
    sys.stderr.write("WARN leftover bare `state` in mind code:\n" + "\n".join(leftovers[:10]) + "\n")

# the mind fit() must reserve space for the real (possibly wrapped) topbar
mind_code = mind_code.replace(
    "const padX = 70, padTop = 86, padBottom = 62;",
    "const padX = 70, padTop = topPadPx(26), padBottom = 62;")

# ---------- pull pieces from chain.html ----------
CH_FLOW = line_of(CS, r"const FLOW = \[.*?\];")
CH_CONSTS = line_of(CS, r"const FS_STAGE.*?const HEAD_GAP = [^\n]*\n")
CH_CONTENT = line_of(CS, r"const CONTENT = \{[^}]*\};")
CH_STATE = line_of(CS, r"const state = \{[^}]*\};")

# isCJK / textW / tokenize / wrap2 已提升到共享层；fit1 在原文件里只有定义没有引用，直接丢掉
chain_names = ["markBtn", "txt", "render", "CAPTION_BG", "apply", "fit"]
chain_code = (CH_FLOW + "\n" + CH_CONSTS + "\n" + CH_CONTENT + "\n" + CH_STATE + "\n\n")
for n in chain_names:
    chain_code += func(CS, n) + "\n\n"

# drop the debug document.title hook, keep the geometry available instead
chain_code = re.sub(
    r"\n\s*document\.title = JSON\.stringify\(\{[^}]*\}\);",
    "\n  window.__MM_GEOM = {scale:state.scale,tx:state.tx,ty:state.ty,cw:CONTENT.w,ch:CONTENT.h,vw:svg.clientWidth,vh:svg.clientHeight};",
    chain_code)

# chain's fit() must also read the real topbar height
chain_code = chain_code.replace(
    "padTop = clean ? 34 : 78",
    "padTop = clean ? 34 : topPadPx(20)")

# ---------- CSS ----------
base_css = re.search(r"<style>(.*?)</style>", idx, re.S).group(1)
css = base_css.replace(".legend{\n    position:fixed;right:20px;bottom:14px;", ".legend{\n    position:fixed;right:20px;bottom:66px;")
if css == base_css:
    css = base_css.replace("right:20px;bottom:14px;", "right:20px;bottom:66px;", 1)

# 顶栏：按钮文字不换行；放不下时整颗按钮换行，并把顶栏高度撑开（fit 会按实测高度留边）
css = css.replace(
    "position:fixed;top:0;left:0;right:0;height:60px;z-index:20;\n    display:flex;align-items:center;gap:16px;padding:0 20px;",
    "position:fixed;top:0;left:0;right:0;min-height:60px;z-index:20;\n    display:flex;align-items:center;gap:12px;padding:8px 20px;flex-wrap:wrap;row-gap:6px;")
css = css.replace(
    "cursor:pointer;transition:.14s;box-shadow:0 1px 1px rgba(17,24,39,.03);",
    "cursor:pointer;transition:.14s;box-shadow:0 1px 1px rgba(17,24,39,.03);white-space:nowrap;")
css = css.replace(".seg{display:flex;", ".seg{display:flex;flex:none;")
css = css.replace(".stats{display:flex;", ".stats{display:flex;flex:none;")
css += """
  /* 长链图的标记按钮 */
  .mk{cursor:pointer}
  .mk:hover circle{stroke-width:2.6}
  /* 右下角：模式切换 */
  .modeswitch{
    position:fixed;right:20px;bottom:14px;z-index:22;
    display:flex;align-items:center;gap:8px;
    font-family:var(--font);font-size:12.5px;font-weight:700;color:#fff;
    background:#111827;border:1px solid #111827;
    padding:9px 16px;border-radius:999px;cursor:pointer;
    box-shadow:0 6px 18px rgba(17,24,39,.20);transition:.16s;
  }
  .modeswitch:hover{background:#1f2937;transform:translateY(-1px);box-shadow:0 9px 24px rgba(17,24,39,.26)}
  .modeswitch .ico{font-size:14px;line-height:1;opacity:.85}
  .modeswitch:focus-visible{outline:2px solid #93c5fd;outline-offset:2px}
  .golink{position:fixed;left:20px;bottom:52px;z-index:20;font-size:11px;font-weight:700;color:#374151;
    text-decoration:none;background:rgba(255,255,255,.9);border:1px solid #dedad2;padding:6px 11px;
    border-radius:8px;box-shadow:var(--shadow);transition:.15s}
  .golink:hover{background:#fff;border-color:#c9c4ba;color:#111827}

  /* 窄屏：先让出副标题，再整体收紧，尽量保持一行 */
  @media (max-width:1580px){ .brand .sub{display:none} }
  @media (max-width:1420px){
    .topbar{gap:9px;padding:7px 14px}
    button{padding:5px 8px;font-size:11.5px}
    .seg a{padding:4px 9px;font-size:11.5px}
    .stats{font-size:11px;gap:8px}
  }
"""

# ---------- HTML ----------
html_head = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>前后端数据沟通全链路 · 思维导图</title>
<style>%s</style>
</head>
<body>
<div id="app">
  <div class="topbar">
    <div class="brand">
      <h1>前后端数据沟通全链路</h1>
      <span class="sub" id="brandsub">用户注册案例 · 六段式时序</span>
    </div>
    <div class="spacer"></div>
    <div class="seg">
      <a class="on">全链路图</a>
      <a href="graph.html?tab=mysql" title="MySQL 知识栏目">MySQL</a>
      <a href="blog.html">博客源码</a>
    </div>
    <div class="btns">
      <button id="btn-expand">全部展开</button>
      <button id="btn-collapse">只看阶段</button>
      <button id="btn-items">展开到环节</button>
      <button id="btn-fit">适应窗口</button>
    </div>
    <div class="stats" id="stats"></div>
    <button id="btn-author" title="把作者内置的标记载入到当前浏览器">载入作者标记</button>
    <button id="btn-export">导出标记</button>
    <button id="btn-import">导入标记</button>
    <input type="file" id="file-import" accept=".json,application/json" style="display:none">
    <button id="btn-reset">清空标记</button>
    <div class="zoom">
      <button id="btn-out">\u2212</button><span class="val" id="zoomval">100%%</span><button id="btn-in">+</button>
    </div>
  </div>
  <svg id="map"><defs>
    <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#94a3b8"/>
    </marker>
    <marker id="arwR" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
      <path d="M 0 0 L 10 5 L 0 10 z" fill="#cbb8a6"/>
    </marker>
  </defs><g id="scene"></g></svg>
  <div class="hint" id="hint"><b>点击节点</b>展开/折叠 · <b>滚轮</b>缩放 · <b>拖拽</b>平移</div>
  <div class="legend" id="legend"></div>
  <a class="golink" href="graph.html" title="打开知识图谱：网状全景 + 4 条业务逻辑">🗺 知识图谱 →</a>
  <button class="modeswitch" id="btn-mode" title="切换到长链图模式">
    <span class="ico">\u21c4</span><span id="btn-mode-label">切到长链图</span>
  </button>
</div>
""" % css

GLUE = r"""
/* ================= 共享层：元素、标记、缩放、模式 ================= */
const NS = "http://www.w3.org/2000/svg";
const svg = document.getElementById("map");
const scene = document.getElementById("scene");
function el(tag, attrs){ const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }
const $ = id => document.getElementById(id);
/* 顶栏可能因窗口变窄而换行：按实测高度留上边距，避免内容被顶栏压住 */
function topPadPx(extra){
  const b = document.querySelector(".topbar");
  const h = (b && b.offsetHeight) ? b.offsetHeight : 60;
  return h + extra;
}

/* ================= 文字测量与折行（两种模式共用一套） =================
   用 Canvas measureText 真实测量宽度（不是按字符数估算），
   再按「CJK 单字成词、英文按空格切词」折行，避免把 Axios 劈成 A / xios。 */
function isCJK(ch){ return /[\u3000-\u303f\u4e00-\u9fff\uff00-\uffef]/.test(ch); }
const _mc = document.createElement("canvas").getContext("2d");
let _fontFam = null;
const _wCache = new Map();
function textW(s, fs, weight){
  const w = weight || 400;
  const key = w + "|" + fs + "|" + s;
  const hit = _wCache.get(key);
  if (hit !== undefined) return hit;
  if (_fontFam === null) _fontFam = getComputedStyle(document.body).fontFamily;
  _mc.font = w + " " + fs + "px " + _fontFam;
  const v = _mc.measureText(s).width;
  _wCache.set(key, v);
  return v;
}
function tokenize(s){
  // CJK/标点 单字成词；英文按空格切词（空格并入前一词，作为断行点）
  const out = []; let buf = "";
  for (const ch of s){
    if (isCJK(ch)){
      if (buf){ out.push(buf); buf = ""; }
      out.push(ch);
    } else if (ch === " "){
      buf += ch; out.push(buf); buf = "";
    } else {
      buf += ch;
    }
  }
  if (buf) out.push(buf);
  // 收尾标点并到前一个词，避免“）”单独占一行
  const merged = [];
  for (const tk of out){
    if (merged.length && /^[）】」』，。、；：？！\)\]%]+$/.test(tk)) merged[merged.length-1] += tk;
    else merged.push(tk);
  }
  return merged;
}
/* 单词本身就比行宽还长时（超长标识符），才退化成按字符切 */
function splitLong(tk, fs, budget, weight){
  if (textW(tk, fs, weight) <= budget) return [tk];
  const out = []; let rest = tk;
  while (rest){
    let n = 1;
    while (n < rest.length && textW(rest.slice(0, n+1), fs, weight) <= budget) n++;
    out.push(rest.slice(0, n));
    rest = rest.slice(n);
  }
  return out;
}
function wrap2(s, fs, budget, maxL, weight){
  const toks = [];
  tokenize(s).forEach(tk => splitLong(tk, fs, budget, weight).forEach(x => toks.push(x)));
  const lines = []; let cur = "";
  for (const tk of toks){
    const test = cur + tk;
    if (cur && textW(test, fs, weight) > budget){
      lines.push(cur); cur = tk;
      if (lines.length >= maxL){ cur = ""; break; }
    } else cur = test;
  }
  if (cur && lines.length < maxL) lines.push(cur);
  // 用「去空白后的字符数」判断是否真的有内容没放下（避免空格导致误判）
  const full = toks.join("").replace(/\s/g, "");
  const used = lines.join("").replace(/\s/g, "");
  if (used.length < full.length && lines.length){
    let last = lines[lines.length-1];
    while (last.length > 1 && textW(last+"…", fs, weight) > budget) last = last.slice(0,-1);
    lines[lines.length-1] = last + "…";
  }
  return lines;
}

const MARK_COLORS = ["#9ca3af", "#DC2626", "#F59E0B", "#16A34A"];
const MARK_TINTS  = ["#ffffff", "#FEF2F2", "#FFFBEB", "#F0FDF4"];
const MARK_NAMES  = ["未标记", "不会", "仅了解", "理解"];
const LS_KEY = "mm-marks-v1";
const LS_SEEDED = "mm-marks-seeded-v1";
const LS_MODE = "mm-mode-v1";

const DATA = __DATA__;

/* 作者内置标记：首次访问时作为初始状态，清空后不再自动恢复 */
const MARK_DEFAULTS = __MARKS__;

let marks = {};
try { marks = JSON.parse(localStorage.getItem(LS_KEY) || "{}") || {}; }
catch (e) { marks = {}; }
function saveMarks(){ try { localStorage.setItem(LS_KEY, JSON.stringify(marks)); } catch(e){} }
function markGet(p){ return marks[p] || 0; }
function markCyclePath(p){
  const next = (markGet(p) + 1) % 4;
  if (next === 0) delete marks[p]; else marks[p] = next;
  saveMarks(); redraw(true); updateStats();
}
function seedAuthorMarks(){
  try{
    if (localStorage.getItem(LS_SEEDED)) return 0;
    if (Object.keys(marks).length){ localStorage.setItem(LS_SEEDED, "1"); return 0; }
    const keys = Object.keys(MARK_DEFAULTS || {});
    if (!keys.length){ localStorage.setItem(LS_SEEDED, "1"); return 0; }
    marks = JSON.parse(JSON.stringify(MARK_DEFAULTS));
    saveMarks();
    localStorage.setItem(LS_SEEDED, "1");
    return keys.length;
  }catch(e){ return 0; }
}
function loadAuthorMarks(){
  const keys = Object.keys(MARK_DEFAULTS || {});
  if (!keys.length){ alert("这个页面没有内置标记数据。"); return; }
  if (Object.keys(marks).length &&
      !confirm("会用作者内置的 " + keys.length + " 条标记覆盖你当前的标记，继续？")) return;
  marks = JSON.parse(JSON.stringify(MARK_DEFAULTS));
  saveMarks();
  localStorage.setItem(LS_SEEDED, "1");
  redraw(true); updateStats();
}
function updateStats(){
  const c = [0,0,0,0];
  if (MODE === "mind"){
    (function walk(n){ if (!(n.c && n.c.length)) c[markGet(n._path)]++; (n.c||[]).forEach(walk); })(DATA);
  } else {
    CHAIN.forEach(st => st.items.forEach(it => {
      if (it.details.length) it.details.forEach(d => c[markGet(d.p)]++);
      else c[markGet(it.p)]++;
    }));
  }
  const box = $("stats");
  if (!box) return;
  box.innerHTML =
      `<span><i class="dot" style="background:${MARK_COLORS[1]}"></i>不会 <b>${c[1]}</b></span>`
    + `<span><i class="dot" style="background:${MARK_COLORS[2]}"></i>仅了解 <b>${c[2]}</b></span>`
    + `<span><i class="dot" style="background:${MARK_COLORS[3]}"></i>理解 <b>${c[3]}</b></span>`
    + `<span style="opacity:.65">未标记 <b>${c[0]}</b></span>`;
}

/* ---------- 缩放 / 平移：两套状态各自保留 ---------- */
const mindState = { collapsed:new Set(), scale:1, tx:0, ty:0 };
let MODE = "mind";
const seen = { mind:false, chain:false };
function curState(){ return MODE === "mind" ? mindState : ChainView.state; }
function applyZoom(){
  const st = curState();
  scene.setAttribute("transform", `translate(${st.tx},${st.ty}) scale(${st.scale})`);
  $("zoomval").textContent = Math.round(st.scale*100) + "%";
}
function redraw(keep){
  if (MODE === "mind") renderMind(!!keep); else ChainView.render(!!keep);
}

/* ================= 思维导图引擎 ================= */
__MIND__

/* 先给全部节点分配路径（折叠的也要有），标记才能跨视图对上 */
assignPaths(DATA, "r");

/* ================= 长链图数据：复用同一棵树的阶段一~六 ================= */
const CHAIN = DATA.c.slice(1, 7).map((st, i) => ({
  idx: i + 1,
  title: st.t,
  color: st.color,
  items: (st.c || []).map(it => ({
    t: it.t,
    p: it._path,
    details: (it.c || []).map(d => ({ t: d.t, p: d._path }))
  }))
}));

/* ================= 长链图引擎（作用域隔离，避免与导图重名） ================= */
const ChainView = (function(){
const DATA = { main: CHAIN };

function markOf(p){ return markGet(p); }
function cycleMark(p){ markCyclePath(p); }

__CHAIN__

return { render: render, fit: fit, apply: apply, state: state };
})();

/* ================= 顶栏文案 / 图例 / 模式按钮 ================= */
let CLEAN = false;
let seedNote = "";
function updateChrome(){
  const mind = MODE === "mind";
  $("btn-mode-label").textContent = mind ? "切到长链图" : "切到思维导图";
  $("btn-mode").title = mind ? "切换到长链图模式" : "切换到思维导图模式";
  $("brandsub").textContent = mind ? "用户注册案例 · 六段式时序" : "用户注册案例 · 一条链走完 6 个阶段";
  $("btn-expand").textContent = mind ? "全部展开" : "展开细节";
  $("hint").innerHTML = (mind
      ? "<b>点击节点</b>展开/折叠 · <b>滚轮</b>缩放 · <b>拖拽</b>平移"
      : "<b>点阶段</b>收起/展开环节 · <b>点环节</b>看细节 · <b>滚轮</b>缩放 · <b>拖拽</b>平移") + seedNote;
  $("legend").style.display = (mind && !CLEAN) ? "" : "none";
  document.title = "前后端数据沟通全链路 · " + (mind ? "思维导图" : "长链图");
}
function setMode(m, silent){
  MODE = (m === "chain") ? "chain" : "mind";
  updateChrome();
  const keep = seen[MODE];
  seen[MODE] = true;
  redraw(keep);
  if (!silent){
    try { localStorage.setItem(LS_MODE, MODE); } catch(e){}
    try {
      const u = new URL(location.href);
      if (MODE === "chain") u.searchParams.set("mode", "chain");
      else u.searchParams.delete("mode");
      history.replaceState(null, "", u.href);
    } catch(e){}
  }
}
$("btn-mode").onclick = () => setMode(MODE === "mind" ? "chain" : "mind");

/* ================= 工具栏 ================= */
$("btn-expand").onclick = () => {
  if (MODE === "mind") mindSetAll(() => false);
  else { ChainView.state.collapsedStage.clear(); ChainView.state.collapsedItem.clear(); ChainView.render(false); }
};
$("btn-collapse").onclick = () => {
  if (MODE === "mind") mindSetAll((n, d) => d >= 1);
  else {
    ChainView.state.collapsedStage.clear(); ChainView.state.collapsedItem.clear();
    CHAIN.forEach((_, i) => ChainView.state.collapsedStage.add(i));
    ChainView.render(false);
  }
};
$("btn-items").onclick = () => {
  if (MODE === "mind") mindSetAll((n, d) => d >= 2);
  else {
    ChainView.state.collapsedStage.clear(); ChainView.state.collapsedItem.clear();
    CHAIN.forEach((st, i) => st.items.forEach((it, j) => {
      if (it.details.length) ChainView.state.collapsedItem.add(i + "-" + j);
    }));
    ChainView.render(false);
  }
};
$("btn-fit").onclick = () => redraw(false);
$("btn-in").onclick = () => { const st = curState(); st.scale = Math.min(st.scale*1.18, 3); applyZoom(); };
$("btn-out").onclick = () => { const st = curState(); st.scale = Math.max(st.scale/1.18, MODE === "mind" ? 0.06 : 0.08); applyZoom(); };
$("btn-reset").onclick = () => {
  if (!confirm("确定清空所有学习状态标记？")) return;
  marks = {}; saveMarks();
  try { localStorage.setItem(LS_SEEDED, "1"); } catch(e){}
  redraw(true); updateStats();
};
$("btn-author").onclick = loadAuthorMarks;

/* ================= 导出 / 导入 ================= */
function exportMarks(){
  const keys = Object.keys(marks);
  const payload = {
    app: "前后端数据沟通全链路-学习标记",
    version: 1,
    exportedAt: new Date().toISOString(),
    total: keys.length,
    marks: marks
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const d = new Date();
  const ymd = d.getFullYear() + "-" +
              String(d.getMonth()+1).padStart(2,"0") + "-" +
              String(d.getDate()).padStart(2,"0");
  const a = document.createElement("a");
  a.href = url;
  a.download = "学习标记-" + ymd + ".json";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
  alert("已导出 " + keys.length + " 条标记\n\n文件名：学习标记-" + ymd + ".json\n（在浏览器下载目录里）\n\n把它拷到 U 盘，换电脑时用「导入标记」恢复。");
}
function importMarks(file){
  const fr = new FileReader();
  fr.onload = () => {
    try {
      const obj = JSON.parse(fr.result);
      const m = obj.marks || obj;
      if (typeof m !== "object" || m === null || Array.isArray(m)) throw new Error("不是有效的标记文件");
      const keys = Object.keys(m).filter(k => /^r(-\d+)+$/.test(k) && m[k] >= 1 && m[k] <= 3);
      if (!keys.length) throw new Error("文件里没有可用的标记");
      if (!confirm("将导入 " + keys.length + " 条标记。\n\n规则：同一知识点以导入文件为准，其余保留你当前的标记。\n\n继续？")) return;
      keys.forEach(k => { marks[k] = m[k]; });
      saveMarks(); redraw(true); updateStats();
      alert("导入完成。\n当前共 " + Object.keys(marks).length + " 条标记。");
    } catch (e) {
      alert("导入失败：" + e.message + "\n\n请确认选的是「导出标记」生成的 json 文件。");
    }
  };
  fr.readAsText(file, "utf-8");
}
$("btn-export").onclick = exportMarks;
$("btn-import").onclick = () => $("file-import").click();
$("file-import").addEventListener("change", ev => {
  const f = ev.target.files && ev.target.files[0];
  if (f) importMarks(f);
  ev.target.value = "";
});

/* ================= 缩放 / 平移交互（两种模式共用） ================= */
svg.addEventListener("wheel", e => {
  e.preventDefault();
  const r = svg.getBoundingClientRect();
  const mx = e.clientX - r.left, my = e.clientY - r.top;
  const k = e.deltaY < 0 ? 1.12 : 1/1.12;
  const st = curState();
  const lo = MODE === "mind" ? 0.06 : 0.08;
  const ns = Math.min(Math.max(st.scale*k, lo), 3);
  const q = ns / st.scale;
  st.tx = mx - (mx - st.tx)*q;
  st.ty = my - (my - st.ty)*q;
  st.scale = ns;
  applyZoom();
}, { passive:false });

let drag = false, lx = 0, ly = 0;
svg.addEventListener("mousedown", e => { drag = true; lx = e.clientX; ly = e.clientY; svg.classList.add("dragging"); });
window.addEventListener("mousemove", e => {
  if (!drag) return;
  const st = curState();
  st.tx += e.clientX - lx; st.ty += e.clientY - ly;
  lx = e.clientX; ly = e.clientY;
  applyZoom();
});
window.addEventListener("mouseup", () => { drag = false; svg.classList.remove("dragging"); });
window.addEventListener("resize", () => { clearTimeout(window._t); window._t = setTimeout(applyZoom, 120); });

/* ================= 初始化 ================= */
(function(){
  const q = new URLSearchParams(location.search);

  /* 导图：默认展开到环节 */
  mindState.collapsed.clear();
  const v = q.get("view") || "items";
  if (v === "items"){
    const walk = (n, d) => { if (d >= 2) mindState.collapsed.add(n); (n.c||[]).forEach(ch => walk(ch, d+1)); };
    DATA.c.forEach(st => walk(st, 1));
  } else if (v === "collapse"){
    DATA.c.forEach(st => mindState.collapsed.add(st));
  }

  /* 长链图：默认展开到环节（细节折叠） */
  ChainView.state.collapsedStage.clear();
  ChainView.state.collapsedItem.clear();
  if (q.get("detail") !== "1"){
    CHAIN.forEach((st, i) => st.items.forEach((it, j) => {
      if (it.details.length) ChainView.state.collapsedItem.add(i + "-" + j);
    }));
  }

  /* 净图模式：隐藏所有界面元素，便于截图 */
  if (q.get("clean") === "1"){
    CLEAN = true;
    document.querySelector(".topbar").style.display = "none";
    $("hint").style.display = "none";
    $("legend").style.display = "none";
    $("btn-mode").style.display = "none";
    document.body.style.backgroundImage = "none";
  }

  /* 首次访问：把作者标记作为初始状态 */
  const seeded = seedAuthorMarks();
  if (seeded) seedNote = ' · <b>已载入作者 ' + seeded + ' 条标记</b>';

  /* 初始模式：URL 优先，其次记住上次 */
  let m = "mind";
  if (q.get("mode") === "chain" || q.get("detail") === "1") m = "chain";
  else if (q.get("view")) m = "mind";
  else { try { if (localStorage.getItem(LS_MODE) === "chain") m = "chain"; } catch(e){} }
  setMode(m, true);
})();
"""

# ---------- assemble ----------
glue = GLUE.replace("__DATA__", DATA_LIT).replace("__MARKS__", MARK_LIT)
glue = glue.replace("__MIND__", mind_code).replace("__CHAIN__", chain_code)

out = html_head + "<script>" + glue + "</script>\n</body>\n</html>\n"

io.open(BASE + r"\index.html", "w", encoding="utf-8", newline="\n").write(out)
print("written index.html:", len(out.encode("utf-8")), "bytes")
print("DATA literal chars:", len(DATA_LIT))
print("MARK literal chars:", len(MARK_LIT))
print("mind code chars:", len(mind_code))
print("chain code chars:", len(chain_code))
