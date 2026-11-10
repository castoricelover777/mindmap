#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 ml.html / llm.html 的「作者默认标记」快照（供页面 MARK_DEFAULTS 播种）。

用法（任意目录均可执行）：
    python graph/tools/gen_author_marks.py            # 生成/刷新两个 JSON（幂等：内容不变则字节不变）
    python graph/tools/gen_author_marks.py --check    # 只校验现有 JSON 与页面是否完全一致，不写文件

输入：直接解析页面里的 `const DATA = {...};`（json 部分用 json 模块解析，不依赖仓库外文件）。
标记键 = 页面叶子路径（页面内 assignPaths(DATA, "r") 的规则：根为 "r"，子节点追加 "-<i>"）。
输出：graph/data/ml-marks.json、graph/data/llm-marks.json，格式对齐 graph/data/fastapi-marks.json。

定级规则（对每个叶子卡的标题文本，按顺序取第一条命中；这是「作者默认复习基线」，不是用户自评）：
    1. 标题以「类比」开头                    -> 3（直觉可懂）
    2. 标题以「科研提示」开头                -> 1（需结合自己课题实践）
    3. 其余标题含 LEVEL1_WORDS 之一（进阶/踩坑类） -> 1
    4. 其余标题含 LEVEL2_WORDS 之一（方法/注意类） -> 2
    5. 其余                                  -> 3

脚本内置自校验（任一失败即非零退出）：
    * 叶子数量 == 页面叶子路径数量（ml 104 / llm 92）；
    * marks 的键集合与页面叶子路径集合完全一致，且路径形如 r-<i>-<j>-<k>、无重复；
    * 等级取值只允许 1/2/3，且不能全部同一档；
    * 序列化两次字节一致、反序列化再序列化字节一致（幂等）；UTF-8 直写中文（无 \\u 转义、无 BOM/CRLF）。
"""

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve()
ROOT = HERE.parents[2]  # graph/tools/gen_author_marks.py -> 仓库根

EXPORTED_AT = "2026-11-10T20:00:00+08:00"
VERSION = 1

# 页面规格：app 命名、期望叶子数、输出文件
PAGES = (
    {
        "html": "ml.html",
        "app": "ml-mindmap",
        "expected": 104,
        "out": "graph/data/ml-marks.json",
    },
    {
        "html": "llm.html",
        "app": "llm-mindmap",
        "expected": 92,
        "out": "graph/data/llm-marks.json",
    },
)

# 规则 3 / 规则 4 的关键词（先规则 3 后规则 4）
# LEVEL1 = 需要动手/推导/踩过坑才真懂的进阶内容；LEVEL2 = 需要一点背景的方法类内容
LEVEL1_WORDS = (
    "推导", "证明", "复杂度", "爆炸", "泄漏", "失败", "边界", "极限",
    "坑", "陷阱", "风险", "报错", "梯度", "收敛", "显存", "内存",
)
LEVEL2_WORDS = (
    "调参", "数值", "注意", "参数", "配置", "对比", "区别", "步骤",
    "流程", "技巧", "口诀", "经验", "选择", "取舍", "适用", "判断",
)

DATA_RE = re.compile(r"\bconst\s+DATA\s*=")
PATH_RE = re.compile(r"^r(?:-\d+)+$")
NOTE_TMPL = (
    "{html} 的作者默认基线，按标题形态定级（类比/科研提示/关键词），"
    "非用户自评；供页面 MARK_DEFAULTS 播种使用；生成脚本 graph/tools/gen_author_marks.py。"
)


def fail(msg):
    raise SystemExit("[FAIL] " + msg)


def load_page_data(html_path):
    """从页面解析 `const DATA = {...};`，返回 (data, 原始文本, DATA 字面量结束下标)。"""
    text = html_path.read_text(encoding="utf-8")
    m = DATA_RE.search(text)
    if not m:
        fail("%s 里找不到 const DATA =" % html_path.name)
    i = m.end()
    while i < len(text) and text[i].isspace():
        i += 1
    try:
        data, end = json.JSONDecoder().raw_decode(text, i)
    except json.JSONDecodeError as exc:
        fail("%s 的 DATA 不是合法 JSON 片段：%s" % (html_path.name, exc))
    if not isinstance(data, dict) or "t" not in data:
        fail("%s 的 DATA 结构不符（缺少根节点 t）" % html_path.name)
    return data, text, end


def walk_leaves(node, path):
    """递归遍历：页面里 assignPaths(DATA, "r") 的路径规则，返回 (path, title)。"""
    children = node.get("c") or []
    if not children:
        yield path, node.get("t", "")
        return
    for idx, child in enumerate(children):
        yield from walk_leaves(child, "%s-%d" % (path, idx))


def leaf_title_map_iterative(root):
    """独立实现（显式栈）再遍历一遍，用于交叉验证递归结果与路径规则。"""
    result = {}
    stack = [(root, "r")]
    while stack:
        node, path = stack.pop()
        children = node.get("c") or []
        if not children:
            result[path] = node.get("t", "")
            continue
        for idx in range(len(children) - 1, -1, -1):
            stack.append((children[idx], "%s-%d" % (path, idx)))
    return result


def classify(title):
    """五条定级规则，按顺序取第一条命中；返回 (等级, 命中说明)。"""
    t = (title or "").strip()
    if t.startswith("类比"):
        return 3, "rule1:类比"
    if t.startswith("科研提示"):
        return 1, "rule2:科研提示"
    for word in LEVEL1_WORDS:
        if word in t:
            return 1, "rule3:" + word
    for word in LEVEL2_WORDS:
        if word in t:
            return 2, "rule4:" + word
    return 3, "rule5:default"


def build_doc(spec):
    """解析页面 + 套规则 + 全部自校验，返回 (doc, stats)。"""
    html_path = ROOT / spec["html"]
    if not html_path.is_file():
        fail("找不到页面 %s" % html_path)

    data, _text, _end = load_page_data(html_path)
    leaves = list(walk_leaves(data, "r"))

    n = len(leaves)
    if n != spec["expected"]:
        fail("%s 叶子数 %d != 期望 %d" % (spec["html"], n, spec["expected"]))

    # 页面叶子集合（键集合的唯一权威来源）
    page_leaves = {}
    for path, title in leaves:
        if path in page_leaves:
            fail("%s 叶子路径重复：%s" % (spec["html"], path))
        page_leaves[path] = title

    # 交叉验证：独立栈式遍历的结果必须一致（路径规则 + 全部叶子都覆盖）
    iter_map = leaf_title_map_iterative(data)
    if iter_map != page_leaves:
        fail("%s 递归/迭代两次遍历的叶子集合不一致" % spec["html"])

    marks = {}
    reasons = Counter()
    depth_counter = Counter()
    for path, title in leaves:
        if not PATH_RE.match(path):
            fail("%s 叶子路径格式不符：%s" % (spec["html"], path))
        depth = path.count("-")  # "r-0-0-0" -> 3
        depth_counter[depth] += 1
        level, reason = classify(title)
        if level not in (1, 2, 3):
            fail("%s 等级越界：%s -> %r" % (spec["html"], path, level))
        marks[path] = level
        reasons[reason.split(":")[0]] += 1

    # 校验 1+2：数量与键集合
    if len(marks) != spec["expected"]:
        fail("%s marks 数量 %d != 期望 %d" % (spec["html"], len(marks), spec["expected"]))
    only_page = set(page_leaves) - set(marks)
    only_marks = set(marks) - set(page_leaves)
    if only_page or only_marks:
        fail("%s 键集合与页面叶子不一致：多页面 %r / 多 marks %r"
             % (spec["html"], sorted(only_page)[:5], sorted(only_marks)[:5]))
    if set(marks) != set(page_leaves):
        fail("%s 键集合与页面叶子集合不完全一致" % spec["html"])

    # 校验 3：等级分布不能全部同一档
    dist = Counter(marks.values())
    if len(dist) < 2:
        fail("%s 等级分布只有一档：%r" % (spec["html"], dict(dist)))
    if sum(dist.values()) != len(marks):
        fail("%s 等级分布总数不等于 marks 数量" % spec["html"])

    doc = {
        "app": spec["app"],
        "version": VERSION,
        "exportedAt": EXPORTED_AT,
        "total": len(marks),
        "note": NOTE_TMPL.format(html=spec["html"]),
        "marks": marks,
    }

    # 校验：note 必须写明「作者默认基线 / 按标题形态定级 / 非用户自评 / 生成脚本」
    for keyword in ("作者默认基线", "按标题形态定级", "非用户自评",
                    "graph/tools/gen_author_marks.py"):
        if keyword not in doc["note"]:
            fail("%s 的 note 缺少说明：%s" % (spec["html"], keyword))

    # 校验 4：序列化幂等（同一输入两次 dumps 字节一致；反序列化再序列化字节一致）
    payload = json.dumps(doc, ensure_ascii=False, indent=1)
    payload_again = json.dumps(doc, ensure_ascii=False, indent=1)
    if payload.encode("utf-8") != payload_again.encode("utf-8"):
        fail("%s 两次序列化字节不一致" % spec["html"])
    if json.dumps(json.loads(payload), ensure_ascii=False, indent=1) != payload:
        fail("%s 反序列化再序列化字节不一致" % spec["html"])
    if "\\u" in payload:
        fail("%s 输出出现了 \\u ASCII 转义（应 ensure_ascii=False 直写中文）" % spec["html"])

    stats = {
        "html": spec["html"],
        "leaves": n,
        "dist": dist,
        "reasons": reasons,
        "depths": depth_counter,
        "payload": payload,
        "out": ROOT / spec["out"],
    }
    return doc, stats


def report(stats):
    d = stats["dist"]
    print("[%s] leaves=%d dist L1=%d L2=%d L3=%d (1=不会/2=仅了解/3=理解)"
          % (stats["html"], stats["leaves"], d.get(1, 0), d.get(2, 0), d.get(3, 0)))
    print("[%s] OK 数量=%d，键集合与页面叶子完全一致，等级 ∈ {1,2,3}，非单一档"
          % (stats["html"], stats["leaves"]))
    print("[%s] OK 规则命中 %s；叶子深度 %s"
          % (stats["html"],
             dict(sorted(stats["reasons"].items())),
             dict(sorted(stats["depths"].items()))))
    print("[%s] OK 序列化幂等（两次字节一致、往返一致、UTF-8 无 \\u 转义）"
          % stats["html"])


def main():
    parser = argparse.ArgumentParser(description="生成 ml/llm 作者默认标记快照")
    parser.add_argument("--check", action="store_true",
                        help="只校验现有 JSON 是否与重新生成的结果逐字节一致，不写文件")
    args = parser.parse_args()

    specs = [build_doc(spec) for spec in PAGES]

    # 幂等断言：独立再生成一遍（模拟脚本第二次运行），输出必须逐字节一致
    specs_again = [build_doc(spec) for spec in PAGES]
    for (_doc1, stats1), (_doc2, stats2) in zip(specs, specs_again):
        if stats1["payload"].encode("utf-8") != stats2["payload"].encode("utf-8"):
            fail("%s 两次独立生成（模拟重跑）的输出字节不一致" % stats1["html"])
    print("OK 两次独立生成（模拟脚本重跑）输出字节一致：%s"
          % ", ".join(stats["html"] for _doc, stats in specs))

    for doc, stats in specs:
        report(stats)

    if args.check:
        for _doc, stats in specs:
            out = stats["out"]
            if not out.is_file():
                fail("缺少输出文件 %s（先不带 --check 跑一次）" % out)
            existing = out.read_bytes()
            expected = stats["payload"].encode("utf-8")
            if existing != expected:
                fail("%s 与重新生成的结果不一致（%d vs %d 字节）"
                     % (out, len(existing), len(expected)))
            print("[%s] OK --check 与现有文件逐字节一致：%s"
                  % (stats["html"], out.relative_to(ROOT).as_posix()))
        print("ALL CHECKS PASSED")
        return 0

    for _doc, stats in specs:
        out = stats["out"]
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = stats["payload"].encode("utf-8")
        existed = out.is_file()
        if existed and out.read_bytes() == payload:
            print("[%s] 已是最新，字节未变（幂等）：%s"
                  % (stats["html"], out.relative_to(ROOT).as_posix()))
            continue
        out.write_bytes(payload)
        print("[%s] %s %s（%d bytes）"
              % (stats["html"], "更新" if existed else "写出",
                 out.relative_to(ROOT).as_posix(), len(payload)))
    print("DONE: ml-marks.json / llm-marks.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
