# -*- coding: utf-8 -*-
"""
source_view.py —— 源码视图 v2：在画布里从场景卡左侧长出源码树

与 v1 的区别：不再是全屏覆盖层，而是和右侧知识点一样的 SVG 画布
      场景卡（右） ← 三层架构框（中） ← 类框（左），贝塞尔连线
      点层框展开/收起该类下的类框；点类框 → 右侧滑出代码抽屉（行号 + 语法高亮 + Maven 面包屑）

由 build_page.py 注入：SRC_CSS / SRC_BODY / SRC_JS（含 __SRC__ 占位符）
"""

SRC_CSS = r"""
/* ================= 源码树（画布内） ================= */
.snode{cursor:pointer}
.snode text{font-family:var(--font);dominant-baseline:middle;pointer-events:none}

#srcActions{position:fixed;left:16px;bottom:16px;z-index:35;display:none;align-items:center;gap:8px;
  background:rgba(255,255,255,.96);border:1px solid #e2ded6;border-radius:10px;padding:7px 9px;
  box-shadow:0 4px 16px rgba(17,24,39,.08);font-size:11.5px;color:#6b7280}
#srcActions.show{display:flex}
#srcActions .who{font-weight:800;color:#111827;margin-right:2px}
#srcActions button{font-family:inherit;font-size:11.5px;font-weight:600;color:#374151;background:#fff;
  border:1px solid #dedad2;padding:5px 10px;border-radius:7px;cursor:pointer}
#srcActions button:hover{background:#f2efe9}

/* ================= 代码抽屉 ================= */
#srcDrawer{position:fixed;top:0;right:0;bottom:0;width:min(620px,52vw);z-index:55;
  background:#fff;border-left:1px solid #e2ded6;display:flex;flex-direction:column;
  transform:translateX(102%);transition:transform .22s cubic-bezier(.3,.7,.3,1);
  box-shadow:-10px 0 34px rgba(17,24,39,.14)}
#srcDrawer.show{transform:none}
#srcDTop{flex:none;display:flex;align-items:center;gap:10px;padding:10px 14px;
  border-bottom:1px solid #e8e5de;background:#faf9f6}
#srcDTop .nm{font-size:13.5px;font-weight:800;color:#111827;font-family:var(--mono)}
#srcDTop .sp{flex:1}
#srcDTop button{font-family:inherit;font-size:11.5px;font-weight:600;color:#374151;background:#fff;
  border:1px solid #dedad2;padding:5px 9px;border-radius:7px;cursor:pointer}
#srcDTop button:hover{background:#f2efe9}
#srcDClose{border:0;background:#f1efea;width:28px;height:28px;border-radius:7px;
  font-size:17px;line-height:1;color:#6b7280;cursor:pointer}

#srcCrumb{flex:none;padding:8px 14px;border-bottom:1px solid #f1eee8;font-size:11px;color:#9ca3af;
  white-space:nowrap;overflow-x:auto;font-family:var(--mono);background:#fff}
#srcCrumb b{color:#111827;font-weight:700}
#srcCrumb .sep{color:#d1cdc5;margin:0 4px}
#srcMeta{flex:none;padding:7px 14px;border-bottom:1px solid #f1eee8;background:#fbfaf8;
  font-size:11px;color:#6b7280;white-space:nowrap;overflow-x:auto}
#srcMeta code{font-family:var(--mono);color:#b91c1c;background:#f7f3ee;padding:1px 5px;border-radius:4px}
#srcMeta .chip{display:inline-block;background:#e8f4f2;color:#0f766e;padding:1px 7px;
  border-radius:999px;font-weight:700;margin-right:8px}

#srcView{flex:1;overflow:auto;background:#0f172a;min-height:0}
#srcView .box{display:flex;min-height:100%;width:max-content;min-width:100%}
#srcGut{flex:none;padding:12px 9px 40px 12px;text-align:right;font-family:var(--mono);
  font-size:12px;line-height:1.62;color:#4b5f7a;user-select:none;background:#0d1424;
  white-space:pre;overflow:hidden;border-right:1px solid rgba(255,255,255,.06)}
#srcPre{flex:1;margin:0;padding:12px 20px 40px 14px;font-family:var(--mono);font-size:12px;
  line-height:1.62;color:#e2e8f0;white-space:pre;tab-size:4}
#srcPre .k{color:#c792ea}
#srcPre .t{color:#82aaff}
#srcPre .s{color:#c3e88d}
#srcPre .n{color:#f78c6c}
#srcPre .c1{color:#5f7288;font-style:italic}
#srcPre .an{color:#ffcb6b}
#srcPre .tg{color:#7dd3fc}
#srcPre .at{color:#ffcb6b}
#srcPre .pi{color:#94a3b8}

@media (max-width: 900px){
  #srcDrawer{width:100%}
  #srcActions{left:8px;bottom:8px;font-size:10.5px;padding:6px 7px}
  #srcGut,#srcPre{font-size:11px}
}
"""

SRC_BODY = r"""
<div id="srcActions">
  <span class="who" id="srcWho"></span>
  <button id="srcToChain">▸ 排成长链</button>
  <button id="srcToNet">↩ 返回知识网络</button>
</div>
<div id="srcDrawer">
  <div id="srcDTop">
    <span class="nm" id="srcDName">源码</span>
    <span class="sp"></span>
    <button id="srcPrev" title="上一个文件">‹</button>
    <button id="srcNext" title="下一个文件">›</button>
    <button id="srcCopy">复制</button>
    <button id="srcDClose">×</button>
  </div>
  <div id="srcCrumb"></div>
  <div id="srcMeta"></div>
  <div id="srcView"></div>
</div>
"""

SRC_JS = r"""
<script>
/* ================= 源码树（画布内，向左生长） ================= */
const SRC = __SRC__;

const SRC_LAYER_COLOR = {
  controller: "#2563EB", service: "#047857", mapper: "#C2410C", pojo: "#7C3AED",
  exception: "#B45309", config: "#475569", utils: "#0F766E", shared: "#9333EA"
};
const SRC_ICON = { controller: "▣", service: "◈", mapper: "◉", pojo: "◆",
                   exception: "⚠", config: "⚙", utils: "✎", shared: "❖", dao: "◉" };

const SRCV = { sid: null, expanded: new Set(), key: null, drawer: false };

/* 尺寸 */
const S_CARD_W = 186, S_CARD_H = 56;
const S_LAYER_W = 212, S_LAYER_H = 48, S_GAP_CL = 104;
const S_CLASS_W = 258, S_CLASS_H = 38, S_GAP_LC = 74, S_CLASS_GAP = 8, S_LAYER_GAP = 14;

function sEsc(s){
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/* ---------- 语法高亮 ---------- */
const JAVA_KW = new Set(("abstract assert boolean break byte case catch char class const continue "
  + "default do double else enum extends final finally float for goto if implements import "
  + "instanceof int interface long native new package private protected public return short "
  + "static super switch synchronized this throw throws transient try void volatile while var "
  + "record yield true false null").split(" "));
const JAVA_TYPE = new Set(("String Integer Long Double Float Boolean Object List Map Set ArrayList "
  + "HashMap LocalDate LocalDateTime BigDecimal Optional Stream").split(" "));

function hlJava(code){
  let out = "", i = 0;
  while (i < code.length){
    const rest = code.slice(i);
    let m;
    if ((m = rest.match(/^\/\/[^\n]*/)) || (m = rest.match(/^\/\*[\s\S]*?\*\//))){
      out += '<span class="c1">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^("(?:\\.|[^"\\\n])*"|'(?:\\.|[^'\\\n])*')/))){
      out += '<span class="s">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^@[A-Za-z_][\w.]*/))){
      out += '<span class="an">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^\d+(?:\.\d+)?[LlFfDd]?/))){
      out += '<span class="n">' + m[0] + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^[A-Za-z_$][\w$]*/))){
      const w = m[0];
      let cls = null;
      if (JAVA_KW.has(w)) cls = "k";
      else if (JAVA_TYPE.has(w)) cls = "t";
      out += cls ? '<span class="' + cls + '">' + sEsc(w) + '</span>' : sEsc(w);
      i += w.length; continue;
    }
    out += sEsc(code[i]); i++;
  }
  return out;
}

function hlXml(code){
  let out = "", i = 0;
  while (i < code.length){
    const rest = code.slice(i);
    let m;
    if ((m = rest.match(/^<!--[\s\S]*?-->/))){
      out += '<span class="c1">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^<\?[\s\S]*?\?>/))){
      out += '<span class="pi">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^<!\[CDATA\[[\s\S]*?\]\]>/))){
      out += '<span class="s">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^<\/?[\w:.-]+/)) || (m = rest.match(/^\/?>/))){
      out += '<span class="tg">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^"[^"]*"/))){
      out += '<span class="s">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    if ((m = rest.match(/^[\w:.-]+(?==)/))){
      out += '<span class="at">' + sEsc(m[0]) + '</span>'; i += m[0].length; continue;
    }
    out += sEsc(code[i]); i++;
  }
  return out;
}

/* ---------- 布局 ---------- */
function srcLayout(){
  const sc = SRC.scenes[SRCV.sid];
  const layers = sc.layers;
  // 层框竖直排列
  let y = 0;
  const L = [];
  layers.forEach((Ly, i) => {
    L.push({ def: Ly, x: 0, y: y, w: S_LAYER_W, h: S_LAYER_H });
    y += S_LAYER_H + S_LAYER_GAP;
  });
  const layerH = y - S_LAYER_GAP;
  const cardY = layerH / 2 - S_CARD_H / 2;

  // 类框：挂在展开的层左侧
  const C = [];
  L.forEach(l => {
    if (!SRCV.expanded.has(l.def.id)) return;
    const items = l.def.items;
    const totalH = items.length * S_CLASS_H + (items.length - 1) * S_CLASS_GAP;
    let cy = l.y + S_LAYER_H / 2 - totalH / 2;
    items.forEach(k => {
      C.push({ key: k, layer: l, x: 0, y: cy, w: S_CLASS_W, h: S_CLASS_H });
      cy += S_CLASS_H + S_CLASS_GAP;
    });
  });

  // 水平位置（向左生长）
  const classX = -(S_GAP_CL + S_LAYER_W + S_GAP_LC + S_CLASS_W);
  L.forEach(l => { l.x = -(S_GAP_CL + S_LAYER_W); });
  C.forEach(c => { c.x = classX; });

  // 包围盒 → 归一化到 (0,0) 起步
  let minX = 0, maxX = S_CARD_W, minY = 0, maxY = layerH;
  L.forEach(l => { minX = Math.min(minX, l.x); minY = Math.min(minY, l.y); maxY = Math.max(maxY, l.y + l.h); });
  C.forEach(c => { minX = Math.min(minX, c.x); minY = Math.min(minY, c.y); maxY = Math.max(maxY, c.y + c.h); });
  const dx = -minX;
  const cardX = dx;
  L.forEach(l => { l.x += dx; });
  C.forEach(c => { c.x += dx; });
  const totalW = dx + S_CARD_W;
  const totalH = Math.max(maxY - minY, layerH) + 20;
  const dy = 10 - minY;

  const nodes = { card: { x: cardX, y: cardY + dy, w: S_CARD_W, h: S_CARD_H } };
  L.forEach(l => { l.y += dy; });
  C.forEach(c => { c.y += dy; });
  nodes.layers = L; nodes.classes = C;
  return { nodes, totalW, totalH, classX: classX + dx, layerX: -(S_GAP_CL + S_LAYER_W) + dx };
}

/* ---------- 绘制 ---------- */
function srcRender(keep){
  const sc = SRC.scenes[SRCV.sid];
  if (!sc){ backToNet(); return; }
  const keepView = keep ? { s: state.scale, x: state.tx, y: state.ty } : null;
  const L = srcLayout();

  scene.innerHTML = "";
  const gE = el("g", {});

  // 场景卡 → 层框
  const card = L.nodes.card;
  L.nodes.layers.forEach(l => {
    const x1 = card.x, y1 = card.y + card.h / 2;
    const x2 = l.x + l.w, y2 = l.y + l.h / 2;
    const mx = (x1 + x2) / 2;
    gE.appendChild(el("path", {
      d: `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`,
      fill: "none", stroke: SRC_LAYER_COLOR[l.def.id] || "#475569",
      "stroke-width": 2, opacity: .55
    }));
  });
  // 层框 → 类框
  L.nodes.classes.forEach(c => {
    const x1 = c.layer.x, y1 = c.layer.y + c.layer.h / 2;
    const x2 = c.x + c.w, y2 = c.y + c.h / 2;
    const mx = (x1 + x2) / 2;
    gE.appendChild(el("path", {
      d: `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`,
      fill: "none", stroke: SRC_LAYER_COLOR[c.layer.def.id] || "#475569",
      "stroke-width": 1.3, opacity: .4
    }));
  });
  scene.appendChild(gE);

  const gN = el("g", {});

  // ---- 场景卡（右侧） ----
  const gsc = scById[SRCV.sid] || { label: SRCV.sid, sub: "", color: "#111827" };
  const gc = el("g", { class: "snode" });
  gc.appendChild(el("rect", { x: card.x, y: card.y, width: card.w, height: card.h, rx: card.h / 2,
    fill: "#fff", stroke: gsc.color, "stroke-width": 1.8 }));
  gc.appendChild(el("circle", { cx: card.x + 20, cy: card.y + card.h / 2, r: 6, fill: gsc.color }));
  const ct = el("text", { x: card.x + 36, y: card.y + card.h / 2 - 4, "font-size": 14,
    "font-weight": 800, fill: "#111827" });
  let lab = gsc.label;
  while (lab.length > 2 && textW(lab, 14, 800) > card.w - 46) lab = lab.slice(0, -1);
  if (lab !== gsc.label) lab += "…";
  ct.textContent = lab;
  gc.appendChild(ct);
  const cs = el("text", { x: card.x + 36, y: card.y + card.h / 2 + 13, "font-size": 10, fill: "#6b7280" });
  cs.textContent = "源码 " + (sc.layers.reduce((n, x) => n + x.items.length, 0)) + " 个文件";
  gc.appendChild(cs);
  gN.appendChild(gc);

  // ---- 层框（中间列） ----
  L.nodes.layers.forEach(l => {
    const color = SRC_LAYER_COLOR[l.def.id] || "#475569";
    const open = SRCV.expanded.has(l.def.id);
    const g = el("g", { class: "snode" });
    g.setAttribute("data-layer", l.def.id);
    g.appendChild(el("rect", { x: l.x, y: l.y, width: l.w, height: l.h, rx: 10,
      fill: "#fff", stroke: color, "stroke-width": 1.5 }));
    g.appendChild(el("rect", { x: l.x, y: l.y + 8, width: 4, height: l.h - 16, rx: 2, fill: color }));
    const t = el("text", { x: l.x + 18, y: l.y + l.h / 2 - 7, "font-size": 12.5,
      "font-weight": 700, fill: "#1f2937" });
    t.textContent = SRC_ICON[l.def.id] + " " + l.def.label;
    g.appendChild(t);
    const t2 = el("text", { x: l.x + 18, y: l.y + l.h / 2 + 10, "font-size": 10, fill: "#9ca3af" });
    let d = l.def.desc || "";
    while (d.length > 4 && textW(d, 10, 400) > l.w - 54) d = d.slice(0, -1);
    t2.textContent = d;
    g.appendChild(t2);
    // 计数 + 展开标记
    const bx = l.x + l.w - 34;
    g.appendChild(el("circle", { cx: bx, cy: l.y + l.h / 2, r: 11,
      fill: open ? color : "#f1eee8" }));
    const bt = el("text", { x: bx, y: l.y + l.h / 2 + 0.5, "text-anchor": "middle",
      "font-size": 10.5, "font-weight": 800, fill: open ? "#fff" : "#6b7280" });
    bt.textContent = open ? "−" : String(l.def.items.length);
    g.appendChild(bt);
    g.appendChild(el("title", {})).textContent = l.def.label + "：" + (l.def.desc || "");
    g.style.cursor = "pointer";
    g.addEventListener("click", ev => {
      ev.stopPropagation();
      if (SRCV.expanded.has(l.def.id)) SRCV.expanded.delete(l.def.id);
      else SRCV.expanded.add(l.def.id);
      srcRender(true);
    });
    gN.appendChild(g);
  });

  // ---- 类框（左列） ----
  L.nodes.classes.forEach(c => {
    const f = SRC.files[c.key];
    const color = SRC_LAYER_COLOR[c.layer.def.id] || "#475569";
    const act = (c.key === SRCV.key);
    const g = el("g", { class: "snode" });
    g.setAttribute("data-key", c.key);
    g.appendChild(el("rect", { x: c.x, y: c.y, width: c.w, height: c.h, rx: 8,
      fill: act ? "#e8f4f2" : "#fff",
      stroke: act ? "#0d9488" : "#e2ded6", "stroke-width": act ? 1.8 : 1 }));
    g.appendChild(el("rect", { x: c.x, y: c.y + 7, width: 3, height: c.h - 14, rx: 1.5,
      fill: color, opacity: .8 }));
    const nm = el("text", { x: c.x + 13, y: c.y + c.h / 2, "font-size": 11.5,
      "font-weight": act ? 700 : 500, fill: act ? "#0f766e" : "#1f2937",
      "font-family": "var(--mono)" });
    nm.textContent = f.name;
    g.appendChild(nm);
    const ln = el("text", { x: c.x + c.w - 10, y: c.y + c.h / 2, "text-anchor": "end",
      "font-size": 9.5, fill: "#9ca3af" });
    ln.textContent = f.lines + " 行";
    g.appendChild(ln);
    g.appendChild(el("title", {})).textContent = f.rel + "（" + f.lines + " 行）";
    g.style.cursor = "pointer";
    g.addEventListener("click", ev => { ev.stopPropagation(); srcPick(c.key); });
    gN.appendChild(g);
  });

  scene.appendChild(gN);

  if (keepView){ state.scale = keepView.s; state.tx = keepView.x; state.ty = keepView.y; applyZoom(); }
  else srcFit();
  updateSrcActions();
}

/* 适配：抽屉打开时按剩余宽度居中 */
function srcFit(){
  const L = srcLayout();
  const svgW = svg.clientWidth, svgH = svg.clientHeight;
  const bar = document.querySelector(".topbar");
  const padTop = (bar ? bar.offsetHeight : 58) + 20, padBottom = 64;
  const drawerW = SRCV.drawer ? Math.min(620, Math.round(svgW * 0.52)) : 0;
  const availW = Math.max(320, svgW - drawerW - 60);
  const availH = Math.max(240, svgH - padTop - padBottom);
  const sc = Math.min(availW / L.totalW, availH / L.totalH, 1.25);
  state.scale = Math.max(sc, 0.14);
  const w = L.totalW * state.scale, h = L.totalH * state.scale;
  state.tx = Math.round(30 + (availW - w) / 2);
  state.ty = Math.round(padTop + (availH - h) / 2);
  applyZoom();
}

/* ---------- 打开 ---------- */
function openSrcTree(sid){
  const sc = SRC.scenes[sid];
  if (!sc){ alert("这个场景还没有关联源码。"); return; }
  SRCV.sid = sid;
  SRCV.key = null;
  SRCV.expanded = new Set();
  // 默认展开前两层（Controller / Service），让用户一眼看到结构
  sc.layers.slice(0, 2).forEach(l => SRCV.expanded.add(l.id));
  MODE = "src";
  netSel = null; armedScenario = sid; curScenario = null;
  setChip(sid);
  $("panel").classList.remove("show");
  ["legend", "themes", "hint"].forEach(id => {
    const e = $(id); if (e) e.style.display = "none";
  });
  $("btn-back").classList.add("show");
  $("srcActions").classList.add("show");
  $("srcWho").textContent = (scById[sid] || {}).label || sid;
  $("btn-expand-all").classList.remove("show");
  srcRender(false);
}
window.openSrcTree = openSrcTree;
window.openSrc = openSrcTree;   // 兼容旧入口（双击卡片 / 顶栏按钮）

function closeSrcTree(){
  SRCV.sid = null; SRCV.key = null;
  closeSrcDrawer();
  $("srcActions").classList.remove("show");
}

function srcFirstKey(){
  const sc = SRC.scenes[SRCV.sid];
  if (!sc) return null;
  for (const l of sc.layers){ if (l.items.length) return l.items[0]; }
  return null;
}

function srcPick(key){
  SRCV.key = key;
  // 展开所属层
  const sc = SRC.scenes[SRCV.sid];
  sc.layers.forEach(l => { if (l.items.indexOf(key) >= 0) SRCV.expanded.add(l.id); });
  srcRender(true);
  openSrcDrawer(key);
}

/* ---------- 代码抽屉 ---------- */
function openSrcDrawer(key){
  const f = SRC.files[key];
  if (!f) return;
  const sc = SRC.scenes[SRCV.sid];
  const pj = SRC.projects[f.proj];
  $("srcDName").textContent = f.name;

  const segs = f.rel.split("/");
  $("srcCrumb").innerHTML = ['<b>' + sEsc(pj.name) + '</b>']
    .concat(segs.map((s, i) => (i === segs.length - 1) ? '<b>' + sEsc(s) + '</b>' : sEsc(s)))
    .join('<span class="sep">›</span>');

  const layer = sc.layers.find(l => l.items.indexOf(key) >= 0) || {};
  $("srcMeta").innerHTML =
      '<span class="chip">' + sEsc(layer.label || "") + '</span>'
    + (f.pkg ? 'package <code>' + sEsc(f.pkg) + '</code> · ' : '')
    + f.lines + ' 行'
    + (f.methods && f.methods.length ? ' · 方法: ' + sEsc(f.methods.join(", ")) : '');

  const isXml = /\.xml$/i.test(f.rel || f.name);
  const body = isXml ? hlXml(f.code) : hlJava(f.code);
  const n = f.code.split("\n").length;
  let gut = "";
  for (let i = 1; i <= n; i++) gut += i + (i < n ? "\n" : "");
  $("srcView").innerHTML = '<div class="box"><div id="srcGut"></div><pre id="srcPre"></pre></div>';
  $("srcGut").textContent = gut;
  $("srcPre").innerHTML = body;
  $("srcDrawer").classList.add("show");
  const wasOpen = SRCV.drawer;
  SRCV.drawer = true;
  if (!wasOpen) srcFit();          // 抽屉占位后重新适配，树不被挡
}

function closeSrcDrawer(){
  $("srcDrawer").classList.remove("show");
  if (SRCV.drawer){ SRCV.drawer = false; if (MODE === "src") srcFit(); }
}

function srcStep(d){
  const sc = SRC.scenes[SRCV.sid];
  if (!sc) return;
  const list = [];
  sc.layers.forEach(l => l.items.forEach(k => list.push(k)));
  if (!list.length) return;
  let i = list.indexOf(SRCV.key);
  i = (i < 0) ? 0 : (i + d + list.length) % list.length;
  srcPick(list[i]);
}

function updateSrcActions(){
  const on = (MODE === "src");
  $("srcActions").classList.toggle("show", on);
  if (on) $("srcWho").textContent = (scById[SRCV.sid] || {}).label || (SRCV.sid || "");
}

/* ---------- 事件 ---------- */
$("srcDClose").onclick = closeSrcDrawer;
$("srcPrev").onclick = () => srcStep(-1);
$("srcNext").onclick = () => srcStep(+1);
$("srcCopy").onclick = () => {
  const f = SRC.files[SRCV.key];
  if (!f) return;
  const btn = $("srcCopy");
  const done = () => { btn.textContent = "已复制"; setTimeout(() => btn.textContent = "复制", 1200); };
  if (navigator.clipboard) navigator.clipboard.writeText(f.code).then(done).catch(fb);
  else fb();
  function fb(){
    const ta = document.createElement("textarea");
    ta.value = f.code; document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); done(); } catch (e) {}
    ta.remove();
  }
};
$("srcToNet").onclick = () => {
  closeSrcTree();
  ["themes", "hint", "legend"].forEach(id => {
    const e = $(id); if (e) e.style.display = "";
  });
  backToNet();
};
$("srcToChain").onclick = () => {
  const sid = SRCV.sid;
  closeSrcTree();
  ["themes", "hint", "legend"].forEach(id => {
    const e = $(id); if (e) e.style.display = "";
  });
  focusScenario(sid);
};
document.addEventListener("keydown", ev => {
  if (ev.key === "Escape"){ if (SRCV.drawer) closeSrcDrawer(); else if (MODE === "src") $("srcToNet").click(); }
});

/* 顶栏「源码」按钮：对当前选中/聚焦的场景打开源码树 */
(function(){
  const btn = document.getElementById("btn-src");
  if (!btn) return;
  btn.onclick = () => {
    const sid = (typeof netSel !== "undefined" && netSel) ? netSel
      : ((typeof curScenario !== "undefined" && curScenario) ? curScenario : armedScenario);
    if (!sid){ alert("请先点左侧一个场景卡（例如「用户注册全链路」）。"); return; }
    openSrcTree(sid);
  };
})();
</script>
"""

SRC_JS_LEGACY_GUARD = ""
