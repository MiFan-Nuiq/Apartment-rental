# 公寓租赁管理系统 · 自动化测试工程

基于 pytest + Allure 的接口/UI 自动化测试工程，覆盖核心业务链路：
**登录 -> 房源查询 -> 看房预约** 以及登录页 UI 冒烟。

---

## 与实际项目的差异记录（以实际代码为准）

任务描述中所述「现有脚本 test/test_core_flow.py、test/ui_test_login.py 位于 test/ 根目录」与实际不符，实际位置为：
- [test/automation/test_core_flow.py](../automation/test_core_flow.py) —— 接口链路一次性脚本（**保留作备份**，不参与新工程收集）
- [test/automation/ui_test_login.py](../automation/ui_test_login.py) —— UI 登录脚本（**保留作备份**，不参与新工程收集）

UI 框架确认为 **Playwright**（非 Selenium），本工程继续沿用 Playwright。
接口路径、账号密码、端口均以原脚本及后端配置（application.yml：后端端口 8080）为准。

## 目录结构

```
test/automation/
├── apis/                     # 接口层：封装后端 REST 接口
│   ├── login_api.py          #   POST /api/auth/login
│   ├── apartment_api.py      #   GET  /api/apartments（含未携带 token 场景）
│   └── appointment_api.py    #   POST /api/appointments
├── testcases/                # 测试用例层
│   ├── test_core_flow.py     #   登录-房源-预约 核心链路（7 个用例，Allure 注解）
│   └── test_ui_login.py      #   登录页 UI 冒烟（Playwright，Allure 注解）
├── utils/                    # 工具层
│   ├── request_util.py       #   requests.Session 封装（统一 base_url/超时/日志）
│   └── assert_util.py        #   常用断言封装（状态码/业务码/字段/列表）
├── conftest.py               # 共享 fixture：base_url / api_client / auth_token / auth_headers / appointment_data
├── pytest.ini                # pytest 配置（路径、markers、Allure 输出）
├── requirements.txt          # 依赖清单
└── README.md                 # 本说明
```

## 环境要求

| 组件 | 要求 | 说明 |
| --- | --- | --- |
| Python | 3.9+ | 使用 requests / pytest / allure / playwright |
| 后端服务 | Spring Boot，端口 8080 | 需已启动，地址可用 `BASE_URL` 环境变量覆盖 |
| 前端服务 | Vite，端口 5173 | 仅 UI 用例需要，地址可用 `UI_BASE_URL` 覆盖 |
| 浏览器 | Chromium | 仅 UI 用例需要，执行 `playwright install chromium` 安装 |

## 安装依赖

```bash
cd test/automation
pip install -r requirements.txt   # 安装 requests/pytest/allure-pytest/playwright 等
playwright install chromium       # 安装 UI 用例所需的 Chromium 浏览器（仅 UI 需要）
```

## 启动后端与前端

```bash
# 后端（终端 1）：Spring Boot 默认端口 8080
cd backend
mvn spring-boot:run                # 或使用 IDEA 运行启动类

# 前端（终端 2）：Vite 默认端口 5173
cd frontend
npm install                        # 首次需要
npm run dev                        # 启动开发服务器
```

> 后端内置初始化账号（DataInitializer）：`tenant/123456`、`landlord/123456`、`admin/123456`。

## 运行测试

所有命令均在 `test/automation` 目录下执行。

```bash
# ① 运行核心流程冒烟用例（登录-房源-预约，api + smoke 标签）
pytest -m smoke

# ② 运行全部接口用例
pytest -m api

# ③ 运行全部 UI 用例（需前端已启动 + Chromium 已安装）
pytest -m ui

# ④ 运行全部用例
pytest

# ⑤ 指定单个文件
pytest testcases/test_core_flow.py
```

### 通过环境变量覆盖配置

```bash
# 例：切换后端地址与测试账号
$env:BASE_URL="http://192.168.1.10:8080"; $env:TEST_USERNAME="tenant"; $env:TEST_PASSWORD="123456"
pytest -m smoke
```

支持的环境变量：`BASE_URL`、`UI_BASE_URL`、`TEST_USERNAME`、`TEST_PASSWORD`、
`APARTMENT_ID`、`TENANT_ID`、`LANDLORD_ID`、`APPOINTMENT_TIME`、`APPOINTMENT_REMARK`、`HEADLESS`。

> 预约数据默认值：房源 APARTMENT_ID=3、租户 TENANT_ID=3、房东 LANDLORD_ID=2、预约时间 2026-10-01 10:00:00，
> 若本地数据不同请通过环境变量覆盖。

## 生成 Allure 报告

```bash
# ① 运行测试时已通过 pytest.ini 的 addopts 自动产出 allure-results
pytest -m smoke

# ② 生成并打开 HTML 报告
allure serve allure-results
```

> 需先安装 Allure 命令行工具（`pip install allure-pytest` 仅提供插件，报告的 serve 命令来自 Allure CLI）：
> - Windows（含 scoop/choco）或官网下载二进制：https://allure.qatools.ru
> - 或 `winget install Allure.Allure`

## 关键组件说明

### conftest.py（共享 fixture）
| fixture | scope | 返回值 | 说明 |
| --- | --- | --- | --- |
| `base_url` | session | str | 后端地址，环境变量 `BASE_URL` 覆盖 |
| `ui_base_url` | session | str | 前端地址，环境变量 `UI_BASE_URL` 覆盖 |
| `api_client` | session | RequestUtil | 共享 requests.Session 请求工具 |
| `auth_token` | session | str | 登录 token（登录失败会抛出清晰断言） |
| `auth_headers` | session | dict | `{"Authorization": "Bearer <token>"}` |
| `appointment_data` | session | dict | 预约关联数据（房源/租户/房东/时间/备注） |

### utils（工具层）
- `request_util.py`：`RequestUtil(base_url, timeout)`，提供 `get/post/put/delete`，统一拼接 URL、超时与日志。
- `assert_util.py`：`assert_status_code` / `assert_business_code` / `assert_field_exists` / `assert_field_equal` / `assert_list_not_empty`。

### apis（接口层）
统一通过 `api_client` 调用，路径相对 `base_url` 拼接，不写死完整 URL；
每个方法返回 `requests.Response`，由用例层负责 `resp.json()` 与断言。

### markers（pytest.ini 注册）
- `smoke`：核心链路快速回归
- `regression`：边界与异常场景
- `api`：接口用例 | `ui`：UI 用例

## 运行记录

- 最近执行（2026-09-16，后端 8080 与前端 5173 均已启动）：
  - 全量用例：9 passed in 2.24s（接口 7 个 + UI 2 个）
  - 接口核心链路（-m api）：7 passed in 1.00s
  - UI 登录（-m ui，HEADLESS=true）：2 passed in 4.40s
  - allure-results 产物：正常生成（70 个 JSON 文件）