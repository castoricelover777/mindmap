# -*- coding: utf-8 -*-
"""
build_source_index.py —— 扫描源码工程，生成 graph/data/source.json

两个工程：
  tlias    D:\\web-ai-project02\\tlias-web-management   部门/员工/统计（当前主线工程）
  webcase  F:\\myusb\\web-ai-code\\web-project01\\springboot-web-case   用户注册（早期三层示例）

产出结构：
  projects: {id: {name, kind, roots[]}}
  files:    {"<proj>|<relpath>": {proj, rel, pkg, name, layer, methods[], lines, code}}
  scenes:   {scenarioId: {proj, layers: [{id,label,desc,items:[fileKey,...]}], note}}

约定：只收源码与 mapper XML，不收 static/资源包/target；单文件超过 LIMIT 的跳过。
"""
import io, json, os, re, sys

sys.stdout.reconfigure(encoding="utf-8")

PROJECTS = {
    "tlias": {
        "name": "tlias-web-management",
        "kind": "Maven / Spring Boot",
        "root": r"D:\web-ai-project02\tlias-web-management",
    },
    "webcase": {
        "name": "springboot-web-case",
        "kind": "Maven / Spring Boot（早期三层示例）",
        "root": r"F:\myusb\web-ai-code\web-project01\springboot-web-case",
    },
}

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "graph", "data", "source.json")
LIMIT = 120 * 1024     # 单文件上限
SKIP_DIRS = {".git", ".idea", "target", "node_modules", ".git-old-20261026", "logs", "uploads"}


def layer_of(path, src):
    p = path.replace("\\", "/").lower()
    if "/controller/" in p:
        return "controller"
    if "/service/impl/" in p or "/service/" in p:
        return "service"
    if "/mapper/" in p or "/dao/" in p or p.endswith("mapper.xml"):
        return "mapper"
    if "/pojo/" in p or "/entity/" in p or "/domain/" in p:
        return "pojo"
    if "/exception/" in p:
        return "exception"
    if "/config/" in p:
        return "config"
    if "/utils/" in p or "/util/" in p:
        return "utils"
    return "other"


LAYER_META = {
    "controller": ("Controller 层", "表现层：接收请求、校验参数、调用 Service、封装 Result 返回"),
    "service":    ("Service 层", "业务层：业务规则、事务、多表组合，接口 + Impl 成对出现"),
    "mapper":     ("Mapper 层", "持久层：SQL 与结果映射（接口 + XML）"),
    "dao":        ("Dao 层", "持久层（早期示例用 Dao 而非 Mapper）"),
    "pojo":       ("Pojo 实体", "数据载体：与表字段一一对应，或接口出参"),
    "exception":  ("异常与兜底", "自定义异常 + 全局异常处理器"),
    "config":     ("配置类", "WebMvc / 对象存储参数绑定等"),
    "utils":      ("工具类", "与业务无关的通用能力"),
}

files = {}
stats = {"scanned": 0, "kept": 0, "skipped_big": 0}


def scan(pid, proj):
    root = proj["root"]
    if not os.path.isdir(root):
        print("  [跳过] 工程不存在:", root)
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if not fn.endswith((".java", ".xml")):
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root).replace("\\", "/")
            # 只收 main 下的源码与 mapper 配置
            if rel.startswith("src/main/") is False and rel.startswith("src/test/") is False:
                continue
            if rel.startswith("src/test/"):
                continue
            if fn.endswith(".xml") and "mapper" not in rel.lower():
                continue
            stats["scanned"] += 1
            size = os.path.getsize(full)
            if size > LIMIT:
                stats["skipped_big"] += 1
                continue
            try:
                code = io.open(full, encoding="utf-8").read()
            except UnicodeDecodeError:
                try:
                    code = io.open(full, encoding="gbk").read()
                except Exception:
                    continue
            code = code.replace("\r\n", "\n")
            pkg = ""
            name = fn.rsplit(".", 1)[0]
            methods = []
            if fn.endswith(".java"):
                m = re.search(r"^package\s+([\w.]+);", code, re.M)
                if m:
                    pkg = m.group(1)
                methods = re.findall(
                    r"^\s{0,4}(?:public|protected)\s+(?:static\s+)?(?:<[^>]+>\s*)?"
                    r"[\w<>\[\], .?]+\s+(\w+)\s*\([^;]*?\)\s*(?:throws [\w., ]+)?\{",
                    code, re.M)
                methods = [x for x in methods if x not in ("if", "for", "while", "switch", "catch")]
            key = pid + "|" + rel
            files[key] = {
                "proj": pid, "rel": rel, "pkg": pkg, "name": name,
                "layer": layer_of(rel, code),
                "methods": methods[:12], "lines": code.count("\n") + 1,
                "code": code,
            }
            stats["kept"] += 1
    return


def find(pid, suffix):
    """按相对路径结尾找文件 key，忽略目录差异"""
    hits = [k for k in files if k.startswith(pid + "|") and k.lower().endswith(suffix.lower())]
    return hits


def pick(pid, *suffixes):
    out = []
    for s in suffixes:
        out += find(pid, s)
    # 去重保序
    seen, res = set(), []
    for k in out:
        if k not in seen:
            seen.add(k)
            res.append(k)
    return res


def scene(pid, spec, note=""):
    """spec: [(layerId, [文件后缀...]), ...]"""
    layers = []
    for lid, suffixes in spec:
        items = pick(pid, *suffixes)
        if not items:
            continue
        label, desc = LAYER_META.get(lid, (lid, ""))
        layers.append({"id": lid, "label": label, "desc": desc, "items": items})
    return {"proj": pid, "layers": layers, "note": note}


def main():
    for pid, proj in PROJECTS.items():
        scan(pid, proj)
        print("  %-8s %s" % (pid, proj["root"]))

    S = {}
    # 用户注册：早期三层示例（Controller → Service → Dao）
    S["s.register"] = scene("webcase", [
        ("controller", ["controller/UserController.java"]),
        ("service", ["service/UserService.java", "service/impl/UserServiceImpl.java"]),
        ("mapper", ["dao/UserDao.java", "dao/impl/UserDaoImpl.java"]),
        ("pojo", ["pojo/User.java"]),
    ], note="注册链路用的是早期的三层示例工程：Controller → Service → Dao（当时还没上 MyBatis）。"
            "另有 UserController2/3、UserServiceImpl2、UserDaoImpl2 是课件里的变体写法，未列入。")

    S["s.dept"] = scene("tlias", [
        ("controller", ["controller/DeptController.java"]),
        ("service", ["service/DeptService.java", "service/impl/DeptServiceImpl.java"]),
        ("mapper", ["mapper/DeptMapper.java"]),
        ("pojo", ["pojo/Dept.java"]),
        ("exception", ["exception/GlobalExceptionHandler.java", "exception/BusinessException.java"]),
    ])

    S["s.emp"] = scene("tlias", [
        ("controller", ["controller/EmpController.java", "controller/UploadController.java"]),
        ("service", ["service/EmpService.java", "service/impl/EmpServiceImpl.java",
                     "service/EmpLogService.java", "service/impl/EmpLogServiceImpl.java"]),
        ("mapper", ["mapper/EmpMapper.java", "mapper/EmpExprMapper.java", "mapper/EmpLogMapper.java",
                    "mapper/EmpMapper.xml", "mapper/EmpExprMapper.xml"]),
        ("pojo", ["pojo/Emp.java", "pojo/EmpExpr.java", "pojo/EmpQueryParam.java",
                  "pojo/EmpLog.java", "pojo/PageResult.java"]),
        ("exception", ["exception/GlobalExceptionHandler.java", "exception/BusinessException.java"]),
        ("config", ["config/AliyunOssProperties.java"]),
        ("utils", ["utils/AliyunOSSUtils.java"]),
    ])

    S["s.clazz"] = scene("tlias", [
        ("controller", ["controller/ReportController.java"]),
        ("service", ["service/ReportService.java", "service/impl/ReportServiceImpl.java"]),
        ("mapper", ["mapper/ReportMapper.java"]),
        ("pojo", ["pojo/EmpJobData.java", "pojo/PageResult.java"]),
        ("exception", ["exception/GlobalExceptionHandler.java", "exception/BusinessException.java"]),
    ], note="第 11 节是「照接口文档自己完成」的作业：ClazzController / ClazzService / ClazzMapper / "
            "StudentController 等源码不在工程里。这里只列已实现的统计部分（Report*）与公共类。")

    S["s.ref"] = {"proj": "tlias", "layers": [], "note": "附录是查漏补缺的索引页，不对应具体源码。"}

    # 公共件：挂到每个有代码的场景里，方便随时点开 Result / 全局异常
    shared = pick("tlias", "pojo/Result.java", "pojo/PageResult.java",
                  "exception/GlobalExceptionHandler.java", "exception/BusinessException.java")
    for sid in ("s.dept", "s.emp", "s.clazz"):
        have = set()
        for L in S[sid]["layers"]:
            have |= set(L["items"])
        need = [k for k in shared if k not in have]
        if need:
            S[sid]["layers"].append({"id": "shared", "label": "公共件",
                                     "desc": "统一响应与全局异常兜底，每个业务都会用到",
                                     "items": need})

    data = {
        "projects": {pid: {"name": p["name"], "kind": p["kind"]} for pid, p in PROJECTS.items()},
        "files": files,
        "scenes": S,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")))

    size = os.path.getsize(OUT)
    print()
    print("  扫描 %d / 收下 %d / 超大跳过 %d" % (stats["scanned"], stats["kept"], stats["skipped_big"]))
    print("  输出 %s  %.1f KB" % (OUT, size / 1024))
    print()
    print("  各场景文件数：")
    for sid, sc in S.items():
        n = sum(len(L["items"]) for L in sc["layers"])
        print("    %-12s %2d 个文件 / %d 层" % (sid, n, len(sc["layers"])))

    # 逐层打印，便于核对
    print()
    for sid in ("s.register", "s.dept", "s.emp", "s.clazz"):
        print("  == %s ==" % sid)
        for L in S[sid]["layers"]:
            print("    [%s] %s" % (L["label"], L["desc"][:30]))
            for k in L["items"]:
                f = files[k]
                print("        %-58s %4d 行  %s" % (f["rel"], f["lines"], ",".join(f["methods"][:5])))


if __name__ == "__main__":
    main()
