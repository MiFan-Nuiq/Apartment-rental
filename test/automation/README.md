# 公寓租赁管理系统 · 自动化测试工程

基于 **pytest + Allure** 的接口 / UI / 数据库三层自动化测试工程，覆盖核心业务链路：
**登录 -> 房源查询 -> 看房预约**，并包含登录页 UI 冒烟与合同-缴费数据一致性校验。

测试数据采用「**静态种子数据打底 + 动态 fixture 隔离**」策略：公共稳定的数据（账号、基础房源）由
[data.sql](../../test/sql/data.sql) 提供，业务操作产生的数据（临时房源、临时预约）由 fixture 动态创建并在用例后自动清理，
详见 [十、测试数据管理策略](#十测试数据管理策略静态种子数据打底--动态-fixture-隔离)。

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
│   ├── apartment_api.py         #   GET /api/apartments（含未携带 token 场景）
│   │                            #   【新增】GET /{id}、POST /api/apartments、DELETE /api/apartments/{id}（动态数据用）
│   └── appointment_api.py       #   POST /api/appointments
│                                #   【新增】GET /{id}、DELETE /api/appointments/{id}（动态数据用）
├── pages/                       # UI Page Object 层
│   ├── base_page.py             #   基类：goto/fill/click/wait_for_url/get_text/screenshot 等
│   └── login_page.py            #   登录页对象（定位对齐 Login.vue 真实代码）
├── data/                        # 数据驱动 YAML
│   ├── login_data.yaml          #   登录：正常/密码错误/用户不存在
│   └── appointment_data.yaml    #   预约：正常/缺失字段/无效房源
├── testcases/                   # 测试用例层
│   ├── test_core_flow.py        #   核心链路 8 例（含数据库落库校验 + 动态数据演示用例）
│   ├── test_data_isolation.py   #   【新增】动态数据隔离 3 例（id 不同/互不影响/清理生效）
│   ├── test_ui_login.py         #   登录页 UI 2 例（PO 模式）
│   ├── test_data_consistency.py #   3 条一致性 SQL 用例化
│   └── test_login_ddt.py        #   登录/预约数据驱动用例（预约正向场景改用动态临时房源）
├── utils/                       # 工具层
│   ├── request_util.py          #   requests.Session 封装
│   ├── assert_util.py           #   常用断言封装
│   └── db_util.py               #   pymysql 数据库封装（query_one/query_all/execute）
├── screenshots/                 # 【自动生成】UI 失败截图输出目录
├── traces/                      # 【自动生成】Playwright trace 输出目录
├── allure-results/              # 【自动生成】Allure 原始数据
├── allure-report/               # 【自动生成】Allure 静态 HTML 报告
├── clean.sh                     # 清理全部运行产物与 Python 缓存
├── run_smoke.sh                 # 清理 + 跑冒烟用例 + 生成 Allure 报告
├── run_api.sh                   # 清理 + 跑接口用例 + 生成 Allure 报告
├── conftest.py                  # 共享 fixture：接口/数据库/UI + 【新增】动态数据（unique_suffix、temp_apartment、temp_appointment、dynamic_data_cleaner）+ 失败截图钩子
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

## 十、测试数据管理策略（静态种子数据打底 + 动态 fixture 隔离）

本工程的数据管理遵循一条原则：**公共稳定的数据用静态种子打底，业务操作产生的变化数据用动态 fixture 隔离。**

### 10.1 两类数据的分工

| 数据类别 | 来源 | 管什么 | 生命周期 |
| --- | --- | --- | --- |
| 静态种子数据 | [data.sql](../../test/sql/data.sql) | 登录账号（`admin`/`landlord`/`tenant`）、基础房源（`id=1/2/3`）、基础合同与缴费流水、基础权限关系 | 长期存在；CI 与本地导入一次即可，重复导入幂等 |
| 动态 fixture 数据 | [conftest.py](../../test/automation/conftest.py) 中的 `temp_apartment` / `temp_appointment` | 业务操作产生的、会变化的数据：**临时房源、临时预约** | 仅存活于单个用例；用例结束立即删除 |

> 为什么这样分：登录账号与基础房源是所有用例的**共同前置条件**，适合固定；
> 而"提交预约"这类用例本身会写数据，如果共用同一条固定房源，
> 就会出现用例互相污染、重复运行堆脏数据、`apartment_id` 写死后换环境即失败等问题。

### 10.2 动态 fixture 清单

| fixture | 级别 | 依赖 | 返回值 | 用例后清理 |
| --- | --- | --- | --- | --- |
| `unique_suffix` | function | 无 | 时间戳 + 8 位短 uuid 的唯一字符串（如 `20260919103000-3f9a1c2b`） | 无需清理 |
| `temp_apartment` | function | `api_client`、`auth_headers`、`unique_suffix` | 临时房源 dict：`id` / `name` / `landlord_id` / `suffix` / `raw` | `DELETE /api/apartments/{id}` |
| `temp_appointment` | function | `api_client`、`auth_headers`、`appointment_data`、`temp_apartment` | 临时预约 dict：`id` / `apartment_id` / `tenant_id` / `landlord_id` / `appointment_time` / `remark` / `raw` | `DELETE /api/appointments/{id}` |
| `dynamic_data_cleaner` | function | `request`、`api_client`、`auth_headers` | 登记函数 `register(delete_func, record_id, label)` | 按登记顺序**倒序**删除（后进先出） |

配套的两个模块级辅助（`conftest.py` 中，供 fixture 与用例复用）：

| 辅助函数 | 作用 | 被谁使用 |
| --- | --- | --- |
| `safe_delete(delete_func, client, token, record_id, label)` | 统一的安全删除：失败只打印中文警告（`[警告] 清理临时房源 id=xx 失败：...`），不抛异常 | `temp_apartment` / `temp_appointment` / `dynamic_data_cleaner` |
| `build_temp_apartment_payload(name)` | 统一临时房源的请求体口径（`status="空置"`、`auditStatus="审核通过"`、`landlord.id=LANDLORD_ID`） | `temp_apartment`、`test_data_isolation.py`、`test_login_ddt.py` |

> `dynamic_data_cleaner` 解决的是"**用例体内自己创建**的数据"的清理问题：
> 例如 `test_data_isolation.py` 手动创建的房源/预约、`test_login_ddt.py` 正向用例创建的预约，
> 它们不属于任何 fixture；若不登记清理，`temp_apartment` 删除房源时会因**外键约束**失败（HTTP 500），
> 导致房源与预约双双残留。用例只需调用一次 `dynamic_data_cleaner(delete_appointment, id, "临时预约")`，
> 用例结束（**含失败**）时便会自动删除。

清理顺序为 **后进先出**：`temp_appointment` 先删预约 → `temp_apartment` 再删房源，
因此不会出现"房源下还挂着预约、导致删除失败"的外键问题。

### 10.3 数据隔离的做法

| 手段 | 说明 |
| --- | --- |
| 用例级作用域 | 三个 fixture 全部为 `scope="function"`，**每个用例一套独立数据**，用例之间天然隔离 |
| 唯一数据标识 | 房源名称/地址/备注统一拼接 `unique_suffix`（时间戳 + 短 uuid），避免唯一约束或命名冲突，也便于事后用 SQL 定位残留 |
| 不使用写死的业务 id | 预约用例的 `apartment_id` 一律来自 `temp_apartment["id"]`；数据驱动用例（`test_login_ddt.py`）的**正向**场景同样改为动态建房，YAML 中的 `apartment_id` 仅对负向场景生效 |
| 静态数据只读不改 | 动态用例不修改静态种子数据，保证基础数据的稳定性 |
| 断言精确到记录 | 数据库校验改为 `WHERE id = %s` 精确查询，而非"取最新一条"，避免同用例内多条动态数据相互干扰 |

### 10.4 清理策略

- **清理时机**：用例结束（**含用例失败**）时由 fixture 的 `yield` 之后代码执行，无需用例自己处理；
- **清理方式**：调用后端真实删除接口（`DELETE /api/apartments/{id}`、`DELETE /api/appointments/{id}`），**不做物理删库、不修改后端代码**；
- **清理失败**：统一由 `safe_delete` 捕获异常并打印中文警告（`[警告] 清理临时房源 id=xx 失败：...`），
  **不抛异常、不静默吞异常**——既不掩盖原始断言错误，也提示人工确认是否有残留；
- **用例体内自建数据**（如 `test_data_isolation.py` 手动创建的房源/预约、`test_login_ddt.py` 正向用例创建的预约）：
  通过 `dynamic_data_cleaner` fixture（内部用 `request.addfinalizer`）登记清理，保证断言失败时同样会执行清理；
  登记顺序为"先房源、后预约"，finalizer **后进先出**，因此预约先被删除，不会触发外键约束。

### 10.5 动态数据用到的接口契约（均取自后端 controller，未臆造）

| 操作 | 方法 + 路径 | 来源 |
| --- | --- | --- |
| 创建房源 | `POST /api/apartments`（`@RequestBody Apartment`，`landlord` 以嵌套对象传入） | `ApartmentController#save` |
| 删除房源 | `DELETE /api/apartments/{id}` | `ApartmentController#delete` |
| 查询单个房源 | `GET /api/apartments/{id}` | `ApartmentController#findById` |
| 创建预约 | `POST /api/appointments` | `AppointmentController#save` |
| 删除预约 | `DELETE /api/appointments/{id}` | `AppointmentController#delete` |
| 查询单个预约 | `GET /api/appointments/{id}` | `AppointmentController#findById` |

> **差异记录**：任务描述要求"临时房源状态为**可预约**"，但后端 `ApartmentService.save` 的默认状态
> 与全项目真实枚举均为 **`空置`**（项目中不存在"可预约"枚举值），因此动态 fixture 使用 `status="空置"`。

### 10.6 如何验证动态数据管理生效

```bash
# ① 连续跑两次冒烟：两次都应有相同数量的用例通过，且数据库不出现重复/脏数据
pytest -m smoke
pytest -m smoke

# ② 跑一次回归与全量（回归会跑到数据驱动正向用例，同样不应残留）
pytest -m regression
pytest -q

# ③ 用 SQL 确认没有任何动态数据残留（以下 5 个计数正常应全部为 0）
mysql --host=127.0.0.1 --port=3306 --user=apartment --password=123456 apartment_rental_db `
  --execute="
    SELECT COUNT(*) AS 残留房源 FROM apartments WHERE name LIKE '自动化临时房源-%';
    SELECT COUNT(*) AS 残留预约_核心链路 FROM appointments WHERE remark LIKE '%pytest 自动化提交的看房预约%';
    SELECT COUNT(*) AS 残留预约_数据驱动 FROM appointments WHERE remark = '数据驱动-正常预约';
    SELECT COUNT(*) AS 残留预约_数据隔离 FROM appointments WHERE remark LIKE '%数据隔离验证%';
    SELECT COUNT(*) AS 总房源数, (SELECT COUNT(*) FROM appointments) AS 总预约数 FROM apartments;"

# ④ 数据隔离用例全部通过（验证 id 不同、互不影响、清理真实生效）
pytest testcases/test_data_isolation.py -v
```

> 判据：连续多次运行后，上面的「残留」计数全部为 0，且「总房源数 / 总预约数」保持不变
> （不会随运行次数增长）——这即证明"用例后清理、不留脏数据"真实生效。

## 十一、UI Page Object 模式说明

- `pages/base_page.py`：页面基类，封装 `goto/fill/click/wait_for_url/get_text/is_visible/screenshot/get_local_storage` 等通用操作。
- `pages/login_page.py`：登录页对象，定位器与操作全部内聚：
  - `USERNAME_INPUT` = `input[placeholder="请输入用户名"]`
  - `PASSWORD_INPUT` = `input[placeholder="••••••••"]`
  - `SUBMIT_BUTTON` = `button.submit-btn`
  - `ERROR_MESSAGE` = `.error-message`
  - `login(username, password)` 一键完成 填账号 -> 填密码 -> 点登录
  - `wait_redirect(role)` 按角色等待跳转（`ROLE_REDIRECT` 映射对齐 `Login.vue` 的 `redirectByRole`）

用例中不再出现裸选择器，页面样式变更时只需修改 Page Object 一处。

## 十二、失败截图与 trace 位置

`conftest.py` 中的 `pytest_runtest_makereport` 钩子会在 **UI 用例 call 阶段失败** 时自动：

| 产物 | 输出目录 | 说明 |
| --- | --- | --- |
| 失败截图 | `test/automation/screenshots/<用例名>.png` | 页面全屏截图 |
| Playwright trace | `test/automation/traces/<用例名>.zip` | 含截图、DOM 快照、网络与源码 |

查看 trace：
```bash
playwright show-trace traces/<用例名>.zip     # 打开可视化回放器
```

## 十三、GitHub Actions 使用说明

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

### 13.1 CI 数据库初始化（本次修复重点）

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
| `APARTMENT_ID` | `3` | `apartments.id = 3`（静态房源，仍用于房源列表类断言；**预约用例已改用临时房源**，不再依赖它做外键） |
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

### 13.2 CI 前端依赖安装注意事项（本次修复重点）

#### 13.2.1 故障现象与真正的根因

CI 日志里的三个现象是**同一条因果链**：

```
npm install --no-audit --no-fund   -> "added 3 packages in 3s"（明显没装全）
nohup npm run dev ...              -> /tmp/frontend.log: "sh: 1: vite: Permission denied"
30 次探测 5173                      -> 全部失败，最终 exit 1
```

> **根因不是 `NODE_ENV=production`**（本仓库未设置该变量，也确认过没有 `.npmrc`）。

真正的原因是：**`frontend/node_modules` 被提交进了 git**。

| 事实 | 数据 |
| --- | --- |
| `frontend/node_modules` 被 git 跟踪的文件数 | **12941** |
| `backend/target` 被跟踪的文件数 | 129 |
| 仓库总跟踪文件数 | 13644（**95.8% 是构建产物**） |
| `git ls-files -s frontend/node_modules/.bin/vite` 的权限位 | **`100644`**（没有可执行位） |

链条如下：

1. 这些文件是在 **Windows** 上提交的，git 记录的权限位是 `100644`；
2. `actions/checkout` 在 Linux 上按该权限位还原 → `node_modules/.bin/vite` **不可执行**；
3. `npm install` 看到依赖树"已满足"，只补装 3 个缺失包就退出（3 秒完成），**根本不会修复权限位**；
4. `npm run dev` 通过 `sh` 执行 `.bin/vite` → `sh: 1: vite: Permission denied`。

同时，从 Windows 提交的 `node_modules` 也**不含 Linux 平台的原生二进制**（如 `@esbuild/linux-x64`），
即使绕过权限问题，Vite 仍可能因 esbuild 平台不匹配而启动失败。

#### 13.2.2 修复动作

**① 仓库层面：新增 [.gitignore](../../.gitignore)**，忽略 `node_modules/`、`target/`、`dist/` 等，
防止依赖目录与构建产物再次被提交（`node_modules` 必须由 CI 自己安装，绝不能入库）。

**② workflow 层面：`安装前端依赖` 步骤改为**

```bash
# 环境诊断（先打印 Node/npm 版本与 npm 配置，便于在 Actions 日志里直接定位）
node -v ; npm -v
npm config get production     # 若为 true 会跳过 devDependencies
npm config get omit           # 若含 dev 同样会跳过 devDependencies
cat package.json              # 确认 vite 在 devDependencies（本仓库已确认在，无需修改）

rm -rf node_modules           # 关键：删掉被 git 带进来的 Windows 版依赖树
npm install --include=dev --no-audit --no-fund   # 显式安装 devDependencies，确保 vite 装上
chmod -R +x node_modules/.bin || true            # 补齐 .bin 下 shim 的可执行权限
# 校验 node_modules/vite/bin/vite.js 存在，不存在则立即失败并给出原因
```

**③ workflow 层面：启动命令改为直接用 node 执行 vite 入口**

```bash
nohup node node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5173 --strictPort > /tmp/frontend.log 2>&1 &
echo $! > /tmp/frontend.pid                    # 记录 PID
# 循环 curl http://localhost:5173，最多 30 次 × 2 秒
# cat /tmp/frontend.log 打印日志，并再次确认 5173 可访问，否则本步骤直接失败
```

三种启动方式的兼容性对比（本项目选第三种）：

| 启动方式 | 是否受 `.bin` 权限问题影响 | 说明 |
| --- | --- | --- |
| `npm run dev` | **会** | 走 `node_modules/.bin/vite` 的 sh shim，正是本次报错的入口 |
| `npx --no-install vite` | **会** | `npx` 最终仍去执行 `.bin` 下的 shim，同样可能 `Permission denied` |
| `node node_modules/vite/bin/vite.js` | **不会** | 只依赖 `node` 本身，彻底绕开 shim 与 `PATH`，兼容性最好 |

#### 13.2.3 其他要点

- `--strictPort`：5173 被占用时**直接失败**，避免 Vite 自动切到 5174、UI 用例却仍连 5173；
- `安装前端依赖` 与 `启动前端服务` 两个步骤都用 `working-directory: frontend`，
  `cat package.json`、`rm -rf node_modules` 等相对路径均相对于 `frontend/` 执行（任务四）；
- 去掉了启动步骤的 `continue-on-error`：服务起不来就在该步骤明确报错，不再拖到用例里变成"连接被拒绝"；
- 后端启动步骤同样加了 `curl` 就绪等待（`/api/auth/login` 是 POST 接口，GET 探测返回 405 也算服务已就绪）。

### 13.3 其他说明

- CI 中会启动 MySQL 8 服务容器（库名 `apartment_rental_db`，账号 `apartment/123456`），与后端默认配置一致；
- UI 用例通过 `HEADLESS=true` 无头运行；
- `构建后端` 步骤保留了 `continue-on-error: true`，但后续"启动后端"步骤不再吞错——jar 没构建出来就会在此明确失败；
- **首次使用需人工在 GitHub 仓库开启 Actions 并验证一次流水线**（见下节）。

## 十四、生成 Allure 报告

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

## 十五、Shell 脚本（一键清理与一键执行）

`test/automation/` 下提供 3 个 Shell 脚本，把"清理产物 → 跑用例 → 生成报告"这条固定流程封装成一条命令。
**CI 和本地都可以用**：CI 里可直接调用（如 `bash ./run_smoke.sh`），本地则用于日常回归。

### 15.1 脚本清单

| 脚本 | 用途 | 是否需要前端 5173 | 是否需要后端 8080 | 是否需要 MySQL |
| --- | --- | --- | --- | --- |
| [clean.sh](../../test/automation/clean.sh) | 清理全部测试运行产物与 Python 缓存 | 否 | 否 | 否 |
| [run_smoke.sh](../../test/automation/run_smoke.sh) | 清理 → `pytest -m smoke` → 成功后生成 Allure 报告 | **是**（UI 冒烟用例） | 是 | 是 |
| [run_api.sh](../../test/automation/run_api.sh) | 清理 → `pytest -m api` → 成功后生成 Allure 报告 | **否** | 是 | 是 |

### 15.2 用法

```bash
cd test/automation

# ① 只清理产物：删除 allure-results / allure-report / screenshots / traces
#    / .pytest_cache / 所有 __pycache__ 与 *.pyc，逐项打印中文提示
./clean.sh

# ② 一键冒烟：清理后跑 pytest -m smoke，通过则生成 Allure 报告
#    前置条件：后端 8080 + 前端 5173 + MySQL 均已启动
./run_smoke.sh

# ③ 一键接口回归：清理后跑 pytest -m api，通过则生成 Allure 报告
#    前置条件：只需后端 8080（不需要启动前端，因此比 ② 更快）
./run_api.sh

# 不想加可执行权限时，用 bash 显式执行（效果完全相同）
bash clean.sh && bash run_smoke.sh
```

### 15.3 退出码与产物策略

三个脚本的退出码都可直接用于 CI 串联判断（`run_*.sh` 透传 pytest 的退出码）：

| 场景 | 脚本输出 | allure-results | allure-report |
| --- | --- | --- | --- |
| 用例全部通过（退出码 0） | `冒烟测试通过` / `接口测试通过` | 保留 | **生成** |
| 有用例失败（退出码非 0） | `冒烟测试失败，请查看日志` / `接口测试失败，请查看日志` | **刻意保留**（便于排查） | 不生成 |

失败时刻意保留 `allure-results` 与 `.pytest_cache`，这样可以直接用
`allure serve ./allure-results` 看失败详情，或用 `pytest -m smoke --lf` 只重跑失败用例。

> 若脚本提示 `未检测到 allure 命令，跳过报告生成`，说明当前终端没刷新到 Allure 的 PATH。
> 新开一个终端即可；报告生成失败**不影响**测试结果的判定（脚本仍按 pytest 退出码返回）。

### 15.4 可执行权限说明（Linux / Mac / Windows 的差异）

| 环境 | 操作方式 | 说明 |
| --- | --- | --- |
| Linux / Mac | 先执行 `chmod +x clean.sh run_smoke.sh run_api.sh`，然后 `./clean.sh` | 没有可执行位时直接 `./xxx.sh` 会报 `Permission denied` |
| Linux / Mac（不想改权限） | `bash clean.sh` | 用解释器显式执行，无需可执行位 |
| Windows | **用 Git Bash 执行**，不要用 PowerShell / cmd | PowerShell 无法直接运行 `.sh`；Git Bash 中同样建议 `bash clean.sh` |
| Windows（Git Bash） | `cd /d/projects/Apartment-rental/test/automation && bash run_smoke.sh` | 路径用 `/d/...` 形式；脚本内部会自动 `cd` 到自身所在目录 |

> 脚本已使用 **LF 换行符**（非 CRLF）。这一点很关键：CRLF 换行会让 Linux 报
> `bad interpreter: /usr/bin/env bash^M`，脚本在 CI 上直接无法执行。
> 若后续在 Windows 上编辑这些脚本，请确认编辑器未把换行符改成 CRLF
> （Git 用户可加 `.gitattributes` 强制 `*.sh text eol=lf`）。

## 十六、需要人工完成的事项

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
- [ ] `test_core_flow.py::test_submit_appointment` 的落库断言已改为使用**动态临时房源**，因此只需 `LANDLORD_ID`（默认 2）与 `TENANT_ID`（默认 3）真实存在即可，不再要求 `apartment_id=3` 存在。
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
- [ ] 数据驱动新增用例时，需人工确认 YAML 中的 `tenant_id` / `landlord_id` 与真实数据一致；
      `apartment_id` 仅在 `expect_success=false` 的负向场景生效（正向场景由用例动态创建临时房源）。
- [ ] **种子数据需要长期维护**：若后续改了 `conftest.py` 里的 `TENANT_ID` / `LANDLORD_ID`，
      必须同步修改 `test/sql/data.sql`（见 13.1 的对应关系表），否则 CI 会重新出现外键约束失败。
- [ ] **动态数据的落库校验依赖 `db_util.py` 的 `autocommit=True`**：`db_connection` 是 session 级长连接，
      若关闭自动提交，第一次查询就会建立 REPEATABLE READ 一致性读快照，导致读不到后端新提交的动态数据（误判"未落库"），
      请勿移除该配置。
- [ ] 若数据库表结构（实体）发生变更，`schema.sql` 需要同步更新（用 12.1 的 `mysqldump --no-data` 重新导出即可）。
- [ ] Windows PowerShell 5.1 的两个坑已在 13.1 中给出规避写法：
      ① 原生命令参数里的点号会被拆开（`-h127.0.0.1` 失效），要改用 `--host=127.0.0.1`；
      ② 不支持 `<` 输入重定向，要改用 `mysql --execute="source xxx.sql"`。

### 7. 仓库瘦身：把 node_modules / target 从 git 中移除（**强烈建议，优先级最高**）

workflow 里的 `rm -rf node_modules` 只是**兜底绕过**，让 CI 不再被污染；
但仓库里仍然跟踪着 **12941 个 `node_modules` 文件 + 129 个 `backend/target` 文件**。
只要它们还在 git 里，就会出现"本地删了又被 checkout 回来""仓库 clone 极慢""跨平台权限位反复出问题"。

我已新增 `.gitignore`，剩下这一步需要你手动执行（**属于 git 索引操作，涉及一次大批量提交，需你确认后再做**）：

```bash
# 1) 从 git 索引中移除依赖目录、构建产物与测试运行产物（--cached 表示只删索引，不动本地文件）
git rm -r --cached frontend/node_modules
git rm -r --cached backend/target
# 测试运行产物同样被误提交了：跑一次 clean.sh 就会产生几百个文件的 diff
git rm -r --cached test/automation/allure-results
git rm -r --cached test/automation/allure-report
git rm -r --cached test/automation/screenshots
git rm -r --cached test/automation/traces

# 2) 确认 .gitignore 生效（应输出路径，表示已被忽略）
git check-ignore -v --no-index frontend/node_modules test/automation/allure-results

# 3) 提交这次清理（提交后仓库跟踪文件会从 13644 降到约 300）
git add .gitignore
git commit -m "chore: 忽略并移除误提交的 node_modules、target 与测试运行产物"

# 4) 推送
git push
```

> 若希望进一步减小仓库体积（历史提交里仍有这些大文件），需要重写历史（`git filter-repo` 或
> BFG Repo-Cleaner），属于破坏性操作，**务必先备份**，可参考但不强制。

> ⚠️ **`.gitignore` 语法坑**：它**只支持整行注释**（`#` 必须在行首），
> **不支持行尾注释**——`node_modules/    # 说明` 这种写法会让整行变成一个无效模式，规则静默失效。
> 本项目的 `.gitignore` 已按正确写法组织（说明单独占一行），修改时请勿改成行尾注释。
> 验证规则是否生效：`git check-ignore -v --no-index frontend/node_modules`（应回显命中的规则行号）。

### 8. 依赖安装完成后的人工确认
- [ ] 先执行 `git rm -r --cached` 清理（见第 7 节）再推送，否则 CI 每次仍会检出 12,941 个污染文件。
- [ ] 推送后在 Actions 日志里确认 `安装前端依赖` 步骤打印的 `npm config production` **不是 `true`**。
- [ ] 首次 CI 通过后，建议在本地也执行一次干净安装（见下方"本地验证命令"），确认 `vite` 可正常启动。

### 9. Shell 脚本相关的人工操作
- [ ] **Linux / Mac 上首次使用需手动加可执行权限**：`chmod +x clean.sh run_smoke.sh run_api.sh`
      （本仓库的脚本未内置 `chmod`，也不建议把可执行位依赖本地文件系统状态）。
- [ ] **Windows 上请用 Git Bash 执行**（PowerShell / cmd 无法直接运行 `.sh`），例如：
      `cd /d/projects/Apartment-rental/test/automation && bash run_smoke.sh`。
- [ ] 运行 `run_smoke.sh` 前，需自行确认 **后端 8080 + 前端 5173 + MySQL 3306** 三个服务都已启动，
      脚本不会代你启动服务（CI 由 workflow 负责启动，本地需手工启动）。
- [ ] 若脚本提示"未检测到 allure 命令"，说明当前终端未刷新到 Allure 的 PATH，**新开一个终端**即可。
- [ ] 在 Windows 上编辑这些 `.sh` 文件后，请确认换行符仍为 **LF**（可用 `file clean.sh` 或
      `git diff --check` 检查），改成 CRLF 会导致 CI（Linux）报 `bad interpreter`。

## 十七、运行记录

### 17.1 动态测试数据管理验证（2026-09-19，最新）

实现内容：新增 `unique_suffix` / `temp_apartment` / `temp_appointment` / `dynamic_data_cleaner` 四个 fixture
（`conftest.py`）、新增模块级辅助 `safe_delete` / `build_temp_apartment_payload`、
新增 `testcases/test_data_isolation.py`（3 例）、改造 `test_core_flow.py`（新增 1 例并改用动态房源）、
`test_login_ddt.py` 正向预约用例改用动态房源、`apis` 层补充创建/删除房源与删除预约方法。

环境：后端 8080 + 前端 5173 + MySQL 3306 均已启动（本机实测）。

| 验证项 | 命令 | 实际结果 |
| --- | --- | --- |
| 接口用例 | `pytest -m api -q` | **17 passed, 5 deselected** |
| 冒烟第 1 次 | `pytest -m smoke -q -s` | **7 passed, 15 deselected**，无 `[警告]` 清理失败输出 |
| 冒烟第 2 次（连续） | `pytest -m smoke -q -s` | **7 passed, 15 deselected**，无 `[警告]` 清理失败输出 |
| 回归用例 | `pytest -m regression -q` | **14 passed, 7 deselected, 1 xfailed**（xfailed 为 BUG-DATA-001） |
| 全量用例 | `pytest -q` | **21 passed, 1 xfailed**（共 22 例） |
| 残留检查 | SQL 统计动态数据 | `自动化临时房源-%` = **0**；`数据隔离验证` 残留 = **0**；`数据驱动-正常预约` 残留 = **0**；`pytest 自动化提交的看房预约` 残留 = **0** |
| 总量稳定性 | 连续 5 次运行后统计 | `apartments` = **6**、`appointments` = **3**，**不随运行次数增长** |

本次同时清理了历史遗留脏数据（此前用例写死 `apartment_id=3` 且不清理所产生）：

| 数据 | 条数 | 来源 | 处理 |
| --- | --- | --- | --- |
| `appointments.remark = '数据驱动-正常预约'` | 15 | `test_login_ddt.py` 正向用例 | 删除（用例已改为动态数据） |
| `appointments.remark = 'pytest 自动化提交的看房预约'` | 60 | 早期 `test_core_flow.py` 写死静态房源 | 删除（用例已改为动态数据） |

> 说明：`data.sql` 中的种子预约（`自动化测试种子预约：历史看房预约`）与手工测试产生的数据**未做任何改动**。

### 17.2 Shell 脚本验证（2026-09-19）

新增 `clean.sh` / `run_smoke.sh` / `run_api.sh` 三个脚本，并逐一实测：

| 验证项 | 命令 | 实际结果 |
| --- | --- | --- |
| 换行符检查 | 逐字节统计 CRLF 数量 | 三个脚本 CRLF 均为 **0**（LF），Linux 下不会报 `bad interpreter` |
| 语法校验 | `bash -n clean.sh run_smoke.sh run_api.sh` | 全部 exit=0 |
| `clean.sh` 清理效果 | 清理前统计 → 执行 → 清理后统计 | 清理前 367 个产物文件；执行后**无任何残留** |
| `clean.sh` 幂等性 | 连续执行第 2 次 | 全部提示"目录不存在，无需清理"，exit=0，不报错 |
| `run_smoke.sh` 成功分支 | `bash run_smoke.sh` | `6 passed`，打印"冒烟测试通过"，生成 `allure-report/index.html`，exit=0 |
| `run_api.sh` 成功分支 | `bash run_api.sh` | `13 passed`，打印"接口测试通过"，生成 Allure 报告，exit=0 |
| `run_smoke.sh` 无 allure 场景 | PATH 中不含 allure 时执行 | 打印"未检测到 allure 命令，跳过报告生成"，测试结果判定不受影响 |
| `run_api.sh` 失败分支 | `BASE_URL=http://127.0.0.1:9999 bash run_api.sh` | 打印"接口测试失败，请查看日志"，exit=1，**保留 allure-results（22 个文件）、不生成 allure-report** |

> 失败分支用「把 `BASE_URL` 指向未监听端口」的方式触发（仅改环境变量，未改动任何用例与断言）。

### 17.3 前端启动失败修复的验证（2026-09-18）

修复对象：CI 中 `启动前端服务并等待就绪` 步骤失败
（`npm install` 只装 3 个包 → `sh: 1: vite: Permission denied` → 5173 探测 30 次全失败）。

| 验证项 | 命令 / 方式 | 实际结果 |
| --- | --- | --- |
| 根因定位 | `git ls-files -s frontend/node_modules/.bin/vite` | 权限位为 **100644**，确认无可执行位 |
| 误提交规模 | `git ls-files \| Measure-Object` | node_modules 12941 + target 129 = 13644 个跟踪文件中占 95.8% |
| package.json 检查 | 读取 `frontend/package.json` | `vite`、`@vitejs/plugin-vue` **已在 devDependencies**，无需修改 |
| 新的启动命令 | `node frontend/node_modules/vite/bin/vite.js --version` | 输出 `vite/5.4.21 node-v24.15.0`，exit 0 |
| workflow YAML 语法 | `yaml.safe_load(auto-test.yml)` | 通过，共 **15 个步骤** |
| workflow 内所有 shell 脚本 | `bash -n`（Git Bash 逐个校验 9 个 run 块） | 全部 `[OK]`，失败数 0 |

### 17.4 数据库与服务启动修复的验证（2026-09-18）

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

### 17.5 历史运行记录（2026-09-16）

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