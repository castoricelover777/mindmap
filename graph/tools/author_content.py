# -*- coding: utf-8 -*-
"""内容层：知识点库 / 部门管理场景 / 母题 / 步骤→知识点映射。

只有这个文件需要人工维护；改完重跑 build_graph.py 即可。
"""
import io, json, os
import os
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OUT = os.path.join(ROOT, "graph", "data")
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- 层
LAYERS = [
    {"id": "frontend",    "label": "前端",     "color": "#2563EB"},
    {"id": "protocol",    "label": "网络协议", "color": "#0E7490"},
    {"id": "server",      "label": "容器部署", "color": "#7C3AED"},
    {"id": "framework",   "label": "框架架构", "color": "#047857"},
    {"id": "persistence", "label": "持久层",   "color": "#C2410C"},
    {"id": "database",    "label": "数据库",   "color": "#BE123C"},
    {"id": "tooling",     "label": "工程工具", "color": "#B45309"},
]

# ---------------------------------------------------------------- 知识点
# (id, 中文标签, 英文/注解, 层, 一句话, 学习日期, 集数)
C = [
 # ---- 前端 ----
 ("c.html-form","HTML 表单","form / input","frontend","form 把一组输入框聚合成一次提交，input 采集单个字段","2026-10-11","第1~10集"),
 ("c.vue.model","v-model 双向绑定","v-model","frontend","data 与输入框互相同步，是 :value + @input 的语法糖","2026-10-13","第19~26集"),
 ("c.vue.event","@click 事件绑定","v-on:click","frontend","把 DOM 点击事件绑到 methods 里的方法上","2026-10-13","第19~26集"),
 ("c.js.object","JS 对象字面量","{}","frontend","花括号直接构成对象，是前端这一层的通用货币","2026-10-12","第18集"),
 ("c.js.async","async/await 异步等待","async / await","frontend","await 只挂起当前函数，页面不冻结","2026-10-14","第27~32集"),
 ("c.axios.post","axios.post","axios","frontend","自动 JSON.stringify + 自动设 Content-Type","2026-10-14","第27~32集"),
 ("c.json","JSON 格式","JSON","frontend","前后端唯一都认的数据格式，键必须双引号","2026-10-12","第18集"),
 ("c.validate.client","前端校验","","frontend","提升体验但挡不住绕过，后端必须再校验","2026-10-14","第30集"),
 ("c.dom.render","数据驱动渲染","v-for / v-html","frontend","数据一变视图自动更新，不用手动操作 DOM","2026-10-13","第26集"),
 ("c.frontend.xss","innerHTML 与 XSS","","frontend","把用户输入当 HTML 解析执行，本质是「把数据当代码」","2026-10-12","第18集"),
 # ---- 网络协议 ----
 ("c.tcp","TCP 连接","三次握手","protocol","HTTP 建立在 TCP 之上，先建连再发报文","2026-10-16","第39~47集"),
 ("c.http.request","HTTP 请求报文","请求行/头/空行/体","protocol","四部分：请求行 + 请求头 + 空行 + 请求体","2026-10-16","第40集"),
 ("c.http.response","HTTP 响应报文","状态行/头/体","protocol","三部分：状态行 + 响应头 + 响应体","2026-10-16","第41集"),
 ("c.http.method","HTTP 请求方法","GET / POST / PUT / DELETE","protocol","GET 查、POST 增、PUT 改、DELETE 删","2026-10-16","第41集"),
 ("c.http.status","HTTP 状态码","200 / 404 / 405 / 415 / 500","protocol","4xx 是你的请求有问题，5xx 是服务器有问题","2026-10-16","第41集"),
 ("c.http.content-type","Content-Type","application/json","protocol","决定后端用哪个 HttpMessageConverter 解析请求体","2026-10-16","第40集"),
 ("c.url","URL 结构","协议://主机:端口/路径?查询#锚点","protocol","路径交给路由查表，查询串交给参数绑定","2026-10-16","第42集"),
 ("c.cors","跨域与预检","CORS / OPTIONS","protocol","同源策略是浏览器限制，服务端要靠响应头放行","2026-10-16","第46集"),
 ("c.restful","RESTful 风格","REST","protocol","URL 定位资源，HTTP 动词描述操作；复数表资源","2026-10-20","第75集"),
 # ---- 容器部署 ----
 ("c.tomcat","内嵌 Tomcat","","server","SpringBoot 把容器打成依赖，一个 jar 就能跑","2026-10-16","第44集"),
 ("c.servlet.request","HttpServletRequest","","server","Tomcat 把字节流解析成 Request/Response 对象","2026-10-16","第44集"),
 ("c.nginx.proxy","Nginx 反向代理","proxy_pass","server","浏览器 → Nginx(:90) → Tomcat，多一层转发/安全/负载均衡","2026-10-21","第79集"),
 # ---- 框架架构 ----
 ("c.springboot.app","SpringBoot 启动类","@SpringBootApplication","framework","三个注解的合体：配置类 + 自动配置 + 组件扫描","2026-10-16","第44集"),
 ("c.springboot.scan","组件扫描范围","@ComponentScan","framework","启动类必须放在所有业务类的父包下，否则扫不到","2026-10-16","第44集"),
 ("c.spring.ioc","IoC 控制反转","","framework","对象创建权从程序员手里交给容器","2026-10-17","第48集"),
 ("c.spring.di","DI 依赖注入","","framework","要什么让容器给，注入的是接口而不是实现类","2026-10-17","第49集"),
 ("c.annotation.autowired","@Autowired","","framework","按类型注入；同类型多个要用 @Qualifier / @Primary","2026-10-17","第49集"),
 ("c.annotation.component","@Service / @Repository","@Component","framework","标记为组件交给容器管理，默认单例","2026-10-17","第50集"),
 ("c.springmvc.dispatcher","DispatcherServlet","","framework","前端控制器：问 HandlerMapping 这个路径该谁处理","2026-10-16","第45集"),
 ("c.springmvc.mapping","@RequestMapping 路由","@GetMapping …","framework","路径 + 方法 → 处理函数；衍生注解把方法定死","2026-10-16","第45集"),
 ("c.springmvc.mapping-class","类级路径抽取","@RequestMapping(\"/depts\")","framework","完整路径 = 类上 + 方法上；消除重复前缀","2026-10-22","第83集"),
 ("c.annotation.method-mapping","请求方式映射","@GetMapping/@PostMapping/@PutMapping/@DeleteMapping","framework","@RequestMapping 按 method 定死的衍生注解","2026-10-21","第77集"),
 ("c.annotation.restcontroller","@RestController","= @Controller + @ResponseBody","framework","返回值直接写进响应体，不当视图名解析","2026-10-16","第45集"),
 ("c.annotation.requestbody","@RequestBody","","framework","读整个请求体，交给 Jackson 反序列化成对象","2026-10-16","第45集"),
 ("c.annotation.requestparam","@RequestParam","","framework","取 query 参数或表单字段；名字对上可省略","2026-10-22","第80集"),
 ("c.annotation.pathvariable","@PathVariable","","framework","取路径占位 /depts/{id} 里的参数","2026-10-22","第82集"),
 ("c.param.simple","简单参数接收三方案","request.getParameter / @RequestParam / 同名形参","framework","本质是「参数在 HTTP 的哪个位置」","2026-10-22","第80集"),
 ("c.arch.three-layer","三层架构","Controller / Service / Mapper","framework","每层只做自己的事，靠约定串起来","2026-10-16","第47集"),
 ("c.arch.controller","Controller 职责","","framework","接参、调 Service、包返回；不写 SQL、不写事务","2026-10-16","第47集"),
 ("c.arch.service","Service 职责","","framework","业务规则、校验、事务边界、补全公共字段","2026-10-16","第47集"),
 ("c.arch.mapper","Mapper 职责","","framework","只管 SQL，不关心业务","2026-10-16","第47集"),
 ("c.result.wrapper","Result 统一响应","{code,msg,data}","framework","前端只写一套解析逻辑；契约落在代码结构上","2026-10-21","第78集"),
 ("c.jackson","Jackson 序列化","","framework","Java 对象 ⇄ JSON，@RestController 自动调用","2026-10-16","第45集"),
 ("c.exception.handler","全局异常处理","@RestControllerAdvice","framework","别把 500 和堆栈直接甩给前端","2026-10-22","第84集"),
 ("c.biz.validation","业务校验","","framework","后端才是安全边界，前端校验可被绕过","2026-10-21","第81集"),
 ("c.biz.transaction","事务 @Transactional","","framework","多表操作要么全成功要么全回滚","2026-10-21","第64集"),
 ("c.arch.separation","前后端分离","","framework","拆成两个工程，靠接口文档对齐","2026-10-20","第74集"),
 ("c.spec.api-doc","接口文档","","framework","前后端的合同：地址、参数、响应类型","2026-10-20","第74集"),
 ("c.java.interface","接口与实现类","","framework","面向接口编程，换实现不改调用方","2026-10-05","Java day4"),
 # ---- 持久层 ----
 ("c.mybatis.mapper","@Mapper 接口","","persistence","只有签名没有实现，启动时由 MyBatis 生成","2026-10-18","第60集"),
 ("c.mybatis.proxy","动态代理","JDK Proxy","persistence","接口名/方法名/namespace/id 必须严丝合缝对上","2026-10-18","第60集"),
 ("c.mybatis.mapping","注解 vs XML 写 SQL","@Select / <select>","persistence","简单用注解，动态 SQL 用 XML","2026-10-19","第70集"),
 ("c.mybatis.hash","#{} 预编译占位符","？","persistence","编译成 ? 走 PreparedStatement，值永远是值","2026-10-19","第70集"),
 ("c.mybatis.dollar","${} 字符串拼接","","persistence","直接拼进 SQL，有注入风险；只能用于表名/字段名","2026-10-19","第70集"),
 ("c.mybatis.resultmap","结果映射","resultType / RowMapper","persistence","数据库的行变成 Java 对象，靠列名匹配属性名","2026-10-18","第62集"),
 ("c.mybatis.camel-case","驼峰映射开关","map-underscore-to-camel-case","persistence","create_time → createTime；不开就静悄悄留 null","2026-10-21","第78集"),
 ("c.mybatis.generated-keys","主键回填","@Options(useGeneratedKeys,keyProperty)","persistence","插入后自增 id 回填到对象上","2026-10-18","第63集"),
 ("c.jdbc","JDBC","","persistence","一套访问数据库的标准接口，六步模板代码","2026-10-18","第56集"),
 ("c.jdbc.driver","JDBC 驱动","mysql-connector-j","persistence","标准接口的具体实现，换数据库只换驱动","2026-10-18","第56集"),
 ("c.pool.hikari","HikariCP 连接池","","persistence","借还代替建销，把连接成本摊到启动时","2026-10-19","第68集"),
 # ---- 数据库 ----
 ("c.sql","SQL 语言","","database","标准；MySQL/Oracle 是各自的实现","2026-10-17","第48集"),
 ("c.sql.dml","DML 增删改","insert/update/delete","database","影响的是数据行，返回受影响行数","2026-10-18","第57集"),
 ("c.sql.ddl","建库建表","create table","database","dept 表：id/name/create_time/update_time","2026-10-21","第76集"),
 ("c.mysql","MySQL","","database","只懂 SQL，不关心是谁在问","2026-10-17","第52集"),
 # ---- 工程工具 ----
 ("c.tool.maven","Maven","pom.xml","tooling","依赖管理与标准构建，版本要锁死","2026-10-14","第31~32集"),
 ("c.tool.apifox","Apifox","","tooling","接口文档 + 调试 + Mock；浏览器只能发 GET 所以要它","2026-10-20","第75集"),
 ("c.config.yml","application.yml","","tooling","缩进即层级，不能 Tab；把变化挪出代码","2026-10-20","第73集"),
 ("c.log.slf4j","Slf4j 日志门面","","tooling","一套标准接口，底下可以换任意日志实现","2026-10-22","第84集"),
 ("c.log.logback","Logback","logback.xml","tooling","Slf4j 的实现，按配置输出到控制台/文件","2026-10-22","第84集"),
 ("c.log.println","System.out.println","","tooling","硬编码、只到控制台、不分级 —— 日志要替代它","2026-10-22","第84集"),
 ("c.log.level","日志级别","ALL/DEBUG/INFO/WARN/ERROR","tooling","优先级由低到高，配置文件里控制输出到哪一级","2026-10-22","第85集"),
 ("c.arch.package","包结构约定","controller/service/mapper/pojo","tooling","约定优于配置，扫包靠它","2026-10-21","第76集"),
]

# ---------------------------------------------------------------- 注册场景 步骤→知识点
REGISTER_MAP = {
 "1.1": ["c.html-form"],
 "1.2": ["c.vue.model"],
 "1.3": ["c.validate.client"],
 "1.4": ["c.vue.event"],
 "1.5": ["c.js.object"],
 "1.6": ["c.axios.post", "c.http.content-type", "c.json"], "1.7": ["c.js.async"],
 "1.8": ["c.json"],
 "2.1": ["c.tcp"],
 "2.2": ["c.http.request", "c.http.content-type"],
 "2.3": ["c.http.method"],
 "2.4": ["c.url"],
 "2.5": ["c.cors"],
 "3.1": ["c.springboot.app", "c.springboot.scan"],
 "3.2": ["c.tomcat"],
 "3.3": ["c.servlet.request"],
 "3.4": ["c.springmvc.dispatcher", "c.springmvc.mapping"],
 "3.5": ["c.springmvc.mapping", "c.springmvc.mapping-class"],
 "3.6": ["c.annotation.restcontroller", "c.jackson"],
 "3.7": ["c.annotation.method-mapping", "c.springmvc.mapping"],
 "3.8": ["c.annotation.requestbody", "c.jackson", "c.http.content-type"],
 "3.9": ["c.arch.controller", "c.arch.three-layer"],
 "4.1": ["c.spring.ioc"],
 "4.2": ["c.annotation.component"],
 "4.3": ["c.spring.di", "c.annotation.autowired"],
 "4.4": ["c.arch.service", "c.arch.three-layer"],
 "4.5": ["c.biz.validation", "c.biz.transaction"],
 "4.6": ["c.arch.mapper"],
 "5.1": ["c.mybatis.mapper"],
 "5.2": ["c.mybatis.proxy", "c.java.interface"],
 "5.3": ["c.mybatis.mapping"],
 "5.4": ["c.mybatis.hash", "c.mybatis.dollar"],
 "5.5": ["c.pool.hikari"],
 "5.6": ["c.sql.dml", "c.sql", "c.biz.transaction"],
 "5.7": ["c.mybatis.resultmap", "c.mybatis.camel-case"],
 "6.1": ["c.arch.service"],
 "6.2": ["c.result.wrapper"],
 "6.3": ["c.jackson", "c.annotation.restcontroller"],
 "6.4": ["c.http.response", "c.http.content-type"],
 "6.5": ["c.http.status"],
 "6.6": ["c.exception.handler"],
 "6.7": ["c.tomcat"],
 "6.8": ["c.js.async", "c.axios.post"],
 "6.9": ["c.dom.render", "c.http.status"],
}

# ---------------------------------------------------------------- 部门管理场景
# 部门管理场景搬到 content_dept.py 里单独维护（18 个环节，与课件 07 原文对齐）
from content_dept import DEPT, REF_MAP
from content_emp import EMP, EXTRA_CONCEPTS
from content_clazz import CLAZZ, EXTRA_CONCEPTS_CLAZZ

C = C + EXTRA_CONCEPTS + EXTRA_CONCEPTS_CLAZZ   # 员工(09/10)与班级(11)带来的新知识点


# ---------------------------------------------------------------- 概念之间的关系边
# type: depends 依赖 / contrast 对照 / replaces 替代
EDGES = [
 ("c.vue.model",      "c.js.object",        "depends"),
 ("c.axios.post",     "c.json",             "depends"),
 ("c.js.async",       "c.axios.post",       "depends"),
 ("c.json",           "c.http.request",     "depends"),
 ("c.http.request",   "c.tcp",              "depends"),
 ("c.http.response",  "c.http.status",      "depends"),
 ("c.http.request",   "c.http.content-type","depends"),
 ("c.annotation.requestbody", "c.http.content-type", "depends"),
 ("c.annotation.requestbody", "c.jackson",  "depends"),
 ("c.annotation.requestbody", "c.json",     "depends"),
 ("c.tomcat",         "c.servlet.request",  "depends"),
 ("c.nginx.proxy",    "c.tomcat",           "depends"),
 ("c.springmvc.dispatcher", "c.springmvc.mapping", "depends"),
 ("c.springmvc.mapping",    "c.annotation.method-mapping", "depends"),
 ("c.annotation.restcontroller", "c.jackson", "depends"),
 ("c.spring.di",      "c.spring.ioc",       "depends"),
 ("c.annotation.autowired", "c.spring.di",  "depends"),
 ("c.annotation.component", "c.spring.ioc", "depends"),
 ("c.arch.controller","c.arch.three-layer", "depends"),
 ("c.arch.service",   "c.arch.mapper",      "depends"),
 ("c.arch.service",   "c.biz.validation",   "depends"),
 ("c.arch.service",   "c.biz.transaction",  "depends"),
 ("c.result.wrapper", "c.jackson",          "depends"),
 ("c.exception.handler", "c.result.wrapper","depends"),
 ("c.mybatis.mapper", "c.mybatis.proxy",    "depends"),
 ("c.mybatis.mapper", "c.mybatis.mapping",  "depends"),
 ("c.mybatis.mapping","c.mybatis.hash",     "depends"),
 ("c.mybatis.hash",   "c.mybatis.dollar",   "contrast"),
 ("c.mybatis.resultmap","c.mybatis.camel-case","depends"),
 ("c.pool.hikari",    "c.jdbc",             "depends"),
 ("c.jdbc",           "c.sql",              "depends"),
 ("c.jdbc",           "c.jdbc.driver",      "depends"),
 ("c.sql.dml",        "c.sql",              "depends"),
 ("c.sql.ddl",        "c.mysql",            "depends"),
 ("c.log.logback",    "c.log.slf4j",        "depends"),
 ("c.log.level",      "c.log.logback",      "depends"),
 ("c.log.logback",    "c.log.println",      "replaces"),
 ("c.restful",        "c.spec.api-doc",     "depends"),
 ("c.restful",        "c.http.method",      "depends"),
 ("c.tool.apifox",    "c.spec.api-doc",     "depends"),
 ("c.springboot.app", "c.springboot.scan",  "depends"),
 ("c.springboot.app", "c.tomcat",           "depends"),
 ("c.springmvc.mapping-class", "c.springmvc.mapping", "depends"),
 ("c.param.simple",   "c.annotation.requestparam", "depends"),
 ("c.annotation.pathvariable", "c.url",     "depends"),
 ("c.config.yml",     "c.springboot.app",   "depends"),
 ("c.frontend.xss",   "c.mybatis.dollar",   "contrast"),
]

# ---------------------------------------------------------------- 母题（横贯边）
THEMES = [
 {"id": "t.std-impl", "label": "标准 vs 实现", "color": "#111827",
  "note": "上层只依赖标准接口，底层可换实现；你笔记里记了四次。",
  "members": ["c.sql", "c.mysql", "c.jdbc", "c.jdbc.driver", "c.java.interface", "c.log.slf4j", "c.log.logback"]},
 {"id": "t.data-as-code", "label": "把数据当代码执行", "color": "#DC2626",
  "note": "XSS 与 SQL 注入是同一个病；解法都是让数据和代码分开。",
  "members": ["c.frontend.xss", "c.mybatis.dollar", "c.mybatis.hash"]},
 {"id": "t.convention", "label": "约定优于手写", "color": "#047857",
  "note": "能推导出来的，就不该让人再写一遍。",
  "members": ["c.mybatis.camel-case", "c.mybatis.hash", "c.result.wrapper", "c.spec.api-doc", "c.arch.package", "c.springmvc.mapping-class"]},
 {"id": "t.config-out", "label": "把变化挪出代码", "color": "#B45309",
  "note": "yml、logback.xml、开关，都是同一件事。",
  "members": ["c.config.yml", "c.log.logback", "c.log.level", "c.mybatis.camel-case"]},
]


def main():
    concepts = [{"id": i, "label": lbl, "aka": aka, "layer": lay,
                 "gloss": g, "learned": d, "ep": ep}
                for (i, lbl, aka, lay, g, d, ep) in C]
    ids = [c["id"] for c in concepts]
    assert len(ids) == len(set(ids)), "概念 id 重复"
    known = set(ids)

    # 校验映射里没有拼错的概念 id
    bad = []
    for k, v in REGISTER_MAP.items():
        for cid in v:
            if cid not in known:
                bad.append(("register", k, cid))
    for st in DEPT["steps"]:
        for cid in st["concepts"]:
            if cid not in known:
                bad.append(("dept", st["label"][:12], cid))
    for st in EMP["steps"]:
        for cid in st["concepts"]:
            if cid not in known:
                bad.append(("emp", st["label"][:12], cid))
    for st in CLAZZ["steps"]:
        for cid in st["concepts"]:
            if cid not in known:
                bad.append(("clazz", st["label"][:12], cid))
    for t in THEMES:
        for cid in t["members"]:
            if cid not in known:
                bad.append(("theme", t["id"], cid))
    for v in REF_MAP.values():
        for cid in v:
            if cid not in known:
                bad.append(("refmap", "-", cid))
    for (a, b, typ) in EDGES:
        for cid in (a, b):
            if cid not in known:
                bad.append(("edge", a + "->" + b, cid))
    if bad:
        print("!! 未定义的概念 id：")
        for b in bad:
            print("   ", b)
        raise SystemExit(1)

    json.dump({"layers": LAYERS, "concepts": concepts},
              io.open(os.path.join(OUT, "concepts.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(DEPT, io.open(os.path.join(OUT, "scenario-dept.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(EMP, io.open(os.path.join(OUT, "scenario-emp.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(CLAZZ, io.open(os.path.join(OUT, "scenario-clazz.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(THEMES, io.open(os.path.join(OUT, "themes.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(REGISTER_MAP, io.open(os.path.join(OUT, "map-register.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump(REF_MAP, io.open(os.path.join(OUT, "map-ref.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    json.dump([{"s": a, "t": b, "type": typ} for (a, b, typ) in EDGES],
              io.open(os.path.join(OUT, "edges.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print("概念 %d 个，层 %d 个，关系边 %d 条" % (len(concepts), len(LAYERS), len(EDGES)))
    print("部门场景 %d 步 / %d 条细节" % (len(DEPT["steps"]), sum(len(s["details"]) for s in DEPT["steps"])))
    print("班级场景 %d 步 / %d 条细节" % (len(CLAZZ["steps"]), sum(len(s["details"]) for s in CLAZZ["steps"])))
    print("母题 %d 条" % len(THEMES))
    from collections import Counter
    print("层分布:", dict(Counter(c["layer"] for c in concepts)))
    used = set()
    for v in REGISTER_MAP.values():
        used |= set(v)
    for st in DEPT["steps"]:
        used |= set(st["concepts"])
    print("被场景引用的概念 %d / %d" % (len(used), len(concepts)))
    print("只被单场景用到的:", sorted(known - used)[:10])


if __name__ == "__main__":
    main()
