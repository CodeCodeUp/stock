# AGENTS.md — Stock Monitoring & Backtest System

全程使用中文交流。

本文件提供给在本仓库内工作的 agentic coding agents，帮助你快速理解架构、命令、代码风格、改动边界和新增的回测链路。

## 1. 项目概览

- 项目类型：股票增减持监控与回测分析系统，Monorepo，前后端分离，Docker Compose 编排
- 前端：`frontend/`，Vue 3 + TypeScript + Vite + Element Plus + ECharts
- 后端：`backend/`，Spring Boot 3.4.5 + MyBatis XML + MySQL + Java 17
- Python：`python/`，Flask 数据 API + 采集脚本 + APScheduler
- 文档：`docs/`
- 根目录关键文件：`docker-compose.yml`、`.env.example`、`AGENTS.md`

## 2. 外部规则文件

- 已检查 `.cursor/rules/`
- 已检查 `.cursorrules`
- 已检查 `.github/copilot-instructions.md`
- 当前仓库未发现额外的 Cursor / Copilot 规则文件

## 3. 关键数据流

### 3.1 监控主链路

- `daily_stock_change`：增减持事实表，来源于 Python 导入脚本
- `stock_base`：由 `daily_stock_change` 派生的股票跟踪清单
- `stock_price_tracking`：价格追踪表，来源于 Python 定时采价任务
- 列表页主表和展开区标记主要依赖本地数据库
- 展开区价格图默认查本地 `stock_price_tracking`
- “查看更多历史数据”弹窗才会通过后端转调 Python API，再由 Python 调 AKShare / 东方财富接口

### 3.2 回测主链路

- `stock_daily_bar`：回测用历史日线表，来源于外部历史行情接口同步后落库
- `stock_signal_event`：按“股票 + 信号日 + 事件范围”聚合的增持事件表
- `stock_backtest_metric`：单事件在 5 / 10 / 20 / 60 日窗口下的收益、回撤、命中率结果
- `stock_backtest_summary`：股票级历史表现画像与回测评分
- `backtest_job_log`：每日增量 / 每周全量回测任务日志

### 3.3 链路原则

- 外部行情链路当前不稳定，主查询链路必须优先保证本地库可用
- 外部历史接口可以作为回测的数据输入源，但不应成为前端查询时的实时依赖
- 回测结果、评分结果、汇总结果必须落库保存
- 当前源数据没有明确“公告披露日”，第一阶段更准确地说是“事件研究 / 回测分析”，不要在实现里默认宣称为严格可交易策略

## 4. 环境变量与配置

- 敏感信息必须走环境变量，禁止硬编码
- 后端 `application.yml` 会自动导入根目录 `.env`
- Python `runtime.py` 也会自动读取根目录 `.env`
- 前端开发态通过 Vite proxy 转发 `/api` 和 `/data/api`

### 4.1 数据库核心变量

- `DB_HOST`
- `DB_PORT`
- `DB_USER`
- `DB_PASSWORD`
- `DB_NAME`
- `DB_USE_SSL`
- `DB_ALLOW_PUBLIC_KEY_RETRIEVAL`

### 4.2 监控链路变量

- `DATA_API_URL`
- `DATA_API_PORT`
- `APP_CORS_ALLOWED_ORIGINS`
- `ENABLE_SCHEDULER`
- `ENABLE_IMPORTER`
- `ENABLE_PRICE_TRACKING`
- `AKSHARE_RETRY_TIMES`
- `AKSHARE_RETRY_DELAY_SECONDS`
- `EASTMONEY_KLINE_INTERVAL_SECONDS`

### 4.3 回测链路变量

- `ENABLE_BACKTEST_PIPELINE`
- `ENABLE_BACKTEST_WEEKLY_FULL_REFRESH`
- `BACKTEST_DAILY_LOOKBACK_DAYS`
- `BACKTEST_BAR_SYNC_OVERLAP_DAYS`
- `BACKTEST_DAILY_BAR_MAX_WORKERS`
- `BACKTEST_BUILD_BATCH_STOCKS`
- `BACKTEST_DAILY_BAR_RETRY_TIMES`
- `BACKTEST_DAILY_BAR_RETRY_DELAY_SECONDS`
- `BACKTEST_DAILY_BAR_ADJUST`
- `BACKTEST_HORIZONS`
- `BACKTEST_EVENT_VERSION`
- `BACKTEST_CALC_VERSION`

## 5. 构建 / 运行 / 验证命令

### 5.1 Docker（根目录）

```bash
cp .env.example .env
docker compose up -d --build
docker compose logs -f
docker compose down
docker compose exec data-api python stock_change_importer.py
docker compose exec data-api python stock_price_tracking.py
docker compose exec data-api python backtest_pipeline.py --mode incremental
docker compose exec data-api python backtest_pipeline.py --mode full
```

### 5.2 前端（`frontend/`）

```bash
npm install
npm run dev
npm run dev -- --host 0.0.0.0
npm run build
npm run build-only
npm run preview
npm run lint
npm run format
```

单测命令（当前仓库尚无现成测试文件）：

```bash
npx vitest run
npx vitest run src/path/to/foo.test.ts
npx vitest run -t "test name"
```

### 5.3 后端（`backend/`）

```bash
./mvnw test
./mvnw spring-boot:run
./mvnw -q -DskipTests compile
mvn test
mvn spring-boot:run
mvn -q -DskipTests compile
```

说明：

- 当前仓库已包含 `mvnw` 与 `mvnw.cmd`
- 如果本机没有全局 Maven，优先使用 Wrapper

### 5.4 Python（`python/`）

```bash
pip install -r requirements.txt
python data_api.py
python stock_change_importer.py
python stock_price_tracking.py
python stock_daily_bar_sync.py --mode incremental
python stock_daily_bar_sync.py --mode full
python stock_backtest_builder.py --mode incremental
python stock_backtest_builder.py --mode full
python backtest_pipeline.py --mode incremental
python backtest_pipeline.py --mode full
python scheduler.py
python -m py_compile data_api.py
python -m py_compile stock_change_importer.py
python -m py_compile stock_price_tracking.py
python -m py_compile stock_daily_bar_sync.py
python -m py_compile stock_backtest_builder.py
python -m py_compile backtest_pipeline.py
python -m py_compile scheduler.py
```

## 6. 修改后至少做什么

- 改前端后，至少运行：`npm run lint`、`npm run build`
- 改后端后，至少运行：`./mvnw -q -DskipTests compile` 或 `mvn -q -DskipTests compile`
- 改 Python 后，至少运行：`python -m py_compile ...`
- 涉及数据库查询或 API 契约时，优先同时检查前端类型、后端 DTO、MyBatis XML、Python 返回结构
- 涉及回测口径、评分字段、窗口定义时，必须同步检查 `docs/backtest-design.md`

## 7. 前端代码规范

- Prettier：无分号、单引号、`printWidth: 100`
- 缩进 2 空格，换行保持 LF
- 导入顺序：标准库 / 第三方 / `@/` 别名 / 相对路径
- 能用 `import type` 时必须用 `import type`
- 路径别名：`@/* -> frontend/src/*`
- 使用 `defineComponent()`，当前代码以 `setup()` 风格为主，不要突然切成 `script setup` 混搭
- 组件文件名 PascalCase；composable 使用 `useXxx.ts`；服务层函数使用 `fetchXxx`
- 类型集中在 `frontend/src/types/`
- UI 文本统一中文，保持现有浅色、卡片式、信息密度适中的风格
- 避免把表格列越改越宽；优先 `show-overflow-tooltip`
- 重组件或大库优先懒加载，尤其是 ECharts 和历史弹窗
- 不要手动全局注册 Element Plus；当前走 `unplugin-auto-import` + `unplugin-vue-components`
- API 调用统一经过 `services/stockApi.ts`，不要在组件里直接拼 axios 请求
- 用户可见错误统一 `ElMessage`；空数据与异常必须区分

## 8. 后端代码规范

- 包结构保持：`com.example.brich.{controller,service,mapper,model,config}`
- Controller 只做参数接收、调用服务、返回响应
- Service 负责业务校验和编排
- SQL 放在 MyBatis XML，不要把复杂 SQL 写进注解
- HTTP 响应统一使用 `ApiResponse<T>`，分页统一使用 `PageResult<T>`
- DTO / Model 字段使用 camelCase
- 数据库列使用 snake_case，由 MyBatis 做映射
- 请求参数优先用注解校验：`@Pattern`、`@Min`、`@Max` 等
- 业务校验失败优先抛 `ResponseStatusException`
- 全局异常由 `GlobalExceptionHandler` 处理，禁止 `printStackTrace()`
- 新增接口时，必须考虑数据库连接失败、下游服务失败、参数非法三类场景
- 配置优先从 `.env` / 环境变量读取，禁止把 DB、URL、账号密码写死在 Java 代码里

### 8.1 回测接口约束

- 回测查询接口统一挂在 `/api/backtest`
- 第一阶段至少区分“总览”“事件列表”“股票画像”三类接口
- 事件列表排序字段必须显式白名单校验，不能放任前端自由拼接
- 事件回测窗口当前固定为 5 / 10 / 20 / 60，修改时要同步 Python 计算逻辑和文档

## 9. Python 代码规范

- 使用 snake_case 命名
- 统一使用 `runtime.py` 中的 `get_logger()`、`get_db_engine()`、`get_env_int()`
- 禁止重复实现 `.env` 解析、日志初始化、数据库连接创建
- Pandas 转字典前后必须注意 `NaN -> None`
- 数据库写入使用 SQLAlchemy + `text()`
- 批量写入优先分批，不要一次性超大事务
- 与外部接口交互时要考虑重试、降级、空结果和编码问题
- 对外部请求异常，优先记录结构化日志，再决定返回空数据还是抛错

### 9.1 回测脚本约束

- 建表逻辑统一走 `python/backtest_schema.py`
- 历史日线同步统一走 `python/stock_daily_bar_sync.py`
- 事件聚合、回测计算、汇总评分统一走 `python/stock_backtest_builder.py`
- 编排任务统一走 `python/backtest_pipeline.py`
- 日增量模式只同步受影响股票，但重建时要按目标股票的完整历史重建
- 周全量模式必须重拉历史行情并全量重算，不能只重算汇总
- 全量重建默认按股票分批处理，批大小由 `BACKTEST_BUILD_BATCH_STOCKS` 控制
- 历史日线同步默认允许受控并发抓取，并发数由 `BACKTEST_DAILY_BAR_MAX_WORKERS` 控制

## 10. 命名与类型约定

- 变量 / 函数：camelCase（前端、后端）或 snake_case（Python）
- 类 / 接口 / 组件：PascalCase
- 常量：UPPER_SNAKE_CASE
- 布尔变量优先使用 `is` / `has` / `enable` / `can` 前缀
- 金额、比例、日期字段命名要保持语义明确，不要复用含糊名称
- 回测指标字段统一使用：
  - `returnPct`
  - `maxReturnPct`
  - `maxDrawdownPct`
  - `hit5PctFlag`
  - `hit10PctFlag`
  - `signalScore`
  - `backtestScore`

## 11. 修改时的注意事项

- 不要编辑 `frontend/auto-imports.d.ts`、`frontend/components.d.ts`，除非你改了插件配置并重新生成
- 涉及前端金额显示时，优先复用 `frontend/src/utils/formatters.ts`
- 涉及展开图和弹窗历史图时，先区分“本地数据库图”与“外部历史图”两条链路
- 涉及定时采集逻辑时，先确认影响的是 `daily_stock_change`、`stock_price_tracking`，还是新增的回测链路
- 回测逻辑不要直接依赖 `stock_price_tracking` 作为长历史数据源；长历史回测默认使用 `stock_daily_bar`
- 同一股票同一交易日多人增持时，默认按单事件聚合，不要直接按原始明细重复计样
- 如果改了评分模型、窗口定义、任务调度，必须同步更新 `docs/backtest-design.md` 与本文件

## 12. 当前测试现状

- 前端：无现成测试文件
- 后端：只有 `BrichApplicationTests` 冒烟测试
- Python：无正式测试框架，依赖脚本执行和语法校验
- 因此代理在做改动时，验证不能只依赖测试通过，还应结合构建、运行日志和关键路径手工检查

## 13. 文档入口

- 回测系统设计文档：`docs/backtest-design.md`
- 回测建表脚本：`python/sql/backtest_schema.sql`
