# -*- coding: utf-8 -*-
"""
content_fastapi.py —— 生成 graph/data/scenario-fastapi.json

来源：2026-11-02 ~ 11-06 四篇 FastAPI 博客复盘
（day1 第1~15集 入门 / day2 第16~20集 依赖注入与 ORM / day3 第29~36集 工程化与跨域 /
  day4 第42~46集 注册链路与统一响应）
每条细节尽量标注「对照 JavaWeb：…」，方便和已学框架对照。
"""
import io, json, os, sys

sys.stdout.reconfigure(encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "graph", "data", "scenario-fastapi.json")

PHASES = [
    ("入门与第一个程序", "#0EA5E9"),
    ("路由与三种参数",   "#2563EB"),
    ("响应与统一格式",   "#7C3AED"),
    ("异常与中间件",     "#B45309"),
    ("依赖注入与 ORM",   "#047857"),
    ("工程化与跨域",     "#DB2777"),
    ("注册链路与上线",   "#BE123C"),
]

# (label, phase, [细节…])
STEPS = [
    # ---------------- 阶段一 ----------------
    ("1.1 FastAPI 是什么：Starlette + Pydantic 拼出来的框架", 0, [
        "定位：现代、高性能的 Python Web 框架，底层由两块拼成——Starlette 负责 ASGI/路由/中间件，Pydantic 负责数据校验与序列化。",
        "三个卖点：性能高（原生 async）、开发快（少写样板代码）、接口文档白送（/docs 自动生成）。",
        "对照 JavaWeb：SpringBoot = Spring MVC + Jackson + Validation + springdoc 的组合体，FastAPI 相当于「一个依赖把这些全带上」。",
        "关键认知：类型注解在 FastAPI 里不是注释，是配置——写 int 就等于声明「必须能转成整数，否则 422」。",
        "对照 JavaWeb：这相当于把 @RequestParam Integer id 的类型信息 + 校验注解 + 文档注解三件事合进一个类型标注。",
    ]),
    ("1.2 和 Flask / Django 的差别：为什么又学一个框架", 0, [
        "Flask：同步、极简，没有内置校验和文档，跨域/ORM 全靠插件自己拼。",
        "Django：全家桶（Admin/ORM/模板/迁移），但要写 API 还得上 Django REST Framework。",
        "FastAPI：介于两者之间——像 Flask 一样轻，但有 SpringBoot 式的约定（校验、文档、依赖注入）。",
        "对照 JavaWeb：Flask ≈ 裸 Servlet + 手写 if 校验；Django ≈ 完整脚手架（RuoYi 那类）；FastAPI ≈ SpringBoot 的定位。",
        "选型感受：已经会 SpringBoot 的人迁移最快，因为概念一一对应，缺的只是语法。",
    ]),
    ("1.3 虚拟环境与依赖隔离", 0, [
        "python -m venv .venv 建虚拟环境，激活后 pip install fastapi \"uvicorn[standard]\"。",
        "导出一份 requirements.txt 锁版本，团队/换机时 pip install -r requirements.txt 即可。",
        "对照 JavaWeb：venv 提供的是「项目级依赖隔离」，对应 Maven 的 per-project 仓库 + classpath 隔离。",
        "对照 JavaWeb：requirements.txt ≈ pom.xml 的 <dependencies>；只锁版本没有传递依赖树，比 Maven 粗糙。",
        "坑：不激活 venv 直接跑，装到全局环境，换机器立刻 ImportError。",
    ]),
    ("1.4 最小程序：两行代码跑起来一个接口", 0, [
        "app = FastAPI() 创建应用实例；@app.get(\"/\") 装饰器把函数注册成路由。",
        "async def root(): return {\"message\": \"Hello World\"}——返回 dict 会自动被序列化成 JSON。",
        "对照 JavaWeb：FastAPI() ≈ @SpringBootApplication 启动类；@app.get ≈ @GetMapping；return dict ≈ @ResponseBody + Jackson。",
        "对照 JavaWeb：Spring 要写启动类 + Controller 类 + 方法三个结构体，FastAPI 三件事塞进一个文件。",
        "注意：函数顺序无关，路由按装饰器注册顺序进表，冲突时先注册的生效。",
    ]),
    ("1.5 启动：uvicorn main:app --reload", 0, [
        "uvicorn 是 ASGI 服务器；main:app = 模块名:应用实例（去 main.py 找名叫 app 的对象）。",
        "--reload 是热重载，改代码保存即生效，只能开发用；生产千万别加（内存泄漏 + 重复加载）。",
        "默认端口 8000；文档在 http://127.0.0.1:8000/docs。",
        "对照 JavaWeb：uvicorn ≈ 内嵌 Tomcat；--reload ≈ spring-boot-devtools；main:app 的冒号 ≈ 「启动类全限定名」的定位作用。",
        "生产写法：gunicorn -k uvicorn.workers.UvicornWorker -w 4 main:app，多进程扛并发。",
    ]),
    ("1.6 /docs：白送的接口文档", 0, [
        "访问 /docs 得到 Swagger UI，可展开、可填参数、可直接发请求；/redoc 是另一种排版；/openapi.json 是原始契约。",
        "文档内容由路由签名 + Pydantic 模型自动推导，不需要额外写注解。",
        "对照 JavaWeb：相当于 knife4j / springdoc-openapi，但那边要加依赖、写 @Operation/@Schema/@ApiModelProperty。",
        "对照 JavaWeb：FastAPI 的类型注解就是 Spring 里「参数类型 + @ApiModel + 校验注解」三者的合体。",
        "这也意味着：改动函数签名等于改动 API 契约，前后端联调时文档永远是最新的。",
    ]),

    # ---------------- 阶段二 ----------------
    ("2.1 路由装饰器与方法对应", 1, [
        "@app.get / @app.post / @app.put / @app.delete / @app.patch，一个函数对应一个 HTTP 方法。",
        "路径里的 {name} 是占位符，函数同名参数接收。",
        "对照 JavaWeb：@GetMapping(\"/users\") 一一对应；Spring 也可以用 @RequestMapping(method=RequestMethod.POST) 合并写法，FastAPI 不合并。",
        "对照 JavaWeb：FastAPI 的路由表在启动时构建，行为类似 Spring 的 HandlerMapping。",
        "同一路径不同方法可以共存，装饰器不同即可。",
    ]),
    ("2.2 路径参数与自动类型转换", 1, [
        "@app.get(\"/items/{item_id}\") def read(item_id: int)——标注 int 后会自动把字符串转成整数。",
        "转换失败不会抛 500，而是返回 422 + 明确说明（loc 指到具体参数）。",
        "对照 JavaWeb：@PathVariable Long itemId；Spring 类型转换失败抛 MethodArgumentTypeMismatchException，默认 400。",
        "对照 JavaWeb：Spring 转换成功与否取决于有没有配 ConversionService，FastAPI 直接看注解。",
        "路径参数是必填的，没有默认值这一说。",
    ]),
    ("2.3 Path：给路径参数加约束", 1, [
        "item_id: int = Path(..., ge=1, le=1000, description=\"商品 ID\")，省略号表示必填。",
        "常用约束：gt/ge/lt/le（数值）、min_length/max_length（字符串）、regex（正则）、title/description（文档展示）。",
        "对照 JavaWeb：@Min/@Max/@Positive + 类上 @Validated 才生效；FastAPI 写在参数声明里就地生效。",
        "对照 JavaWeb：description 等价于 @Parameter(description=...)，但不用额外注解。",
        "约束失败同样走 422，错误信息里带 constraint 类型。",
    ]),
    ("2.4 查询参数：不是路径就是 query", 1, [
        "函数参数里没出现在路径占位符中的，一律被当成查询参数：/items?q=abc&page=2。",
        "给了默认值就是可选（q: str = None）；不给默认值就是必填。",
        "对照 JavaWeb：@RequestParam(value=\"q\", required=false) String q；required 的语义靠「有没有默认值」表达。",
        "对照 JavaWeb：Spring 的 @RequestParam 还能绑定 POJO（多参数聚成对象），FastAPI 用 Pydantic 模型 + Depends 也能做到。",
        "布尔参数注意：?flag=false 传的是字符串 \"false\"，FastAPI 会按 bool 规则解析（true/1/yes 等）。",
    ]),
    ("2.5 Query：给查询参数加约束与多值", 1, [
        "q: str | None = Query(default=None, min_length=2, max_length=20)。",
        "多值：tags: list[str] = Query(default=[])——?tags=a&tags=b 自动聚成列表。",
        "对照 JavaWeb：@RequestParam List<String> tags + @Size；Spring 同样用重复 key 传数组。",
        "对照 JavaWeb：@RequestParam(defaultValue=\"1\") 的分页参数，在 FastAPI 里就是 page: int = Query(1, ge=1)。",
        "Query 与 Path 的区别只在「参数从哪来」，约束写法几乎一样。",
    ]),
    ("2.6 请求体：Pydantic 模型接收 JSON", 1, [
        "class Item(BaseModel): name: str; price: float; 然后 def create(item: Item) 直接拿到解析好的对象。",
        "缺字段、类型不对都会自动 422，并指出哪个字段错；不用写一行校验代码。",
        "对照 JavaWeb：@RequestBody ItemDTO + Jackson 反序列化；但 Spring 不加 @Valid 就不会校验，FastAPI 默认就校验。",
        "对照 JavaWeb：Pydantic 模型 ≈ DTO + Lombok + 校验注解 + @JsonIgnore 的合体。",
        "请求体只能是单个模型参数，多个模型要用嵌套模型或用 Body(...) 分别声明。",
    ]),
    ("2.7 Field：给请求体字段加约束", 1, [
        "name: str = Field(..., min_length=1, max_length=50, description=\"商品名\")。",
        "支持嵌套模型（子模型也会被校验）、List[子模型]、枚举、EmailStr 等特殊类型。",
        "对照 JavaWeb：@NotBlank/@Size/@Email + 类上 @Valid，嵌套时子对象字段加 @Valid 级联。",
        "对照 JavaWeb：Field 的 description/example 直接进 OpenAPI 文档，相当于 @Schema。",
        "自定义校验：@field_validator 装饰器，等价于 Spring 的自定义 ConstraintValidator。",
    ]),
    ("2.8 校验失败长什么样：422", 1, [
        "返回体形如 {\"detail\": [{\"loc\": [\"body\",\"price\"], \"msg\": \"Input should be greater than 0\", \"type\": \"greater_than\"}]}。",
        "loc 是定位路径，能精确到「body 里的第 3 个字段」，前端可直接对着标红。",
        "对照 JavaWeb：MethodArgumentNotValidException 默认返回 400，且结构是 Spring 自己的；要统一格式必须写 @RestControllerAdvice。",
        "对照 JavaWeb：FastAPI 的 422 是框架默认行为，想改成自己的 code/msg 结构，同样要自定义异常处理器（见 4.2）。",
        "注意：422 是「语义错误」，400 才是「语法错误」，两者别混。",
    ]),

    # ---------------- 阶段三 ----------------
    ("3.1 默认响应：返回 dict 就是 JSON", 2, [
        "返回 dict / list / Pydantic 模型都可以，框架自动 jsonable_encoder 序列化（datetime、Decimal 都能处理）。",
        "默认状态码 200；POST 想返回 201 就写 @app.post(..., status_code=201)。",
        "对照 JavaWeb：@ResponseBody + Jackson 的 ObjectMapper；FastAPI 不需要注解，返回什么就是什么。",
        "对照 JavaWeb：ResponseEntity.status(HttpStatus.CREATED) 的作用，在 FastAPI 里是装饰器参数 status_code。",
        "不能直接返回 Pydantic 之外的自定义对象，否则会报序列化错误——要转 dict 或用 response_model。",
    ]),
    ("3.2 response_model：输出过滤与脱敏", 2, [
        "@app.get(\"/users/{id}\", response_model=UserOut)——返回值按 UserOut 裁剪，多余字段不输出。",
        "典型用途：数据库实体里有 password，输出模型里不写它，就不会泄露。",
        "对照 JavaWeb：VO/DTO 输出 + @JsonIgnore；或者用 Spring 的 projection / @JsonView。",
        "对照 JavaWeb：response_model 还负责把 ORM 对象转成可序列化结构，相当于 Jackson 的 getter 提取。",
        "注意：response_model 是「过滤 + 校验」，不是「改名」，字段名必须对得上。",
    ]),
    ("3.3 响应类型类：不只是 JSON", 2, [
        "HTMLResponse / PlainTextResponse / FileResponse / StreamingResponse / RedirectResponse，直接 return 对应对象即可。",
        "@app.get(\"/html\", response_class=HTMLResponse) 还能让文档标注正确的内容类型。",
        "对照 JavaWeb：produces=MediaType.TEXT_HTML_VALUE、ResponseEntity<Resource> 下载文件、response.sendRedirect。",
        "对照 JavaWeb：FileResponse ≈ ResponseEntity<InputStreamResource> + Content-Disposition 头。",
        "StreamingResponse 适合大文件/日志流，等价于 Spring 的 StreamingResponseBody。",
    ]),
    ("3.4 自定义 JSONResponse：状态码与响应头", 2, [
        "return JSONResponse(content={...}, status_code=201, headers={\"X-Trace\": \"...\"})。",
        "异常处理器里必须用它（不能 return dict），否则状态码不生效。",
        "对照 JavaWeb：ResponseEntity.status(201).header(\"X-Trace\", ...).body(...)。",
        "对照 JavaWeb：ResponseEntity 的链式写法 ≈ JSONResponse 的三个参数。",
        "注意中文：JSONResponse 默认 ensure_ascii，中文会变 \\uXXXX，需要自己设置 json.dumps 参数或交给 ORJSONResponse。",
    ]),
    ("3.5 统一响应格式：Result{code, msg, data}", 2, [
        "把成功/失败封装成统一函数或泛型模型，前端只认一种结构，少写一半判断。",
        "常见约定：code=0 成功、非 0 失败；msg 给人看；data 给程序用。",
        "对照 JavaWeb：Result<T> 泛型封装类 + 静态 success()/fail()，Tlias 项目里就是这么干的。",
        "对照 JavaWeb：Spring 还能用 ResponseBodyAdvice 自动包装，FastAPI 一般靠自己封装的 helper 函数。",
        "关键：统一响应和全局异常必须成对出现，否则成功走一种结构、失败走另一种，前端还是要分叉。",
    ]),

    # ---------------- 阶段四 ----------------
    ("4.1 HTTPException：主动抛标准错误", 3, [
        "raise HTTPException(status_code=404, detail=\"商品不存在\")，框架自动转成 JSON 响应。",
        "还能带 headers（例如 401 带 WWW-Authenticate）。",
        "对照 JavaWeb：throw new ResponseStatusException(HttpStatus.NOT_FOUND, \"商品不存在\")。",
        "对照 JavaWeb：或自定义异常 + 类上 @ResponseStatus(NOT_FOUND)，效果一样但不够灵活。",
        "抛出点就是「业务判断点」，比 return 错误码清晰；同事一眼看出这是异常分支。",
    ]),
    ("4.2 自定义异常处理器：统一错误结构", 3, [
        "@app.exception_handler(MyError) async def handler(request, exc): return JSONResponse(...)。",
        "把业务异常统一映射成 {code, msg, data}，前端只处理一种错误格式。",
        "对照 JavaWeb：@RestControllerAdvice + @ExceptionHandler(MyError.class)，几乎一模一样。",
        "对照 JavaWeb：Spring 的处理器方法签名 (HttpServletRequest, Exception)，FastAPI 是 (Request, Exception)。",
        "差异：Spring 有 HandlerExceptionResolver 链，FastAPI 是按类型精确匹配 + 兜底 Exception。",
    ]),
    ("4.3 注册顺序就是匹配优先级", 3, [
        "从「具体」到「抽象」注册：先注册具体异常，最后注册 Exception 兜底。",
        "顺序反了会被兜底处理器抢先匹配，具体处理器永远不生效——这是最容易踩的坑。",
        "对照 JavaWeb：Spring 按异常类型的「最精确匹配」自动选，不看注册顺序，所以那边没这个坑。",
        "对照 JavaWeb：但 Spring 的 @ExceptionHandler 也有层级规则（同类优先、父类次之），本质一样是「越具体越优先」。",
        "建议：把兜底处理器单独放一个文件，避免后续追加时插错位置。",
    ]),
    ("4.4 开发模式与生产模式的错误信息", 3, [
        "开发时想看堆栈，生产绝不能把堆栈返回给前端（泄露表名、路径、依赖版本）。",
        "做法：按环境变量区分 detail 内容，生产只返回错误码 + 通用文案，堆栈写日志。",
        "对照 JavaWeb：server.error.include-stacktrace=never / include-message=never；日志用 logback 落盘。",
        "对照 JavaWeb：Spring 的 /error 默认返回 whitelabel 页，生产要自定义 ErrorController 或 @RestControllerAdvice 覆盖。",
        "FastAPI 的默认 500 是纯文本 Internal Server Error，比 Spring 的页面更安全但要自己补统一格式。",
    ]),
    ("4.5 中间件：请求链上加一层", 3, [
        "@app.middleware(\"http\") async def add_process_time(request, call_next): 在 call_next 前后各做点事。",
        "典型用途：耗时统计、请求 ID 注入、限流、统一日志、CORS（虽然 CORS 有现成中间件）。",
        "对照 JavaWeb：Servlet 层的 Filter（doFilter + chain.doFilter）语义几乎一致。",
        "对照 JavaWeb：Spring MVC 层的 HandlerInterceptor（preHandle/postHandle）也类似，但拿不到响应体。",
        "差异：FastAPI 中间件覆盖整个 ASGI 调用（含异常），比 Filter 更靠外。",
    ]),
    ("4.6 洋葱模型：call_next 前后都有代码", 3, [
        "请求先进第一层中间件的 call_next 之前，再进第二层……响应按相反顺序回来，像剥洋葱。",
        "所以计时要用 time.perf_counter() 在 call_next 两侧取差——这和 Filter 的写法完全一致。",
        "对照 JavaWeb：Filter 的 doFilter 前/后 = 洋葱的两层；afterCompletion 在 Spring 拦截器里对应「响应回来之后」。",
        "对照 JavaWeb：多个 Filter 的 order（@Order / FilterRegistrationBean）就是洋葱的层序。",
        "注意：中间件里读请求体要谨慎，body 被消费后下游可能读不到（需缓存）。",
    ]),

    # ---------------- 阶段五 ----------------
    ("5.1 依赖注入：把重复的取参逻辑抽出来", 4, [
        "多个接口都要「取 token 拿当前用户」「取分页参数」「取数据库会话」，写成依赖后一句话复用。",
        "写法：def current_user(token: str = Header(...)) -> User: ...，然后参数写 user: User = Depends(current_user)。",
        "对照 JavaWeb：IoC 容器 + @Autowired —— 把创建/获取对象的责任交给框架，业务只声明「我需要什么」。",
        "对照 JavaWeb：区别是 Spring 注入的是「单例 bean」，FastAPI 注入的是「每次请求算一次的函数结果」。",
        "好处：可测试性（测试时覆盖依赖即可，不用起整个容器）、显式依赖（函数签名就是依赖清单）。",
    ]),
    ("5.2 Depends 的四种形态", 4, [
        "函数依赖：def get_db(): ...，最常用。",
        "类依赖：class CommonParams: def __init__(self, q: str = None, page: int = 1)，实例即是聚合参数。",
        "生成器依赖：def get_db(): db = SessionLocal(); try: yield db; finally: db.close()——yield 前初始化、后清理。",
        "带参数的依赖工厂：def pagination(page: int = 1, size: int = 10) 再 Depends(pagination)。",
        "对照 JavaWeb：生成器依赖 ≈ @Bean + 生命周期回调（@PostConstruct/@PreDestroy）、或 try-with-resources 的封装。",
    ]),
    ("5.3 依赖缓存：同一请求只算一次", 4, [
        "同一个依赖在一次请求内被多个函数引用时，默认只执行一次，结果复用（use_cache=True）。",
        "想每次都重算，写 Depends(get_db, use_cache=False)。",
        "对照 JavaWeb：相当于 bean 作用域——singleton（整个应用一份）vs request（每个请求一份）。",
        "对照 JavaWeb：FastAPI 绝大多数依赖的效果接近 request 作用域，因此天然线程/请求隔离，不会像单例那样共享可变状态。",
        "这也是为什么「当前登录用户」「数据库会话」适合做成依赖：每个请求独立。",
    ]),
    ("5.4 ORM 是什么：模型类 ↔ 表", 4, [
        "ORM 把「表」映射成「类」、「行」映射成「对象」，写 Python 对象就等于写 SQL。",
        "SQLAlchemy 的两层：Core（SQL 表达式）+ ORM（模型/Session）。",
        "对照 JavaWeb：MyBatis 是「SQL 映射」，你写 SQL、框架帮你转对象；JPA/Hibernate 是「对象映射」，框架帮你生成 SQL。",
        "对照 JavaWeb：SQLAlchemy ORM 更接近 JPA/Hibernate；SQLAlchemy Core 更接近 MyBatis 的 XML + 动态 SQL。",
        "优点：换数据库只改连接串；缺点：复杂 SQL 仍然要手写，性能问题不好排查。",
    ]),
    ("5.5 声明式模型：Base + __tablename__ + Column", 4, [
        "Base = declarative_base()；class User(Base): __tablename__ = \"user\"；id = Column(Integer, primary_key=True)。",
        "常用列类型：Integer/String(50)/Text/Boolean/DateTime/Float/Numeric；约束：unique/index/nullable/default。",
        "对照 JavaWeb：@Entity + @Table(name=\"user\") + @Id + @GeneratedValue(strategy=IDENTITY)。",
        "对照 JavaWeb：Column(String(50), nullable=False) ≈ @Column(length=50, nullable=false)。",
        "关系映射：relationship() 对应 @OneToMany/@ManyToOne，外键用 ForeignKey(\"user.id\")。",
    ]),
    ("5.6 建表：create_all 与迁移", 4, [
        "Base.metadata.create_all(bind=engine) 会「不存在才建」，不会改已有表结构。",
        "开发够用，生产要用 Alembic 做迁移（增量脚本、可回滚、多人协作）。",
        "对照 JavaWeb：spring.jpa.hibernate.ddl-auto=update 的自动建表，对应 create_all。",
        "对照 JavaWeb：Alembic ≈ Flyway / Liquibase，都是「版本化 SQL 脚本 + 执行记录表」。",
        "坑：改了字段类型，create_all 不会报错也不会改表，线上就会「字段还是旧的」——必须走迁移。",
    ]),
    ("5.7 会话与事务：get_db 依赖", 4, [
        "engine = create_engine(URL)；SessionLocal = sessionmaker(bind=engine)；每个请求开一个 Session。",
        "def get_db(): db = SessionLocal(); try: yield db; finally: db.close()——请求结束自动关闭。",
        "写操作必须显式 db.commit()，只 db.add() 不 commit 等于没保存。",
        "对照 JavaWeb：engine ≈ DataSource（HikariCP），SessionLocal ≈ SqlSessionFactory，Session ≈ SqlSession。",
        "对照 JavaWeb：Spring 的 @Transactional 是自动提交/回滚，FastAPI 没有内置声明式事务，要手动 commit/rollback 或用中间件封装。",
    ]),
    ("5.8 查询：query / filter / first", 4, [
        "db.query(User).filter(User.id == 1).first() 取单条；.all() 取列表；.count() 计数。",
        "新式写法是 select(User).where(...) + db.scalars(...)，SQLAlchemy 2.0 推荐。",
        "分页：.offset((page-1)*size).limit(size)，配合总数量查询。",
        "对照 JavaWeb：Mapper 的 selectById / selectList 方法；JPA 的 findById / findAll(Pageable)。",
        "对照 JavaWeb：PageHelper 自动拼 limit 的那套，在 SQLAlchemy 里要自己写 offset/limit + count。",
    ]),

    # ---------------- 阶段六 ----------------
    ("6.1 工程结构：从单文件到分层", 5, [
        "典型结构：app/main.py（装配）、app/routers/（路由）、app/models/（ORM）、app/schemas/（Pydantic）、app/utils/、app/config.py。",
        "main.py 只负责「创建 app + 注册路由 + 注册中间件」，业务逻辑全在 routers。",
        "对照 JavaWeb：main.py ≈ 启动类 + 自动配置；routers ≈ Controller；models ≈ entity；schemas ≈ DTO/VO；utils ≈ utils。",
        "对照 JavaWeb：区别是 Spring 靠包扫描自动装配，FastAPI 必须手写 include_router —— 显式但啰嗦。",
        "判断标准：「能跑」和「结构对」是两回事，按职责切分才敢往上加功能。",
    ]),
    ("6.2 APIRouter：把路由拆成模块", 5, [
        "router = APIRouter(prefix=\"/news\", tags=[\"新闻\"])；然后 @router.get(\"/categories\") 就得到 /news/categories。",
        "tags 会影响 /docs 的分组展示，纯文档用，不影响路由。",
        "对照 JavaWeb：@RestController + 类级 @RequestMapping(\"/news\")，语义完全一致。",
        "对照 JavaWeb：Spring 的 Controller 类天生自带前缀，FastAPI 要显式建 router。",
        "依赖也能挂在 router 上：APIRouter(dependencies=[Depends(verify_token)])，等价于类级统一鉴权。",
    ]),
    ("6.3 include_router：装配与前缀坑", 5, [
        "app.include_router(news.router)；也可以 include 时再叠加 prefix。",
        "最容易踩的坑：prefix 写重——router 里写了 /news，include 时又写 prefix=\"/news\"，最后变 /news/news。",
        "对照 JavaWeb：相当于组件扫描 + @RequestMapping 前缀，但 Spring 是「扫到就注册」，不会重复。",
        "对照 JavaWeb：include_router ≈ Spring Boot 的自动配置注册（@Import / AutoConfiguration），只是这里手动。",
        "建议：prefix 只写在一处，要么 router 里、要么 include 里，别两边都写。",
    ]),
    ("6.4 数据库与 ORM 配置集中", 5, [
        "把 engine、SessionLocal、Base、get_db 统一放 app/db 或 database.py，路由只 from 不重复 create_engine。",
        "连接池参数：pool_size、max_overflow、pool_pre_ping=True（断线重连）。",
        "对照 JavaWeb：application.yml 的 spring.datasource.* + HikariCP 参数（maximum-pool-size / connection-timeout）。",
        "对照 JavaWeb：配置集中化 ≈ @ConfigurationProperties 配置类，两边都忌「到处 new 连接」。",
        "连接串别硬编码在代码里，走环境变量或 .env，避免提交泄露密码。",
    ]),
    ("6.5 第一个完整业务接口：新闻分类列表", 5, [
        "链路：schemas 定义输出模型 → routers 里查数据库 → 用 response_model 包装返回。",
        "顺序很重要：先定「输出结构」，再写查询，最后补异常分支（查不到就返回空列表，不是 404）。",
        "对照 JavaWeb：Controller → Service → Mapper 三段式；这里是 Controller + 直接查（小接口可以省 Service）。",
        "对照 JavaWeb：项目变大后仍建议补 services 层，否则路由里会堆 SQL 和业务判断。",
        "统一返回同一个 Result 结构，列表接口是 data=[]，单条接口是 data={}，前端只写一套解析。",
    ]),
    ("6.6 跨域 CORS：浏览器同源策略拦住了", 5, [
        "现象：前端 5173 调后端 8000，浏览器报 CORS 错误，但服务端日志显示请求其实到了。",
        "方案：app.add_middleware(CORSMiddleware, allow_origins=[...], allow_methods=[\"*\"], allow_headers=[\"*\"], allow_credentials=True)。",
        "注意：allow_credentials=True 时 allow_origins 不能写 \"*\"，必须列具体域名。",
        "对照 JavaWeb：@CrossOrigin(origins=...) 单个接口 / WebMvcConfigurer.addCorsMappings 全局 / CorsFilter。",
        "对照 JavaWeb：本质都是「服务端返回 Access-Control-Allow-* 响应头」，浏览器看到才放行。",
    ]),
    ("6.7 CORS 与反向代理：两条路线别混用", 5, [
        "路线一：后端开 CORS，前端直连不同端口/域名（开发期常用）。",
        "路线二：Nginx 反向代理，前后端同源（生产常用），此时不需要 CORS。",
        "混用的后果：既配了 CORS 又走代理，响应头重复，浏览器报「包含多个值」。",
        "对照 JavaWeb：网关/反代让跨域消失，等价于 Spring Cloud Gateway 或 Nginx 统一入口。",
        "判断标准：只要最终「浏览器的地址栏」和「接口地址」同源，就不存在跨域问题。",
    ]),

    # ---------------- 阶段七 ----------------
    ("7.1 注册接口：先通再填", 6, [
        "先定契约：POST /users/register，请求体 RegisterIn(username, password)，返回统一 Result。",
        "先返回固定成功（不落库），把路由、请求体校验、统一响应跑通，再往里填业务。",
        "对照 JavaWeb：@PostMapping(\"/register\") + @RequestBody RegisterDTO + @Valid。",
        "对照 JavaWeb：Tlias 的注册是全链路案例，链路顺序完全一致：校验 → 查重 → 加密 → 入库 → 返回。",
        "好处：接口契约先定死，前端可以并行开发，联调时不会来回改字段。",
    ]),
    ("7.2 创建用户：密码必须加密", 6, [
        "密码只存哈希：passlib 的 CryptContext(schemes=[\"bcrypt\"]) 或 hashlib + 加盐。",
        "两个致命错误：明文入库、把密码哈希返回给前端。",
        "对照 JavaWeb：BCryptPasswordEncoder（Spring Security）的 encode/matches。",
        "对照 JavaWeb：登录校验是「同一明文再哈希一次比对」，不是解密——哈希不可逆。",
        "校验：注册时前端要二次确认密码；后端只校验强度与一致性，不信任前端。",
    ]),
    ("7.3 Token 方案一：UUID + 数据库表", 6, [
        "生成 uuid4 作 token，存表（user_id, token, expire_at, created_at），校验时查表。",
        "优点：可主动失效（删行=踢人）、可记录多端登录、实现简单。",
        "缺点：每次校验多一次数据库/缓存查询；token 表会膨胀需要清理。",
        "对照 JavaWeb：传统 Session 换成「服务端 token 表」，或把 token 放 Redis 设 TTL。",
        "对照 JavaWeb：这套就是「有状态会话」，只是把 JSESSIONID 换成了自定义 header。",
    ]),
    ("7.4 Token 方案二：JWT", 6, [
        "三段式 header.payload.signature，服务端用密钥签名，payload 里放 user_id/exp。",
        "优点：无状态、校验不查库、适合多服务；缺点：签发后无法主动作废（除非加黑名单）。",
        "对照 JavaWeb：JWT + Spring Security 的 JwtAuthenticationFilter，或 OAuth2 Resource Server。",
        "对照 JavaWeb：安全性不在「加密」而在「签名」——payload 是明文可解的，别放敏感信息。",
        "选型判断：要不要「立刻踢人」——要，选 UUID+表；不要，选 JWT。",
    ]),
    ("7.5 统一响应 + 全局异常必须成对", 6, [
        "成功路径走 success() 封装，失败路径走异常处理器，两条路输出同一个结构。",
        "只做一半的典型症状：正常接口返回 {code,msg,data}，报错却返回 FastAPI 默认的 {detail}。",
        "对照 JavaWeb：Result 封装 + @RestControllerAdvice 必须同时存在，Tlias 项目就是这么配的。",
        "对照 JavaWeb：还能用 ResponseBodyAdvice 统一包装成功响应，减少手写 success()。",
        "自检方法：故意触发 422 / 404 / 500，看三种错误是不是同一个结构。",
    ]),
    ("7.6 部署：别把开发配置带上生产", 6, [
        "生产不要 --reload；用 gunicorn/uvicorn 多 worker，或者 Docker 打包镜像。",
        "环境变量注入配置（数据库地址、密钥），镜像里不写死；日志落盘/采集。",
        "对照 JavaWeb：jar + Dockerfile + 多实例 + Nginx 反代，思路完全一样。",
        "对照 JavaWeb：Java 有 JVM 参数调优，Python 侧对应 worker 数量与连接池大小。",
        "健康检查：/api/health 之类的探针接口，配合容器编排做存活检测。",
    ]),
    ("7.7 学习路线：按依赖关系排，不按集数排", 6, [
        "先打通「路由 → 参数 → 响应」三件套，再学依赖注入与 ORM，最后工程化与认证。",
        "跳着学无妨：21~29 集只做了解，等真正用到再回头补。",
        "对照 JavaWeb：Servlet → Spring MVC → MyBatis → 项目实战，同样是「由窄到宽」。",
        "对照 JavaWeb：两边最像的一点——框架在变，「分层 + 统一响应 + 全局异常 + 依赖注入」这套骨架不变。",
        "落地建议：每学一个 FastAPI 特性，先在 Spring 里找对应物，理解速度会翻倍。",
    ]),
]


def build():
    phases = [{"label": l, "color": c} for l, c in PHASES]
    steps = []
    for label, ph, details in STEPS:
        steps.append({
            "label": label,
            "phase": ph,
            "concepts": [],
            "details": details,
        })
    data = {
        "id": "s.fastapi",
        "label": "FastAPI 后端",
        "sub": "Python Web · 对照 JavaWeb",
        "color": "#0EA5E9",
        "source": "博客 2026-11-02 ~ 11-06 四篇 FastAPI 复盘（第1~46集）",
        "phases": phases,
        "flow": ["建好环境跑通第一个接口", "三种参数都能取到", "响应结构统一", "错误与中间件兜住",
                 "用依赖注入和 ORM 落库", "拆模块、解决跨域", "注册链路跑通并上线"],
        "returnNote": "每一条都能在 JavaWeb 里找到对应物：路由↔@GetMapping、参数↔@PathVariable/@RequestParam/@RequestBody、"
                      "校验↔@Valid、统一响应↔Result<T>、全局异常↔@RestControllerAdvice、依赖注入↔@Autowired、"
                      "中间件↔Filter、APIRouter↔@RequestMapping、ORM↔JPA/MyBatis、CORS↔@CrossOrigin",
        "steps": steps,
    }
    # 校验
    assert len(phases) == len(set(p["label"] for p in phases))
    for st in steps:
        assert 0 <= st["phase"] < len(phases), st["label"]
    io.open(OUT, "w", encoding="utf-8", newline="\n").write(
        json.dumps(data, ensure_ascii=False, indent=1))

    n_det = sum(len(s["details"]) for s in steps)
    print(f"  phases={len(phases)}  steps={len(steps)}  details={n_det}  -> {OUT}")
    from collections import Counter
    print("  每阶段环节数:", dict(Counter(s["phase"] for s in steps)))
    print("  对照 JavaWeb 标注条数:", sum(1 for s in steps for d in s["details"] if "对照 JavaWeb" in d))


if __name__ == "__main__":
    build()
