# -*- coding: utf-8 -*-
"""
patch_llm_toolbar.py —— 数据分析页（llm.html）顶栏太挤导致「导出/导入/清空标记」看不见

做法：
  1) 把三个标记按钮收进「标记 ▾」下拉（保持原 id，原事件不受影响）
  2) 加 ≤1280px 紧凑样式，让 导航+操作+统计+标记+缩放 一行放得下
  3) 点击下拉项后自动收起；点别处也收起

脚本幂等：可重复执行。
"""
import io, os, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
P = os.path.join(ROOT, "llm.html")
MARK = "/* === 标记下拉（窄屏可见性修复）=== */"

t = io.open(P, encoding="utf-8").read()
if MARK in t:
    print("  [--] 已打过补丁，跳过")
    sys.exit(0)

# ---------------- 1) 把三个按钮包进下拉 ----------------
OLD = """      <button id="btn-export">导出标记</button>
    <button id="btn-import">导入标记</button>
    <input type="file" id="file-import" accept=".json,application/json" style="display:none">
    <button id="btn-reset">清空标记</button>"""
NEW = """      <div class="mkmenu" id="mkmenu">
      <button id="btn-mk" title="标记：导出 / 导入 / 清空">标记 ▾</button>
      <div class="mklist" id="mklist">
        <button id="btn-export">导出标记</button>
        <button id="btn-import">导入标记</button>
        <button id="btn-reset">清空标记</button>
        <input type="file" id="file-import" accept=".json,application/json" style="display:none">
      </div>
    </div>"""
if OLD not in t:
    print("  ❌ 找不到三个标记按钮，未修改")
    sys.exit(1)
t = t.replace(OLD, NEW, 1)
print("  OK 三个按钮收进「标记 ▾」下拉")

# ---------------- 2) CSS ----------------
CSS = MARK + """
.mkmenu{position:relative;flex:none}
.mklist{position:absolute;right:0;top:calc(100% + 6px);display:none;flex-direction:column;gap:3px;
  background:#fff;border:1px solid #dedad2;border-radius:9px;padding:5px;min-width:138px;
  box-shadow:0 10px 26px rgba(17,24,39,.16);z-index:60}
.mkmenu.open .mklist{display:flex}
.mklist button{width:100%;text-align:left;border:0;background:#fff;border-radius:6px;
  padding:7px 10px;font-size:11.5px;color:#374151}
.mklist button:hover{background:#f2efe9}
.mkmenu.open>#btn-mk{background:#e8f4f2;border-color:#9fd3cc;color:#0f766e}

@media (max-width: 1280px){
  .topbar{gap:8px;padding:0 10px}
  .brand .sub{display:none}
  .brand h1{font-size:13.5px}
  .seg a{padding:5px 8px;font-size:11.5px}
  .btns{gap:4px}
  .btns button{padding:5px 8px;font-size:11px}
  .stats{font-size:10px;gap:8px}
  #btn-mk{padding:5px 9px;font-size:11px}
  .zoom .val{min-width:36px;font-size:10.5px}
}
"""
t = t.replace("</style>", CSS + "</style>", 1)
print("  OK 注入下拉与窄屏紧凑样式")

# ---------------- 3) JS：开合逻辑 ----------------
JS = """
<script>
/* 标记下拉：点按钮开合，点别处 / 选完自动收起 */
(function(){
  const menu = document.getElementById("mkmenu");
  const btn  = document.getElementById("btn-mk");
  if (!menu || !btn) return;
  const close = () => menu.classList.remove("open");
  btn.addEventListener("click", ev => {
    ev.stopPropagation();
    menu.classList.toggle("open");
  });
  document.addEventListener("click", ev => {
    if (!menu.contains(ev.target)) close();
  }, true);
  // 点击下拉里的任意一项（导出/导入/清空）后收起
  menu.querySelector(".mklist").addEventListener("click", ev => {
    if (ev.target.tagName === "BUTTON") setTimeout(close, 0);
  });
  document.addEventListener("keydown", ev => { if (ev.key === "Escape") close(); });
})();
</script>
"""
t = t.replace("</body>", JS + "</body>", 1)
print("  OK 注入下拉交互脚本")

io.open(P, "w", encoding="utf-8", newline="\n").write(t)
print("  写入完成：%.1f KB" % (os.path.getsize(P) / 1024))
