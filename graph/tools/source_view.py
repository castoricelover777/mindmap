# -*- coding: utf-8 -*-
"""
source_view.py —— 源码视图（左侧三层架构树 + 右侧带语法高亮的源码）

由 build_page.py 注入到 graph.html：
  SRC_CSS  → </style> 前
  SRC_BODY → </body> 前（覆盖层 DOM）
  SRC_JS   → </body> 前（逻辑，含 __SRC__ 占位符，构建时替换成 source.json）

交互：选中场景后点顶栏「源码」或双击场景卡 → 覆盖层从左侧滑出
      左栏：三层架构（Controller/Service/Mapper/Pojo/…）默认折叠，点开列出类
      右栏：Maven 目录面包屑 + package + 行数 + 方法 + 语法高亮源码
"""

SRC_CSS = r"""
/* ================= 源码视图 ================= */
#srcWrap{position:fixed;inset:0;z-index:60;display:flex;flex-direction:column;
  background:#fff;transform:translateX(-102%);transition:transform .26s cubic-bezier(.3,.7,.3,1);
  box-shadow:12px 0 40px rgba(17,24,39,.18)}
#srcWrap.show{transform:none}
body.src-open{overflow:hidden}

#srcTop{flex:none;display:flex;align-items:center;gap:12px;padding:11px 16px;
  border-bottom:1px solid #e8e5de;background:#faf9f6}
#srcTop .ttl{font-size:15px;font-weight:800;color:#111827}
#srcTop .pjt{font-size:11.5px;color:#6b7280;background:#f1eee8;border:1px solid #e2ded6;
  padding:3px 9px;border-radius:999px}
#srcTop .sp{flex:1}
#srcTop button{font-family:inherit;font-size:11.5px;font-weight:600;color:#374151;background:#fff;
  border:1px solid #dedad2;padding:6px 11px;border-radius:7px;cursor:pointer}
#srcTop button:hover{background:#f2efe9}
#srcClose{border:0;background:#f1efea;width:30px;height:30px;border-radius:8px;
  font-size:18px;line-height:1;color:#6b7280;cursor:pointer}

#srcMain{flex:1;display:flex;min-height:0}
#srcTreeWrap{width:340px;flex:none;border-right:1px solid #e8e5de;display:flex;flex-direction:column;
  background:#fcfbf9;min-height:0}
#srcNote{font-size:10.5px;line-height:1.6;color:#8a6d3b;background:#fffbeb;border-bottom:1px solid #f3e8c8;
  padding:8px 12px;max-height:110px;overflow:auto;display:none}
#srcNote.show{display:block}
#srcTree{flex:1;overflow:auto;padding:8px 8px 40px}

.sl{margin:2px 0}
.slh{display:flex;align-items:center;gap:7px;padding:8px 9px;border-radius:8px;cursor:pointer;
  border:1px solid #ece8e1;background:#fff}
.slh:hover{background:#f4f1ec}
.slh .ic{font-size:12px;color:#0d9488;width:14px;text-align:center}
.slh .lb{flex:1;font-size:12.5px;font-weight:700;color:#1f2937}
.slh .ct{font-size:10.5px;color:#6b7280;background:#f1eee8;padding:2px 7px;border-radius:999px}
.slh .tg{font-size:13px;color:#9ca3af;width:12px;text-align:center}
.sld{font-size:10.5px;color:#9ca3af;padding:3px 10px 6px 30px;line-height:1.5}
.sli{margin:2px 0 6px 14px;border-left:2px solid #ece8e1;padding-left:6px}
.sf{display:flex;align-items:center;gap:8px;padding:7px 9px;border-radius:7px;cursor:pointer;
  border:1px solid transparent}
.sf:hover{background:#f4f1ec}
.sf.act{background:#e8f4f2;border-color:#9fd3cc}
.sf .fn{flex:1;font-size:12px;color:#1f2937;font-family:var(--mono);overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.sf .fl{font-size:10px;color:#9ca3af;flex:none}
.sf.act .fn{font-weight:700;color:#0f766e}

#srcCode{flex:1;display:flex;flex-direction:column;min-width:0;min-height:0}
#srcCrumb{flex:none;padding:8px 14px;border-bottom:1px solid #e8e5de;background:#fff;
  font-size:11.5px;color:#9ca3af;white-space:nowrap;overflow-x:auto;font-family:var(--mono)}
#srcCrumb b{color:#111827;font-weight:700}
#srcCrumb .sep{color:#d1cdc5;margin:0 5px}
#srcMeta{flex:none;padding:7px 14px;border-bottom:1px solid #f1eee8;background:#faf9f6;
  font-size:11px;color:#6b7280;white-space:nowrap;overflow-x:auto}
#srcMeta code{font-family:var(--mono);color:#b91c1c;background:#f7f3ee;padding:1px 5px;border-radius:4px}
#srcMeta .chip{display:inline-block;background:#e8f4f2;color:#0f766e;padding:1px 7px;border-radius:999px;
  font-weight:700;margin-right:8px}

#srcView{flex:1;overflow:auto;background:#0f172a;min-height:0}
#srcView .box{display:flex;min-height:100%;width:max-content;min-width:100%}
#srcGut{flex:none;padding:12px 10px 40px 14px;text-align:right;font-family:var(--mono);
  font-size:12px;line-height:1.62;color:#4b5f7a;user-select:none;background:#0d1424;
  white-space:pre;overflow:hidden;
  border-right:1px solid rgba(255,255,255,.06)}
#srcPre{flex:1;margin:0;padding:12px 20px 40px 14px;font-family:var(--mono);font-size:12px;
  line-height:1.62;color:#e2e8f0;white-space:pre;tab-size:4}
/* 语法着色（暗色） */
#srcPre .k{color:#c792ea}       /* 关键字 */
#srcPre .t{color:#82aaff}       /* 类型 */
#srcPre .s{color:#c3e88d}       /* 字符串 */
#srcPre .n{color:#f78c6c}       /* 数字 */
#srcPre .c1{color:#5f7288;font-style:italic}  /* 注释 */
#srcPre .an{color:#ffcb6b}      /* 注解 */
#srcPre .tg{color:#7dd3fc}      /* XML 标签 */
#srcPre .at{color:#ffcb6b}      /* XML 属性 */
#srcPre .pi{color:#94a3b8}      /* <?xml ?> */

@media (max-width: 900px){
  #srcTreeWrap{width:46%}
  #srcTop{padding:9px 10px;gap:8px}
  #srcTop .ttl{font-size:13px}
  #srcTop .pjt{display:none}
  #srcGut,#srcPre{font-size:11px}
}
"""

SRC_BODY = r"""
<div id="srcWrap">
  <div id="srcTop">
    <span class="ttl" id="srcScene">源码</span>
    <span class="pjt" id="srcProj"></span>
    <span class="sp"></span>
    <button id="srcPrev" title="上一个文件">‹</button>
    <button id="srcNext" title="下一个文件">›</button>
    <button id="srcCopy">复制代码</button>
    <button id="srcClose">×</button>
  </div>
  <div id="srcMain">
    <div id="srcTreeWrap">
      <div id="srcNote"></div>
      <div id="srcTree"></div>
    </div>
    <div id="srcCode">
      <div id="srcCrumb"></div>
      <div id="srcMeta"></div>
      <div id="srcView"></div>
    </div>
  </div>
</div>
"""

SRC_JS = r"""
<script>
/* ================= 源码视图 ================= */
const SRC = __SRC__;

const SRC_ICON = { controller: "▣", service: "◈", mapper: "◉", pojo: "◆",
                   exception: "⚠", config: "⚙", utils: "✎", shared: "❖", dao: "◉" };

const srcState = { sid: null, key: null, expanded: new Set() };

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

/* ---------- 打开 / 关闭 ---------- */
function srcSceneOf(sid){ return (sid && SRC.scenes[sid]) ? SRC.scenes[sid] : null; }

function openSrc(sid){
  const sc = srcSceneOf(sid);
  if (!sc){
    alert("这个场景还没有关联源码。");
    return;
  }
  srcState.sid = sid;
  srcState.key = null;
  srcState.expanded = new Set();

  const gs = (typeof scById !== "undefined") ? scById[sid] : null;
  document.getElementById("srcScene").textContent = gs ? gs.label : sid;
  const pj = SRC.projects[sc.proj];
  document.getElementById("srcProj").textContent = pj ? (pj.name + " · " + pj.kind) : "";

  const note = document.getElementById("srcNote");
  if (sc.note){ note.textContent = sc.note; note.classList.add("show"); }
  else { note.textContent = ""; note.classList.remove("show"); }

  document.getElementById("srcWrap").classList.add("show");
  document.body.classList.add("src-open");

  let first = null;
  for (const L of sc.layers){ if (L.items.length){ first = L.items[0]; break; } }
  if (first){ srcState.expanded.add(sc.layers[0].id); }
  renderSrcTree();
  if (first) selectSrcFile(first); else renderSrcEmpty();
}

function closeSrc(){
  document.getElementById("srcWrap").classList.remove("show");
  document.body.classList.remove("src-open");
}

/* ---------- 左栏树 ---------- */
function renderSrcTree(){
  const sc = srcSceneOf(srcState.sid);
  const box = document.getElementById("srcTree");
  if (!sc){ box.innerHTML = ""; return; }
  const html = [];
  sc.layers.forEach(L => {
    const open = srcState.expanded.has(L.id);
    html.push('<div class="sl">');
    html.push('<div class="slh" data-layer="' + L.id + '">'
      + '<span class="ic">' + (SRC_ICON[L.id] || "▣") + '</span>'
      + '<span class="lb">' + sEsc(L.label) + '</span>'
      + '<span class="ct">' + L.items.length + '</span>'
      + '<span class="tg">' + (open ? "−" : "+") + '</span></div>');
    html.push('<div class="sld">' + sEsc(L.desc) + '</div>');
    if (open){
      html.push('<div class="sli">');
      L.items.forEach(k => {
        const f = SRC.files[k];
        const act = (k === srcState.key) ? " act" : "";
        html.push('<div class="sf' + act + '" data-key="' + sEsc(k) + '">'
          + '<span class="fn">' + sEsc(f.name) + '</span>'
          + '<span class="fl">' + f.lines + ' 行</span></div>');
      });
      html.push('</div>');
    }
    html.push('</div>');
  });
  box.innerHTML = html.join("");
}

document.getElementById("srcTree").addEventListener("click", ev => {
  const h = ev.target.closest("[data-layer]");
  if (h){
    const id = h.getAttribute("data-layer");
    if (srcState.expanded.has(id)) srcState.expanded.delete(id); else srcState.expanded.add(id);
    renderSrcTree();
    return;
  }
  const f = ev.target.closest("[data-key]");
  if (f) selectSrcFile(f.getAttribute("data-key"));
});

/* ---------- 右栏代码 ---------- */
function srcList(){
  const sc = srcSceneOf(srcState.sid);
  if (!sc) return [];
  const out = [];
  sc.layers.forEach(L => L.items.forEach(k => out.push(k)));
  return out;
}

function selectSrcFile(key){
  const f = SRC.files[key];
  if (!f) return;
  srcState.key = key;
  const sc = srcSceneOf(srcState.sid);
  sc.layers.forEach(L => { if (L.items.indexOf(key) >= 0) srcState.expanded.add(L.id); });
  renderSrcTree();

  const pj = SRC.projects[f.proj];
  const segs = f.rel.split("/");
  const crumb = ['<b>' + sEsc(pj.name) + '</b>']
    .concat(segs.map((s, i) => (i === segs.length - 1)
      ? '<b>' + sEsc(s) + '</b>'
      : sEsc(s)))
    .join('<span class="sep">›</span>');
  document.getElementById("srcCrumb").innerHTML = crumb;

  const layerLabel = (sc.layers.find(L => L.items.indexOf(key) >= 0) || {}).label || "";
  document.getElementById("srcMeta").innerHTML =
      '<span class="chip">' + sEsc(layerLabel) + '</span>'
    + (f.pkg ? 'package <code>' + sEsc(f.pkg) + '</code> · ' : '')
    + f.lines + ' 行'
    + (f.methods && f.methods.length ? ' · 方法: ' + sEsc(f.methods.join(", ")) : '');

  const isXml = /\.xml$/i.test(f.rel || f.name);
  const body = isXml ? hlXml(f.code) : hlJava(f.code);
  const n = f.code.split("\n").length;
  let gut = "";
  for (let i = 1; i <= n; i++) gut += i + (i < n ? "\n" : "");
  document.getElementById("srcView").innerHTML =
      '<div class="box"><div id="srcGut"></div><pre id="srcPre"></pre></div>';
  document.getElementById("srcGut").textContent = gut;
  const pre = document.getElementById("srcPre");
  pre.innerHTML = body;
  if (!isXml) pre.style.color = "";
}

function renderSrcEmpty(){
  document.getElementById("srcCrumb").textContent = "";
  document.getElementById("srcMeta").textContent = "";
  document.getElementById("srcView").innerHTML =
    '<div style="padding:40px;color:#94a3b8;font-family:var(--mono);font-size:12px">'
    + '该场景暂无源码文件</div>';
}

/* ---------- 上一个 / 下一个 ---------- */
function srcStep(d){
  const list = srcList();
  if (!list.length) return;
  let i = list.indexOf(srcState.key);
  i = (i < 0) ? 0 : (i + d + list.length) % list.length;
  selectSrcFile(list[i]);
}

/* ---------- 事件 ---------- */
document.getElementById("srcClose").onclick = closeSrc;
document.getElementById("srcPrev").onclick = () => srcStep(-1);
document.getElementById("srcNext").onclick = () => srcStep(+1);
document.getElementById("srcCopy").onclick = () => {
  const f = SRC.files[srcState.key];
  if (!f) return;
  const btn = document.getElementById("srcCopy");
  const done = () => { btn.textContent = "已复制"; setTimeout(() => btn.textContent = "复制代码", 1200); };
  if (navigator.clipboard) navigator.clipboard.writeText(f.code).then(done).catch(fb);
  else fb();
  function fb(){
    const ta = document.createElement("textarea");
    ta.value = f.code; document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); done(); } catch (e) {}
    ta.remove();
  }
};
document.addEventListener("keydown", ev => {
  if (ev.key === "Escape" && document.body.classList.contains("src-open")) closeSrc();
});

/* ---------- 入口按钮 ---------- */
(function(){
  const btn = document.getElementById("btn-src");
  if (btn){
    btn.onclick = () => {
      const sid = (typeof netSel !== "undefined" && netSel) ? netSel
                : ((typeof curScenario !== "undefined" && curScenario && curScenario.id) ? curScenario.id : null);
      if (!sid){ alert("请先点左侧的场景卡（例如「用户注册全链路」），再点「源码」。"); return; }
      openSrc(sid);
    };
  }
})();
window.openSrc = openSrc;
</script>
"""
