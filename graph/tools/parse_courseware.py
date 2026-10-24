# -*- coding: utf-8 -*-
"""把课件 docx 抽取文本解析成层级 JSON（章 / 节 / 小节 / 正文 + 表格）。

黑马课件不用 Heading 样式，靠「1.1.1」编号表达层级，所以按编号深度切分。
"""
import io, json, os, re

SRC_DIR = r"E:\mindmap\graph\_src"
OUT = r"E:\mindmap\graph\data\courseware.json"

FILES = [
    ("02", "前端Web开发",        r"F:\JavaBlog\tools\_docx_02_前端Web开发.txt"),
    ("03", "Web后端基础(Maven)", os.path.join(SRC_DIR, "03-Web后端基础(Maven).txt")),
    ("04", "Web后端基础(基础)",  os.path.join(SRC_DIR, "04-Web后端基础.txt")),
    ("05", "数据库",             os.path.join(SRC_DIR, "05-数据库.txt")),
    ("06", "Java操作数据库",     os.path.join(SRC_DIR, "06-java操作数据库.txt")),
    ("07", "部门管理",           os.path.join(SRC_DIR, "07-部门管理.txt")),
    ("08", "员工管理A",          os.path.join(SRC_DIR, "08-员工管理.txt")),
    ("09", "员工管理B",          os.path.join(SRC_DIR, "09-员工管理.txt")),
]

RE_H = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")
RE_TABLE = re.compile(r"^--- \[(\d+)x(\d+)\] ---$")


def read_lines(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read().splitlines()


def parse(path):
    nodes = []
    cur = {"no": "", "depth": 0, "title": "前言", "body": [], "tables": []}
    nodes.append(cur)
    tbl = None
    for raw in read_lines(path):
        line = raw.rstrip()
        m = RE_TABLE.match(line)
        if m:
            tbl = {"rows": int(m.group(1)), "cols": int(m.group(2)), "cells": []}
            cur["tables"].append(tbl)
            continue
        if tbl is not None:
            if line.strip() == "":
                if tbl["cells"]:
                    tbl = None
                continue
            tbl["cells"].append(line.strip())
            continue
        if not line.strip():
            continue
        m = RE_H.match(line)
        if m and len(m.group(2)) <= 60 and not line.startswith("[["):
            no = m.group(1)
            cur = {"no": no, "depth": no.count(".") + 1,
                   "title": m.group(2).strip(), "body": [], "tables": []}
            nodes.append(cur)
            continue
        cur["body"].append(line.strip())
    return [n for n in nodes if n["title"] or n["body"] or n["tables"]]


def main():
    out = []
    for code, name, path in FILES:
        if not os.path.exists(path):
            print("MISS", path)
            continue
        nodes = parse(path)
        depths = {}
        for n in nodes:
            depths[n["depth"]] = depths.get(n["depth"], 0) + 1
        out.append({"code": code, "name": name,
                    "source": os.path.basename(path), "nodes": nodes})
        print("%-4s %-16s nodes=%-4d depth=%s" % (code, name, len(nodes), dict(sorted(depths.items()))))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with io.open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("\n写出", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
