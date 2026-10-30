# -*- coding: utf-8 -*-
"""
source_view.py —— 源码视图 v3

三条要求：
  1) 代码框放左边（抽屉从左滑出）
  2) 点代码框以外的地方自动收起
  3) 右侧知识点网图**不隐藏**——源码树是叠加层，画在场景卡左侧

做法：不再切 MODE，直接在 net 视图上追加一层 <g id="srcTree">，
      场景卡左←三层架构框左←文件框，绘制后按「画布减去左侧抽屉」重新适配。
"""

SRC_CSS = r"""
/* ================= 源码树（叠加在网图上） ================= */
#srcLayer text{font-family:var(--font);dominant-baseline:middle;pointer-events:none}
#srcLayer .snode{cursor:pointer}

#srcBar{position:fixed;left:16px;bottom:16px;z-index:35;display:none;align-items:center;gap:8px;
  background:rgba(255,255,255,.97);border:1px solid #e2ded6;border-radius:10px;padding:7px 9px;
  box-shadow:0 4px 16px rgba(17,24,39,.10);font-size:11.5px;color:#6b7280}
#srcBar.show{display:flex}
#srcBar .who{font-weight:800;color:#111827;margin-right:2px}
#srcBar button{font-family:inherit;font-size:11.5px;font-weight:600;color:#374151;background:#fff;
  border:1px solid #dedad2;padding:5px 10px;border-radius:7px;cursor:pointer}
#srcBar button:hover{background:#f2efe9}

/* ================= 代码抽屉（左侧） ================= */
#srcDrawer{position:fixed;top:0;left:0;bottom:0;width:min(560px,44vw);z-index:55;
  background:#fff;border-right:1px solid #e2ded6;display:flex;flex-direction:column;
  transform:translateX(-102%);transition:transform .22s cubic-bezier(.3,.7,.3,1);
  box-shadow:10px 0 34px rgba(17,24,39,.16)}
#srcDrawer.show{transform:none}
#srcDTop{flex:none;display:flex;align-items:center;gap:9px;padding:10px 14px;
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
  #srcBar{left:8px;bottom:8px;font-size:10.5px;padding:6px 7px}
  #srcGut,#srcPre{font-size:11px}
}
"""

SRC_BODY = r"""
<div id="srcBar">
  <span class="who" id="srcWho"></span>
  <button id="srcToChain">▸ 排成长链</button>
  <button id="srcCloseTree">✕ 收起源码树</button>
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
/* ================= 源码树（叠加在网图上，向左生长） ================= */
const SRC = __SRC__;

const SRC_LAYER_COLOR = {
  controller: "#2563EB", service: "#047857", mapper: "#C2410C", pojo: "#7C3AED",
  exception: "#B45309", config: "#475569", utils: "#0F766E", shared: "#9333EA"
};
const SRC_ICON = { controller: "▣", service: "◈", mapper: "◉", pojo: "◆",
                   exception: "⚠", config: "⚙", utils: "✎", shared: "❖", dao: "◉" };

const SRCV = { sid: null, active: false, expanded: new Set(), key: null, drawer: false, savedView: null };

const S_LAYER_W = 212, S_LAYER_H = 46, S_GAP_CL = 96;
const S_CLASS_W = 250, S_CLASS_H = 36, S_GAP_LC = 70, S_CLASS_GAP = 7, S_LAYER_GAP = 12;

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

/* ---------- 布局：挂在场景卡左侧 ---------- */
function srcPaint(){
  if (!SRCV.active) return;
  const sc = SRC.scenes[SRCV.sid];
  if (!sc) return;
  const card = (netNodes || []).find(n => n.kind === "scenario" && n.id === SRCV.sid);
  if (!card) return;

  const old = document.getElementById("srcLayer");
  if (old) old.remove();

  const g = el("g", { id: "srcLayer" });
  const gE = el("g", {});

  // 层框：卡左侧一列
  const layerRight = card.x - S_GAP_CL;
  const layerX = layerRight - S_LAYER_W;
  const nL = sc.layers.length;
  const blockH = nL * S_LAYER_H + (nL - 1) * S_LAYER_GAP;
  let y0 = card.y + card.h / 2 - blockH / 2;

  const layerPos = {};
  sc.layers.forEach((def, i) => { layerPos[def.id] = { x: layerX, y: y0 + i * (S_LAYER_H + S_LAYER_GAP) }; });

  // 文件框：层框左侧
  const classRight = layerX - S_GAP_LC;
  const classX = classRight - S_CLASS_W;

  // 连线 卡 → 层
  sc.layers.forEach(def => {
    const L = layerPos[def.id];
    const x1 = card.x, y1 = card.y + card.h / 2;
    const x2 = L.x + S_LAYER_W, y2 = L.y + S_LAYER_H / 2;
    const mx = (x1 + x2) / 2;
    gE.appendChild(el("path", {
      d: `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`,
      fill: "none", stroke: SRC_LAYER_COLOR[def.id] || "#475569", "stroke-width": 1.8, opacity: .5
    }));
  });

  // 文件框位置
  const files = [];
  sc.layers.forEach(def => {
    if (!SRCV.expanded.has(def.id)) return;
    const L = layerPos[def.id];
    const items = def.items;
    const totalH = items.length * S_CLASS_H + (items.length - 1) * S_CLASS_GAP;
    let cy = L.y + S_LAYER_H / 2 - totalH / 2;
    items.forEach(k => {
      files.push({ key: k, def: def, x: classX, y: cy });
      cy += S_CLASS_H + S_CLASS_GAP;
    });
  });

  // 连线 层 → 文件
  files.forEach(f => {
    const L = layerPos[f.def.id];
    const x1 = L.x, y1 = L.y + S_LAYER_H / 2;
    const x2 = f.x + S_CLASS_W, y2 = f.y + S_CLASS_H / 2;
    const mx = (x1 + x2) / 2;
    gE.appendChild(el("path", {
      d: `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`,
      fill: "none", stroke: SRC_LAYER_COLOR[f.def.id] || "#475569", "stroke-width": 1.2, opacity: .38
    }));
  });
  g.appendChild(gE);

  // ---- 层框 ----
  sc.layers.forEach(def => {
    const L = layerPos[def.id];
    const color = SRC_LAYER_COLOR[def.id] || "#475569";
    const open = SRCV.expanded.has(def.id);
    const gs = el("g", { class: "snode" });
    gs.setAttribute("data-layer", def.id);
    gs.appendChild(el("rect", { x: L.x, y: L.y, width: S_LAYER_W, height: S_LAYER_H, rx: 10,
      fill: "#fff", stroke: color, "stroke-width": 1.5 }));
    gs.appendChild(el("rect", { x: L.x, y: L.y + 8, width: 4, height: S_LAYER_H - 16, rx: 2, fill: color }));
    const t = el("text", { x: L.x + 18, y: L.y + S_LAYER_H / 2 - 7, "font-size": 12.5,
      "font-weight": 700, fill: "#1f2937" });
    t.textContent = SRC_ICON[def.id] + " " + def.label;
    gs.appendChild(t);
    const t2 = el("text", { x: L.x + 18, y: L.y + S_LAYER_H / 2 + 10, "font-size": 9.5, fill: "#9ca3af" });
    let d = def.desc || "";
    while (d.length > 4 && textW(d, 9.5, 400) > S_LAYER_W - 60) d = d.slice(0, -1);
    t2.textContent = d;
    gs.appendChild(t2);
    const bx = L.x + S_LAYER_W - 24;
    gs.appendChild(el("circle", { cx: bx, cy: L.y + S_LAYER_H / 2, r: 10,
      fill: open ? color : "#f1eee8" }));
    const bt = el("text", { x: bx, y: L.y + S_LAYER_H / 2 + 0.5, "text-anchor": "middle",
      "font-size": 10, "font-weight": 800, fill: open ? "#fff" : "#6b7280" });
    bt.textContent = open ? "−" : String(def.items.length);
    gs.appendChild(bt);
    gs.appendChild(el("title", {})).textContent = def.label + "：" + (def.desc || "");
    gs.addEventListener("click", ev => {
      ev.stopPropagation();
      if (SRCV.expanded.has(def.id)) SRCV.expanded.delete(def.id);
      else SRCV.expanded.add(def.id);
      srcPaint();
    });
    g.appendChild(gs);
  });

  // ---- 文件框 ----
  files.forEach(f => {
    const info = SRC.files[f.key];
    const color = SRC_LAYER_COLOR[f.def.id] || "#475569";
    const act = (f.key === SRCV.key);
    const gs = el("g", { class: "snode" });
    gs.setAttribute("data-key", f.key);
    gs.appendChild(el("rect", { x: f.x, y: f.y, width: S_CLASS_W, height: S_CLASS_H, rx: 8,
      fill: act ? "#e8f4f2" : "#fff",
      stroke: act ? "#0d9488" : "#e2ded6", "stroke-width": act ? 1.8 : 1 }));
    gs.appendChild(el("rect", { x: f.x, y: f.y + 6, width: 3, height: S_CLASS_H - 12, rx: 1.5,
      fill: color, opacity: .85 }));
    const nm = el("text", { x: f.x + 12, y: f.y + S_CLASS_H / 2, "font-size": 11.5,
      "font-weight": act ? 700 : 500, fill: act ? "#0f766e" : "#1f2937", "font-family": "var(--mono)" });
    let n2 = info.name;
    while (n2.length > 3 && textW(n2, 11.5, 600) > S_CLASS_W - 62) n2 = n2.slice(0, -1);
    nm.textContent = n2;
    gs.appendChild(nm);
    const ln = el("text", { x: f.x + S_CLASS_W - 10, y: f.y + S_CLASS_H / 2, "text-anchor": "end",
      "font-size": 9.5, fill: "#9ca3af" });
    ln.textContent = info.lines + " 行";
    gs.appendChild(ln);
    gs.appendChild(el("title", {})).textContent = info.rel + "（" + info.lines + " 行）";
    gs.addEventListener("click", ev => { ev.stopPropagation(); srcPick(f.key); });
    g.appendChild(gs);
  });

  scene.appendChild(g);
  // 注意：这里不自动适配 —— 点击层框/文件框不应该让整个画布跳位置
}

/* 适配：只在打开源码树时调用一次（reserve=true 预留左侧抽屉宽度）。
   之后点层框 / 点文件框 / 开关抽屉都不再改动画布位置。 */
function srcFit(reserve){
  if (!SRCV.active) return;
  const layer = document.getElementById("srcLayer");
  if (!layer) return;
  const b = layer.getBBox();
  if (!b.width || !b.height) return;

  const svgW = svg.clientWidth, svgH = svg.clientHeight;
  const bar = document.querySelector(".topbar");
  const padTop = (bar ? bar.offsetHeight : 58) + 18, padBottom = 56;
  const drawerW = reserve ? Math.min(560, Math.round(svgW * 0.44))
                : (SRCV.drawer ? Math.min(560, Math.round(svgW * 0.44)) : 0);
  const x0 = drawerW + 26, x1 = svgW - 26;
  const availW = Math.max(220, x1 - x0);
  const availH = Math.max(200, svgH - padTop - padBottom);

  // 保持用户当前的缩放比例，只平移，把源码树露在可视区左侧
  const s = state.scale;
  state.tx = Math.round(x0 - b.x * s);
  state.ty = Math.round(padTop + (availH - b.height * s) / 2 - b.y * s);
  applyZoom();
}

/* ---------- 打开 / 收起 ---------- */
function openSrcTree(sid){
  const sc = SRC.scenes[sid];
  if (!sc){ alert("这个场景还没有关联源码。"); return; }
  SRCV.sid = sid; SRCV.active = true; SRCV.key = null;
  SRCV.savedView = { s: state.scale, x: state.tx, y: state.ty };   // 关闭时还原
  SRCV.expanded = new Set();
  sc.layers.slice(0, 2).forEach(l => SRCV.expanded.add(l.id));
  armedScenario = sid; netSel = null; curScenario = null;
  setChip(sid);
  $("panel").classList.remove("show");
  $("srcBar").classList.add("show");
  $("srcWho").textContent = (scById[sid] || {}).label || sid;
  srcPaint();
  srcFit(true);      // 只在这里定位一次，预留左侧抽屉宽度
}
window.openSrcTree = openSrcTree;
window.openSrc = openSrcTree;

function closeSrcTree(){
  SRCV.active = false; SRCV.key = null; SRCV.sid = null;
  armedScenario = null; netSel = null; setChip(null);   // 清掉残留，避免下次点卡片直接跳长链
  closeSrcDrawer();
  const layer = document.getElementById("srcLayer");
  if (layer) layer.remove();
  $("srcBar").classList.remove("show");
  // 恢复网图并还原打开前的视角（缩放/平移都回到原样）
  const v = SRCV.savedView;
  SRCV.savedView = null;
  renderNet(true);
  if (v){ state.scale = v.s; state.tx = v.x; state.ty = v.y; applyZoom(); }
}

function srcFirstKey(){
  const sc = SRC.scenes[SRCV.sid];
  if (!sc) return null;
  for (const l of sc.layers){ if (l.items.length) return l.items[0]; }
  return null;
}

function srcPick(key){
  const sc = SRC.scenes[SRCV.sid];
  sc.layers.forEach(l => { if (l.items.indexOf(key) >= 0) SRCV.expanded.add(l.id); });
  SRCV.key = key;
  srcPaint();
  openSrcDrawer(key);
}

/* ---------- 代码抽屉（左侧） ---------- */
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
  SRCV.drawer = true;
}

function closeSrcDrawer(){
  if (!$("srcDrawer").classList.contains("show")) return;
  $("srcDrawer").classList.remove("show");
  SRCV.drawer = false;
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

/* ---------- 事件 ---------- */
$("srcDClose").onclick = closeSrcDrawer;
$("srcPrev").onclick = () => srcStep(-1);
$("srcNext").onclick = () => srcStep(+1);
$("srcCloseTree").onclick = closeSrcTree;
$("srcToChain").onclick = () => {
  const sid = SRCV.sid;
  SRCV.active = false; closeSrcDrawer();
  const layer = document.getElementById("srcLayer"); if (layer) layer.remove();
  $("srcBar").classList.remove("show");
  focusScenario(sid);
};
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

/* 点代码框以外的地方 → 自动收起代码框 */
document.addEventListener("click", ev => {
  if (!SRCV.drawer) return;
  if (ev.target.closest("#srcDrawer")) return;        // 点在抽屉内
  if (ev.target.closest("#scene g[data-key]")) return; // 点另一个文件：直接切换
  closeSrcDrawer();
}, true);

document.addEventListener("keydown", ev => {
  if (ev.key === "Escape"){
    if (SRCV.drawer) closeSrcDrawer();
    else if (SRCV.active) closeSrcTree();
  }
});

/* 每次重绘网图后，把源码树重新贴回场景卡左侧 */
(function(){
  const _renderNet = renderNet;
  renderNet = function(keep){
    _renderNet(keep);
    if (SRCV.active) srcPaint();
  };
})();

/* 顶栏「源码」按钮 */
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
