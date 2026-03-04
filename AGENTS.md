# AGENTS.md — Stock Monitoring System

全程使用中文交流。本项目是股票增减持数据监控系统，Monorepo 前后端分离架构，Docker Compose 部署。

## 项目结构

```
stock/
├── frontend/           # Vue 3 + TypeScript 前端 (Vite, nginx)
├── backend/            # Spring Boot 3.4.5 后端 (Maven, Java 17)
├── python/             # Python 数据采集 (Flask API + 脚本 + APScheduler)
├── docker-compose.yml  # 编排: frontend + backend + data-api + data-scheduler
├── .env.example        # 环境变量模板 (DB 连接等)
└── AGENTS.md
```

单一 Git 仓库，四个服务通过 Docker Compose 统一编排，MySQL 由外部提供。

## 构建 / 运行 / 测试命令

### Docker 部署 (生产)

```bash
cp .env.example .env        # 填写数据库连接信息
docker compose up -d --build  # 构建并启动全部服务
docker compose logs -f        # 查看日志
docker compose down           # 停止
```

定时任务默认开启（`data-scheduler`）：
- 工作日 09:05,09:35,10:05,10:35,11:05,11:35,13:05,13:35,14:05,14:35,15:05 运行价格追踪
- 工作日 18:10 运行增减持导入

数据采集脚本手动执行：
```bash
docker compose exec data-api python stock_change_importer.py
docker compose exec data-api python stock_price_tracking.py
```

### 前端 (frontend/)

```bash
npm install              # 安装依赖
npm run dev              # 启动开发服务器 (Vite)
npm run build            # 类型检查 + 生产构建 (vue-tsc + vite build)
npm run build-only       # 跳过类型检查直接构建
npm run lint             # ESLint 检查并自动修复
npm run format           # Prettier 格式化
```

开发时需指定后端地址：
```bash
VITE_API_BASE_URL=http://localhost:8080 npm run dev
```

测试框架已预留 (Vitest) 但尚无测试文件：
```bash
npx vitest run                        # 运行全部测试
npx vitest run src/path/to/test.ts    # 运行单个测试文件
npx vitest run -t "test name"         # 按名称运行单个测试
```

### 后端 (backend/)

```bash
mvn clean install              # 完整构建
mvn spring-boot:run            # 启动 (需设置 DB 环境变量或本地 application.yml)
mvn test                       # 运行全部测试
mvn test -Dtest=BrichApplicationTests                    # 运行单个测试类
mvn test -Dtest=BrichApplicationTests#contextLoads       # 运行单个测试方法
```

### Python (python/)

```bash
pip install -r requirements.txt     # 安装依赖
python data_api.py                  # 启动 Flask 数据 API (端口 5000)
python stock_change_importer.py     # 运行增减持数据导入
python stock_price_tracking.py      # 运行价格追踪采集
```

## 环境变量

敏感配置通过环境变量注入，**禁止硬编码到源码中**：

| 变量 | 说明 | 默认值 |
|---|---|---|
| `DB_HOST` | MySQL 地址 | `host.docker.internal` |
| `DB_PORT` | MySQL 端口 | `3306` |
| `DB_USER` | MySQL 用户 | `root` |
| `DB_PASSWORD` | MySQL 密码 | (无默认，必须设置) |
| `DB_NAME` | 数据库名 | `stock` |
| `VITE_API_BASE_URL` | 前端 API 地址 (开发用) | 空 (生产走 nginx 代理) |
| `DATA_API_URL` | 后端访问 Python API 地址 | `http://localhost:5000` |
| `DATA_API_PORT` | Python API 容器监听端口 | `5000` |
| `SCHEDULER_TIMEZONE` | 定时任务时区 | `Asia/Shanghai` |
| `ENABLE_IMPORTER` | 是否启用增减持定时导入 | `true` |
| `ENABLE_PRICE_TRACKING` | 是否启用价格追踪定时采集 | `true` |

## 代码风格

### 前端 TypeScript / Vue

**格式化 (Prettier)**：无分号、单引号、行宽 100、缩进 2 空格、LF 行尾。

**ESLint**：ESLint 9 flat config，`eslint-plugin-vue` (essential) + `@vue/eslint-config-typescript` (recommended)。

**TypeScript**：路径别名 `@/*` -> `./src/*`，类型导入用 `import type`，接口集中在 `src/types/`。

**Vue 组件**：`defineComponent()` + Options API，文件名 PascalCase，composable 以 `use` 前缀命名，`<style scoped>`。

**目录分层**：`config/` -> `types/` -> `services/` -> `composables/` -> `components/` -> `views/`

**命名**：函数/变量 camelCase，接口/类型/组件 PascalCase，常量 UPPER_SNAKE_CASE，UI 文本中文。

### 后端 Java / Spring Boot

**包结构**：`com.example.brich.{controller, service, mapper, model, config}`

**约定**：`@RestController` + `@RequestMapping`，MyBatis XML Mapper，Lombok `@Data`，JUnit 5 测试。

**配置**：`application.yml` 通过 `${ENV_VAR:default}` 支持环境变量覆盖，MyBatis 开启 `map-underscore-to-camel-case`。

**命名**：Java 类 PascalCase，方法/变量 camelCase，数据库列 snake_case (MyBatis 自动映射)。

### Python 脚本

- `logging` 模块记录日志，SQLAlchemy + text SQL 操作数据库
- 函数命名 snake_case，依赖见 `requirements.txt`

## 已知技术债务

1. **无全局异常处理**：Java 端缺少 `@ControllerAdvice`，错误处理用 `e.printStackTrace()`
2. **无统一响应格式**：Controller 直接返回对象，无 `Result<T>` 包装
3. **CORS 全开放**：`allowedOrigins("*")`，仅限开发环境
4. **MySQL 驱动重复**：`pom.xml` 同时引入了 `mysql-connector-java` 和 `mysql-connector-j`
5. **测试覆盖不足**：前端无 Vitest 测试文件，后端仅有 `contextLoads` 冒烟测试
6. **前端包体积偏大**：当前构建主包约 2MB，需后续做按需加载/分包优化
