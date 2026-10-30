# -*- coding: utf-8 -*-
"""生成 graph.html：知识图谱（网状全景 + 点击场景聚焦成链）。

- 复用已验证的 ChainView（从现行 index.html 里原样抽出）画链状视图
- 新写 NetView：按技术层分列画网状图
- 零依赖单文件，数据内联
"""
import io, json, os, re
from source_view import SRC_CSS, SRC_BODY, SRC_JS
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

GRAPH = os.path.join(ROOT, "graph", "data", "graph.json")
MYSQL_JSON = os.path.join(ROOT, "graph", "data", "mysql.json")
SOURCE_JSON = os.path.join(ROOT, "graph", "data", "source.json")
MARKS_JSON = os.path.join(ROOT, "marks.json")
SRC_INDEX = os.path.join(ROOT, "index.html")
OUT = os.path.join(ROOT, "graph.html")


def read(p):
    return io.open(p, encoding="utf-8").read()


def extract_chainview(src):
    m = re.search(r"const ChainView = \(function\(\)\{", src)
    if not m:
        raise SystemExit("找不到 ChainView")
    start = m.start()
    i = src.index("{", start)
    depth = 0
    in_str = False
    esc = False
    tick = False
    while i < len(src):
        ch = src[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        elif tick:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == "`":
                tick = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "`":
                tick = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = src.index("})();", i) + len("})();")
                    return src[start:end]
        i += 1
    raise SystemExit("ChainView 括号不平衡")


CSS = r"""
  :root{
    --bg:#faf9f6; --ink:#111827; --muted:#6b7280;
    --font:"PingFang SC","Microsoft YaHei","Hiragino Sans GB","Noto Sans CJK SC",system-ui,-apple-system,"Segoe UI",sans-serif;
    --shadow:0 1px 2px rgba(17,24,39,.05),0 10px 30px rgba(17,24,39,.07);
  }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0;overflow:hidden}
  body{background:var(--bg);color:var(--ink);font-family:var(--font);
    background-image:radial-gradient(circle at 1px 1px,#e6e3dc 1px,transparent 0);background-size:24px 24px}
  #app{position:fixed;inset:0}
  .topbar{position:fixed;top:0;left:0;right:0;min-height:58px;z-index:20;display:flex;align-items:center;
    gap:12px;padding:8px 20px;flex-wrap:wrap;row-gap:6px;
    background:linear-gradient(180deg,rgba(250,249,246,.97),rgba(250,249,246,.82));
    backdrop-filter:blur(10px);border-bottom:1px solid #e8e5de}
  .brand{display:flex;align-items:baseline;gap:9px}
  .brand h1{margin:0;font-size:15.5px;font-weight:800;letter-spacing:.3px}
  .brand .sub{font-size:11px;color:var(--muted);letter-spacing:.3px}
  @media (max-width:1500px){ .brand .sub{display:none} }
  .spacer{flex:1}
  button{font-family:inherit;font-size:12px;font-weight:600;color:#374151;background:#fff;
    border:1px solid #dedad2;padding:6px 10px;border-radius:7px;cursor:pointer;transition:.14s;
    box-shadow:0 1px 1px rgba(17,24,39,.03);white-space:nowrap}
  button:hover{background:#f2efe9;border-color:#c9c4ba}
  .seg{display:flex;background:#efece6;border:1px solid #dedad2;border-radius:8px;padding:2px;gap:2px;flex:none}
  .seg a{font-size:12px;font-weight:600;color:#6b7280;text-decoration:none;padding:5px 11px;border-radius:6px;transition:.15s;white-space:nowrap}
  .seg a:hover{color:#374151;background:rgba(255,255,255,.6)}
  .seg a.on{background:#fff;color:#111827;box-shadow:0 1px 3px rgba(17,24,39,.14)}
  .chips{display:flex;gap:6px;flex:none}
  .chip{display:flex;align-items:center;gap:6px;font-size:12px;font-weight:700;color:#374151;
    background:#fff;border:1px solid #dedad2;padding:6px 12px;border-radius:999px;cursor:pointer;transition:.15s;white-space:nowrap}
  .chip i{width:8px;height:8px;border-radius:50%;display:block}
  .chip:hover{border-color:#c9c4ba;background:#f7f5f1}
  .chip.on{color:#fff;border-color:transparent}
  .chip.on i{background:#fff!important}
  .stats{display:flex;gap:11px;align-items:center;font-size:11.5px;color:var(--muted);white-space:nowrap;flex:none}
  .stats b{color:#374151;font-weight:700}
  .stats .dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:4px}
  .zoom{display:flex;align-items:center;border:1px solid #dedad2;border-radius:7px;overflow:hidden;background:#fff}
  .zoom button{border:0;border-radius:0;box-shadow:none;padding:6px 9px}
  .zoom .val{font-size:11px;color:var(--muted);padding:0 7px;min-width:42px;text-align:center}
  svg#map{width:100%;height:100%;display:block;cursor:grab}
  svg#map.dragging{cursor:grabbing}
  text{font-family:var(--font);dominant-baseline:middle;pointer-events:none}
  .hint{position:fixed;left:20px;bottom:14px;z-index:20;font-size:11px;color:var(--muted);
    background:rgba(255,255,255,.88);border:1px solid #e8e5de;padding:6px 11px;border-radius:8px;box-shadow:var(--shadow)}
  .hint b{color:#374151}
  .legend{position:fixed;right:20px;bottom:66px;z-index:20;display:flex;gap:11px;flex-wrap:wrap;max-width:56vw;
    font-size:10.5px;color:var(--muted);background:rgba(255,255,255,.88);border:1px solid #e8e5de;
    padding:6px 11px;border-radius:8px;box-shadow:var(--shadow)}
  .legend i{display:inline-block;width:8px;height:8px;border-radius:2px;margin-right:4px}
  .backbtn{position:fixed;right:20px;bottom:14px;z-index:22;display:none;align-items:center;gap:8px;
    font-family:var(--font);font-size:12.5px;font-weight:700;color:#fff;background:#111827;border:1px solid #111827;
    padding:9px 16px;border-radius:999px;cursor:pointer;box-shadow:0 6px 18px rgba(17,24,39,.20);transition:.16s}
  .backbtn:hover{background:#1f2937;transform:translateY(-1px)}
  .backbtn.show{display:flex}
  /* 侧栏 */
  .panel{position:fixed;top:0;right:0;bottom:0;width:380px;max-width:86vw;z-index:30;background:#fff;
    border-left:1px solid #e8e5de;box-shadow:-12px 0 40px rgba(17,24,39,.10);
    transform:translateX(102%);transition:transform .26s cubic-bezier(.4,0,.2,1);display:flex;flex-direction:column}
  .panel.show{transform:none}
  .panel .ph{padding:18px 20px 14px;border-bottom:1px solid #eee}
  .panel .ph .lay{font-size:10.5px;font-weight:800;letter-spacing:.6px;text-transform:uppercase}
  .panel .ph h2{margin:6px 0 2px;font-size:17px;font-weight:800;letter-spacing:.2px}
  .panel .ph .aka{font-size:11.5px;color:var(--muted);font-family:ui-monospace,Menlo,Consolas,monospace}
  .panel .pb{padding:16px 20px;overflow:auto;flex:1;font-size:12.5px;line-height:1.72;color:#374151}
  .panel .pb h3{margin:18px 0 8px;font-size:12px;font-weight:800;color:#111827;letter-spacing:.4px}
  .panel .pb h3:first-child{margin-top:0}
  .panel .kv{display:flex;gap:8px;font-size:11.5px;color:var(--muted);margin:3px 0}
  .panel .kv b{color:#374151;font-weight:700}
  .panel .sc{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:700;padding:3px 9px;
    border-radius:999px;margin:0 5px 5px 0;background:#f2efe9;color:#374151}
  .panel .sc i{width:7px;height:7px;border-radius:50%}
  .panel .close{position:absolute;top:14px;right:16px;border:0;background:none;font-size:20px;color:#9ca3af;
    cursor:pointer;line-height:1;padding:4px}
  .panel .close:hover{color:#111827}
  .panel ul{margin:0;padding-left:18px}
  .panel li{margin:4px 0}
  /* 母题 */
  .themes{position:fixed;left:20px;bottom:56px;z-index:20;display:flex;gap:6px;flex-wrap:wrap;max-width:54vw}
  .tchip{display:flex;align-items:center;gap:6px;font-family:var(--font);font-size:11px;font-weight:700;
    color:#374151;background:rgba(255,255,255,.92);border:1px solid #dedad2;padding:5px 10px;border-radius:999px;
    cursor:pointer;transition:.15s;box-shadow:0 1px 2px rgba(17,24,39,.05);white-space:nowrap}
  .tchip i{width:7px;height:7px;border-radius:50%;display:block}
  .tchip:hover{border-color:#c9c4ba;background:#f7f5f1}
  .tchip.on{color:#fff;border-color:transparent}
  .tcard{position:fixed;left:20px;bottom:96px;z-index:21;width:320px;max-width:80vw;background:#fff;
    border:1px solid #e8e5de;border-radius:10px;box-shadow:0 10px 30px rgba(17,24,39,.13);
    padding:14px 16px 12px;display:none}
  .tcard.show{display:block}
  .tcard h4{margin:0 0 4px;font-size:13.5px;font-weight:800;letter-spacing:.2px}
  .tcard .note{font-size:11px;color:#6b7280;line-height:1.65;margin:0 0 10px}
  .tcard ol{margin:0;padding-left:18px;font-size:11.5px;line-height:1.95;color:#374151}
  .tcard li b{font-weight:700}
  .tcard .ly{font-size:9.5px;color:#9ca3af;margin-left:5px}
  .tcard .x{position:absolute;top:8px;right:10px;border:0;background:none;font-size:16px;color:#9ca3af;cursor:pointer}
  .themes a.tchip{text-decoration:none;color:#6b7280;font-weight:700}
  /* 环节面板里的知识点 chip */
  .panel .kchips{display:flex;flex-wrap:wrap;gap:6px}
  .panel .kchip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;color:#374151;
    background:#f7f5f1;border:1px solid #e8e5de;padding:4px 9px;border-radius:999px;cursor:pointer;transition:.14s}
  .panel .kchip:hover{background:#fff;border-color:#c9c4ba;color:#111827}
  .panel .kchip i{width:7px;height:7px;border-radius:50%;display:block}

  /* MySQL 知识栏目（卡片墙，样式对齐长链图） */
  .mysqlview{position:fixed;left:0;right:0;top:58px;bottom:0;z-index:40;display:none;overflow:auto;
    padding:22px 26px 90px;background:#faf9f7;background-image:radial-gradient(#e6e3dc .8px,transparent .8px);
    background-size:20px 20px}
  .mysqlview.show{display:block}
  .mv-bar{display:flex;align-items:baseline;gap:14px;margin:0 0 18px 2px}
  .mv-bar h2{margin:0;font-size:17px;font-weight:800;color:#111827}
  .mv-bar .mvs{font-size:11px;color:#a8a29a;font-weight:600}
  .mv-cols{display:flex;gap:6px;align-items:flex-start}
  .mv-col{flex:1 1 300px;min-width:264px;max-width:430px}
  .mh{display:flex;align-items:center;gap:9px;border-radius:11px;padding:11px 13px;color:#fff;
    box-shadow:0 3px 12px rgba(17,24,39,.13)}
  .mh i{width:19px;height:19px;border-radius:50%;background:rgba(255,255,255,.26);flex:0 0 19px;
    display:flex;align-items:center;justify-content:center;font-size:10px;font-weight:800;font-style:normal}
  .mh h3{margin:0;font-size:12.5px;font-weight:800;flex:1;line-height:1.3}
  .mh u{width:19px;height:19px;border-radius:50%;background:rgba(255,255,255,.26);flex:0 0 19px;
    display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;text-decoration:none}
  .mg{margin-top:7px}
  .gh{display:flex;align-items:center;gap:8px;padding:9px 11px;background:#fff;border-radius:8px;
    margin-bottom:6px;cursor:pointer;user-select:none;box-shadow:0 1px 3px rgba(17,24,39,.05);
    transition:box-shadow .15s}
  .gh:hover{box-shadow:0 2px 8px rgba(17,24,39,.10)}
  .gh b{font-size:11.5px;font-weight:700;color:#1f2937;flex:1;line-height:1.4}
  .gh em{width:18px;height:18px;border-radius:50%;border:1.3px solid currentColor;flex:0 0 18px;
    display:flex;align-items:center;justify-content:center;font-size:9px;font-weight:800;font-style:normal}
  .gb{display:none;padding:2px 0 2px 10px}
  .gp.open>.gb{display:block}
  .pt{background:#fff;border-radius:0 7px 7px 0;margin-bottom:5px;border-left:2.5px solid currentColor;
    box-shadow:0 1px 2px rgba(17,24,39,.04)}
  .ph{display:flex;align-items:center;gap:7px;padding:7px 9px;cursor:pointer;font-size:11px;
    font-weight:600;color:#374151;user-select:none;line-height:1.42}
  .ph:hover{background:#faf9f6}
  .ph span{flex:1}
  .ph i{flex:0 0 auto;font-style:normal;font-size:9px;font-weight:800;color:#2563eb;background:#eff6ff;
    border-radius:4px;padding:1px 5px}
  .pb{display:none;padding:0 9px 9px}
  .pt.open>.pb{display:block}
  .pb .ms{font-size:10.5px;color:#6b7280;line-height:1.62;margin-top:3px}
  .pb .mo{font-size:10.5px;color:#b45309;line-height:1.55;margin-top:4px}
  .pb pre{margin:7px 0 0;padding:8px 10px;background:#1f2937;color:#e5e7eb;border-radius:6px;
    font-family:ui-monospace,Consolas,"Courier New",monospace;font-size:10.4px;line-height:1.66;
    overflow:auto;white-space:pre-wrap}
  .mvmask{position:fixed;inset:0;background:rgba(250,249,247,.80);z-index:1;display:none;
    opacity:0;transition:opacity .22s ease}
  .mvmask.show{display:block;opacity:1}
  .mvpop{position:fixed;top:92px;right:30px;bottom:44px;width:min(460px,42vw);z-index:2;display:none;
    flex-direction:column;background:#fff;border:1px solid #e8e5de;border-radius:13px;
    box-shadow:0 18px 50px rgba(17,24,39,.20);overflow:hidden;
    transform:translateX(26px);opacity:0;transition:transform .24s cubic-bezier(.34,.02,.2,1),opacity .2s}
  .mvpop.show{display:flex;transform:translateX(0);opacity:1}
  .mvpop .ph-head{display:flex;align-items:flex-start;gap:10px;padding:14px 16px 11px;border-bottom:1px solid #f1eee8}
  .mvpop .ph-head h4{margin:0;font-size:13.5px;font-weight:800;color:#111827;line-height:1.45;flex:1}
  .mvpop .ph-head .x{border:0;background:none;font-size:19px;line-height:1;color:#9ca3af;cursor:pointer;padding:0 2px}
  .mvpop .ph-head .x:hover{color:#111827}
  .mvpop .ph-body{padding:13px 16px 18px;overflow:auto;flex:1}
  .mvpop .ms{font-size:11.8px;color:#4b5563;line-height:1.75;margin-bottom:7px}
  .mvpop .mo{font-size:11.2px;color:#b45309;line-height:1.65;margin:8px 0 4px;
    background:#fffbeb;border:1px solid #fde68a;border-radius:7px;padding:7px 9px}
  .mvpop .ccap{font-size:10.5px;font-weight:700;color:#0E7490;margin:11px 0 -2px;
    padding-left:7px;border-left:2px solid #0E7490}
  .mvpop .ccap-mute{color:#9ca3af;border-left-color:#d6d3cb;font-weight:600}
  .mvpop pre .k{color:#c792ea;font-weight:600}
  .mvpop pre .s{color:#a5d6a7}
  .mvpop pre .n{color:#f78c6c}
  .mvpop pre .c{color:#7f8c98;font-style:italic}
  .mvpop pre .f{color:#82aaff}
  .mvpop pre{margin:8px 0 0;padding:9px 11px;background:#1f2937;color:#e5e7eb;border-radius:7px;
    font-family:ui-monospace,Consolas,"Courier New",monospace;font-size:11px;line-height:1.7;
    overflow:auto;white-space:pre-wrap}
  .mvpop .tag{display:inline-block;font-size:9.5px;font-weight:800;color:#2563eb;background:#eff6ff;
    border-radius:4px;padding:1px 5px;margin-bottom:9px}
  .pt.on{background:#eff6ff;box-shadow:0 1px 3px rgba(37,99,235,.18)}
  .arw{flex:0 0 16px;display:flex;align-items:center;justify-content:center;color:#cfcac0;
    font-size:15px;margin-top:16px;user-select:none}

  /* 右侧信息框：补回被误删的样式 */
  .panel.show{transform:translateX(0)}
  .panel-head{padding:20px 22px 15px;border-bottom:1px solid #f1eee8;flex:0 0 auto}
  .panel .lay{font-size:10.5px;font-weight:800;letter-spacing:.6px;color:#6b7280;margin-bottom:7px}
  .panel h2{margin:0;font-size:18px;font-weight:800;color:#111827;line-height:1.35}
  .panel .aka{font-size:11px;color:#9ca3af;margin-top:5px;
    font-family:ui-monospace,Consolas,"Courier New",monospace}
  .panel-body{padding:15px 22px 44px;overflow:auto;flex:1 1 auto}
  .panel h3{font-size:10.5px;font-weight:800;color:#9ca3af;letter-spacing:.5px;margin:17px 0 8px}
  .panel h3:first-child{margin-top:0}
  .panel p{margin:0 0 10px;font-size:12.5px;line-height:1.78;color:#374151}
  .panel .sc{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:700;
    color:#374151;background:#f7f5f1;border-radius:999px;padding:4px 10px;margin:0 6px 6px 0}
  .panel .sc i{width:7px;height:7px;border-radius:50%;display:block}
  .panel ul{margin:6px 0 0;padding-left:16px}
  .panel li{font-size:12px;line-height:1.72;color:#374151;margin-bottom:5px}
  .panel .kchips{display:flex;flex-wrap:wrap;gap:6px}
  .panel .kchip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;
    color:#374151;background:#f7f5f1;border:1px solid #e8e5de;padding:4px 9px;border-radius:999px;
    cursor:pointer;transition:.14s}
  .panel .kchip:hover{background:#fff;border-color:#c9c4ba;color:#111827}
  .panel .kchip i{width:7px;height:7px;border-radius:50%;display:block}

  /* 右侧信息框（ID 选择器兜底，压住历史规则） */
  #panel{display:flex!important;flex-direction:column!important;
    transform:translateX(103%)!important;transition:transform .26s cubic-bezier(.34,.02,.2,1)!important}
  #panel.show{transform:none!important}
  #panel-head{padding:20px 22px 15px!important;border-bottom:1px solid #f1eee8!important;flex:0 0 auto!important}
  #panel-body{display:block!important;flex:1 1 auto!important;padding:15px 22px 44px!important;
    overflow:auto!important;font-size:12.5px!important;line-height:1.78!important;color:#374151!important}
  /* 全部展开按钮 */
  .expandbtn{position:fixed;right:200px;bottom:14px;z-index:22;display:none;align-items:center;gap:6px;
    font-family:var(--font);font-size:11.5px;font-weight:700;color:#374151;background:#fff;
    border:1px solid #dedad2;padding:7px 13px;border-radius:999px;cursor:pointer;
    box-shadow:0 4px 14px rgba(17,24,39,.10);transition:.15s}
  .expandbtn:hover{background:#f7f5f1;border-color:#c9c4ba}
  .expandbtn.show{display:flex}

  /* MySQL 标记 */
  .mkbar{display:flex;align-items:center;gap:6px;margin:0 0 12px;font-size:10.5px;color:#9ca3af}
  .mkbar b{font-weight:800;color:#6b7280;margin-right:2px}
  .mkbtn{border:1px solid #e8e5de;background:#fff;border-radius:999px;font-size:10.5px;font-weight:700;
    padding:3px 9px;cursor:pointer;color:#6b7280;transition:.14s}
  .mkbtn:hover{border-color:#c9c4ba;color:#111827}
  .mkbtn.on0{background:#FEF2F2;border-color:#FCA5A5;color:#B91C1C}
  .mkbtn.on1{background:#FFFBEB;border-color:#FCD34D;color:#B45309}
  .mkbtn.on2{background:#ECFDF5;border-color:#6EE7B7;color:#047857}
  .pt .mkdot{width:6px;height:6px;border-radius:50%;flex:0 0 6px;margin-left:2px}

  .mv-actions{margin-left:auto;display:flex;gap:8px;align-items:center}
  .mvab{font-family:var(--font);font-size:11px;font-weight:700;color:#374151;background:#fff;
    border:1px solid #e2ded6;border-radius:999px;padding:5px 11px;cursor:pointer;transition:.15s}
  .mvab:hover{background:#f7f5f1;border-color:#c9c4ba}

  .mkbtn .key{display:inline-block;margin-left:5px;font-style:normal;font-size:9px;font-weight:800;
    color:#9ca3af;background:#f4f2ed;border-radius:3px;padding:0 3px;line-height:14px;vertical-align:1px}
  .mkbtn.on0 .key,.mkbtn.on1 .key,.mkbtn.on2 .key{color:inherit;background:rgba(255,255,255,.65)}
  .mkbar .keyhint{margin-left:6px;font-size:9.5px;color:#c2bdb4}

/* === 移动端切换栏 grid 修复 v3（独立站点）=== */
@media (max-width: 900px){
  .topbar{flex-wrap:wrap !important;height:auto !important;overflow:visible !important;
          padding:6px 8px !important;gap:5px !important}
  .brand{flex:1 0 100% !important;margin-bottom:2px}
  .spacer{display:none !important}
  .seg{display:grid !important;grid-template-columns:repeat(4,1fr) !important;
       gap:4px !important;width:100% !important;flex:1 0 100% !important;
       order:-1 !important;padding:3px !important;box-sizing:border-box}
  .seg a{min-width:0 !important;width:auto !important;flex:none !important;
         text-align:center !important;padding:7px 2px !important;
         font-size:11.5px !important;line-height:1.2;white-space:nowrap;
         overflow:hidden;text-overflow:ellipsis;background:transparent;border-radius:6px}
  .seg a.on{background:#fff;box-shadow:0 1px 3px rgba(17,24,39,.14)}
  .btns{flex-wrap:nowrap !important;overflow-x:auto !important;width:100%}
  .btns::-webkit-scrollbar{display:none}
  button{flex:none;font-size:11px;padding:5px 8px;white-space:nowrap}
  .stats{flex:1 0 100% !important;justify-content:center !important;font-size:9.5px !important}
  .legend{display:none !important}
  .hint{font-size:10px;left:8px;bottom:8px;padding:4px 8px;max-width:calc(100% - 16px)}
}
"""

BODY = r"""
<div id="app">
  <div class="topbar">
    <div class="brand">
      <h1>前后端知识图谱</h1>
      <span class="sub" id="brandsub">单击场景看源码树 · 点层展开 · 点类看代码 · 双击排成长链</span>
    </div>
    <div class="spacer"></div>
    <div class="seg">
      <a class="on" id="tab-graph">知识图谱</a>
      <a id="tab-mysql">MySQL</a>
      <a href="https://castoricelover777.github.io/blog/" target="_blank" rel="noopener">博客源码</a>
    
      <a href="llm.html" style="margin-left:6px">数据分析</a></div>
    <div class="chips" id="chips"></div>
    <div class="stats" id="stats"></div>
    <button id="btn-src">源码</button>
    <button id="btn-mk-export" title="导出全部标记为 JSON（换电脑/换浏览器可用它恢复）">导出标记</button>
    <button id="btn-mk-import" title="从 JSON 恢复标记（支持本页导出文件与 ?dump=1 的汇总文件）">导入标记</button>
    <input type="file" id="mk-file" accept=".json,application/json" style="display:none">
    <button id="btn-fit">适应窗口</button>
    <div class="zoom">
      <button id="btn-out">−</button><span class="val" id="zoomval">100%</span><button id="btn-in">+</button>
    </div>
  </div>
  <svg id="map"><g id="scene"></g></svg>
  <div class="hint" id="hint"><b>点场景</b>高亮相关知识点 · <b>再点一次</b>排成长链 · <b>点知识点</b>看详情 · <b>滚轮</b>缩放</div>
  <div class="legend" id="legend"></div>
  <div class="themes" id="themes"></div>
  <div class="tcard" id="themecard"></div>
  <button class="expandbtn" id="btn-expand-all">⊞ 全部展开</button>
  <button class="backbtn" id="btn-back">↩ 返回知识网络</button>
  <div class="panel" id="panel">
    <button class="close" id="panel-close">×</button>
    <div class="ph" id="panel-head"></div>
    <div class="panel-body" id="panel-body"></div>
  </div>
</div>
<div class="mysqlview" id="mysqlview">
  <div class="mv-bar">
    <h2>MySQL 知识栏目</h2>
    <div class="mvs" id="mv-stat"></div>
    <div class="mv-actions">
      <button class="mvab" id="mv-expand" title="一次展开 / 收起所有分组">⊞ 展开全部</button>
      <button class="mvab" id="mv-export" title="把标记导出为 JSON，可换电脑导入">↓ 导出标记</button>
      <button class="mvab" id="mv-import" title="导入之前导出的标记 JSON">↑ 导入标记</button>
      <input type="file" id="mv-file" accept=".json,application/json" style="display:none">
    </div>
  </div>
  <div class="mv-cols" id="mv-body"></div>
  <div class="mvmask" id="mvmask"></div>
  <div class="mvpop" id="mvpop"></div>
</div>
<style>
  .panel{display:flex;flex-direction:column}
  .panel.show{transform:translateX(0)!important}
  .panel-head{padding:20px 22px 15px;border-bottom:1px solid #f1eee8;flex:0 0 auto!important}
  .panel .lay{font-size:10.5px;font-weight:800;letter-spacing:.6px;color:#6b7280;margin-bottom:7px}
  .panel h2{margin:0;font-size:18px;font-weight:800;color:#111827;line-height:1.35}
  .panel .aka{font-size:11px;color:#9ca3af;margin-top:5px}
  .panel-body{display:block!important;flex:1 1 auto;padding:15px 22px 44px;overflow:auto;
    font-size:12.5px;line-height:1.78;color:#374151}
  .panel h3{font-size:10.5px;font-weight:800;color:#9ca3af;letter-spacing:.5px;margin:17px 0 8px}
  .panel h3:first-child{margin-top:0}
  .panel p{margin:0 0 10px}
  .panel .sc{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:700;
    color:#374151;background:#f7f5f1;border-radius:999px;padding:4px 10px;margin:0 6px 6px 0}
  .panel .sc i{width:7px;height:7px;border-radius:50%;display:block}
  .panel ul{margin:6px 0 0;padding-left:16px}
  .panel li{font-size:12px;line-height:1.72;color:#374151;margin-bottom:5px}
  .panel .kchips{display:flex;flex-wrap:wrap;gap:6px}
  .panel .kchip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;
    color:#374151;background:#f7f5f1;border:1px solid #e8e5de;padding:4px 9px;border-radius:999px;
    cursor:pointer}
  .panel .kchip i{width:7px;height:7px;border-radius:50%;display:block}
</style>
"""

JS = r"""
const NS = "http://www.w3.org/2000/svg";
const svg = document.getElementById("map");
const scene = document.getElementById("scene");
const $ = id => document.getElementById(id);
function el(tag, attrs){ const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); return e; }

const MYSQL = __MYSQL__;
const G = __GRAPH__;

/* 顶栏实际高度：链视图 fit() 要用 */
function topPadPx(extra){
  const b = document.querySelector(".topbar");
  const h = (b && b.offsetHeight) ? b.offsetHeight : 58;
  return h + extra;
}

/* ================= 共享文字引擎（Canvas 实测 + 按词折行） ================= */
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
  const out = []; let buf = "";
  for (const ch of s){
    if (isCJK(ch)){ if (buf){ out.push(buf); buf = ""; } out.push(ch); }
    else if (ch === " "){ buf += ch; out.push(buf); buf = ""; }
    else buf += ch;
  }
  if (buf) out.push(buf);
  const merged = [];
  for (const tk of out){
    if (merged.length && /^[）】」』，。、；：？！\)\]%]+$/.test(tk)) merged[merged.length-1] += tk;
    else merged.push(tk);
  }
  return merged;
}
function splitLong(tk, fs, budget, weight){
  if (textW(tk, fs, weight) <= budget) return [tk];
  const out = []; let rest = tk;
  while (rest){
    let n = 1;
    while (n < rest.length && textW(rest.slice(0, n+1), fs, weight) <= budget) n++;
    out.push(rest.slice(0, n)); rest = rest.slice(n);
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
  const full = toks.join("").replace(/\s/g, "");
  const used = lines.join("").replace(/\s/g, "");
  if (used.length < full.length && lines.length){
    let last = lines[lines.length-1];
    while (last.length > 1 && textW(last+"…", fs, weight) > budget) last = last.slice(0,-1);
    lines[lines.length-1] = last + "…";
  }
  return lines;
}

/* ================= 标记 ================= */
const MARK_COLORS = ["#9ca3af", "#DC2626", "#F59E0B", "#16A34A"];
const MARK_TINTS  = ["#ffffff", "#FEF2F2", "#FFFBEB", "#F0FDF4"];
const MARK_NAMES  = ["未标记", "不会", "仅了解", "理解"];
const LS_KEY = "mm-graph-marks-v1";
const LS_OLD = "mm-marks-v1";
const LS_MIG = "mm-graph-migrated-v1";     // 迁移只做一次的标记
const LS_SEED = "mm-graph-seeded-v1";      // 内置快照播种只做一次
const SEED_MARKS = __SEED__;               // marks.json 里的内置标记快照
let marks = {};
try { marks = JSON.parse(localStorage.getItem(LS_KEY) || "{}") || {}; } catch(e){ marks = {}; }
function saveMarks(){ try { localStorage.setItem(LS_KEY, JSON.stringify(marks)); } catch(e){} }
function markGet(p){ return marks[p] || 0; }
function markCyclePath(p){
  const next = (markGet(p) + 1) % 4;
  if (next === 0) delete marks[p]; else marks[p] = next;
  saveMarks(); redraw(true); updateStats();
}
/* 旧标记迁移：老的 r-阶段-环节-细节 路径 → 新的语义 id */
function migrateOldMarks(){
  /* 只做一次，而且只补「当前还没有标记」的位置：
     绝不再用旧快照覆盖你后来改过的标记（旧版每次加载都会覆盖，会吃掉新标记） */
  try { if (localStorage.getItem(LS_MIG) === "1") return 0; } catch(e){}
  let old = null;
  try { old = JSON.parse(localStorage.getItem(LS_OLD) || "null"); } catch(e){}
  if (!old || typeof old !== "object"){
    try { localStorage.setItem(LS_MIG, "1"); } catch(e){}
    return 0;
  }
  const byPath = {};
  G.scenarios.forEach(sc => sc.steps.forEach(st => { if (st.path) byPath[st.path] = st; }));
  let n = 0;
  Object.keys(old).forEach(k => {
    const v = old[k];
    if (!(v >= 1 && v <= 3)) return;
    let m = k.match(/^r-(\d+)-(\d+)-(\d+)$/);
    if (m){
      const st = byPath["r-" + m[1] + "-" + m[2]];
      if (st){
        const id = st.id + "." + m[3];
        if (!marks[id]){ marks[id] = v; n++; }     // 已有就保留
      }
      return;
    }
    m = k.match(/^r-(\d+)-(\d+)$/);
    if (m){
      const st = byPath["r-" + m[1] + "-" + m[2]];
      if (st && !marks[st.id]){ marks[st.id] = v; n++; }
    }
  });
  try { localStorage.setItem(LS_MIG, "1"); } catch(e){}
  if (n) saveMarks();
  return n;
}

/* 内置快照播种：只在「本地一条标记都没有」且没播种过时做一次，
   这样换浏览器 / 清缓存后标记能自动回来；你手动清空过就不再强行灌入。 */
function seedMarks(){
  try {
    if (localStorage.getItem(LS_SEED) === "1") return 0;
    if (Object.keys(marks).length){ localStorage.setItem(LS_SEED, "1"); return 0; }
    let n = 0;
    Object.keys(SEED_MARKS || {}).forEach(k => {
      const v = SEED_MARKS[k];
      if (!marks[k] && v >= 1 && v <= 3){ marks[k] = v; n++; }
    });
    if (n) saveMarks();
    localStorage.setItem(LS_SEED, "1");
    return n;
  } catch(e){ return 0; }
}

/* ================= 统计 ================= */
function dumpAllMarks(){
  const out = { type: "mindmap-all-marks", v: 1,
                exportedAt: new Date().toISOString().slice(0, 19),
                graph: {}, detail: {}, mysql: {}, old: {} };
  const pick = (k) => { try { return JSON.parse(localStorage.getItem(k) || "{}"); } catch (e) { return {}; } };
  out.graph = pick("mm-graph-marks-v1");
  out.detail = pick("mm-detail-marks-v1");
  out.mysql = pick("mm-mysql-marks-v1");
  out.llm = pick("mm-marks-llm-v1");
  out.old = pick("mm-marks-v1");
  const n = Object.keys(out.graph).length + Object.keys(out.detail).length + Object.keys(out.mysql).length + Object.keys(out.llm).length;
  const blob = new Blob([JSON.stringify(out, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "marks-all.json";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 900);
  const box = $("hint");
  if (box) box.textContent = "已导出全部标记：" + n + " 条（marks-all.json 已下载）";
  return n;
}
function updateStats(){
  const c = [0, 0, 0, 0];
  let nDet = 0, nCon = 0, nMy = 0;
  // ① 细节卡（含无细节的环节）
  G.scenarios.forEach(sc => sc.steps.forEach(st => {
    if (st.details.length) st.details.forEach((_, k) => { c[markGet(st.id + "." + k)]++; nDet++; });
    else { c[markGet(st.id)]++; nDet++; }
  }));
  // ② 概念
  G.concepts.forEach(k => { c[markGet(k.id)]++; nCon++; });
  // ③ MySQL（0/1/2 → 1/2/3）
  let myMarked = 0;
  Object.keys(MV_MARKS).forEach(k => { const v = +MV_MARKS[k]; if (v >= 0 && v <= 2){ c[v + 1]++; myMarked++; } });
  nMy = (typeof MYSQL !== "undefined" && MYSQL.meta) ? MYSQL.meta.points : 0;
  if (nMy > myMarked) c[0] += nMy - myMarked;   // MySQL 未标记的也算进去
  const box = $("stats"); if (!box) return;
  const tip = `概念 ${nCon} · 细节卡 ${nDet} · MySQL ${nMy} · 合计 ${nCon + nDet + nMy}`;
  box.title = tip;
  box.innerHTML =
      `<span><i class="dot" style="background:${MARK_COLORS[1]}"></i>不会 <b>${c[1]}</b></span>`
    + `<span><i class="dot" style="background:${MARK_COLORS[2]}"></i>仅了解 <b>${c[2]}</b></span>`
    + `<span><i class="dot" style="background:${MARK_COLORS[3]}"></i>理解 <b>${c[3]}</b></span>`
    + `<span style="opacity:.65">未标记 <b>${c[0]}</b></span>`;
}

/* ================= 链条数据（给 ChainView） ================= */
function chainData(sc){
  return {
    main: sc.phases.map((ph, i) => ({
      idx: i + 1,
      title: ph.label,
      color: ph.color,
      items: sc.steps.filter(st => st.phase === i).map(st => ({
        t: st.label,
        p: st.id,
        details: st.details.map((d, k) => ({ t: d, p: st.id + "." + k })),
      })),
    })).filter(col => col.items.length),
    flow: sc.flow || [],
    returnNote: sc.returnNote || "",
  };
}

__CHAINVIEW__

/* ================= 网状布局 ================= */
const NW = 208, NH = 34, NGX = 58, NGY = 9;
const LAYER_X0 = 250, LAYER_DX = NW + NGX;
const SC_X = 42, SC_W = 186;
let netNodes = [];   // {id,kind,x,y,w,h,...}
let netSel = null;   // 当前聚焦场景 id
let themeSel = null; // 当前聚焦母题 id
let netRefs = {};    // 概念 id -> {g, rect, text}，变形动画用
let netEdges = null; // 网图的边层，淡出用
let curScenario = null;
let MODE = "net";

const conceptById = {};
G.concepts.forEach(c => conceptById[c.id] = c);
const scById = {};
G.scenarios.forEach(s => scById[s.id] = s);
const themeById = {};
G.themes.forEach(t => themeById[t.id] = t);

function layoutNet(){
  const nodes = [];
  const byLayer = {};
  G.layers.forEach(l => byLayer[l.id] = []);
  G.concepts.forEach(c => (byLayer[c.layer] || (byLayer[c.layer] = [])).push(c));
  // 层内排序：先按学习日期，再按标签 —— 纵向顺序≈时间顺序，未来时间轴可直接复用
  Object.keys(byLayer).forEach(k => byLayer[k].sort((a, b) =>
    (a.learned || "9999").localeCompare(b.learned || "9999") || a.label.localeCompare(b.label)));

  const ROWS = 13;                    // 每子列最多放 13 个，超过就并排多列
  const SUBGAP = 14;
  const HEAD = 34;                    // 层标题高度
  const TOP0 = 74;

  // 先算每层几列、总宽
  let cursor = LAYER_X0;
  const metas = G.layers.map(lay => {
    const list = byLayer[lay.id] || [];
    const cols = Math.max(1, Math.ceil(list.length / ROWS));
    const w = cols * NW + (cols - 1) * SUBGAP;
    const m = { lay, list, cols, x: cursor, w, list2: list };
    cursor += w + NGX;
    return m;
  });
  const maxH = Math.min(ROWS, Math.max(1, Math.max.apply(null, metas.map(m => m.list.length)))) * (NH + NGY);

  metas.forEach(m => {
    nodes.push({ kind: "layer", x: m.x, y: TOP0 - HEAD, w: m.w, h: HEAD - 8,
                 label: m.lay.label, color: m.lay.color, count: m.list.length });
    m.list.forEach((c, j) => {
      const col = Math.floor(j / ROWS), row = j % ROWS;
      const rowsInThisCol = (col === m.cols - 1) ? (m.list.length - col * ROWS) : ROWS;
      const colH = rowsInThisCol * (NH + NGY) - NGY;
      const y0 = TOP0 + (maxH - colH) / 2;
      nodes.push({
        kind: "concept", id: c.id, x: m.x + col * (NW + SUBGAP), y: y0 + row * (NH + NGY),
        w: NW, h: NH, label: c.label, layer: m.lay.id, color: m.lay.color, weight: c.weight,
      });
    });
  });
  // 场景锚点：左侧一列，垂直居中
  const scH = G.scenarios.length * (56 + 14);
  const sy0 = TOP0 + (maxH - scH) / 2;
  G.scenarios.forEach((sc, i) => {
    nodes.push({
      kind: "scenario", id: sc.id, x: SC_X, y: sy0 + i * (56 + 14), w: SC_W, h: 56,
      label: sc.label, sub: sc.sub, color: sc.color,
    });
  });
  return { nodes, totalW: cursor - NGX + 20, totalH: TOP0 + maxH + 30 };
}

function netFocusSet(sid){
  const set = new Set();
  if (!sid) return set;
  const sc = scById[sid];
  sc.steps.forEach(st => st.concepts.forEach(c => set.add(c)));
  return set;
}

function renderNet(keep){
  const keepView = keep ? { s: state.scale, x: state.tx, y: state.ty } : null;
  scene.innerHTML = "";
  const { nodes, totalW, totalH } = layoutNet();
  netNodes = nodes;
  const focus = netFocusSet(netSel);
  const themeFocus = themeSel ? new Set(themeById[themeSel].members) : null;

  const gE = el("g", {});
  const pos = {};
  nodes.forEach(n => { pos[n.id || ("layer" + n.x)] = n; });
  const nodePos = {};
  nodes.forEach(n => { if (n.kind === "concept") nodePos[n.id] = n; });
  const scPos = {};
  nodes.forEach(n => { if (n.kind === "scenario") scPos[n.id] = n; });

  function curve(x1, y1, x2, y2, color, op, width, dash, tag){
    const mx = (x1 + x2) / 2;
    const p = el("path", {
      d: `M ${x1} ${y1} C ${mx} ${y1}, ${mx} ${y2}, ${x2} ${y2}`,
      fill: "none", stroke: color, "stroke-width": width,
      "stroke-opacity": op, "stroke-linecap": "round",
    });
    if (dash) p.setAttribute("stroke-dasharray", dash);
    if (tag){
      if (tag.theme) p.setAttribute("data-t", "1");
      else {
        p.setAttribute("data-a", tag.a || ""); p.setAttribute("data-b", tag.b || "");
        p.setAttribute("data-k", tag.k || "");
      }
      p.setAttribute("data-op", String(op));
      p.setAttribute("data-w", String(width));
    }
    gE.appendChild(p);
  }
  const dimEdges = netSel ? 0.9 : 1;

  // 概念↔概念
  G.edges.forEach(e => {
    const a = nodePos[e.s], b = nodePos[e.t];
    if (!a || !b) return;
    let related = !netSel || (focus.has(e.s) && focus.has(e.t));
    if (themeFocus) related = themeFocus.has(e.s) && themeFocus.has(e.t);
    curve(a.x + a.w, a.y + a.h/2, b.x, b.y + b.h/2,
      e.type === "contrast" ? "#DC2626" : "#94a3b8",
      related ? 0.34 : 0.05, 1,
      e.type === "contrast" ? "4 3" : null, { a: e.s, b: e.t, k: "cc" });
  });
  // 场景 → 知识点
  G.uses.forEach(e => {
    const a = scPos[e.s], b = nodePos[e.t];
    if (!a || !b) return;
    const related = !netSel || netSel === e.s;
    const col = scById[e.s].color;
    curve(a.x + a.w, a.y + a.h/2, b.x, b.y + b.h/2,
      col, themeFocus ? 0.03 : (related ? (netSel ? 0.5 : 0.10) : 0.03),
      related ? 1.4 : 1, null, { a: e.s, b: e.t, k: "uses" });
  });
  // 母题：横贯虚线（选中时加粗实线、序号标注）
  G.themes.forEach(t => {
    const ms = t.members.map(id => nodePos[id]).filter(Boolean);
    const on = themeSel === t.id;
    const off = themeSel && !on;
    for (let i = 0; i < ms.length - 1; i++){
      const a = ms[i], b = ms[i + 1];
      curve(a.x + a.w, a.y + a.h/2, b.x, b.y + b.h/2, t.color,
        off ? 0.04 : (on ? 0.95 : 0.22), on ? 2.6 : 1.1, on ? null : "5 4", { theme: true });
    }
    if (on){
      // 在成员节点上标序号，读成一条「同一思想在不同层重复出现」的路径
      ms.forEach((n, i) => {
        const c = el("circle", { cx: n.x - 9, cy: n.y + n.h/2, r: 8.5, fill: t.color });
        gE.appendChild(c);
        const tx = el("text", { x: n.x - 9, y: n.y + n.h/2 + 0.5, "font-size": 9, "font-weight": 800,
          fill: "#fff", "text-anchor": "middle" });
        tx.textContent = String(i + 1);
        gE.appendChild(tx);
      });
    }
  });
  netEdges = gE;
  scene.appendChild(gE);

  const gN = el("g", {});
  netRefs = {};
  nodes.forEach(n => {
    if (n.kind === "layer"){
      const gl = el("g", {}); gl.setAttribute("data-deco", "1");
      const t = el("text", { x: n.x, y: n.y + 13, "font-size": 11, "font-weight": 800,
        fill: n.color, "letter-spacing": ".6" });
      t.textContent = n.label.toUpperCase();
      gl.appendChild(t);
      const t2 = el("text", { x: n.x, y: n.y + 13, "font-size": 10, fill: "#9ca3af",
        "text-anchor": "end" });
      t2.setAttribute("x", n.x + n.w);
      t2.textContent = n.count + " 个";
      gl.appendChild(t2);
      gN.appendChild(gl);
      return;
    }
    if (n.kind === "scenario"){
      const dim = netSel && netSel !== n.id;
      const g = el("g", {}); g.setAttribute("data-deco", "1"); g.setAttribute("data-sc", n.id);
      const r = el("rect", { x: n.x, y: n.y, width: n.w, height: n.h, rx: n.h / 2,
        fill: "#fff", stroke: n.color, "stroke-width": 1.6, opacity: dim ? 0.25 : 1 });
      r.setAttribute("data-sel", "0");
      g.appendChild(r);
      const dot = el("circle", { cx: n.x + 20, cy: n.y + n.h / 2, r: 6, fill: n.color });
      g.appendChild(dot);
      const t1 = el("text", { x: n.x + 36, y: n.y + n.h / 2 - 4, "font-size": 14, "font-weight": 800, fill: "#111827" });
      // 卡片固定宽，文字必须裁到框内，否则会画到卡片外面
      const AVAIL = n.w - 46;
      let lab = n.label;
      while (lab.length > 2 && textW(lab, 14, 800) > AVAIL) lab = lab.slice(0, -1);
      if (lab !== n.label) lab += "…";
      t1.textContent = lab;
      g.appendChild(t1);
      const t2 = el("text", { x: n.x + 36, y: n.y + n.h / 2 + 13, "font-size": 10, fill: "#6b7280" });
      let sb0 = n.sub || "";
      let sb = sb0;
      while (sb.length > 1 && textW(sb, 10, 400) > AVAIL) sb = sb.slice(0, -1);
      if (sb !== sb0) sb += "…";
      t2.textContent = sb;
      g.appendChild(t2);
      const _ttl = el("title", {});
      _ttl.textContent = n.label + (n.sub ? " · " + n.sub : "");
      g.appendChild(_ttl);
      g.style.cursor = "pointer";
      g.addEventListener("click", ev => {
        ev.stopPropagation();
        // 单击只看源码树；延时 220ms，让双击能把这次单击取消掉
        clearTimeout(cardClickTimer);
        cardClickTimer = setTimeout(() => {
          armScenario(n.id);
          if (window.openSrcTree) window.openSrcTree(n.id);
        }, 220);
      });
      g.addEventListener("dblclick", ev => {
        ev.stopPropagation();
        clearTimeout(cardClickTimer);
        focusScenario(n.id);
      });
      gN.appendChild(g);
      return;
    }
    // 概念
    const mk = markGet(n.id);
    const dim = (netSel && !focus.has(n.id)) || (themeFocus && !themeFocus.has(n.id));
    const isShared = n.weight >= 2;
    const unlearned = !conceptById[n.id].learned;
    const g = el("g", {});
    const rect = el("rect", { x: n.x, y: n.y, width: n.w, height: n.h, rx: 7,
      fill: mk ? MARK_TINTS[mk] : "#fff",
      stroke: mk ? MARK_COLORS[mk] : (unlearned ? "#cbd5e1" : "#e2ded6"),
      "stroke-width": mk ? 1.5 : 1,
      opacity: dim ? 0.18 : 1 });
    if (unlearned && !mk) rect.setAttribute("stroke-dasharray", "3 2.4");
    g.appendChild(rect);
    g.appendChild(el("rect", { x: n.x, y: n.y + 6, width: 3, height: n.h - 12, rx: 1.5,
      fill: n.color, opacity: dim ? 0.18 : 1 }));
    const t = el("text", { x: n.x + 12, y: n.y + n.h / 2 + 0.5, "font-size": 11.5,
      "font-weight": isShared ? 700 : 500, fill: "#1f2937", opacity: dim ? 0.18 : 1 });
    let label = n.label;
    while (label.length > 2 && textW(label, 11.5, isShared ? 700 : 500) > n.w - 44) label = label.slice(0, -1);
    if (label !== n.label) label += "…";
    t.textContent = label;
    g.appendChild(t);
    if (isShared){
      const b = el("g", {});
      b.appendChild(el("circle", { cx: n.x + n.w - 15, cy: n.y + n.h / 2, r: 8, fill: "#111827", opacity: dim ? 0.18 : 1 }));
      const bt = el("text", { x: n.x + n.w - 15, y: n.y + n.h / 2 + 0.5, "font-size": 9,
        "font-weight": 800, fill: "#fff", "text-anchor": "middle", opacity: dim ? 0.18 : 1 });
      bt.textContent = "×" + n.weight;
      b.appendChild(bt);
      b.appendChild(el("title", {})).textContent = "被 " + n.weight + " 条业务逻辑复用";
      g.appendChild(b);
    }
    g.appendChild(el("title", {})).textContent = n.label;
    g.style.cursor = "pointer";
    g.addEventListener("click", ev => { ev.stopPropagation(); openPanel(n.id); });
    netRefs[n.id] = { g: g, rect: rect, text: t, wx: n.x + n.w/2, wy: n.y + n.h/2 };
    gN.appendChild(g);
  });
  scene.appendChild(gN);

  CONTENT_NET.w = totalW; CONTENT_NET.h = totalH + 60;
  if (keepView){ state.scale = keepView.s; state.tx = keepView.x; state.ty = keepView.y; applyZoom(); }
  else fitNet();
}

const CONTENT_NET = { w: 0, h: 0 };
const state = { scale: 1, tx: 0, ty: 0 };

function applyZoom(){
  scene.setAttribute("transform", `translate(${state.tx},${state.ty}) scale(${state.scale})`);
  $("zoomval").textContent = Math.round(state.scale * 100) + "%";
}
function fitNet(){
  if (!CONTENT_NET.w) return;
  const W = svg.clientWidth, H = svg.clientHeight;
  const bar = document.querySelector(".topbar");
  const padTop = (bar ? bar.offsetHeight : 58) + 18, padBottom = 54, padX = 54;
  const s = Math.min((W - padX*2) / CONTENT_NET.w, (H - padTop - padBottom) / CONTENT_NET.h, 1.1);
  state.scale = Math.max(s, 0.12);
  state.tx = Math.round((W - CONTENT_NET.w * state.scale) / 2);
  state.ty = Math.round(padTop + (H - padTop - padBottom - CONTENT_NET.h * state.scale) / 2);
  applyZoom();
}

/* ================= 模式与交互 ================= */
const CONTENT_RIB = { w: 0, h: 0 };
const MORPH_MS = 680;

let armedScenario = null;      // 第一次点击：已淡化、未移动
let panelCid = null;           // 右侧信息框当前展示的概念

let cardClickTimer = null;
function redraw(keep){
  if (MODE === "src"){ if (window.srcRender) window.srcRender(keep); return; }
  if (MODE === "net") renderNet(keep);
  else ChainView.render(keep);
}
function setChip(id){
  document.querySelectorAll(".chip").forEach(c => {
    const on = c.dataset.id === (id || "");
    c.classList.toggle("on", on);
    c.style.background = on ? (c.dataset.color || "#111827") : "#fff";
    c.style.borderColor = on ? "transparent" : "#dedad2";
  });
}

/* ---------- 通用适配 ---------- */
function fitTo(w, h){
  if (!w || !h) return;
  const W = svg.clientWidth, H = svg.clientHeight;
  const bar = document.querySelector(".topbar");
  const padTop = (bar ? bar.offsetHeight : 58) + 18, padBottom = 54, padX = 54;
  const sc = Math.min((W - padX*2) / w, (H - padTop - padBottom) / h, 1.1);
  state.scale = Math.max(sc, 0.12);
  state.tx = Math.round((W - w * state.scale) / 2);
  state.ty = Math.round(padTop + (H - padTop - padBottom - h * state.scale) / 2);
  applyZoom();
}

/* ---------- 位置补间（用布局坐标，不依赖 getBoundingClientRect） ---------- */
function captureCenters(){
  const st = { s: state.scale, x: state.tx, y: state.ty };
  const out = {};
  Object.keys(netRefs).forEach(cid => {
    const r = netRefs[cid];
    if (r.wx == null) return;
    out[cid] = { x: st.x + r.wx * st.s, y: st.y + r.wy * st.s };
  });
  return out;
}
function flipFrom(oldPts){
  const moved = [];
  const cur = { s: state.scale, x: state.tx, y: state.ty };
  Object.keys(netRefs).forEach(cid => {
    const o = oldPts && oldPts[cid], ref = netRefs[cid];
    if (!o || ref.wx == null) return;
    const nx = cur.x + ref.wx * cur.s, ny = cur.y + ref.wy * cur.s;
    const dx = (o.x - nx) / cur.s, dy = (o.y - ny) / cur.s;
    if (Math.abs(dx) < 1 && Math.abs(dy) < 1) return;
    ref.g.style.transition = "none";
    ref.g.style.transform = `translate(${dx}px, ${dy}px)`;
    ref.g.style.opacity = "0.35";
    moved.push(ref.g);
  });
  if (!moved.length) return;
  scene.getBoundingClientRect();
  requestAnimationFrame(() => {
    moved.forEach(g => {
      g.style.transition = `transform ${MORPH_MS}ms cubic-bezier(.34,.02,.2,1), opacity .5s ease`;
      g.style.transform = "translate(0px, 0px)";
      g.style.opacity = "1";
    });
  });
}

/* ================= 细节卡标记（复用原有 marks 系统） ================= */
let detSelP = null;
function detRect(p){ return document.querySelector('#scene rect[data-p="' + p + '"]'); }
function detSelect(p){
  detSelP = p;
  document.querySelectorAll('#scene rect[data-p]').forEach(r => {
    if (r.getAttribute("data-sel") === "1"){
      r.setAttribute("data-sel", "0");
      if (r.getAttribute("data-s0") !== null){
        r.setAttribute("stroke", r.getAttribute("data-s0"));
        r.setAttribute("stroke-width", r.getAttribute("data-w0") || ".8");
      }
    }
  });
  const r = detRect(p);
  if (r){
    r.setAttribute("data-s0", r.getAttribute("stroke") || "#94a3b8");
    r.setAttribute("data-w0", r.getAttribute("stroke-width") || ".8");
    r.setAttribute("data-sel", "1");
    r.setAttribute("stroke", "#2563eb");
    r.setAttribute("stroke-width", "2.6");
  }
}
function detMark(lv){
  if (!detSelP) return false;
  if (lv < 1 || lv > 3) lv = 1;
  const cur = markGet(detSelP);
  if (cur === lv) delete marks[detSelP]; else marks[detSelP] = lv;   // 走原有标记
  saveMarks();
  const keep = detSelP;
  redraw(true);          // 重画链：圆钮、底色、边框、统计一起更新
  updateStats();
  setTimeout(function(){
    bindDetailCards();
    if (keep) detSelect(keep);
  }, 30);
  return true;
}
function bindDetailCards(){
  if (MODE !== "chain") return;
  if (!window.__keyBound){
    window.__keyBound = 1;
    document.addEventListener("keydown", mKeydown, true);
  }
  if (!window.__detBound){
    window.__detBound = 1;
    svg.addEventListener("click", function(e){
      if (MODE !== "chain") return;
      let n = e.target, p = null;
      for (let i = 0; i < 3 && n && n !== svg; i++){
        if (n.getAttribute && n.getAttribute("data-p")){ p = n.getAttribute("data-p"); break; }
        if (n.tagName && n.tagName.toLowerCase() === "text"){
          const par = n.parentNode;
          const ty = parseFloat(n.getAttribute("y") || "0");
          const rects = par.querySelectorAll("rect[data-p]");
          for (let k = 0; k < rects.length; k++){
            const y = parseFloat(rects[k].getAttribute("y") || "0");
            const h = parseFloat(rects[k].getAttribute("height") || "0");
            if (ty >= y - 1 && ty <= y + h + 1){ p = rects[k].getAttribute("data-p"); break; }
          }
          if (p) break;
        }
        n = n.parentNode;
      }
      if (p) detSelect(p);
    });
  }
  if (detSelP && detRect(detSelP)) detSelect(detSelP);
}
/* ---------- 连贯变形：旧画面整体缩放/位移并溶解到新画面 ---------- */
function crossMorph(paint, ms){
  const dur = ms || 680;
  const old = { s: state.scale, x: state.tx, y: state.ty };
  let ghost = null;
  try {
    const wrap = document.createElementNS("http://www.w3.org/2000/svg", "g");
    wrap.setAttribute("pointer-events", "none");
    wrap.appendChild(scene.cloneNode(true));
    svg.appendChild(wrap);
    ghost = wrap;
  } catch (e){ ghost = null; }
  paint();
  if (!ghost) return;
  const neu = { s: state.scale, x: state.tx, y: state.ty };
  const k = neu.s / old.s;
  const tx = neu.x - old.x * k, ty = neu.y - old.y * k;
  ghost.style.transformOrigin = "0 0";
  ghost.style.transition = `transform ${dur}ms cubic-bezier(.34,.02,.2,1), opacity ${Math.round(dur*0.78)}ms ease`;
  scene.style.opacity = "0";
  scene.style.transition = "opacity .12s ease";
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      ghost.style.transform = `translate(${tx}px, ${ty}px) scale(${k})`;
      ghost.style.opacity = "0";
      scene.style.opacity = "1";
      scene.style.transition = `opacity ${Math.round(dur*0.5)}ms ease ${Math.round(dur*0.35)}ms`;
    });
  });
  setTimeout(() => { if (ghost && ghost.parentNode) ghost.parentNode.removeChild(ghost); }, dur + 60);
}

/* ---------- 第一次点击：聚光灯（淡化无关 + 高亮选中场景与其连线） ---------- */
function armScenario(id){
  const sc = scById[id];
  if (!sc) return;
  armedScenario = id;
  netSel = null;
  curScenario = null;
  setChip(id);
  const related = netFocusSet(id);

  // 知识点：相关的保持满亮度并加一点浮起阴影，无关的压到 4%
  Object.keys(netRefs).forEach(cid => {
    const g = netRefs[cid].g;
    const on = related.has(cid);
    g.style.transition = "opacity .34s ease, filter .34s ease";
    g.style.opacity = on ? "1" : "0.04";
    g.style.filter = on ? "drop-shadow(0 2px 6px rgba(15,23,42,.20))" : "none";
    // 淡化的知识点不接收点击：既点不开详情，也不抢走鼠标
    g.style.pointerEvents = on ? "auto" : "none";
    g.style.cursor = on ? "pointer" : "default";
  });

  // 连线：按端点逐条判定，连到相关知识点的高亮，其余几乎消失
  if (netEdges){
    netEdges.style.opacity = "1";
    netEdges.style.transition = "none";
    Array.prototype.forEach.call(netEdges.children, p => {
      p.style.transition = "stroke-opacity .34s ease, stroke-width .34s ease";
      const w0 = parseFloat(p.getAttribute("data-w") || "1");
      if (p.getAttribute("data-t") === "1"){       // 母题横贯线
        p.style.strokeOpacity = "0.04";
        p.style.strokeWidth = w0 + "px";
        return;
      }
      const a = p.getAttribute("data-a"), b = p.getAttribute("data-b");
      const k = p.getAttribute("data-k");
      const ra = related.has(a), rb = related.has(b);
      if (k === "cc"){
        // 概念之间的关系：两端都相关 → 最亮；只挂一端 → 中等；无关 → 几乎不见
        if (ra && rb){ p.style.strokeOpacity = "0.92"; p.style.strokeWidth = (w0 + 0.6) + "px"; }
        else if (ra || rb){ p.style.strokeOpacity = "0.22"; p.style.strokeWidth = w0 + "px"; }
        else { p.style.strokeOpacity = "0.02"; p.style.strokeWidth = w0 + "px"; }
      } else {
        // 场景 → 知识点：半透明细线，避免糊成蜘蛛网
        if (ra || rb){ p.style.strokeOpacity = "0.20"; p.style.strokeWidth = (w0 * 0.8) + "px"; }
        else { p.style.strokeOpacity = "0.02"; p.style.strokeWidth = w0 + "px"; }
      }
    });
  }

  // 装饰：选中的场景卡亮起来，其余场景卡与层标题压暗
  document.querySelectorAll('#scene g[data-deco="1"]').forEach(g => {
    const sid = g.getAttribute("data-sc");
    const isSel = sid === id;
    const isSc = !!sid;
    g.style.transition = "opacity .3s ease, filter .3s ease";
    g.style.opacity = isSel ? "1" : (isSc ? "0.34" : "0.18");
    g.style.filter = isSel ? "drop-shadow(0 8px 20px rgba(15,23,42,.20))" : "none";
    if (isSc){
      const col = (scById[sid] || {}).color || "#374151";
      const r = g.querySelector("rect"), tx = g.querySelectorAll("text");
      if (r){
        r.setAttribute("fill", isSel ? col : "#fff");
        r.setAttribute("stroke", col);
        r.setAttribute("data-sel", isSel ? "1" : "0");
      }
      const dot = g.querySelector("circle");
      if (dot) dot.setAttribute("fill", isSel ? "#fff" : col);
      if (tx[0]) tx[0].setAttribute("fill", isSel ? "#fff" : "#111827");
      if (tx[1]) tx[1].setAttribute("fill", isSel ? "rgba(255,255,255,.88)" : "#6b7280");
    }
  });

  $("panel").classList.remove("show");
  panelCid = null;
  $("brandsub").textContent = sc.label + " · 再点一次看链条";
  $("hint").innerHTML = "<b>已选中</b>这条逻辑：相关知识点与连线高亮 · 再点一次 → 排成细节卡视图";
}

/* ---------- 第二次点击：连贯地飞成「细节卡视图」 ---------- */
function focusScenario(id){
  const sc = scById[id];
  if (!sc) return;
  armedScenario = null;
  netSel = id;
  curScenario = id;
  setChip(id);
  $("panel").classList.remove("show");
  panelCid = null;

  crossMorph(() => {
    const cd = chainData(sc);
    ChainView.setData(cd);
    ChainView.state.collapsedStage.clear();
    ChainView.state.collapsedItem.clear();
    cd.main.forEach((col, i) => {
      col.items.forEach((it, j) => { if (it.details.length) ChainView.state.collapsedItem.add(i + "-" + j); });
    });
    MODE = "chain";
    ChainView.render(false);
    setTimeout(bindDetailCards, 30);
  });

  $("btn-back").classList.add("show");
  $("legend").style.display = "none";
  allExpanded = false;
  $("btn-expand-all").textContent = "⊞ 全部展开";
  $("btn-expand-all").classList.add("show");
  $("brandsub").textContent = sc.label + " · " + sc.steps.length + " 个环节";
  $("hint").innerHTML = "<b>点阶段</b>收起/展开 · <b>点环节</b>看细节 · <b>点知识点</b>看详情（再点关闭） · <b>拖拽</b>平移 · <b>滚轮</b>缩放";
  updateStats();
}

let allExpanded = false;
function toggleExpandAll(){
  if (MODE !== "chain") return;
  allExpanded = !allExpanded;
  ChainView.state.collapsedStage.clear();
  ChainView.state.collapsedItem.clear();
  if (!allExpanded){
    const cd = chainData(scById[curScenario]);
    cd.main.forEach((col, i) => {
      col.items.forEach((it, j) => { if (it.details.length) ChainView.state.collapsedItem.add(i + "-" + j); });
    });
  }
  ChainView.render(false);
  setTimeout(bindDetailCards, 30);
  $("btn-expand-all").textContent = allExpanded ? "⊟ 全部收起" : "⊞ 全部展开";
}
function backToNet(){
  if ($("mysqlview").classList.contains("show")) return;
  const oldPts = null;
  armedScenario = null; netSel = null; themeSel = null; curScenario = null;
  MODE = "net";
  $("themecard").classList.remove("show");
  renderThemeChips();
  setChip(null);
  $("btn-back").classList.remove("show");
  $("btn-expand-all").classList.remove("show");
  $("legend").style.display = "";
  $("panel").classList.remove("show");
  panelCid = null;
  $("brandsub").textContent = "单击场景看源码树 · 点层展开 · 点类看代码 · 双击排成长链";
  $("hint").innerHTML = "<b>单击场景</b>看源码树 · <b>双击场景</b>排成长链 · <b>点知识点</b>看详情";
  renderNet(false);
  if (oldPts && Object.keys(oldPts).length) flipFrom(oldPts);
  scene.style.opacity = "0";
  scene.style.transition = "opacity .26s ease";
  requestAnimationFrame(() => { scene.style.opacity = "1"; });
  updateStats();
}

/* ---------- 环节详情抽屉（保留：知识点 + 细节清单） ---------- */
function openStepPanel(st){
  const pi = st.phase;
  const sc = curScenario ? scById[curScenario] : null;
  const color = (sc && sc.phases[pi] && sc.phases[pi].color) || "#334155";
  $("panel-head").innerHTML =
      `<div class="lay" style="color:${color}">环节 · ${sc ? sc.label : ""}</div>`
    + `<h2>${st.label}</h2>`
    + `<div class="aka">${st.details.length} 条细节 · ${st.concepts.length} 个知识点</div>`;
  const chips = st.concepts.map(cid => {
    const c = conceptById[cid];
    const lay = G.layers.find(l => l.id === c.layer) || { label: c.layer, color: "#94a3b8" };
    return `<a class="kchip" data-cid="${cid}"><i style="background:${lay.color}"></i>${c.label}</a>`;
  }).join("");
  const dets = st.details.map(d => `<li>${d}</li>`).join("");
  $("panel-body").innerHTML =
      `<h3>关联的知识点（${st.concepts.length}）</h3>`
    + `<div class="kchips">${chips || '<span style="color:#9ca3af">这个环节没有登记知识点</span>'}</div>`
    + `<h3>细节（${st.details.length}）</h3>`
    + (dets ? `<ul>${dets}</ul>` : '<div style="color:#9ca3af">—</div>');
  $("panel-body").querySelectorAll(".kchip").forEach(a => {
    a.onclick = () => openPanel(a.dataset.cid);
  });
  $("panel").classList.add("show");
}

/* ================= 侧栏 ================= */
/* ================= MySQL 栏目（章节卡 → 组卡 → 知识点卡，逐级展开） ================= */
const MV_COLORS = ["#2563eb", "#0E7490", "#7c3aed", "#dc2626", "#059669", "#ea580c"];
let mysqlBuilt = false;
function mEsc(x){
  return String(x).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
}
let MV_ALL = [];
function mToggle(el){ el.parentNode.classList.toggle("open"); }
let MV_MARKS = {};
try { MV_MARKS = JSON.parse(localStorage.getItem("mm-mysql-marks-v1") || "{}"); } catch (e) { MV_MARKS = {}; }
const MV_MCOLOR = ["#DC2626", "#D97706", "#047857"];
const MV_MNAME = ["不会", "仅了解", "理解"];
function mMark(id, lv){
  if (MV_MARKS[id] === lv) delete MV_MARKS[id]; else MV_MARKS[id] = lv;
  try { localStorage.setItem("mm-mysql-marks-v1", JSON.stringify(MV_MARKS)); } catch (e) {}
  const pop = $("mvpop");
  const idx = +pop.dataset.i;
  const p = MV_ALL[idx];
  if (p) pop.innerHTML = mvPopHtml(p);
  document.querySelectorAll(".pt").forEach(row => {
    const it = MV_ALL[+row.dataset.i];
    if (!it) return;
    const ph = row.querySelector(".ph");
    let dot = ph.querySelector(".mkdot");
    const lv2 = MV_MARKS[it.id];
    if (lv2){
      if (!dot){ dot = document.createElement("em"); dot.className = "mkdot"; ph.appendChild(dot); }
      dot.style.background = MV_MCOLOR[lv2];
    } else if (dot){ dot.remove(); }
  });
}
function mvPopHtml(p){
  const body = (p.text || []).map(t => `<div class="ms">${mEsc(t)}</div>`).join("")
    + (p.tips || []).map(t => `<div class="mo">⚠ ${mEsc(t)}</div>`).join("")
    + (p.code && p.code.length
        ? `<div class="tag">代码示例 · ${p.code.length} 段</div>`
          + p.code.map((c, k) => {
              const note = (c && c.sql !== undefined) ? (c.note || "") : "";
              const sql = (c && c.sql !== undefined) ? c.sql : c;
              const codeHtml = (c && c.html) ? c.html : mEsc(sql);
              return (note ? `<div class="ccap">${mEsc(note)}</div>`
                           : `<div class="ccap ccap-mute">示例 ${k + 1}</div>`)
                + `<pre class="sql">${codeHtml}</pre>`;
            }).join("")
        : "");
  const lv = MV_MARKS[p.id];
  const bar = `<div class="mkbar"><b>标记</b>`
    + MV_MNAME.map((nm, k) =>
        `<button class="mkbtn${lv === k ? " on" + k : ""}" onclick="mMark('${p.id}',${k})">`
        + `${nm}<em class="key">${"ASD"[k]}</em></button>`
      ).join("")
    + `<span class="keyhint">按 A / S / D 也可标记</span></div>`;
  return `<div class="ph-head"><h4>${mEsc(p.label)}</h4><button class="x" onclick="mClose()">×</button></div>`
    + `<div class="ph-body">${bar}${body || '<div class="ms">—</div>'}</div>`;
}
function mOpen(el){
  const row = el.parentNode;
  const idx = +row.dataset.i;
  const p = MV_ALL[idx];
  if (!p) return;
  document.querySelectorAll(".pt.on").forEach(x => x.classList.remove("on"));
  row.classList.add("on");
  const pop = $("mvpop");
  pop.dataset.i = String(idx);
  pop.innerHTML = mvPopHtml(p);
  $("mvmask").classList.add("show");
  pop.setAttribute("tabindex", "-1");
  pop.onkeydown = mKeydown;
  requestAnimationFrame(() => { pop.classList.add("show"); try { pop.focus(); } catch (e) {} });
}

function mClose(){
  $("mvpop").classList.remove("show");
  $("mvmask").classList.remove("show");
  document.querySelectorAll(".pt.on").forEach(x => x.classList.remove("on"));
}
function buildMysql(){
  if (mysqlBuilt) return;
  mysqlBuilt = true;
  const cols = MYSQL.chapters.map((ch, ci) => {
    const col = MV_COLORS[ci % MV_COLORS.length];
    const groups = ch.groups.map((g, gi) => {
      const pts = g.points.map(p => {
        const n = (p.code || []).length;
        const idx = MV_ALL.push(Object.assign({ color: col }, p)) - 1;
        const mkl = MV_MARKS[p.id];
        return `<div class="pt" style="color:${col}" data-i="${idx}">`
          + `<div class="ph" onclick="mOpen(this)"><span>${mEsc(p.label)}</span>`
          + (mkl ? `<em class="mkdot" style="background:${MV_MCOLOR[mkl]}"></em>` : "")
          + (n ? `<i>${n} 段</i>` : "") + `</div></div>`;
      }).join("");
      return `<div class="gp" style="color:${col}">`
        + `<div class="gh" onclick="mToggle(this)"><b>${mEsc(g.label)}</b><em>${g.points.length}</em></div>`
        + `<div class="gb">${pts}</div></div>`;
    }).join("");
    const n = ch.groups.reduce((a, g) => a + g.points.length, 0);
    return `<div class="mv-col"><div class="mh" style="background:${col}">`
      + `<i>${ci + 1}</i><h3>${mEsc(ch.label)}</h3><u>${n}</u></div>`
      + `<div class="mg">${groups}</div></div>`;
  });
  $("mv-body").innerHTML = cols.join('<div class="arw">→</div>');
  mStat();
  window.addEventListener("keydown", mKeydown, true);
}
function mSave(){
  try { localStorage.setItem("mm-mysql-marks-v1", JSON.stringify(MV_MARKS)); } catch (e) {}
}
function mStat(){
  const n = Object.keys(MV_MARKS).length;
  $("mv-stat").textContent = MYSQL.meta.chapters + " 章 · " + MYSQL.meta.groups + " 组 · "
    + MYSQL.meta.points + " 个知识点 · " + MYSQL.meta.withCode + " 段代码"
    + (n ? " · 已标记 " + n : "")
    + " · 来源：" + MYSQL.meta.source;
}
function mRebuild(){
  mysqlBuilt = false;
  MV_ALL = [];
  buildMysql();
}
function mToggleAllGroups(){
  const gs = Array.prototype.slice.call(document.querySelectorAll(".gp"));
  if (!gs.length) return;
  const anyClosed = gs.some(g => !g.classList.contains("open"));
  gs.forEach(g => g.classList.toggle("open", anyClosed));
  $("mv-expand").textContent = anyClosed ? "⊟ 收起全部" : "⊞ 展开全部";
}
function mExport(){
  const payload = { type: "mindmap-mysql-marks", v: 1,
                    exportedAt: new Date().toISOString().slice(0, 19), marks: MV_MARKS };
  const blob = new Blob([JSON.stringify(payload, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = "mm-mysql-marks.json";
  document.body.appendChild(a);
  a.click();
  setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 800);
}
function mImport(file){
  const fr = new FileReader();
  fr.onload = () => {
    try {
      const d = JSON.parse(fr.result);
      const mk = d.marks || d;
      if (!mk || typeof mk !== "object") throw new Error("格式不对");
      let n = 0;
      Object.keys(mk).forEach(k => {
        const v = +mk[k];
        if (v >= 0 && v <= 2){ MV_MARKS[k] = v; n++; }
      });
      mSave();
      mClose();
      mRebuild();
      alert("已导入 " + n + " 条 MySQL 标记");
    } catch (e) {
      alert("导入失败：" + e.message);
    }
  };
  fr.readAsText(file);
}
function mKeydown(e){
  if (!e || e.ctrlKey || e.metaKey || e.altKey) return;
  const tag = (e.target && e.target.tagName || "").toLowerCase();
  if (tag === "input" || tag === "textarea") return;
  const pop = $("mvpop");
  const map = { a: 0, s: 1, d: 2 };
  const k = (e.key || "").toLowerCase();
  if (!(k in map)) return;
  // 长链图：优先作用于选中的细节卡（marks 用 1/2/3，0=未标记，故 +1）
  if (detSelP && MODE === "chain"){ e.preventDefault(); detMark(map[k] + 1); return; }
  if (!pop || !pop.dataset.i) return;
  const p = MV_ALL[+pop.dataset.i];
  if (!p) return;
  e.preventDefault();
  mMark(p.id, map[k]);
}
window.addEventListener("keydown", mKeydown, true);
function setMysqlView(on){
  if (typeof mClose === "function") mClose();
  $("mysqlview").classList.toggle("show", on);
  $("tab-mysql").classList.toggle("on", on);
  $("tab-graph").classList.toggle("on", !on);
  if (on){
    ["themes", "themecard", "legend", "hint", "btn-back"].forEach(id => {
      const e = $(id); if (e) e.style.display = "none";
    });
    $("panel").classList.remove("show");
    panelCid = null;
    buildMysql();
  } else {
    if (MODE === "chain"){ $("legend").style.display = "none"; $("btn-back").classList.add("show"); }
    else { $("legend").style.display = ""; $("btn-back").classList.remove("show"); }
    $("themes").style.display = "";
    $("hint").style.display = "";
    $("themecard").style.display = "";
  }
}
function openPanel(cid){
  const c = conceptById[cid];
  if (!c) return;
  const pop = $("panel");
  if (panelCid === cid && pop.classList.contains("show")){
    pop.classList.remove("show");
    panelCid = null;
    document.querySelectorAll("#scene g.is-active").forEach(g => g.classList.remove("is-active"));
    return;
  }
  panelCid = cid;
  const lay = G.layers.find(l => l.id === c.layer) || { label: c.layer, color: "#666" };
  $("panel-head").innerHTML =
      `<div class="lay" style="color:${lay.color}">${lay.label}</div>`
    + `<h2>${c.label}</h2>`
    + (c.aka ? `<div class="aka">${c.aka}</div>` : "");
  const scs = c.scenarios.map(sid => {
    const sc = scById[sid];
    const steps = sc.steps.filter(st => st.concepts.indexOf(cid) >= 0).map(st => st.label);
    return `<span class="sc"><i style="background:${sc.color}"></i>${sc.label}</span>`
      + `<ul style="margin:2px 0 10px">${steps.map(s => "<li>" + s + "</li>").join("")}</ul>`;
  }).join("");
  const ths = c.themes.map(tid => {
    const t = G.themes.find(x => x.id === tid);
    return `<span class="sc" style="background:${t.color}1a;color:${t.color}">${t.label}</span>`;
  }).join("");
  const dep = G.edges.filter(e => e.s === cid || e.t === cid).map(e => {
    const other = conceptById[e.s === cid ? e.t : e.s];
    const arrow = e.type === "contrast" ? "⇄ 对照" : (e.type === "replaces" ? "→ 替代" : "→ 依赖");
    if (!other) return "";
    return `<li>${arrow} <b>${other.label}</b></li>`;
  }).join("");
  $("panel-body").innerHTML =
      `<h3>一句话</h3><div>${c.gloss}</div>`
    + `<h3>元信息</h3>`
    + `<div class="kv"><b>首次学习</b><span>${c.learned || '<span style="color:#C2410C;font-weight:700">未学</span>'}</span></div>`
    + `<div class="kv"><b>对应集数</b><span>${c.ep || "—"}</span></div>`
    + `<div class="kv"><b>被复用</b><span>${c.weight} 条业务逻辑</span></div>`
    + (ths ? `<h3>所属母题</h3><div>${ths}</div>` : "")
    + (scs ? `<h3>出现在</h3>${scs}` : "")
    + (dep ? `<h3>关系</h3><ul>${dep}</ul>` : "")
    + `<h3>我的标记</h3><div class="kv"><b>${MARK_NAMES[markGet(cid)]}</b></div>`;
  $("panel").classList.add("show");
}
$("panel-close").onclick = () => $("panel").classList.remove("show");

/* ================= 顶栏 chips / 图例 ================= */
(function(){
  const box = $("chips");
  G.scenarios.forEach(sc => {
    const b = document.createElement("button");
    b.className = "chip";
    b.dataset.id = sc.id; b.dataset.color = sc.color;
    b.innerHTML = `<i style="background:${sc.color}"></i>${sc.label}`;
    b.onclick = () => {
      // MySQL 层打开时，顶栏场景 chip 一律不响应，保证 MySQL 不被关掉
      if ($("mysqlview").classList.contains("show")) return;
      if (armedScenario === sc.id) { focusScenario(sc.id); return; }
      if (armedScenario) backToNet();     // 先清掉上一个的淡化
      armScenario(sc.id);
    };
    box.appendChild(b);
  });
  const lg = $("legend");
  lg.innerHTML = G.layers.map(l => `<span><i style="background:${l.color}"></i>${l.label}</span>`).join("")
    + `<span style="opacity:.75">虚线框 = 还没学</span>`;
})();

/* ================= 母题（横贯全图的思想） ================= */
function renderThemeChips(){
  const box = $("themes");
  box.innerHTML = "";
  G.themes.forEach(t => {
    const b = document.createElement("button");
    b.className = "tchip" + (themeSel === t.id ? " on" : "");
    b.style.background = themeSel === t.id ? t.color : "";
    b.innerHTML = `<i style="background:${themeSel === t.id ? "#fff" : t.color}"></i>${t.label}`;
    b.onclick = () => toggleTheme(t.id);
    box.appendChild(b);
  });
  const back = document.createElement("a");
  back.className = "tchip";
  back.href = "index.html";
  back.title = "回到经典导图 / 长链视图";
  back.textContent = "↩ 经典导图";
  box.appendChild(back);
}
function toggleTheme(id){
  if (MODE !== "net") backToNet();
  themeSel = (themeSel === id) ? null : id;
  netSel = null;
  setChip(null);
  renderThemeChips();
  const card = $("themecard");
  if (!themeSel){
    card.classList.remove("show");
    renderNet(false);
    return;
  }
  const t = themeById[themeSel];
  const rows = t.members.map((cid, i) => {
    const c = conceptById[cid];
    const lay = G.layers.find(l => l.id === c.layer) || { label: c.layer };
    return `<li>${i + 1}. <b>${c.label}</b><span class="ly">${lay.label}${c.learned ? "" : " · 未学"}</span></li>`;
  }).join("");
  card.innerHTML = `<button class="x" id="tcard-x">×</button>`
    + `<h4 style="color:${t.color}">${t.label}</h4>`
    + `<p class="note">${t.note}</p>`
    + `<ol>${rows}</ol>`;
  card.classList.add("show");
  card.querySelector("#tcard-x").onclick = () => { themeSel = null; card.classList.remove("show"); renderThemeChips(); renderNet(false); };
  renderNet(false);
}

$("btn-back").onclick = backToNet;
$("btn-expand-all").onclick = toggleExpandAll;
$("mv-expand").onclick = mToggleAllGroups;
$("mv-export").onclick = mExport;
$("mv-import").onclick = () => $("mv-file").click();
$("mv-file").onchange = e => {
  if (e.target.files && e.target.files[0]) mImport(e.target.files[0]);
  e.target.value = "";
};
$("tab-mysql").onclick = () => setMysqlView(true);
$("mvmask").onclick = mClose;
document.addEventListener("keydown", e => { if (e.key === "Escape") mClose(); });
document.addEventListener("keydown", mKeydown);
$("tab-graph").onclick = () => setMysqlView(false);

$("btn-fit").onclick = () => redraw(false);
$("btn-in").onclick = () => { state.scale = Math.min(state.scale * 1.18, 3); applyZoom(); };
$("btn-out").onclick = () => { state.scale = Math.max(state.scale / 1.18, 0.08); applyZoom(); };

svg.addEventListener("wheel", e => {
  e.preventDefault();
  const r = svg.getBoundingClientRect();
  const mx = e.clientX - r.left, my = e.clientY - r.top;
  const k = e.deltaY < 0 ? 1.12 : 1/1.12;
  const st = (MODE === "chain") ? ChainView.state : state;
  const ns = Math.min(Math.max(st.scale * k, 0.08), 3);
  const q = ns / st.scale;
  st.tx = mx - (mx - st.tx) * q;
  st.ty = my - (my - st.ty) * q;
  st.scale = ns;
  if (MODE === "chain") ChainView.apply(); else applyZoom();
}, { passive: false });

let drag = false, lx = 0, ly = 0;
svg.addEventListener("mousedown", e => { drag = true; lx = e.clientX; ly = e.clientY; svg.classList.add("dragging"); });
window.addEventListener("mousemove", e => {
  if (!drag) return;
  const st = (MODE === "chain") ? ChainView.state : state;
  st.tx += e.clientX - lx; st.ty += e.clientY - ly;
  lx = e.clientX; ly = e.clientY;
  if (MODE === "chain") ChainView.apply(); else applyZoom();
});
window.addEventListener("mouseup", () => { drag = false; svg.classList.remove("dragging"); });
svg.addEventListener("click", () => { /* 点空白：保留，便于后续取消选中 */ });
window.addEventListener("resize", () => { clearTimeout(window._t); window._t = setTimeout(() => redraw(false), 150); });


/* ================= 标记导出 / 导入（图谱这一套） ================= */
function markValidIds(){
  const s = new Set();
  G.scenarios.forEach(sc => sc.steps.forEach(st => {
    s.add(st.id);
    (st.details || []).forEach((_, k) => s.add(st.id + "." + k));
  }));
  return s;
}
function exportGraphMarks(){
  const out = { app: "mindmap-graph", version: 1,
                exportedAt: new Date().toISOString().slice(0, 19),
                total: Object.keys(marks).length, marks: marks };
  const d = new Date();
  const ymd = d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0")
            + "-" + String(d.getDate()).padStart(2, "0");
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([JSON.stringify(out, null, 1)], { type: "application/json" }));
  a.download = "graph-marks-" + ymd + ".json";
  document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}
function importGraphMarks(obj){
  let src = null;
  if (obj && typeof obj === "object"){
    if (obj.marks && typeof obj.marks === "object") src = obj.marks;        // marks.json / 本页导出
    else if (obj.graph && typeof obj.graph === "object") src = obj.graph;   // ?dump=1 汇总
    else if (obj.detail && typeof obj.detail === "object") src = obj.detail;
    else src = obj;                                                        // 纯 map
  }
  if (!src) return "文件里没有可识别的标记数据";
  const valid = markValidIds();
  // id 层级因场景而异（注册是 st.register.阶段.环节.细节，其他是 st.emp.环节.细节），
  // 所以只做前缀与取值校验，是否属于当前图谱交给 valid 集合判断
  const keys = Object.keys(src).filter(k =>
    k.indexOf("st.") === 0 && src[k] >= 1 && src[k] <= 3);
  const good = keys.filter(k => valid.has(k));
  const bad = keys.filter(k => !valid.has(k));
  if (!good.length) return "没有匹配到当前图谱的标记（文件中 " + keys.length + " 条都无法对应）";
  const who = (obj.app || obj.type || "标记文件");
  const overwrite = confirm(
    "来源：" + who + "\n" +
    "有效标记 " + good.length + " 条" + (bad.length ? "（另有 " + bad.length + " 条不在当前图谱，将跳过）" : "") + "\n\n" +
    "确定 = 覆盖合并（文件里的值优先）\n" +
    "取消 = 只补空缺（你现有的标记一律不动）");
  // 覆盖前先备份当前状态，万一导错还能救回来
  try { localStorage.setItem("mm-graph-marks-backup-v1", JSON.stringify(marks)); } catch(e){}
  let n = 0;
  good.forEach(k => {
    if (!overwrite && marks[k]) return;
    marks[k] = src[k]; n++;
  });
  saveMarks(); redraw(true); updateStats();
  return "导入 " + n + " 条" + (bad.length ? "，跳过 " + bad.length + " 条" : "") +
         "；当前共 " + Object.keys(marks).length + " 条";
}
(function(){
  const be = document.getElementById("btn-mk-export");
  const bi = document.getElementById("btn-mk-import");
  const fi = document.getElementById("mk-file");
  if (be) be.onclick = exportGraphMarks;
  if (bi && fi){
    bi.onclick = () => fi.click();
    fi.addEventListener("change", ev => {
      const f = ev.target.files && ev.target.files[0];
      if (!f) return;
      const fr = new FileReader();
      fr.onload = () => {
        let msg;
        try { msg = importGraphMarks(JSON.parse(fr.result)); }
        catch (e) { msg = "解析失败：" + e.message; }
        alert(msg);
      };
      fr.readAsText(f, "utf-8");
      ev.target.value = "";
    });
  }
})();

/* ================= 启动 ================= */
(function(){
  const migrated = migrateOldMarks();
  const seeded = seedMarks();
  renderNet(false);
  updateStats();
  renderThemeChips();
  if (migrated){
    $("hint").innerHTML += ' · <b>已迁移旧标记 ' + migrated + ' 条</b>';
  }
  if (seeded){
    $("hint").innerHTML += ' · <b>已载入内置标记 ' + seeded + ' 条</b>';
  }
  const q = new URLSearchParams(location.search);
  /* 净图模式：隐藏所有界面元素，导海报用 */
  if (q.get("dump") === "1"){ setTimeout(dumpAllMarks, 700); }
  if (q.get("clean") === "1"){
    document.querySelector(".topbar").style.display = "none";
    ["hint", "legend", "themes", "themecard", "btn-back"].forEach(id => {
      const e = $(id); if (e) e.style.display = "none";
    });
    document.body.style.backgroundImage = "none";
  }
  const want = q.get("s");
  if (want && scById[want]) focusScenario(want);
  if (q.get("tab") === "mysql") setMysqlView(true);
  const wantT = q.get("t");
  if (wantT && themeById[wantT]) toggleTheme(wantT);
})();
"""

HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>前后端知识图谱 · 网状 / 链状</title>
<style>__CSS__</style>
</head>
<body>__BODY__
<script>__JS__</script>
</body>
</html>
"""


PANEL_FIX = '\n/* 右侧信息框：前置关键规则，避免被后面坏掉的 CSS 区吞掉 */\n.panel{display:flex!important;flex-direction:column!important}\n.panel.show{transform:translateX(0)!important}\n.panel:not(.show){transform:translateX(100%)!important}\n.panel-head{padding:20px 22px 15px!important;border-bottom:1px solid #f1eee8!important;flex:0 0 auto!important}\n.panel-body{display:block!important;flex:1 1 auto!important;padding:15px 22px 44px!important;\n  overflow:auto!important;font-size:12.5px!important;line-height:1.78!important;color:#374151!important}\n.panel .lay{font-size:10.5px;font-weight:800;letter-spacing:.6px;color:#6b7280;margin-bottom:7px}\n.panel h2{margin:0;font-size:18px;font-weight:800;color:#111827;line-height:1.35}\n.panel .aka{font-size:11px;color:#9ca3af;margin-top:5px}\n.panel h3{font-size:10.5px;font-weight:800;color:#9ca3af;letter-spacing:.5px;margin:17px 0 8px}\n.panel p{margin:0 0 10px}\n.panel .sc{display:inline-flex;align-items:center;gap:6px;font-size:11px;font-weight:700;\n  color:#374151;background:#f7f5f1;border-radius:999px;padding:4px 10px;margin:0 6px 6px 0}\n.panel .sc i{width:7px;height:7px;border-radius:50%;display:block}\n.panel ul{margin:6px 0 0;padding-left:16px}\n.panel li{font-size:12px;line-height:1.72;color:#374151;margin-bottom:5px}\n.panel .kchips{display:flex;flex-wrap:wrap;gap:6px}\n.panel .kchip{display:inline-flex;align-items:center;gap:5px;font-size:11px;font-weight:600;\n  color:#374151;background:#f7f5f1;border:1px solid #e8e5de;padding:4px 9px;border-radius:999px;cursor:pointer}\n.panel .kchip i{width:7px;height:7px;border-radius:50%;display:block}\n'


def main():
    graph = json.load(io.open(GRAPH, encoding="utf-8"))
    src = read(SRC_INDEX)
    chain = extract_chainview(src)
    # 让 ChainView 的数据可替换
    chain = chain.replace("const DATA = { main: CHAIN };", "let DATA = { main: [], flow: [], returnNote: \"\" };\nfunction setData(x){ DATA = { main: x.main || x, flow: x.flow || [], returnNote: x.returnNote || \"\" }; }")
    chain = chain.replace("return { render: render, fit: fit, apply: apply, state: state };",
                          "return { render: render, fit: fit, apply: apply, state: state, setData: setData };")
    if "setData" not in chain:
        raise SystemExit("ChainView 替换失败")
    # 箭头标签与回流文案改为按场景取值，不再写死成注册场景
    chain = chain.replace("FLOW[i] || \"\"", "(DATA.flow[i] || \"\")")
    # 细节卡打上路径，供点击选中 + A/S/D 标记
    chain = chain.replace('x:cx+14, y:dd.y, width:DETAIL_W',
                          '"data-p": dd.p, x:cx+14, y:dd.y, width:DETAIL_W')

    chain = chain.replace('"响应 JSON + 200 回到前端，渲染提示"', '(DATA.returnNote || "")')

    mysql = json.load(io.open(MYSQL_JSON, encoding="utf-8"))
    source = json.load(io.open(SOURCE_JSON, encoding="utf-8"))
    try:
        seed_marks = json.load(io.open(MARKS_JSON, encoding="utf-8"))
        seed_marks = seed_marks.get("marks", seed_marks) if isinstance(seed_marks, dict) else {}
    except Exception:
        seed_marks = {}
    js = JS.replace("__GRAPH__", json.dumps(graph, ensure_ascii=False, separators=(",", ":")))
    js = js.replace("__MYSQL__", json.dumps(mysql, ensure_ascii=False, separators=(",", ":")))
    js = js.replace("__CHAINVIEW__", chain)
    js = js.replace("__SEED__", json.dumps(seed_marks, ensure_ascii=False, separators=(",", ":")))
    page = HTML.replace("__CSS__", CSS).replace("__BODY__", BODY).replace("__JS__", js)
    page = page.replace("<style>", "<style>" + PANEL_FIX, 1)
    page = page.replace("</style>", SRC_CSS + "\n</style>", 1)
    page = page.replace("</body>", SRC_BODY + SRC_JS + "\n</body>", 1)
    page = page.replace("__SRC__", json.dumps(source, ensure_ascii=False, separators=(",", ":")))
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(page)
    print("写出", OUT, os.path.getsize(OUT), "bytes")
    print("  概念", len(graph["concepts"]), " 场景", len(graph["scenarios"]),
          " 步骤", graph["meta"]["steps"], " 关系边", len(graph["edges"]))


if __name__ == "__main__":
    main()
