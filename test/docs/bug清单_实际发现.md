# Bug 清单_实际发现

> 用途：登记登录模块在实测过程中**实际发现**的缺陷（区别于「Bug清单模板.md」的通用登记模板）。
> 说明：文件已预填若干登录模块**示例** Bug 供对照（均标注「示例」），
> 请将你实测中真实复现的 Bug 按同样格式追加，并把「示例」字样删除、状态改为「实际」。
> 单条记录格式与「Bug清单模板.md」一致，可直接复制填写。

---

## 一、Bug 清单汇总（概览表）

| Bug编号 | 所属模块 | Bug标题 | 严重程度 | 优先级 | 发现类型 | 状态 | 处理人 | 发现版本 |
| --- | --- | --- | --- | --- | --- | --- |-----|  |
| BUG-DATA-001 | 缴费管理 | 已终止合同关联缴费记录未清理 | 一般 | 中 | 实际 | 待处理 | 王炜垲 | v1.0 |
| BUG-PAY-001 | 缴费管理 | 同一合同可重复创建支付流水，无重复缴费校验 | 严重 | 高 | 实际 | 待处理 | 王炜垲 | v1.0 |
| BUG-PAY-002 | 缴费管理 | 支付金额与合同约定金额不一致时仍可创建成功 | 严重 | 高 | 实际 | 待处理 | 王炜垲 | v1.0 |
| BUG-PAY-003 | 缴费管理 | 支付成功后合同状态无任何联动更新 | 一般 | 中 | 实际 | 待处理 | 王炜垲 | v1.0 |
| BUG-PERM-001 | 权限 | 房东可越权访问管理员专属接口（用户管理） | 严重 | 高 | 实际 | 待处理 | 王炜垲 | v1.0 |
| BUG-PERM-002 | 权限 | 租客可越权访问管理员专属接口（用户管理） | 严重 | 高 | 实际 | 待处理 | 王炜垲 | v1.0 |
| BUG-PERM-003 | 权限 | 租客可越权发布房源（房东专属动作） | 严重 | 高 | 实际 | 待处理 | 王炜垲 | v1.0 |
| BUG-PERM-004 | 权限 | 用户管理接口响应体中携带 BCrypt 密码哈希（敏感信息泄露） | 严重 | 高 | 实际 | 待处理 | 王炜垲 | v1.0 |
| BUG-L001 | 认证 | 错误密码登录提示文案与预期不一致 | 一般 | 中 | 示例 | 待处理 |     | v1.0 |
| BUG-L002 | 认证 | 登录异常统一返回 HTTP 200，语义不清晰 | 一般 | 中 | 示例 | 待处理 |     | v1.0 |
| BUG-L003 | 认证 | 注册接口支持弱密码，无强度校验 | 轻微 | 低 | 示例 | 待处理 |     | v1.0 |
| BUG-L004 | 认证 | 登录接口对参数缺失未做提示 | 轻微 | 低 | 示例 | 待处理 |     | v1.0 |

### 严重程度分级
| 级别 | 说明 |
| --- | --- |
| 致命 (Critical) | 系统崩溃、数据丢失、核心链路不可用 |
| 严重 (Major) | 主要功能受影响、有规避方案 |
| 一般 (Minor) | 功能基本可用，局部异常 |
| 轻微 (Low) | 体验/美观问题 |

---

## 二、登录模块 Bug 记录模板（单条，复制填写）

```
【基本信息】
- Bug编号：BUG-LXXX
- 所属模块：认证
- 严重程度：□致命 □严重 □一般 □轻微
- 优先级：  □高 □中 □低
- 发现类型：□实际 □示例
- 发现人 / 测试环境 / 发现版本：______ / ______ / ______
- 关联测试用例：如 AUTH_006

【Bug标题】
（一句话概括）

【前置条件】
（登录前需要的数据与环境准备）

【重现步骤】(Steps)
1.
2.
3.

【预期结果】(Expected)
（依据测试用例 AUTH_XXX 与业务规则得出）

【实际结果】(Actual)
（实际观察到的现象，含 HTTP 状态码 / code / message）

【截图/日志位置】
- 截图：`test/evidence/BUG-LXXX/screenshot.png`
- 接口/后端日志：`test/evidence/BUG-LXXX/xxx.log`

【备注 / 定位分析】
（可选的初步根因分析）
```

---

## 三、登录模块 Bug（示例，仅供对照）

### BUG-L001　【认证 / 一般】　※ 标注类型：示例
- **Bug标题**：错误密码登录时前端提示文案与后端返回不一致
- **前置条件**：存在用户 `tenant`（密码 123456）
- **重现步骤**
  1. 打开登录页 `http://localhost:5173/login`；
  2. 输入用户名 `tenant`、错误密码 `wrong`；
  3. 点击「登录」并观察页面提示。
- **预期结果**：展示与后端一致的错误提示（后端 `AuthController.login` 返回 message="用户名或密码错误"）。
- **实际结果**：前端 `handleLogin` 的 catch 分支统一展示「用户名或密码错误」，此时后端因 `findByUsername` 正常返回该文案一致，无明显异常；但若出现网络/超时等非业务错误，前端同样被识别为「用户名或密码错误」，提示与真实原因不符。
- **定位分析**：`Login.vue` 的 `handleLogin().catch()` 未区分业务错误与网络错误，统一归为密码错误。

---
## 四、实际发现Bug

### BUG-DATA-001 已终止合同关联缴费记录未清理
- **发现时间**：2026-09-10
- **发现人**：王炜垲
- **所属模块**：缴费管理 / 合同管理
- **严重程度**：一般
- **优先级**：中

#### 前置条件
合同编号 `HT2026031600`，合同 ID `15`，状态为“已终止”

#### 重现步骤
1. 查询 `contracts` 表，确认合同状态为“已终止”；
2. 使用 `contract_id = 15` 在 `payments` 表中检索关联缴费记录；
3. 发现存在一条缴费记录（ID=5），状态为“已支付”。

#### 预期结果
合同终止后，关联缴费记录应同步清理或状态变更为“已失效”。

#### 实际结果
合同已终止，仍存在一条已支付的水电费缴费记录：
- payment_type：水电费
- amount：1000.00
- payment_date：2026-03-31
- status：已支付

#### 问题截图
`test/evidence/BUG-DATA-001/sql_result_01.png`
`test/evidence/BUG-DATA-001/sql_result_02.png`


### BUG-PAY-001 同一合同可重复创建支付流水，无重复缴费校验
- **发现时间**：2026-10-05
- **发现人**：王炜垲
- **所属模块**：缴费管理
- **严重程度**：严重
- **优先级**：高

#### 前置条件
存在一条有效合同（本用例动态创建，月租 2000.00）

#### 重现步骤
1. 对同一合同 `POST /api/payments` 创建第一条支付流水（金额 2000.00），返回成功；
2. 对**同一合同**再次 `POST /api/payments` 创建第二条支付流水（金额、类型、日期完全相同）；
3. 观察第二次请求的响应。

#### 预期结果
同一合同、同一缴费类型/周期已存在缴费记录时，后端应做重复缴费校验并返回业务错误，不允许重复创建。

#### 实际结果
第二次请求同样返回 **HTTP 200 / code 200**，并成功落库（两条流水均标记"待支付"，各自生成缴费单号）。
即同一合同可被无限次重复创建缴费流水，存在重复收费与账目重复的风险。

#### 关联测试用例
`test/automation/testcases/test_payment.py::TestPayment::test_duplicate_payment_rejected`（当前 xfail）

#### 复现命令
```bash
cd test/automation
pytest testcases/test_payment.py::TestPayment::test_duplicate_payment_rejected --runxfail -q
```

#### 定位分析
`backend/.../service/PaymentService.java` 的 `save(Payment)` 只做了两件事：
`paymentNo` 为空时自动生成单号，然后直接 `paymentRepository.save(payment)`，
**没有任何业务校验**（既未按 `contract_id` + `payment_type` 查询已有流水，也无唯一约束）。
`payments` 表也未对"同一合同同类型缴费"设置唯一索引。

---

### BUG-PAY-002 支付金额与合同约定金额不一致时仍可创建成功
- **发现时间**：2026-10-05
- **发现人**：王炜垲
- **所属模块**：缴费管理
- **严重程度**：严重
- **优先级**：高

#### 前置条件
存在一条有效合同，`monthlyRent = 2000.00`

#### 重现步骤
1. 读取合同月租（2000.00）；
2. `POST /api/payments` 创建支付流水，但 `amount` 传 **1.00**（与合同月租严重不符）；
3. 观察请求响应与数据库落库金额。

#### 预期结果
支付金额应与合同约定金额（月租/押金等）一致；不一致时后端应拒绝并返回业务错误。

#### 实际结果
请求返回 **HTTP 200 / code 200**，`payments` 表成功写入一条 `amount = 1.00` 的租金流水。
金额完全由前端传入，后端不做任何比对，存在少缴/错缴无法拦截的资金风险。

#### 关联测试用例
`test/automation/testcases/test_payment.py::TestPayment::test_payment_amount_mismatch_rejected`（当前 xfail）

#### 复现命令
```bash
cd test/automation
pytest testcases/test_payment.py::TestPayment::test_payment_amount_mismatch_rejected --runxfail -q
```

#### 定位分析
`PaymentService.save(Payment)` 未读取关联合同（`payment.getContract()`）的 `monthlyRent`/`deposit`，
也没有任何金额比对逻辑，`amount` 直接以请求体原值落库。

---

### BUG-PAY-003 支付成功后合同状态无任何联动更新
- **发现时间**：2026-10-05
- **发现人**：王炜垲
- **所属模块**：缴费管理 / 合同管理
- **严重程度**：一般
- **优先级**：中

#### 前置条件
存在一条状态为"待确认"的合同及其待支付流水

#### 重现步骤
1. 创建合同（状态"待确认"）与一条"待支付"流水；
2. 执行支付动作：`PUT /api/payments/{id}`，将 `status` 置为"已支付"并写入 `payTime`；
3. 查询 `GET /api/contracts/{id}` 与 `contracts` 表，观察合同状态。

#### 预期结果
支付完成后，合同状态应发生联动更新（例如流转为"已到期"或进入与缴费进度对应的状态），
使合同生命周期与缴费进度保持一致。

#### 实际结果
流水状态已变为"已支付"、`pay_time` 已写入，但**合同状态仍停留在初始的"待确认"**，
缴费与合同状态之间完全没有联动。

#### 关联测试用例
`test/automation/testcases/test_payment.py::TestPayment::test_contract_status_updated_after_payment`（当前 xfail）

#### 复现命令
```bash
cd test/automation
pytest testcases/test_payment.py::TestPayment::test_contract_status_updated_after_payment --runxfail -q
```

#### 定位分析
`PaymentService` 只依赖 `PaymentRepository`，未注入 `ContractService`/`ContractRepository`，
`save` 与 `update` 都不会回写合同状态。
合同状态目前只由 `ContractService` 自身维护（定时任务置"已到期"、`terminate` 置"已终止"），
与缴费模块零耦合。

#### 备注
本条属于"业务规则缺失"，是否应当联动取决于产品定义；
若产品确认"缴费不影响合同状态"，则应收敛该测试用例的预期（去掉 xfail 并改为断言状态不变）。


### BUG-PERM-001 房东可越权访问管理员专属接口（用户管理）
- **发现时间**：2026-10-05
- **发现人**：王炜垲
- **所属模块**：权限
- **严重程度**：严重
- **优先级**：高

#### 前置条件
存在房东账号 `landlord/123456`（`users.id=2`，角色 `LANDLORD`）

#### 重现步骤
1. 用 `landlord` 账号登录，取得 token；
2. 携带该 token 调用**管理员专属接口** `GET /api/users`（用户管理）；
3. 观察响应。

#### 预期结果
房东不属于管理员角色，调用管理员专属接口应被拒绝（返回 403 或业务错误），
符合"不同角色能调用的接口不同，管理员专属接口不应被房东调用"的权限设计。

#### 实际结果
请求返回 **HTTP 200 / code 200**，并完整返回了全部 3 个用户的账号数据
（含用户名、真实姓名、手机号、角色），越权成功。

#### 关联测试用例
`test/automation/testcases/test_permission.py::TestPermission::test_landlord_cannot_access_admin_endpoint`（当前 xfail）

#### 复现命令
```bash
cd test/automation
pytest testcases/test_permission.py::TestPermission::test_landlord_cannot_access_admin_endpoint --runxfail -q
```

#### 定位分析
`backend/.../config/SecurityConfig.java` 的授权规则只有：
```java
.antMatchers("/api/auth/**").permitAll()
.antMatchers("/uploads/**").permitAll()
.antMatchers("/api/**").authenticated()   // 只校验"是否登录"，不校验角色
.anyRequest().permitAll();
```
全项目**没有任何基于角色的授权**：搜索不到 `hasRole` / `hasAuthority` / `@PreAuthorize`；
`JwtAuthenticationFilter` 构建认证对象时传入的是**空权限集合** `new ArrayList<>()`，
即令牌里的角色信息（登录响应中的 `role`）从未被写入 SecurityContext。
因此"只登录、不鉴权"，任何角色都能访问任何 `/api/**` 接口。

---

### BUG-PERM-002 租客可越权访问管理员专属接口（用户管理）
- **发现时间**：2026-10-05
- **发现人**：王炜垲
- **所属模块**：权限
- **严重程度**：严重
- **优先级**：高

#### 前置条件
存在租客账号 `tenant/123456`（`users.id=3`，角色 `TENANT`）

#### 重现步骤
1. 用 `tenant` 账号登录，取得 token；
2. 携带该 token 调用**管理员专属接口** `GET /api/users`；
3. 观察响应。

#### 预期结果
租客调用管理员专属接口应被拒绝（返回 403 或业务错误）。

#### 实际结果
请求返回 **HTTP 200 / code 200**，完整返回全部用户数据，越权成功。
另实测 `GET /api/statistics/admin`（管理员统计）用租客 token 调用同样返回 200/code 200。

#### 关联测试用例
`test/automation/testcases/test_permission.py::TestPermission::test_tenant_cannot_access_admin_endpoint`（当前 xfail）

#### 复现命令
```bash
cd test/automation
pytest testcases/test_permission.py::TestPermission::test_tenant_cannot_access_admin_endpoint --runxfail -q
```

#### 定位分析
同 BUG-PERM-001，根因是"只认证、不鉴权"。属系统性问题，
影响面为全部 `/api/**` 接口，而非单个接口的遗漏。

---

### BUG-PERM-003 租客可越权发布房源（房东专属动作）
- **发现时间**：2026-10-05
- **发现人**：王炜垲
- **所属模块**：权限
- **严重程度**：严重
- **优先级**：高

#### 前置条件
存在租客账号 `tenant/123456`

#### 重现步骤
1. 用 `tenant` 账号登录，取得 token；
2. 携带该 token 调用**房东专属接口** `POST /api/apartments`（房源发布）；
3. 观察响应，并查询数据库确认房源是否真的落库。

#### 预期结果
租客不具备房源发布权限，调用房东专属接口应被拒绝（返回 403 或业务错误）。

#### 实际结果
请求返回 **HTTP 200 / code 200**，并**真实创建出一条房源**（实测生成 `apartments.id=91`，
`name=自动化临时房源-...-perm`、`status=空置`、`landlord_id=2`）。
即租客不仅能越权读，还能**越权写**，可直接污染房源数据。

#### 关联测试用例
`test/automation/testcases/test_permission.py::TestPermission::test_tenant_cannot_publish_apartment`（当前 xfail）

#### 复现命令
```bash
cd test/automation
pytest testcases/test_permission.py::TestPermission::test_tenant_cannot_publish_apartment --runxfail -q
```

#### 定位分析
同 BUG-PERM-001/002。`ApartmentController#save` 未注入/校验当前登录用户角色，
Service 层也没有归属校验（未校验 `apartment.landlord.id` 是否等于当前登录用户），
因此任意登录用户都能以任意 `landlord_id` 发布房源。

---

### BUG-PERM-004 用户管理接口响应体中携带 BCrypt 密码哈希（敏感信息泄露）
- **发现时间**：2026-10-05
- **发现人**：王炜垲
- **所属模块**：权限 / 敏感数据保护
- **严重程度**：严重
- **优先级**：高

#### 前置条件
任意可登录账号（当前实测 `admin` / `landlord` / `tenant` 均可，见 BUG-PERM-001/002）

#### 重现步骤
1. 登录取得 token；
2. 调用 `GET /api/users`；
3. 观察响应体中每个用户对象的 `password` 字段。

#### 预期结果
用户管理接口不应返回密码相关字段（即使是哈希值）；应通过 `@JsonIgnore`
或在 DTO 中剔除 `password`，避免敏感信息外泄。

#### 实际结果
响应中每个用户都带有**明文可见的 BCrypt 密码哈希**，例如：
```
"username": "admin",
"password": "$2a$10$ciZ2htni/HqazRxVlTD11.EKta54TCPxeZqlKkHIhnPU0vw7VLP1K",
"role": "ADMIN"
```
三个种子账号（admin/landlord/tenant，密码均为 123456）的哈希全部返回，
攻击者可离线做彩虹表/字典暴力破解。

#### 关联测试用例
`test/automation/testcases/test_permission.py::TestSensitiveDataProtection::test_user_endpoint_does_not_leak_password`（当前 xfail）

#### 复现命令
```bash
# 方式一：直接跑自动化用例（--runxfail 可看到真实的断言失败信息）
cd test/automation
pytest testcases/test_permission.py::TestSensitiveDataProtection::test_user_endpoint_does_not_leak_password --runxfail -q

# 方式二：手工复现
# 1) 登录拿 token
curl -s -X POST http://localhost:8080/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'
# 2) 调用用户管理接口，观察响应中的 password 字段
curl -s http://localhost:8080/api/users -H "Authorization: Bearer <上一步返回的 token>"
```

#### 定位分析
`UserController#findAll` / `findById` 直接返回 JPA 实体 `User`，
而 `User` 实体的 `password` 字段没有任何序列化屏蔽
（无 `@JsonIgnore`、也没有使用 DTO 转换），导致持久层字段被直接序列化进响应体。
`AuthController#login` 返回的是 `LoginResponse` DTO，因此登录接口不受影响——
问题集中在直接返回实体的接口上。


## 附：模板对照
- 追加实际记录时，`发现类型` 填「实际」，`关联测试用例` 引用 `测试用例.md` 中 AUTH_ 编号。
- 截图/日志统一存放到 `test/evidence/<Bug编号>/`。