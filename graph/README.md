# graph —— 知识图谱（网状 / 链状）

`graph.html`（仓库根目录）是产物，**不要手改**。改内容改 `tools\`，再重跑构建。

## 现在的规模

| 项 | 数量 |
|---|---|
| 知识点（概念） | 104，分 7 层（其中 32 个是「未学」，网图用虚线框标出） |
| 场景（业务逻辑） | 5：用户注册全链路 / 部门管理 CRUD / 员工管理 CRUD / 班级与学员管理 / 参考与附录 |
| 环节（步骤） | 124 |
| 细节 | 727 |
| 关系边 | 233（场景→知识点 186 + 概念间 47） |
| 母题 | 4 |
| 跨场景复用概念 | 54 |

五个场景的细节量：注册 228、部门 171、员工 175、班级 100、附录 53（合 727）。
页面顶部「未标记」= 概念 104 + 细节卡 731（727 条细节 + 4 个无细节环节）+ MySQL 84 = **919**，鼠标悬停可看明细。

## 目录

| 路径 | 作用 |
|---|---|
| `data/concepts.json` | 72 个知识点（层 / 一句话 / 学习日期 / 集数） |
| `data/scenario-register.json` | 注册场景 6 阶段 / 44 环节 / 228 细节 |
| `data/scenario-dept.json` | 部门场景 6 阶段 / 19 环节 / 171 细节 |
| `data/scenario-emp.json` | 员工场景 9 阶段 / 25 环节 / 175 细节（课件 08/09/10） |
| `data/scenario-clazz.json` | 班级与学员场景 4 阶段 / 20 环节 / 100 细节（课件 11 + 接口文档） |
| `data/map-register.json` | 注册「环节 → 知识点」映射 |
| `data/map-ref.json` | 附录「条目 → 知识点」映射 |
| `data/edges.json` | 47 条概念间关系（依赖 / 对照 / 替代） |
| `data/themes.json` | 4 条母题 |
| `data/courseware.json` | 7 章课件解析结果（361 节点） |
| `data/notes-index.json` | 54 篇笔记的日期 / 集数范围 |
| `data/graph.json` | 渲染器唯一输入 |
| `_src/*.txt` | 课件 docx 抽取的纯文本 |
| `data/source.json` | 源码索引：48 个文件 / 2 个工程 / 5 个场景的三层映射 |
| `_shots/*.png` | 效果图 |

## 只有三个文件需要人工维护

- `tools/author_content.py` —— **知识点库 / 母题 / 关系边 / 注册场景映射**
- `tools/content_dept.py` —— **部门场景（19 环节 / 171 细节）**
- `tools/content_emp.py` —— **员工管理场景（25 环节 / 175 细节）+ 29 个新增知识点**（课件 08/09/10）
- `tools/content_clazz.py` —— **班级与学员管理场景（20 环节 / 100 细节）+ 3 个新增知识点**（课件 11 + 接口文档）
- `tools/source_view.py` —— **源码视图**（左三层树 + 右高亮代码 + 目录面包屑）
- `tools/build_source_index.py` —— **源码索引生成器**（扫描 Maven 工程 → data/source.json）
- `tools/build_page.py` —— **渲染器**（网状布局、聚焦成链、侧栏）
- `tools/mobile_fix.py` —— 移动端顶栏 CSS，由 `build_page.py` 注入（生成物里的样式会被重建冲掉）

> 注意：所有脚本的路径都基于 `__file__` 推导仓库根目录，换机器/换盘符不用改代码。
> 新增内容步骤一律**追加在末尾**，避免 `st.emp.N` 编号位移导致已保存的学习标记错位。

另外 `tools/build_index.py` 是 **`index.html`（导图+链）的生成器**：读 `_src/_orig/index.html` 与
`_src/_orig/chain.html`（合并前的原始版），输出 `..\index.html`。实测重建结果与现文件
**SHA-256 完全一致**，可放心改。

## 重新生成

```bash
# 在仓库根目录执行；改动内容层时只需后三条
python graph/tools/parse_courseware.py      # 课件 docx -> courseware.json（课件变了才跑）
python graph/tools/parse_notes_register.py  # 笔记索引 + 注册场景（笔记变了才跑）
python graph/tools/author_content.py        # 内容层 + 校验（概念 id 拼错直接报错）
python graph/tools/build_graph.py           # 合并 -> graph.json（打印复用统计）
python graph/tools/build_page.py            # 内联 -> graph.html
```

实测：不改内容时 `build_page.py` 重建的 `graph.html` 与仓库版本**逐字节一致**（仅 `meta.built` 时间戳变化）。

## 数据约定

- **概念 id**：`c.<层>.<名字>`，跨场景共享，一个概念只存一份。
- **步骤 id**：`st.<场景>.<序号>`，如 `st.dept.3`；附录用 `st.ref.<原阶段序号>.<条目序号>`。
- **细节 id**：`<步骤 id>.<序号>`，标记就记在这个 id 上。
- **`path` 字段**：只保留在注册与附录步骤上（`r-阶段-环节`），**旧标记迁移靠它，别删**。
- **共享概念**（被 ≥2 个场景引用）在网图上带 `×N` 角标，当前 31 个。
- **时间轴预留**：概念有 `learned`（首次学习日期）与 `ep`（对应集数），网图层内顺序即按 `learned` 排。

## 旧标记迁移（已验证）

`graph.html` 启动时读旧的 `mm-marks-v1`（`r-阶段-环节-细节`），按步骤上的 `path` 映射为语义 id，写入 `mm-graph-marks-v1`。

实测：真实 `marks.json` 的 **228 条 → 迁移 228 条**，分布 50/97/81 原样保留，页面统计同步显示 `不会50 仅了解97 理解81 未标记228`。非法键（如 `r-99-9-9`）被忽略。


## 交互：两次点击（v4.8）

网图左侧四张场景卡是**胶囊样式**（白底 + 彩色圆点 + 深色标题），和顶栏的四个 chip 同一套语言。

| 次数 | 发生什么 | 画面 |
|---|---|---|
| 第 1 次 | 卡片**填充成场景色 + 白字**；相关知识点保持满亮度并浮起，概念之间的关系线加亮；无关的压到 4% 且**不可点击**（`pointer-events:none`），位置一个像素不动 | 仍是网图 |
| 第 2 次 | 整体镜头位移 + 溶解（680ms），连贯地飞成**长链图**（阶段卡 + 环节行） | 长链图 |
| 点环节 | 展开该环节的细节卡 | 长链图 |
| 点知识点 | 右侧信息框打开，**再点同一个 → 关闭** | 任意 |

v4.8 起删除了「知识点链条」这一套视图（`renderRibbon` / `layoutRibbon` / 浮层细节卡 / 视图切换按钮），
现在只有两种画面：**网图** 和 **长链图（ChainView）**。

实现要点：

- 连贯变形 = `crossMorph(paint)`：克隆 `#scene` 成幽灵层 → `paint()` 画新画面 → 幽灵层做 `translate+scale` 补间并淡出 → 结束移除
- 场景卡选中态靠 `rect[data-sel]` + 直接改 `fill`/`stroke`/文字颜色，**不要重建 DOM**（重建会丢位置）
- 淡化的知识点同时设 `pointer-events:none`，点不中也不抢鼠标；换选别的场景时会被重新打开
- 信息框开关靠 `panelCid`：同 id 且显示中 → 直接关闭
- 验证可点性要用 `document.elementFromPoint()`，**不能用 `dispatchEvent`**（后者绕过命中测试，指针事件不起作用）
- 删视图时注意残留引用（`btn-classic` / `closeDetailPop` / `#dx`），漏一个就是启动即 `Uncaught`

## MySQL 知识栏目（v5.0）

顶栏第二个 tab「MySQL」，独立于知识图谱，用卡片墙展示。

- 数据：`data/mysql.json`，由 `tools/gen_mysql.py` 从 `_src/05-数据库.txt`（44K）与
  `_src/06-java操作数据库.txt`（36K）解析而来，**不是手写**，重建时数据跟着课件走
- 规模：8 组 / 54 个知识点 / 24 段代码
- 分组：MySQL概述·连接 / MySQL概述·数据模型 / SQL语句·DDL / DML / DQL / JDBC·查询数据 / JDBC·增删改 / Mybatis·介绍
- 代码块来自课件原文（docx 把换行压成 ` / `，`gen_mysql.py` 里 `split_code()` 负责还原）
- 顺序：先跑 `gen_mysql.py` 生成 json，再跑 `build_page.py`
- 层级：MySQL 层 `z-index:40` 盖住画布；打开时收起图例/母题/提示/返回按钮，任何切场景或切 tab 的动作都会先 `setMysqlView(false)`，两层不会互相吞

**覆盖边界**：课件 05/06 只到「MySQL 概述 + DDL/DML/DQL + JDBC/MyBatis」。
索引原理、MVCC、锁、主从、分库分表在这些课件里**没有**（词频为 0），所以栏目里也没有 —— 需要补的话得先补课件。

## 标记数据（v6.5，重要）

标记全部存在**浏览器 localStorage**，按页面各一套，互不相通：

| 页面 | localStorage 键 | 说明 |
|---|---|---|
| `index.html` 全链路图 | `mm-marks-v1` | 路径键 `r-阶段-环节-细节` |
| `graph.html` 知识图谱 | `mm-graph-marks-v1` | 语义键 `st.场景.环节[.细节]`，**本页主库** |
| `graph.html` MySQL 栏目 | `mm-mysql-marks-v1` | 独立一套 |
| `llm.html` 数据分析 | `mm-marks-llm-v1` | 独立一套 |
| `blog.html` 博客源码 | `mm-marks-blog-v1` | 独立一套 |

同源（`castoricelover777.github.io`）下多个页面共用 localStorage，但**键不同**，
所以一个页面的标记不会出现在另一个页面——这是「看起来丢了」最常见的原因。

### 三条保护（v6.5 修的问题）

1. **旧键迁移只做一次，且只补空缺**
   旧版每次打开页面都会把 `mm-marks-v1` 的 228 条**重新写回**语义 id，
   结果是「你后来改过的注册/附录标记被旧快照悄悄覆盖」。现在：
   - 迁移完成写 `mm-graph-migrated-v1 = 1`，之后不再跑
   - 目标的 id 已有标记就跳过，绝不覆盖

2. **内置快照自动播种**
   `marks.json`（505 条：不会 54 / 仅了解 174 / 理解 277）在构建时内联进 `graph.html`。
   只有当「本地一条标记都没有」且没播种过（`mm-graph-seeded-v1`）时，才自动载入，
   提示条会显示「已载入内置标记 505 条」。
   换浏览器 / 清缓存后标记能自动回来；你手动清空过则不再强灌。

3. **顶栏「导出标记 / 导入标记」**
   - 导出：`graph-marks-YYYY-MM-DD.json`
   - 导入：支持三种文件——本页导出、`marks.json`、`?dump=1` 的四套汇总
   - 导入时问一次模式：**覆盖合并**（文件优先）/ **只补空缺**（现有不动）
   - 覆盖前自动把当前状态备份到 `mm-graph-marks-backup-v1`

### id 形态因场景而异（导入过滤要小心）

```
st.register.<阶段>.<环节>.<细节>   注册场景（多一层）
st.ref.<阶段>.<条目>.<细节>       附录
st.emp.<环节>.<细节>              部门 / 员工 / 班级：场景后直接是环节序号
```

所以导入只校验 `st.` 前缀 + 取值 1~3，是否属于当前图谱由「当前 id 集合」判断。

### 三个标记库的快照与自动补齐

| 库 | 键 | 快照文件 | 数量 | 补齐标志 |
|---|---|---|---|---|
| 细节/环节 | `mm-graph-marks-v1` | `marks.json` | 505（注册228+部门171+员工106） | `mm-graph-seeded-v2` |
| MySQL 栏目 | `mm-mysql-marks-v1` | `mysql-marks.json` | 54（理解36/仅了解18） | `mm-mysql-seeded-v2` |
| 概念 | 同上 `mm-graph-marks-v1` | 无 | 0 | — |

三者都是「只补本地缺失、绝不覆盖已有值，且只做一次」。
**概念级标记从未产生过快照**（历史里 `marks.json` 两版都只有 step 级），所以概念那行永远是 0。

### 排查标记问题

- 想知道本地到底存了什么：打开 `graph.html?dump=1`，会下载四套标记的汇总 JSON
- 换电脑/换浏览器：先在旧环境「导出标记」，再到新环境「导入标记」
- U 盘快照：仓库根目录 `marks.json`、`mysql-marks.json`

### 数据分析页（llm.html）的标记入口

`llm.html` 是**手工维护**的文件（没有生成器）。它的顶栏原本把
「导出标记 / 导入标记 / 清空标记」平铺在最右边，窗口不够宽时会被
`body{overflow:hidden}` 直接裁掉——表现为「看不到导入」。

已改成「**标记 ▾**」下拉（`tools/patch_llm_toolbar.py`，幂等可重跑），
并加了 ≤1280px / ≤1080px 两档紧凑样式，窄屏也能一行放下。
下拉里的按钮保留原 id，原有事件不受影响。

## 源码视图（v6.4）

**单击场景卡** → 源码树从卡片**左侧**长出来，**右侧知识点网图不隐藏**（源码树是叠加层）。
单击**不会**进长链视图；**双击场景卡**才排成长链。

```
[ 代码抽屉 ]  [ 文件框 ]  [ 三层架构框 ]  [ 场景卡 ]  [ 知识点网图 → ]
UserController   Controller 层    用户注册全链路
UserService      Service 层（2）
UserServiceImpl  Mapper 层（2）
                 Pojo 实体（1）
```

交互约定（v6.3 / v6.4 修过的坑）：
- **代码抽屉在左侧**（`min(560px, 44vw)`），点抽屉以外的地方自动收起
- **单击 = 只看源码树**（延时 220ms 判定，双击会取消这次单击）；**双击 = 长链视图**
- **点层框/点文件框/开关抽屉都不改画布视角**；打开源码树时保持当前缩放只做平移，
  关闭时**还原打开前的视角**
- **拖拽不会误触发点击**：拖拽超过 5px 后松手，浏览器补发的 click / dblclick 会被吞掉
- **不再有「点空白处收起源码树」**；收起源码树用底部 `✕ 收起源码树` 或 Esc
  （Esc 先关代码抽屉，再按一次才收树）
- 层框：Controller / Service / Mapper / Pojo / 异常 / 配置 / 工具，圆钮显示文件数，默认展开前两层
- 代码抽屉内容：行号 + 语法高亮 + Maven 目录面包屑 + package + 行数 + 方法 + 复制/翻页

**数据来源**（源码不在本仓库，构建时扫描并内联，产物仍是自包含单文件）：

| 工程 | 路径 | 用于 |
|---|---|---|
| `tlias-web-management` | `D:\web-ai-project02\tlias-web-management` | 部门 / 员工 / 班级学员（统计部分） |
| `springboot-web-case` | `F:\myusb\web-ai-code\web-project01\springboot-web-case` | 用户注册（早期三层示例，Dao 而非 Mapper） |

场景 → 文件的映射写在 `tools/build_source_index.py` 的 `scene(...)` 调用里。

**覆盖实情**：
- 注册链路用的是早期示例工程（Controller → Service → Dao），UserController2/3 等课件变体未列入
- 第 11 节是「照接口文档自己完成」的作业，`ClazzController` / `StudentController` 等**源码不存在**，
  班级场景只列已实现的统计部分（Report*）与公共类

**重新生成源码索引**（源码变了才需要跑）：

```bash
python graph/tools/build_source_index.py   # 扫描两个工程 -> data/source.json
python graph/tools/build_page.py           # 内联进 graph.html
```

U 盘未插时 tlias 工程会被跳过，沿用上一篇 `source.json`，不会报错。

## 现状

- 已做：4 场景 / 92 概念 / 35 个复用点 / 4 条母题 / 标记迁移 / 网状↔链状切换 / 知识点侧栏 / 每场景独立的箭头标签 / 未学概念区分 / **母题独立视图**
- 未做：时间轴拖动；登录与权限（接口文档 6.x 有，讲义未展开）

## 母题视图（v4.2）

左下角有 4 个母题 chip，点一下进入「母题视角」：

- 非成员节点淡化，该母题的连线**加粗成实线**，成员节点上标 ①②③…
- 同时弹出一张卡片，按顺序列出成员（含所在层、是否未学）
- 和「场景聚焦」互斥：点场景会自动退出母题视角
- 支持深链：graph.html?t=t.std-impl
- 母题 chip 行末尾的「↩ 经典导图」回到 index.html；index.html 左下角也有「🗺 知识图谱 →」反向入口（两边都不新增 tab）

	ools/author_content.py 里的 THEMES 就是母题定义：members 的**数组顺序即卡片与连线上的序号**，调整顺序就调整叙事。
- 未做：时间轴拖动、母题独立视图、移动端适配、班级与学员管理场景（讲义未提供）