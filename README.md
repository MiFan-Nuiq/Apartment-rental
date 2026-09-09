# 公寓租赁管理系统 · 测试项目

本项目为「公寓租赁管理系统」的测试专项工程，覆盖**手工测试用例、接口自动化、数据库一致性校验、UI 自动化、缺陷管理**五个维度，用于毕业设计的测试作品集展示与日后回归验证。

## 目录结构

```
Apartment-rental/
├── README.md                          # 本说明文件
├── backend/                           # 系统后端源码（Spring Boot，作为被测对象）
├── frontend/                          # 系统前端源码（Vue3，作为被测对象）
└── test/                              # 测试工程（本目录为测试资产所在位置）
    ├── docs/
    │   ├── 测试用例.md                # 全模块手工测试用例（16 章，按业务模块划分）
    │   ├── Bug清单模板.md             # 通用 Bug 登记模板 + 示例 Bug
    │   └── Bug清单_实际发现.md        # 登录模块 Bug 实际发现记录（预置示例，待实际填写）
    ├── automation/
    │   ├── test_core_flow.py          # pytest 接口自动化：登录→房源查询→预约提交
    │   └── ui_test_login.py           # Playwright UI 自动化：登录页冒烟测试
    └── sql/
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

## 测试环境与准备

- 后端：`http://localhost:8080`（Spring Boot），默认初始化账号见 `DataInitializer`：`admin|123456`、`landlord|123456`、`tenant|123456`。
- 前端：`http://localhost:5173`（Vite）。
- 鉴权：除 `/api/auth/**`、`/uploads/**` 外，所有 `/api/**` 需携带 `Authorization: Bearer <token>`。
- 自动化脚本中的`用户 / 房源 / 合同 ID`等参数需按实际测试数据在脚本配置区调整。

## 使用建议

1. 先依据 `测试用例.md` 完成手工冒烟，确认核心模块可用；
2. 再顺序执行 SQL 一致性校验与接口/UI 自动化；
3. 将任一环节发现的问题按 `Bug清单_实际发现.md` 格式登记（登录模块已建示例）；
4. 每次执行自动化后，把结果回填至脚本顶部的 **运行记录** 与 SQL 末尾的 **执行结果摘要**，形成完整测试证据链。