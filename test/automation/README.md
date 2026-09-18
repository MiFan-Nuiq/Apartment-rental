# 公寓租赁管理系统 · 自动化测试工程

基于 **pytest + Allure** 的接口 / UI / 数据库三层自动化测试工程，覆盖核心业务链路：
**登录 -> 房源查询 -> 看房预约**，并包含登录页 UI 冒烟与合同-缴费数据一致性校验。

---

## 一、与实际项目的差异记录（以实际代码为准）

| 项 | 任务描述 | 实际情况（以代码为准） |
| --- | --- | --- |
| 原脚本位置 | `test/test_core_flow.py`、`test/ui_test_login.py` | 实际位于 `test/automation/` 下，已**保留作备份**，不参与新工程收集 |
| UI 框架 | Selenium 或 Playwright | 实际为 **Playwright**，故不引入 selenium |
| 预约表租户字段 | 任务要求校验 `appointments.user_id` | `appointments` 表**无 user_id 列**，实际字段为 `tenant_id` / `landlord_id`（见 `backend/.../entity/Appointment.java`），代码按真实字段校验 |
| 合同状态枚举 | 任务描述“已签约” | 业务代码中合同生效状态为 **`生效中`**，不存在“已签约” |
| 错误码语义 | 未说明 | 后端 `ApiResponse.error()` 业务码恒为 **500**，且 **HTTP 状态码恒为 200**（异常被 try/catch 吞入响应体） |
| 数据库 | 未给出 | `backend/src/main/resources/application.yml`：`localhost:3306/apartment_rental_db`，账号 `apartment/123456` |

> 后端 JPA 使用 `ddl-auto: update` 自动建表，`DataInitializer` 自动初始化账号：`tenant/123456`、`landlord/123456`、`admin/123456`。

## 二、目录结构

```
test/automation/
├── apis/                        # 接口层：封装后端 REST 接口
│   ├── login_api.py             #   POST /api/auth/login
│   ├── apartment_api.py         #   GET  /api/apartments（含未携带 token 场景）
│   └── appointment_api.py       #   POST /api/appointments
├── pages/                       # 【新增】UI Page Object 层
│   ├── base_page.py             #   基类：goto/fill/click/wait_for_url/get_text/screenshot 等
│   └── login_page.py            #   登录页对象（定位对齐 Login.vue 真实代码）
├── data/                        # 【新增】数据驱动 YAML
│   ├── login_data.yaml          #   登录：正常/密码错误/用户不存在
│   └── appointment_data.yaml    #   预约：正常/缺失字段/无效房源
├── testcases/                   # 测试用例层
│   ├── test_core_flow.py        #   核心链路 7 例（含数据库落库校验）
│   ├── test_ui_login.py         #   登录页 UI 2 例（PO 模式）
│   ├── test_data_consistency.py #   【新增】3 条一致性 SQL 用例化
│   └── test_login_ddt.py        #   【新增】登录/预约数据驱动用例
├── utils/                       # 工具层
│   ├── request_util.py          #   requests.Session 封装
│   ├── assert_util.py           #   常用断言封装
│   └── db_util.py               #   【新增】pymysql 数据库封装（query_one/query_all/execute）
├── screenshots/                 # 【自动生成】UI 失败截图输出目录
├── traces/                      # 【自动生成】Playwright trace 输出目录
├── allure-results/              # 【自动生成】Allure 原始数据
├── allure-report/               # 【自动生成】Allure 静态 HTML 报告
├── conftest.py                  # 共享 fixture（接口/数据库/UI）+ 失败截图钩子
├── pytest.ini                   # pytest 配置（markers、strict-markers、allure 输出）
├── requirements.txt             # 依赖清单
└── README.md                    # 本说明

test/sql/                        # 测试用 SQL 脚本（CI 会导入其中的前两个）
├── schema.sql                   # 【新增】建表脚本：users/apartments/appointments/contracts/payments
├── data.sql                     # 【新增】种子数据：3 账号 + 3 房源 + 合同/流水/预约
└── contract_payment_consistency.sql   # 手工执行的 3 条一致性校验 SQL（已用例化到 test_data_consistency.py）
```

## 三、环境要求

| 组件 | 要求 | 说明 |
| --- | --- | --- |
| Python | 3.9+ | 使用 requests / pytest / allure / playwright / pymysql / pyyaml |
| 后端服务 | Spring Boot，端口 8080 | 需已启动，地址可用 `BASE_URL` 覆盖 |
| 前端服务 | Vite，端口 5173 | 仅 UI 用例需要，地址可用 `UI_BASE_URL` 覆盖 |
| MySQL | 8.x，端口 3306 | **DB 用例必需**，连接信息可用 `DB_*` 覆盖 |
| Chromium | Playwright 自带 | 仅 UI 用例需要 |
| Allure CLI | 2.x（需 Java 8+） | 生成 HTML 报告，`allure-pytest` 只是数据插件 |

## 四、安装依赖

```bash
cd test/automation
pip install -r requirements.txt     # 安装 requests/pytest/allure/pymysql/pyyaml/playwright 等
playwright install chromium          # 安装 UI 用例所需浏览器
```

## 五、启动服务

```bash
# 后端（终端 1）：Spring Boot 8080，需本地 MySQL 已启动
cd backend
mvn spring-boot:run                  # 或 java -jar target/apartment-rental-1.0.0.jar

# 前端（终端 2）：Vite 5173
cd frontend
npm install                          # 首次执行
npm run dev
```

## 六、markers 说明表

| marker | 含义 | 典型用例 |
| --- | --- | --- |
| `smoke` | 冒烟：核心链路快速回归 | 登录成功、房源查询、预约提交、UI 登录成功 |
| `regression` | 回归：边界与异常场景 | 密码错误、用户不存在、数据一致性校验 |
| `api` | 接口层用例（requests） | test_core_flow、test_login_ddt |
| `ui` | UI 层用例（Playwright） | test_ui_login |
| `db` | 需直连 MySQL 校验的用例 | test_data_consistency、预约落库校验 |
| `slow` | 耗时较长的用例 | 端到端全链路 test_full_flow |

> `pytest.ini` 已开启 `--strict-markers`：使用未注册的 marker 会直接报错，避免标签拼错导致用例被静默漏跑。

## 七、运行命令汇总

所有命令均在 `test/automation` 目录下执行。

```bash
pytest -m smoke            # 冒烟：核心链路（接口 + UI + 落库校验）
pytest -m api              # 全部接口用例
pytest -m ui               # 全部 UI 用例（需前端 5173 + Chromium）
pytest -m db               # 全部数据库校验用例（需 MySQL）
pytest -m regression       # 全部回归用例（异常场景 + 数据一致性）
pytest -m "smoke and not slow"   # 冒烟但排除慢用例
pytest -n auto             # 多进程并行执行（需 pytest-xdist）
pytest testcases/test_data_consistency.py   # 只跑指定文件
```

### 环境变量覆盖

```bash
# 例：切换后端/数据库地址与测试账号（PowerShell）
$env:BASE_URL="http://192.168.1.10:8080"; $env:DB_HOST="192.168.1.10"; $env:TEST_USERNAME="tenant"; pytest -m api
```

支持：`BASE_URL`、`UI_BASE_URL`、`TEST_USERNAME`、`TEST_PASSWORD`、`APARTMENT_ID`、`TENANT_ID`、
`LANDLORD_ID`、`APPOINTMENT_TIME`、`APPOINTMENT_REMARK`、`HEADLESS`、
`DB_HOST`、`DB_PORT`、`DB_USER`、`DB_PASSWORD`、`DB_NAME`。

## 八、数据驱动用法

数据文件位于 `data/`，由 `testcases/test_login_ddt.py` 通过 `@pytest.mark.parametrize` + `yaml.safe_load` 读取。

新增一条用例只需在 YAML 中追加一段，无需改代码：

```yaml
# data/login_data.yaml
cases:
  - id: login_success          # 作为用例 id 显示
    title: 正常登录            # 写入 Allure 动态标题
    username: tenant
    password: "123456"
    expected_code: 200         # 期望业务码
    expected_message: 登录成功  # 期望提示文案
    expect_token: true         # 是否期望返回 token
```

预约用例同理见 `data/appointment_data.yaml`（字段 `payload` + `expect_success`）。

## 九、数据库断言用法

`utils/db_util.py` 提供 `DBUtil`（连接信息统一从环境变量读取，默认对齐 `application.yml`）：

```python
# 在用例中通过 conftest 的 db_connection fixture 使用（session 级长连接）
row = db_connection.query_one("SELECT id, status FROM appointments ORDER BY id DESC LIMIT 1")
rows = db_connection.query_all("SELECT id FROM contracts WHERE status = %s", ("生效中",))
affected = db_connection.execute("UPDATE ... ")   # 写操作，会自动 commit
```

- `query_one`：返回单条 `dict` 或 `None`
- `query_all`：返回 `list[dict]`
- `execute`：返回受影响行数
- 表名/字段名对齐后端 JPA 实体（驼峰转下划线），如 `appointments`、`contracts`、`payments`、`users`

### 一致性校验用例（test_data_consistency.py）

| 用例 | 校验内容 | 预期 |
| --- | --- | --- |
| `test_active_contract_without_payment` | 生效中合同是否有对应缴费记录 | 结果为空（无不一致） |
| `test_payment_exists_for_inactive_contract` | 非生效中合同是否残留缴费流水 | 结果为空（**当前 xfail**，见下） |
| `test_landlord_contract_statistics_consistency` | 房东合同汇总统计 vs 合同明细 | 数量与金额完全一致 |

> ️ 第 2 条用例标记了 `xfail`：当前测试数据中确有一条已终止合同（`contract_id=15`，`HT2026031600`）仍残留 1 条缴费流水，
> 已登记为缺陷 **BUG-DATA-001**。断言本身保持严格（要求结果为空），数据修复后会自动转为 XPASS。

## 十、UI Page Object 模式说明

- `pages/base_page.py`：页面基类，封装 `goto/fill/click/wait_for_url/get_text/is_visible/screenshot/get_local_storage` 等通用操作。
- `pages/login_page.py`：登录页对象，定位器与操作全部内聚：
  - `USERNAME_INPUT` = `input[placeholder="请输入用户名"]`
  - `PASSWORD_INPUT` = `input[placeholder="••••••••"]`
  - `SUBMIT_BUTTON` = `button.submit-btn`
  - `ERROR_MESSAGE` = `.error-message`
  - `login(username, password)` 一键完成 填账号 -> 填密码 -> 点登录
  - `wait_redirect(role)` 按角色等待跳转（`ROLE_REDIRECT` 映射对齐 `Login.vue` 的 `redirectByRole`）

用例中不再出现裸选择器，页面样式变更时只需修改 Page Object 一处。

## 十一、失败截图与 trace 位置

`conftest.py` 中的 `pytest_runtest_makereport` 钩子会在 **UI 用例 call 阶段失败** 时自动：

| 产物 | 输出目录 | 说明 |
| --- | --- | --- |
| 失败截图 | `test/automation/screenshots/<用例名>.png` | 页面全屏截图 |
| Playwright trace | `test/automation/traces/<用例名>.zip` | 含截图、DOM 快照、网络与源码 |

查看 trace：
```bash
playwright show-trace traces/<用例名>.zip     # 打开可视化回放器
```

## 十二、GitHub Actions 使用说明

工作流文件：`.github/workflows/auto-test.yml`，触发条件为 `push` / `pull_request`（并支持手动触发）。

完整流水线（步骤编号与 workflow 中的注释一致）：

```
检出代码 -> Python 3.11 -> 安装测试依赖 -> 安装 Chromium -> Java 17
  -> ⑥ 等待 MySQL 就绪（mysqladmin ping，最多 30 次 × 2 秒）
  -> ⑦ 导入数据库结构和种子数据（test/sql/schema.sql + data.sql）
  -> ⑧ 构建后端 -> ⑨ 启动后端并等待 8080 就绪（curl，最多 30 次 × 2 秒）
  -> ⑩ 启动前端并等待 5173 就绪（nohup + PID + 日志）
  -> ⑪ pytest -m smoke
  -> ⑫⑬⑭ 上传 allure-results / screenshots / traces 为 artifact
```

### 12.1 CI 数据库初始化（本次修复重点）

CI 上的 MySQL 容器是**全新空库**，JPA 的 `ddl-auto: update` 只会建出空表，
缺数据会导致：房源列表为空、`apartment_id=3` 不存在而触发外键约束失败。
因此 workflow 在**启动后端之前**固定执行两步导入：

| 顺序 | 文件 | 内容 | 是否幂等 |
| --- | --- | --- | --- |
| ① | [schema.sql](../../test/sql/schema.sql) | 建表：`users` / `apartments` / `appointments` / `contracts` / `payments` | 是（`CREATE TABLE IF NOT EXISTS`） |
| ② | [data.sql](../../test/sql/data.sql) | 种子数据：3 个账号、3 条房源、2 份合同、2 条流水、1 条预约 | 是（`INSERT ... ON DUPLICATE KEY UPDATE`） |

种子数据与测试代码的对应关系（改任一侧都要同步）：

| 常量（conftest.py） | 值 | 对应种子数据 |
| --- | --- | --- |
| `USERNAME` / `PASSWORD` | `tenant` / `123456` | `users.id = 3`（BCrypt 密文取自本项目后端） |
| `LANDLORD_ID` | `2` | `users.id = 2` |
| `TENANT_ID` | `3` | `users.id = 3` |
| `APARTMENT_ID` | `3` | `apartments.id = 3`（**必须存在**，否则预约外键失败） |
| `APPOINTMENT_TIME` | `2026-10-01 10:00:00` | 房源 3 上**不能有生效中合同**，否则预约会被 `AppointmentService` 拦截 |

> schema.sql 中的表结构与字段，全部取自后端实体与 Hibernate 实际生成的 DDL（含索引/约束名），
> 未臆造任何表名或字段名；其余业务表由 JPA `ddl-auto=update` 自动创建。

**本地导出种子数据的命令（mysqldump 示例）**：

```powershell
# 1) 只导出表结构（不含数据），作为 schema.sql 的来源
mysqldump --host=127.0.0.1 --port=3306 --user=apartment --password=123456 --no-data --skip-comments `
  apartment_rental_db users apartments appointments contracts payments > schema_dump.sql

# 2) 只导出指定表的数据（不含建表语句），作为 data.sql 的来源
mysqldump --host=127.0.0.1 --port=3306 --user=apartment --password=123456 --no-create-info --skip-comments `
  apartment_rental_db users apartments appointments contracts payments > data_dump.sql

# 3) 本地按 CI 的顺序导入（Windows PowerShell 5.1 请用下面的 --key=value + source 写法）
#    注意：PowerShell 5.1 会把 -h127.0.0.1 里的点号拆开（报 Unknown MySQL server host '127'），
#          所以务必使用 --host=xxx 形式；另外 < 输入重定向在 PowerShell 中不可用，故用 source 命令
mysql --host=127.0.0.1 --port=3306 --user=apartment --password=123456 --default-character-set=utf8mb4 `
  --execute="source test/sql/schema.sql" apartment_rental_db
mysql --host=127.0.0.1 --port=3306 --user=apartment --password=123456 --default-character-set=utf8mb4 `
  --execute="source test/sql/data.sql" apartment_rental_db

# 4) 导入后核对（应能看到 3 个账号、3 条房源）
mysql --host=127.0.0.1 --port=3306 --user=apartment --password=123456 `
  --execute="SELECT id,name,status,audit_status FROM apartments WHERE id<=3 ORDER BY id" apartment_rental_db
```

> 注意：`data.sql` 是**手工精简**过的种子数据（固定 id + 幂等写法），
> 而不是直接 `mysqldump` 全量导出——因为本地库里含 `BUG-DATA-001` 等脏数据，
> 全量导出会把脏数据带进 CI，一致性用例②就再也无法通过。

### 12.2 CI 前端启动方式（本次修复重点）

早期写法只有 `nohup npm run dev &`，没有记录 PID、没有等待就绪、失败日志也被 `continue-on-error` 吞掉，
于是 UI 用例只表现为 `net::ERR_CONNECTION_REFUSED at http://localhost:5173/login`，很难定位。
现在改为：

```bash
npm install --no-audit --no-fund                       # 先装依赖
nohup npm run dev -- --host 0.0.0.0 --port 5173 --strictPort > /tmp/frontend.log 2>&1 &
echo $! > /tmp/frontend.pid                            # 记录 PID，便于排查
# 循环 curl http://localhost:5173，最多 30 次 × 2 秒
# 之后 cat /tmp/frontend.log 打印日志，并再次确认 5173 可访问，否则本步骤直接失败
```

- `--strictPort`：5173 被占用时**直接失败**，避免 Vite 自动切到 5174、UI 用例却仍连 5173；
- 去掉了该步骤的 `continue-on-error`：服务起不来就在该步骤明确报错，不再拖到用例里变成"连接被拒绝"；
- 后端启动步骤同样加了 `curl` 就绪等待（`/api/auth/login` 是 POST 接口，GET 探测返回 405 也算服务已就绪）。

### 12.3 其他说明

- CI 中会启动 MySQL 8 服务容器（库名 `apartment_rental_db`，账号 `apartment/123456`），与后端默认配置一致；
- UI 用例通过 `HEADLESS=true` 无头运行；
- `构建后端` 步骤保留了 `continue-on-error: true`，但后续"启动后端"步骤不再吞错——jar 没构建出来就会在此明确失败；
- **首次使用需人工在 GitHub 仓库开启 Actions 并验证一次流水线**（见下节）。

## 十三、生成 Allure 报告

```bash
cd test/automation
pytest -m smoke                       # ① 跑测试，自动产出 allure-results/
allure serve allure-results           # ② 临时服务 + 自动打开浏览器
allure generate allure-results -o allure-report --clean   # 或生成静态报告
```

> 若当前终端提示 `allure : 无法将“allure”项识别为 cmdlet...`，说明该终端未刷新到最新 PATH。
> 两种解决方式：① 新开一个终端；② 直接用绝对路径执行：
> `& "C:\Users\王炜垲\.local\share\allure\allure-2.46.1\bin\allure.bat" generate allure-results -o allure-report --clean`
>
> 报告产物：`allure-results/`（原始 JSON 数据）+ `allure-report/`（静态 HTML，入口 `index.html`）。

## 十四、需要人工完成的事项

以下事项无法由工具自动完成，需要你本人在本地或 GitHub 上操作：

### 1. 环境与依赖安装
- [ ] 执行 `pip install -r test/automation/requirements.txt`（本次新增了 `pymysql`、`pyyaml`、`pytest-xdist`，需重新安装）。
- [ ] 执行 `playwright install chromium`（若尚未安装浏览器）。
- [ ] 确认本机 **MySQL 已启动**，且库 `apartment_rental_db`、账号 `apartment/123456` 可用（DB 用例必需）。
- [ ] 确认 **Allure CLI** 已安装且在 PATH 中（本机已装 2.46.1，新开终端执行 `allure --version` 验证）。

### 2. 服务启动（DB / UI 用例的前置条件）
- [ ] 启动后端：`cd backend && mvn spring-boot:run`（或运行打好的 jar）。
- [ ] 启动前端：`cd frontend && npm run dev`（UI 用例必需）。
- [ ] 若端口被占用或地址不同，用 `BASE_URL` / `UI_BASE_URL` / `DB_*` 环境变量覆盖。

### 3. 真实数据库连接才能验证的步骤
- [ ] `pytest -m db` 必须在 **MySQL 可用且有真实数据** 的前提下执行，否则 `db_connection` fixture 会给出连接失败提示并 fail。
- [ ] `test_core_flow.py::test_submit_appointment` 的落库断言需要 `APARTMENT_ID`（默认 3）真实存在且与房东匹配。
- [ ] 一致性用例依赖真实业务数据；`test_payment_exists_for_inactive_contract` 已按已知缺陷 `BUG-DATA-001` 标记 `xfail`。
- [ ] 本地导入种子数据（`test/sql/schema.sql` + `data.sql`）需要数据库写权限；**若想完整模拟"全新空库"（CI 场景），需要 MySQL 的
      `CREATE DATABASE` / `DROP DATABASE` 权限**——当前 `apartment` 账号只有 `apartment_rental_db.*` 权限，
      自动化工具无法建临时库做这一步验证。请用有权限的账号（如 root）执行，或直接在 CI 首次运行时验证。
- [ ] 导入后请人工确认 **表结构与后端一致**：后端启动日志中 Hibernate 若对该 5 张表执行了 `alter table`，
      说明 `schema.sql` 与实体有偏差，需要按实体修正（正常情况应为"无变更"）。

### 4. GitHub 账号相关操作
- [ ] 将代码 `git push` 到 GitHub 仓库（工作流才会生效）。本次新增/修改了 `.github/workflows/auto-test.yml`、
      `test/sql/schema.sql`、`test/sql/data.sql`，**必须推送后 CI 才会用上新逻辑**。
- [ ] 在仓库 **Settings -> Actions -> General** 确认 Actions 已启用（Allow all actions）。
- [ ] 首次推送后到 **Actions** 页手动触发一次 `workflow_dispatch`，确认流水线可跑通（CI 环境无法在本地验证）。
- [ ] 重点看这 4 步的日志：`等待 MySQL 就绪`、`导入数据库结构和种子数据`、`启动后端服务并等待就绪`、
      `启动前端服务并等待就绪`——本次修复的 4 个失败用例都依赖它们。
- [ ] 若 CI 中数据库/端口与默认值不同，需在仓库 **Settings -> Secrets and variables -> Actions** 配置对应变量或改 workflow。
- [ ] 如需 Allure 在线报告（如 GitHub Pages），需额外配置 Pages 部署，当前仅上传 artifact。

### 5. 需要手动截图放进 README 的操作
- [ ] 运行 `pytest -m smoke` 后，打开 `allure serve allure-results`，截图报告首页与用例详情，放入 README 或论文附录。
- [ ] 让某条 UI 用例故意失败（如改错密码断言），截图 `screenshots/` 中的失败截图，作为"失败自动截图"能力的证据。
- [ ] 截图 GitHub Actions 运行成功的页面，作为 CI 接入的证据。

### 6. 其他无法代劳的事
- [ ] 首次运行 `pytest -m db` 前，建议先手工执行 `test/sql/contract_payment_consistency.sql` 确认数据现状。
- [ ] `xfail` 用例的数据修复（BUG-DATA-001）需由开发侧处理，修复后建议将 `xfail` 改为普通断言。
- [ ] 数据驱动新增用例时，需人工确认 YAML 中的 `apartment_id` / `tenant_id` / `landlord_id` 与真实数据一致。
- [ ] **种子数据需要长期维护**：若后续改了 `conftest.py` 里的 `APARTMENT_ID` / `TENANT_ID` / `LANDLORD_ID`，
      必须同步修改 `test/sql/data.sql`（见 12.1 的对应关系表），否则 CI 会重新出现外键约束失败。
- [ ] 若数据库表结构（实体）发生变更，`schema.sql` 需要同步更新（用 12.1 的 `mysqldump --no-data` 重新导出即可）。
- [ ] Windows PowerShell 5.1 的两个坑已在 12.1 中给出规避写法：
      ① 原生命令参数里的点号会被拆开（`-h127.0.0.1` 失效），要改用 `--host=127.0.0.1`；
      ② 不支持 `<` 输入重定向，要改用 `mysql --execute="source xxx.sql"`。

## 十五、运行记录

### 15.1 本次 CI 失败修复的验证（2026-09-18）

修复对象：CI 中失败的 4 个 `pytest -m smoke` 用例
（`test_query_apartments` / `test_submit_appointment` / `test_full_flow` / `test_ui_login`）。

| 验证项 | 命令 / 方式 | 实际结果 |
| --- | --- | --- |
| schema.sql 可执行 | 导入 `test/sql/schema.sql` | 5 条建表语句全部成功 |
| data.sql 可执行 | 导入 `test/sql/data.sql` | 5 条数据语句全部成功，中文无乱码 |
| 种子数据幂等 | 连续导入 2 次 | 用户 5 条、房源 6 条不变，无重复行 |
| 种子数据正确性 | `SELECT ... FROM apartments WHERE id<=3` | 房源 1/2/3 均为 `空置` + `审核通过`，`landlord_id=2` |
| 冒烟用例 | `pytest -m smoke` | **6 passed, 12 deselected in 3.06s** |
| 数据库用例 | `pytest -m db` | 3 passed, 1 xfailed（4 selected） |
| workflow 语法 | `yaml.safe_load(auto-test.yml)` | 校验通过，14 个步骤顺序正确 |

### 15.2 历史运行记录（2026-09-16）

| 执行命令 | 实际结果 |
| --- | --- |
| `pytest -m smoke` | 6 passed, 12 deselected in 6.11s |
| `pytest -m api` | 13 passed, 5 deselected in 1.12s |
| `pytest`（全量） | **17 passed, 1 xfailed in 5.34s** |
| `allure generate allure-results -o allure-report --clean` | Report successfully generated to allure-report |

说明：
- 全量 18 个用例 = 核心链路 7 + 数据一致性 3 + 数据驱动 6 + UI 2；
- 唯一的 xfailed 为 `test_payment_exists_for_inactive_contract`，对应已知缺陷 **BUG-DATA-001**（已终止合同仍残留缴费流水），断言本身严格，数据修复后会自动转 XPASS；
- 「UI 失败自动截图 + trace」能力已实测验证：临时制造一次 UI 用例失败后，`screenshots/test_tmp_force_fail.png`（36 KB）与 `traces/test_tmp_force_fail.zip`（227 KB）均正常产出（验证产物已删除）。