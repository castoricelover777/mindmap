# -*- coding: utf-8 -*-
"""班级与学员管理场景（课件 11「自己完成」+ 接口文档）与随之新增的知识点。

课件 11 是综合练习：给定接口文档与建表 SQL，自己实现班级管理、学员管理、统计与功能完善。
所以这个场景的重点不在「新语法」，而在「把前面学过的套路在两张新表上复用一遍」，
以及两个新东西：班级状态按时间推导、业务规则失败要抛自定义异常。

接口全部来自《接口文档.docx》（班级管理 3.x / 学员管理 4.x / 数据统计 5.3 5.4 / 员工 2.6）。

知识点同样都是**还没学**的（笔记只到第 84 集），learned / ep 一律 None。
新步骤追加在场景末尾，st.clazz.N 从 0 开始，不与已有场景编号冲突。
"""

EXTRA_CONCEPTS_CLAZZ = [
  # (id, 中文标签, 英文/注解, 层, 一句话, learned, ep)
  ("c.clazz.status", "班级状态推导", "未开班 / 在读中 / 已结课", "framework",
   "状态不存库，按当前时间与开课、结课日期现算，避免定时任务刷新", None, None),
  ("c.exception.custom", "自定义业务异常", "BusinessException", "framework",
   "业务规则不满足时抛自定义异常，由全局处理器转成可读提示而不是 500", None, None),
  ("c.sql.increment", "字段自增更新", "set x = x + 1", "persistence",
   "计数、扣分这类累加交给数据库算，避免「先查后改」的并发覆盖", None, None),
]

CLAZZ = {
 "id": "s.clazz", "label": "班级与学员管理", "sub": "照接口文档自己写：班级 + 学员 + 统计",
 "color": "#0D9488", "source": "课件 11-后端Web实战(自己完成) + 接口文档",
 "phases": [
   {"label": "数据准备", "color": "#BE123C"},
   {"label": "班级管理", "color": "#2563EB"},
   {"label": "学员管理", "color": "#047857"},
   {"label": "统计与守卫", "color": "#7C3AED"},
 ],
 "flow": ["三张表串起来", "班级增删改查", "学员增删改查", "统计与业务守卫"],
 "returnNote": "这一节没有新框架，考的是把前几节的模板套到新表上还不出错",
 "steps": [
  # ---------------------------------------------------------------- 数据准备
  {"label": "1.1 建表：clazz 与 student", "phase": 0,
   "concepts": ["c.sql.ddl", "c.db.unique"],
   "details": [
     "接口文档是唯一契约：路径、方法、参数名、响应结构全按文档来，否则联调必出问题（课件把这句话重复了三遍）。",
     "clazz 表：name 唯一、begin_date / end_date 必填、master_id 关联员工表、subject 是学科枚举（1 java … 6 嵌入式）。",
     "student 表：no 学号、phone、id_card 三个字段都是唯一约束，任一重复都会插入失败。",
     "student.clazz_id 非空：学员必须挂在某个班级下，没有「无班级」的学员。",
     "violation_count / violation_score 默认 0，前端新增学员时不必传。",
     "create_time / update_time 由业务代码或 SQL 填充，不在接口参数里。",
   ]},
  {"label": "1.2 三张表串起来：部门→员工→班级→学员", "phase": 0,
   "concepts": ["c.db.relation", "c.db.fk", "c.db.fk-physical"],
   "details": [
     "clazz.master_id → emp.id：一个班级有一个班主任，而班主任就是这个企业的员工。",
     "student.clazz_id → clazz.id：一个班级下多个学员，典型一对多。",
     "emp.dept_id → dept.id：部门与员工的关系，前面部门场景已经建过。",
     "四张表串起来就是 tlias 的数据骨架，后面所有接口都在这个骨架上操作。",
     "仍然用逻辑外键：数据库不建约束，一致性由业务代码保证。",
     "所以「删班级前要检查有没有学员」不是数据库拦你，是你得自己写——这就是 2.7 的由来。",
   ]},

  # ---------------------------------------------------------------- 班级管理
  {"label": "2.1 班级条件分页查询", "phase": 1,
   "concepts": ["c.query.param-object", "c.mybatis.dynamic-sql", "c.page.limit"],
   "details": [
     "GET /clazzs?name=java&begin=2023-01-01&end=2023-06-30&page=1&pageSize=5",
     "三个条件：班级名称模糊匹配、开课时间范围（begin / end 闭区间）。",
     "沿用员工列表那一套：散参收进 ClazzQueryParam 对象，前端参数名与属性名对齐即可自动绑定。",
     "动态 SQL 用 where + if：只传了姓名就只拼姓名的条件。",
     "分页仍是 LIMIT 开始索引, 条数，并且要返回 total 供前端算总页数。",
     "顺序建议按课件：先跑通查询，再做后面的增删改——列表能出来，后面才有参照。",
   ]},
  {"label": "2.2 班级状态是算出来的", "phase": 1,
   "concepts": ["c.clazz.status"],
   "details": [
     "页面要显示「未开班 / 在读中 / 已结课」，但数据库里根本没有状态字段。",
     "规则：当前时间 > 结课时间 → 已结课；当前时间 < 开课时间 → 未开班；其余 → 在读中。",
     "为什么不在库里存状态：状态每天都会变，存库就得靠定时任务刷新，一停机就全是错的。",
     "做法：查出来后用 LocalDate.now() 与 begin_date / end_date 比较，算完赋给实体的 status 属性。",
     "这类「派生字段」在项目里很常见：能不存就不存，用到时再算，永远是最新值。",
     "注意边界：同一天开课算在读中，同一天结课也算在读中，判断用「大于 / 小于」而不是「大于等于」。",
   ]},
  {"label": "2.3 查询全部员工：班主任下拉", "phase": 1,
   "concepts": ["c.spec.api-doc", "c.arch.controller"],
   "details": [
     "GET /emps/list，不分页，一次返回所有员工。",
     "为什么单独开一个接口：下拉框要的是全量列表，用分页接口拿不全。",
     "班主任就是员工，数据源是 emp 表，不需要为它新建表。",
     "复用员工场景的查询，只是去掉分页与筛选条件。",
     "命名约定：/emps 是分页，/emps/list 是全量，/emps/{id} 是单条——看到 list 后缀就该想到全量。",
   ]},
  {"label": "2.4 新增班级", "phase": 1,
   "concepts": ["c.annotation.requestbody", "c.mybatis.mapping"],
   "details": [
     "POST /clazzs，请求体是班级 JSON。",
     "用 @RequestBody 接收，JSON 键名与实体属性名一一对应才能自动绑定。",
     "name 有唯一约束：重名会抛 Duplicate entry，正好被全局异常处理器兜住并转成提示。",
     "subject、begin_date、end_date 都是必填，插入前先做非空校验。",
     "插入成功后返回 Result.success()，前端刷新列表即可。",
   ]},
  {"label": "2.5 根据 ID 查询：回显", "phase": 1,
   "concepts": ["c.annotation.pathvariable", "c.arch.service"],
   "details": [
     "GET /clazzs/{id}，id 从路径取，用 @PathVariable 绑定。",
     "路径参数与查询参数的分工：前者标识资源（/clazzs/1），后者做筛选（?name=java）。",
     "回显只需要单表数据，一条 select 就够，不涉及 resultMap。",
     "Controller → Service → Mapper 三层链路与查询列表完全一致，只是参数变少。",
   ]},
  {"label": "2.6 修改班级", "phase": 1,
   "concepts": ["c.sql.dynamic-update", "c.annotation.method-mapping"],
   "details": [
     "PUT /clazzs，请求体里带 id。",
     "RESTful 的方法约定：GET 查询、POST 新增、PUT 修改、DELETE 删除。",
     "用动态 update：只更新前端实际传了值的字段，避免把没填的字段清空。",
     "where 条件必须是 id，漏了就是全表更新——这是最危险的失误。",
     "改完再查一次详情，确认字段真的落到库里了，而不是只看接口返回成功。",
   ]},
  {"label": "2.7 删除班级：有学员时禁止", "phase": 1,
   "concepts": ["c.biz.validation", "c.exception.custom", "c.annotation.exception-handler"],
   "details": [
     "DELETE /clazzs/{id}，接口本身很简单，难在业务规则。",
     "规则：班级下还有学员时不允许删除，提示「对不起, 该班级下有学生, 不能直接删除」。",
     "第一步：先按 clazz_id 统计学员数，大于 0 就抛自定义异常。",
     "自定义异常继承 RuntimeException，把提示文案带在异常对象里。",
     "第二步：全局异常处理器里加 @ExceptionHandler(对应的自定义异常)，把它转成 Result.error(msg) 返回。",
     "为什么不用返回 Result.error 了事：Service 层只负责表达「业务不允许」，统一格式交给处理器，职责才干净。",
   ]},

  # ---------------------------------------------------------------- 学员管理
  {"label": "3.1 查询所有班级：下拉", "phase": 2,
   "concepts": ["c.spec.api-doc"],
   "details": [
     "GET /clazzs/list，新增学员时下拉展示全部班级。",
     "命名与员工一致：/clazzs 分页、/clazzs/list 全量、/clazzs/{id} 单条。",
     "全量接口通常只返回下拉需要的两个字段（id、name），不必返回整行。",
   ]},
  {"label": "3.2 学员条件分页查询", "phase": 2,
   "concepts": ["c.query.param-object", "c.mybatis.dynamic-sql", "c.sql.join"],
   "details": [
     "GET /students，条件通常是：姓名、学历、班级（clazzId）、性别。",
     "最常用的是按 clazzId 过滤：点某个班级，只看这个班的学员。",
     "列表要显示班级名称，所以要 left join clazz 并起别名 clazzName，Emp 式的字段名对齐规则照样适用。",
     "参数对象 + 动态 SQL + LIMIT 这一套，在员工、班级、学员三个列表里已经复用了三遍。",
     "复习点：什么时候必须 left join——学员的班级一定存在，但主表侧要保证不丢行时依然优先左连接。",
   ]},
  {"label": "3.3 新增学员", "phase": 2,
   "concepts": ["c.annotation.requestbody", "c.db.unique"],
   "details": [
     "POST /students，请求体是学员 JSON。",
     "三个唯一约束：学号 no、手机号 phone、身份证 id_card，任一个重复都会插入失败。",
     "clazz_id 必填，学员必须挂在某个班级下。",
     "violation_count / violation_score 用数据库默认值补 0，前端不传。",
     "失败时由全局异常处理器把 Duplicate entry 转成「手机号已存在」这类可读提示。",
   ]},
  {"label": "3.4 根据 ID 查询学员", "phase": 2,
   "concepts": ["c.annotation.pathvariable"],
   "details": [
     "GET /students/{id}，修改前的表单回显用。",
     "回显要带出班级名称，页面上才显示得出「JavaEE就业163期」而不是一个 clazzId。",
     "单个学员就是单条记录，不需要一对多 resultMap。",
   ]},
  {"label": "3.5 修改学员", "phase": 2,
   "concepts": ["c.sql.dynamic-update"],
   "details": [
     "PUT /students，请求体带 id。",
     "同样用动态 update，避免把没传的字段写成 null。",
     "改学号 / 手机号 / 身份证同样会撞唯一约束，异常走同一个全局处理器。",
     "注意别让前端把 violation 相关字段一起提交——那两个字段只能通过违纪处理接口改。",
   ]},
  {"label": "3.6 删除学员：批量删除", "phase": 2,
   "concepts": ["c.mvc.array-param", "c.mybatis.foreach"],
   "details": [
     "DELETE /students/{ids}，路径里带逗号分隔的多个 id。",
     "@PathVariable 直接接收 List<Integer> ids，Spring 会按逗号自动切分成集合。",
     "用 foreach 拼 IN 条件，一条 delete 删完，不循环发 N 条 SQL。",
     "删学员只动 student 一张表，不涉及事务。",
     "对比记忆：删员工要动两张表（加事务）、删班级要先查学员（抛异常）、删学员最轻——每个删除的代价都不一样。",
   ]},
  {"label": "3.7 违纪处理：字段自增更新", "phase": 2,
   "concepts": ["c.sql.increment", "c.annotation.pathvariable"],
   "details": [
     "PUT /students/violation/{id}/{score}，两个路径参数：学员 id 和本次扣分。",
     "规则：违纪次数 +1，违纪扣分 + 前端输入的分数。",
     "错误写法：先 select 出当前次数和分数，在 Java 里加完再 update 写回。并发下两个请求会互相覆盖。",
     "正确写法：把加法交给数据库——set violation_count = violation_count + 1, violation_score = violation_score + #。",
     "这种「自增更新」在扣库存、加积分、点赞数这些场景里是同一个套路。",
     "注意 score 从路径进来是字符串，绑定到 Integer 形参时 Spring 会自动转换。",
   ]},

  # ---------------------------------------------------------------- 统计与守卫
  {"label": "4.1 班级人数统计", "phase": 3,
   "concepts": ["c.sql.aggregate", "c.report.echarts"],
   "details": [
     "GET /report/studentCountData。",
     "SQL 思路：select c.name, count(s.id) from clazz c left join student s on s.clazz_id = c.id group by c.id, c.name。",
     "必须用 left join：没有学员的班级也要出现在图上，人数显示 0。",
     "如果用 inner join，空班级会被直接吞掉——这是统计查询里最常见的坑。",
     "返回两段：clazzList（类目）+ dataList（数值），正好是柱状图的形状。",
   ]},
  {"label": "4.2 学员学历统计", "phase": 3,
   "concepts": ["c.sql.aggregate", "c.report.echarts"],
   "details": [
     "GET /report/studentDegreeData。",
     "SQL：select degree, count(*) from student group by degree。",
     "库里 degree 是 1~6 的数字（初中/高中/大专/本科/硕士/博士），返回前端前要映射成文案。",
     "返回 name/value 对象数组，直接喂给 ECharts 饼图。",
     "数字到文案的映射放在服务层，别让前端猜——这是接口设计的基本礼貌。",
   ]},
  {"label": "4.3 删除部门前的守卫（功能完善）", "phase": 3,
   "concepts": ["c.biz.validation", "c.exception.custom"],
   "details": [
     "需求补完：部门下还有员工时，不允许删除该部门，提示「对不起，当前部门下有员工，不能直接删除！」",
     "做法与删班级完全一样：先 count 员工数 → 大于 0 抛自定义异常 → 全局处理器转成提示。",
     "同一个套路在部门、班级两个地方复用，说明它是通用模式而不是特例。",
     "回头看：如果没有全局异常处理器，这里就只能返回 Result.error 或写 try-catch，代码会散在 Controller 里。",
   ]},
  {"label": "4.4 复盘：这七个接口其实是同一个模板", "phase": 3,
   "concepts": ["c.arch.three-layer", "c.spec.api-doc"],
   "details": [
     "统一流程：读接口文档 → 建表与实体 → Mapper 写 SQL → Service 管事务与业务规则 → Controller 收参转发 → Apifox 测 → 前端联调。",
     "分页查询：参数对象 + 动态 SQL + LIMIT，三张表一模一样。",
     "删除：先判断关联数据，再决定是抛异常还是执行删除。",
     "统计：group by 出数据，服务端只负责把它整理成前端要的形状。",
     "真正的收获不是记住了七个接口，而是能对着接口文档独立把一个模块写完——这正是课件 11 想练的能力。",
     "下一步：拿到一个新模块，先看文档有几个接口、每个接口的入参出参，再动手写代码。",
   ]},
 ],
}
