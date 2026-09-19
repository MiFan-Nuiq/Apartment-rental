[![自动化测试](https://github.com/MiFan-Nuiq/Apartment-rental/actions/workflows/auto-test.yml/badge.svg?branch=main)](https://github.com/MiFan-Nuiq/Apartment-rental/actions/workflows/auto-test.yml)
# 公寓租赁管理系统 · 测试项目

本项目为「公寓租赁管理系统」的测试专项工程，覆盖**手工测试用例、接口自动化、数据库一致性校验、UI 自动化、缺陷管理**五个维度，用于毕业设计的测试作品集展示与日后回归验证。

## 目录结构

```
Apartment-rental/
├── README.md                          # 本说明文件
├── docker-compose.yml                 # 【新增】Docker 一键启动编排：MySQL + 后端 + 前端
├── .env.example                       # 【新增】docker-compose 环境变量模板（复制为 .env 使用）
├── backend/                           # 系统后端源码（Spring Boot，作为被测对象）
│   ├── Dockerfile                     # 【新增】后端镜像：多阶段构建（Maven 编译 -> JRE 运行）
│   └── .dockerignore                  # 【新增】后端构建上下文排除清单（target、.git 等）
├── frontend/                          # 系统前端源码（Vue3，作为被测对象）
│   ├── Dockerfile                     # 【新增】前端镜像：多阶段构建（Node 装依赖 -> Vite dev server）
│   └── .dockerignore                  # 【新增】前端构建上下文排除清单（node_modules、dist 等）
└── test/                              # 测试工程（本目录为测试资产所在位置）
    ├── docs/
    │   ├── 测试用例.md                # 全模块手工测试用例（16 章，按业务模块划分）
    │   ├── Bug清单模板.md             # 通用 Bug 登记模板 + 示例 Bug
    │   └── Bug清单_实际发现.md        # 登录模块 Bug 实际发现记录
    ├── automation/                    # pytest + Allure + Playwright 自动化测试工程
    │   ├── apis/                      # 接口层（登录 / 房源 / 预约）
    │   ├── pages/                     # UI Page Object 层
    │   ├── data/                      # 数据驱动 YAML（登录、预约）
    │   ├── testcases/                 # 用例：核心链路 / 数据隔离 / UI / 数据一致性 / 数据驱动
    │   ├── utils/                     # 请求、断言、数据库工具
    │   ├── conftest.py                # 共享 fixture（含动态数据 fixture 与失败截图钩子）
    │   ├── pytest.ini                 # pytest 配置（markers、allure 输出）
    │   ├── clean.sh / run_smoke.sh / run_api.sh   # 一键清理与一键执行脚本
    │   └── README.md                  # 自动化测试工程详细说明
    ├── evidence/
    │   └── BUG-DATA-001
    └── sql/
        ├── schema.sql                 # 建表脚本（Docker 与 CI 都会导入）
        ├── data.sql                   # 种子数据（Docker 与 CI 都会导入）
        └── contract_payment_consistency.sql  # 合同状态与支付流水一致性 SQL + 执行结果摘要
```

## 一、测试用例（手工）

- 文件：[test/docs/测试用例.md](test/docs/测试用例.md)
- 内容：按系统真实业务模块编写，覆盖 **16 章**，对应用户、房源、预约、合同、缴费、报障、消息、投诉、评价、收藏、统计、上传、权限等模块。
- 特点：每条用例包含`前置条件 / 输入参数 / 预期结果`，`预期结果`中的提示文案、状态枚举均取自后端真实代码。

## 二、接口自动化（Requests + pytest）

- 文件：[test/automation/test_core_flow.py](test/automation/test_core_flow.py)
- 链路：`登录(获取 token) → 房源查询 → 提交预约`，并使用 token 贯穿整条业务链路。
- 断言：HTTP 状态码、`ApiResponse.code/message`、返回字段（token/role/id、房源字段、预约默认状态"待处理"）、未鉴权返回 401。
- 附带边界用例：错误密码、用户不存在、未携带 token。
- 文件顶部含 **运行记录**，供记录每次执行结果。

### 运行方式
```bash
pip install requests pytest
pytest test/automation/test_core_flow.py -v
```

## 三、数据库一致性校验（SQL）

- 文件：[test/sql/contract_payment_consistency.sql](test/sql/contract_payment_consistency.sql)
- 3 条多表连接查询：
  1. `生效中`合同但无任何缴费记录（漏生成流水）；
  2. 有缴费记录但合同状态非`生效中`（失效合同残留流水）；
  3. 指定房东名下合同的总租金/总押金统计。
- 表名、列名、状态枚举均对齐后端 JPA 实体；文件末尾含 **执行结果摘要** 供填写实际数据。
- 注意：项目合同生效状态取值实为 **`生效中`**（代码中无`已签约`），脚本已按此实现。

## 四、UI 自动化（Playwright）

- 文件：[test/automation/ui_test_login.py](test/automation/ui_test_login.py)
- 场景：`输入账号 → 输入密码 → 点击登录 → 断言跳转成功`，另含错误密码不回跳用例。
- 定位选择器与跳转路由取自前端 [Login.vue](frontend/src/views/Login.vue) 真实代码（placeholder、`.submit-btn`、`redirectByRole` 路由）。

### 运行方式
```bash
pip install pytest-playwright
playwright install chromium
pytest test/automation/ui_test_login.py -v
```

## 五、缺陷管理

- 通用模板：[test/docs/Bug清单模板.md](test/docs/Bug清单模板.md)
- 实际发现记录：[test/docs/Bug清单_实际发现.md](test/docs/Bug清单_实际发现.md)（登录模块预置示例已标注「示例」，实测待填写）
- 结构：汇总概览表 + 单条 Bug 模板（标题 / 严重程度 / 优先级 / 重现步骤 / 预期结果 / 实际结果 / 截图与日志位置）。
- 截图/日志统一存放：`test/evidence/<Bug编号>/`

## 六、Docker 一键启动（本地测试环境复现）

一条命令拉起 **MySQL + 后端 + 前端** 三个容器，把本地测试环境复现出来，供 `test/automation` 下的 pytest（接口 / UI / 数据库）直接运行。

涉及文件：

| 文件 | 作用 |
| --- | --- |
| [docker-compose.yml](docker-compose.yml) | 编排 MySQL、后端、前端三个服务（端口、依赖顺序、健康检查、数据卷、网络） |
| [.env.example](.env.example) | 环境变量模板（库名/账号/密码、三个端口、npm 源），复制为 `.env` 后生效 |
| [backend/Dockerfile](backend/Dockerfile) | 后端镜像：多阶段构建，Maven 编译 → JRE 运行 |
| [frontend/Dockerfile](frontend/Dockerfile) | 前端镜像：多阶段构建，Node 装依赖 → 运行 Vite dev server（5173） |
| [backend/.dockerignore](backend/.dockerignore) / [frontend/.dockerignore](frontend/.dockerignore) | 排除 `target`、`node_modules`、`.git` 等，减小构建上下文 |

### 6.1 前置条件

- 安装 **Docker Desktop**（Windows 需开启 **WSL2** 后端），安装后执行 `docker version`、`docker compose version` 确认命令可用；
- 首次启动需拉取 `mysql:8.0`、`maven`、`node`、`eclipse-temurin` 等基础镜像，**耗时较长**，请确保能访问 Docker Hub；
- 确认 **3306 / 8080 / 5173** 三个端口未被本机已启动的服务占用（占用时见 6.5）。

### 6.2 启动命令

```bash
# ① 进入项目根目录（docker-compose.yml 所在位置）
cd Apartment-rental

# ② 可选：复制环境变量模板（不复制也能跑，会使用 compose 内置默认值）
Copy-Item .env.example .env        # Windows PowerShell
cp .env.example .env               # Linux / macOS / Git Bash

# ③ 构建镜像并后台启动三个服务（首次构建较慢）
docker compose up -d

# ④ 查看服务状态：期望 mysql 与 backend 为 healthy
docker compose ps
```

### 6.3 查看日志与停止服务

```bash
# 实时查看后端日志（应能看到 "Tomcat started on port(s): 8080"）
docker compose logs -f backend
# 查看 MySQL 日志（应能看到 schema.sql / data.sql 的导入过程）
docker compose logs -f mysql
# 查看前端日志（应能看到 "VITE v5.x  ready in xxx ms"）
docker compose logs -f frontend

# 停止并删除容器（保留数据卷，数据库数据不丢）
docker compose down

# 停止并删除容器 + 数据卷（清空数据库；下次启动会重新导入 schema.sql 与 data.sql）
docker compose down -v

# 源码改动后重新构建并启动
docker compose up -d --build
```

### 6.4 服务依赖与数据初始化说明

| 环节 | 说明 |
| --- | --- |
| MySQL 首次启动 | 官方镜像会自动执行 `/docker-entrypoint-initdb.d/` 下的脚本：`01-schema.sql`（建表）→ `02-data.sql`（种子数据）。`test/sql/` 下的源文件**未做任何修改** |
| 后端启动 | `depends_on` 配置为 `condition: service_healthy`，等 MySQL 健康检查（`mysqladmin ping`）通过后才启动，避免"连不上库"导致启动失败 |
| 前端启动 | 同样等待后端健康检查通过后才启动 |
| 端口 | 后端 8080、前端 5173、MySQL 3306，与本地直接启动时**完全一致**，因此 `test/automation` 的默认配置无需改动 |
| 环境变量 | 全部通过根目录 `.env` 覆盖（模板见 `.env.example`）；数据库连接由 compose 注入后端的 `SPRING_DATASOURCE_*` 环境变量 |

> **重要**：初始化脚本只在**数据卷为空**时执行一次。若已启动过、想重新导入种子数据，需先 `docker compose down -v` 清空数据卷，再 `docker compose up -d`。

后端没有引入 `spring-boot-starter-actuator`，因此健康检查探测的是 `/api/auth/login`：它是 POST 接口，GET 访问返回 405，但只要能拿到响应就说明 Tomcat 已就绪（与 CI 的探测思路一致）。

### 6.5 端口被占用怎么办

若本机已有 MySQL / 后端 / 前端在跑，请**先停止本地服务**，或修改 `.env` 换端口：

```bash
# .env 中改为空闲端口
MYSQL_PORT=3307
BACKEND_PORT=8081
FRONTEND_PORT=5174
```

改端口后需要同步把测试工程的地址指过去，否则 pytest 仍会连默认端口：

```bash
# Windows PowerShell（在 test/automation 下执行）
$env:DB_PORT="3307"; $env:BASE_URL="http://localhost:8081"; $env:UI_BASE_URL="http://localhost:5174"
pytest -m api
```

**本机最容易撞的是 3306**：若本地装了 MySQL 并通过 Windows 服务常驻（本机为 `MySQL80`），
它会一直占着 3306。两种处理方式：

```powershell
# 方式一（推荐）：临时停掉本地 MySQL 服务，Docker 用默认 3306，pytest 零改动
#   注意：需要以「管理员身份」运行 PowerShell，否则会报 Cannot open MySQL80 service
Stop-Service MySQL80

# 用完 Docker 后恢复本地 MySQL 服务
Start-Service MySQL80

# 方式二：不动本地服务，把 .env 的 MYSQL_PORT 改成 3307，
#         跑 pytest 时额外设置 $env:DB_PORT="3307"
```

> 提醒：`MySQL80` 服务的启动类型是「自动」，**重启电脑后它会自动恢复并再次占用 3306**，
> 下次用 Docker 前需要重新 `Stop-Service MySQL80`。

### 6.6 与 CI 方案的关系及差异记录

**关系**：CI（GitHub Actions）用的是 workflow 里的 **MySQL service 容器**，本地用的是 **docker-compose**，两者思路完全一致——都是"先起 MySQL → 导入 schema.sql + data.sql → 起后端 → 起前端 → 跑 pytest"，因此本地 Docker 环境能较好地复现 CI 的失败场景。CI 仍保留原有 service 容器方式，**未替换为 docker-compose**。

**差异记录（以实际代码为准）**：

| 项 | 任务描述 | 实际情况与处理 |
| --- | --- | --- |
| JDK 版本 | 建议使用 `eclipse-temurin:17-jre-alpine` 等 | `backend/pom.xml` 声明 `<java.version>1.8</java.version>`，但 CI 使用的是 **Java 17** 且全绿。为与 CI 保持一致，Docker 同样选用 **JDK 17**（JDK 17 编译 source/target=1.8 合规，Spring Boot 2.7.18 支持在 Java 17 运行） |
| 初始化脚本顺序 | 直接挂载 `schema.sql` 与 `data.sql` | 官方镜像按**文件名字典序**执行，`data.sql` 排在 `schema.sql` 之前会导致"先插数据后建表"。故容器内挂载为 `01-schema.sql`、`02-data.sql` 强制顺序，**源文件不改名、不修改** |
| 后端健康检查 | 探测 `/api/auth/login` 或 `/actuator/health` | 项目未引入 actuator，`/actuator/health` 不存在，故使用 `/api/auth/login` |
| 前端容器如何连后端 | 未说明 | 前端 `/api` 由 Vite dev server 代理，代理发生在**前端容器内部**，写 `localhost` 会指向容器自身。因此 [frontend/vite.config.js](frontend/vite.config.js) 增加了 `VITE_API_TARGET` 环境变量支持，Docker 下注入 `http://backend:8080`；**本地开发不设置该变量时仍为 `http://localhost:8080`，行为与改动前完全一致** |
| npm 依赖源 | 未说明 | 实测在容器内用官方源 `registry.npmjs.org` 装依赖会 **ECONNRESET（网络重置）导致构建失败**；开发机 npm 本就配置了国内镜像，故容器内默认改用 `registry.npmmirror.com`，并支持用 `.env` 的 `NPM_REGISTRY` 覆盖。改用镜像后前端依赖安装从"152 秒后失败"变为 **7 秒成功** |
| 健康检查地址 | 未说明 | 容器内 `localhost` 会解析为 **IPv6 的 `::1`**，而 Tomcat/Vite 监听的是 **IPv4 的 `0.0.0.0`**，用 `localhost` 探测会一直 `Connection refused`。因此两个健康检查统一写 **`127.0.0.1`**（MySQL 的 `mysqladmin ping -h 127.0.0.1` 同理） |

### 6.7 如何验证 Docker 方案生效

```bash
# ① 三个容器都在运行（STATUS 列应显示 Up / healthy）
docker compose ps

# ② MySQL 日志中能看到 schema.sql 与 data.sql 已导入
docker compose logs mysql | Select-String -Pattern "01-schema.sql|02-data.sql"
# 也可直接连库核对：应有 3 个账号、3 条基础房源
mysql --host=127.0.0.1 --port=3306 --user=apartment --password=123456 `
  --execute="SELECT COUNT(*) AS 用户数 FROM users; SELECT id,name,status FROM apartments WHERE id<=3 ORDER BY id;" apartment_rental_db

# ③ 后端日志出现 Tomcat 启动成功
docker compose logs backend | Select-String -Pattern "Tomcat started on port"

# ④ 前端日志出现 Vite ready
docker compose logs frontend | Select-String -Pattern "ready in"

# ⑤ 浏览器访问前端页面（应能正常打开登录页）
Start-Process http://localhost:5173                          # Windows
open http://localhost:5173                                   # macOS

# ⑥ 探测后端（GET 访问登录接口返回 405 即说明服务已就绪）
curl http://localhost:8080/api/auth/login

# ⑦ 跑接口测试（MySQL/后端/前端容器都在运行时执行）
cd test/automation
pytest -m api
```

**实测结果（2026-09-19，Docker Desktop 29.8.0 / Compose v2，Windows + WSL2）**：

| 验证项 | 命令 | 实际结果 |
| --- | --- | --- |
| 三个容器状态 | `docker compose ps` | `backend / frontend / mysql` 均 **running + healthy** |
| 端口映射 | `docker compose ps` | `0.0.0.0:8080->8080`、`0.0.0.0:5173->5173`、`0.0.0.0:3306->3306` |
| MySQL 初始化脚本顺序 | `docker compose logs mysql` | 依次执行 `01-schema.sql` → `02-data.sql`（先建表后插数据，顺序修正生效） |
| 种子数据 | SQL 查询 | `users` = **3**、`apartments` = **3**（id 1/2/3，状态 `空置` + 审核 `审核通过`）、`appointments` = **1** |
| 后端就绪 | `docker compose logs backend` | 出现 `Tomcat started on port(s): 8080`、`Started ApartmentRentalApplication` |
| 后端接口 | `curl http://localhost:8080/api/auth/login` | **HTTP 405**（服务已就绪） |
| 前端就绪 | `docker compose logs frontend` | `VITE v5.4.21 ready in 382 ms` |
| 前端页面 | `curl http://localhost:5173` | **HTTP 200**，HTML 含 Vue 挂载点 `#app` |
| 接口用例 | `pytest -m api` | **17 passed, 5 deselected** |
| 冒烟用例（含 UI） | `pytest -m smoke` | **7 passed, 15 deselected**（UI 用例证明了浏览器经 Vite 代理 `backend:8080` 调用后端成功） |
| 全量用例 | `pytest -q` | **21 passed, 1 xfailed**（xfailed 为 BUG-DATA-001） |
| 动态数据残留 | SQL 统计 | 残留房源 / 残留隔离 / 残留 DDT 均为 **0**，`apartments` 仍为 3、`appointments` 仍为 1 |

> 说明：`pytest` 在**宿主机**上执行，通过 `localhost` 映射端口（8080/5173/3306）访问三个容器，
> 因此 `test/automation` 的默认配置完全不需要改动，这也是"容器端口与本地一致"的价值所在。

### 6.8 局限与建议

- **开发时建议仍用本地启动**：容器内的前后端代码是构建时拷贝进去的，没有挂载源码，**热更新（HMR）不方便**；日常开发用本地 `mvn spring-boot:run` + `npm run dev`，**测试环境/复现问题用 Docker**；
- **CI 不替换为 docker-compose**：GitHub Actions 的 service 容器已稳定工作，除非后续需要"本地与 CI 完全同一套编排"，否则不必替换；
- 前端镜像目前跑的是 **dev server**（测试需要），若要部署生产环境需改用 `npm run build` + Nginx（做法已写在 `frontend/Dockerfile` 顶部注释中）。

## 测试环境与准备

- 后端：`http://localhost:8080`（Spring Boot），默认初始化账号见 `DataInitializer`：`admin|123456`、`landlord|123456`、`tenant|123456`。
- 前端：`http://localhost:5173`（Vite）。
- 鉴权：除 `/api/auth/**`、`/uploads/**` 外，所有 `/api/**` 需携带 `Authorization: Bearer <token>`。
- 自动化脚本中的`用户 / 房源 / 合同 ID`等参数需按实际测试数据在脚本配置区调整。
- 除本地直接启动外，也可用 Docker 一键拉起同等的三件套环境（见 [六、Docker 一键启动](#六docker-一键启动本地测试环境复现)），端口与默认配置完全一致，测试工程无需改动。

## 使用建议

1. 先依据 `测试用例.md` 完成手工冒烟，确认核心模块可用；
2. 再顺序执行 SQL 一致性校验与接口/UI 自动化；
3. 将任一环节发现的问题按 `Bug清单_实际发现.md` 格式登记（登录模块已建示例）；
4. 每次执行自动化后，把结果回填至脚本顶部的 **运行记录** 与 SQL 末尾的 **执行结果摘要**，形成完整测试证据链。
