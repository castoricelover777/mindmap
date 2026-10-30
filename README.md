# 前后端数据沟通全链路 · 思维导图知识库

**在线查看：<https://castoricelover777.github.io/mindmap/>**

> 详细使用/维护/两台电脑协作说明见 **《[交接文档.md](交接文档.md)》**（v4.0）。
> 本文只作快速索引。

## 三个页面

| 页面 | 文件 | 内容 |
|---|---|---|
| **知识图谱**（主交付物） | `graph.html` | 网状全景 + 场景长链 + MySQL 栏目 + 源码树/代码抽屉；概念 104 / 场景 5 / 环节 124 / 细节 727 / 关系边 233 / MySQL 84 点 |
| **全链路图** | `index.html` | 以「用户注册」串联一次请求全过程；353 节点 / 深度 4 / 11 条二级分支 |
| **数据分析** | `llm.html` | Python 第 1~20 节（概述 + NumPy）；129 节点 / 5 阶段 |
| 旧链接桩 | `chain.html` | 自动跳转到 `index.html?mode=chain` |

两个 `graph.html` / `index.html` 由脚本从 `source.md` 与 `graph/data/*.json` 生成，
**直接手改会被下次构建覆盖**；`llm.html` 是手写页，可直接编辑。

## 标记快照（仓库内）

| 文件 | 条数 | 说明 |
|---|---|---|
| `marks.json` | **505** | 细节/环节标记：注册 228 + 部门 171 + 员工 106；不会 54 / 仅了解 174 / 理解 277 |
| `mysql-marks.json` | **54** | MySQL 栏目：仅了解 36 / 不会 18 |

页面首次打开或本地缺失时会**自动补齐**这些快照（只补空缺、不覆盖已有值、只做一次）。
标记本身存在浏览器 localStorage，换设备要用页面上的「导出标记 / 导入标记」。

## 怎么用（知识图谱）

| 操作 | 效果 |
|---|---|
| **单击**场景卡 | 左侧弹出源码树，右侧网图保留 |
| **双击**场景卡 | 进入该场景长链图 |
| 点层 / 点类 | 展开；点类打开左侧代码抽屉 |
| 拖抽屉右边缘 | 改宽度（记忆） |
| 抽屉右上「无注释 / 简略 / 详细」 | 注释强度三档（记忆） |
| 长链图里点细节卡圆点 / A S D | 标记 不会 / 仅了解 / 理解 |
| 拖拽 / 滚轮 | 平移 / 缩放（交互不会重置视角） |

## 内容规模

- 场景：用户注册全链路、部门管理 CRUD、员工管理 CRUD、班级与学员管理、参考与附录
- 源码索引：48 个文件（`tlias` 后端 + `webcase` 案例）
- MySQL：5 章 13 组 84 知识点 101 段代码

## 自己改

内容源在 `graph/data/` 与 `source.md`，生成脚本在 `graph/tools/`：

```bash
python graph/tools/build_graph.py    # 合并源数据 → graph/data/graph.json
python graph/tools/build_page.py     # → graph.html
python graph/tools/build_index.py    # → index.html
```

**只改样式或交互**时只需跑 `build_page.py`。

## 许可

[MIT](LICENSE)
