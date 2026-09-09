# Bug 提交清单模板

> 适用范围：基于本项目「测试用例.md」开展的功能/接口/UI 测试所发现缺陷的登记与流转。
> 每条 Bug 对应一份独立记录（可复制下方「Bug 记录模板」填写），并支持按严重程度与模块归类统计。

---

## 一、Bug 清单汇总（概览表）

| Bug编号 | 所属模块 | Bug标题 | 严重程度 | 优先级 | 状态 | 处理人 | 发现版本 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BUG-001 | 合同管理 | 示例 | 严重 | 高 | 待处理 |  | v1.0 |
|  |  |  |  |  |  |  |  |

### 严重程度分级（Severity）
| 级别 | 说明 | 示例如本系统 |
| --- | --- | --- |
| 致命 (Critical) | 系统崩溃、数据丢失、核心链路不可用 | 登录接口 500、合同数据被误删 |
| 严重 (Major) | 主要功能受影响、有规避方案 | 缴费流水与合同状态不一致 |
| 一般 (Minor) | 功能基本可用，局部异常 | 列表缺字段、提示文案错误 |
| 轻微 (Low) | 体验/美观问题 | 排版、错别字 |

### 优先级分级（Priority）
高：立即处理 / 中：本迭代处理 / 低：后续优化

---

## 二、Bug 记录模板（单条）

```
【基本信息】
- Bug编号：BUG-XXX
- 所属模块：□认证 □房源 □预约 □合同 □缴费 □报障 □消息 □投诉 □评价 □收藏 □统计 □其他
- 严重程度：□致命 □严重 □一般 □轻微
- 优先级：  □高 □中 □低
- 发现人 / 测试环境 / 发现版本：______ / ______ / ______
- 关联测试用例：如 APP_005

【Bug标题】
（一句话概括：何人/何操作/何结果，例如：租户提交预约成功但预约列表查询不到）

【前置条件】
（执行前的数据与环境准备，例如：存在一个 start_date~end_date 均已生效的合同）

【重现步骤】(Steps)
1. 
2. 
3. 

【预期结果】(Expected)
（依据测试用例与业务规则得出，例如：应返回 code=200，status='待处理'）

【实际结果】(Actual)
（实际观察到的现象，含 code / message / 报错堆栈）

【截图/日志位置】
- 截图：`test/evidence/BUG-XXX/screenshot1.png`
- 接口日志 / 后端日志：`test/evidence/BUG-XXX/xxx.log`

【备注 / 定位分析】
（可选的初步根因分析，例如：ApartmentController.delete 仅调用 deleteById，缺少业务校验）
```

---

## 三、示例 Bug（可直接登记或仿写）

### BUG-001　【合同管理 / 严重】
- **Bug标题**：删除存在 `生效中` 合同的房源时，接口无业务校验直接报错，前端提示不友好
- **前置条件**：存在一个 `status='生效中'` 的合同，其关联的房源 id 已知
- **重现步骤**
  1. 准备一条 `status='生效中'` 的合同及对应房源；
  2. 以房东身份调用 `DELETE /api/apartments/{apartmentId}`；
  3. 观察返回。
- **预期结果**：存在关联合同时应返回明确业务提示，如「该房源存在生效合同，无法删除」。
- **实际结果**：`ApartmentService.delete()` 直接 `deleteById`，无业务校验；因合同表存在外键引用，抛出数据库约束异常并返回 `code=500`（HTTP 200）的错误结构，前端表现为操作失败且提示信息不明确。
- **定位分析**：参照 `UserService.delete()` 已做了合同/公寓/预约关联校验，但 [ApartmentService.java](file:///d:/projects/Apartment-rental/backend/src/main/java/com/rental/service/ApartmentService.java) 的 `delete` 未做同样的外键保护。

### BUG-002　【认证 / 一般】
- **Bug标题**：业务异常统一返回 HTTP 200，仅凭 body 的 code 区分，不符合 REST 语义
- **重现步骤**
  1. `POST /api/auth/login` 传入错误密码；
  2. 观察 HTTP 状态码与 body。
- **预期结果**：认证失败应返回 HTTP 401/400 语义状态码。
- **实际结果**：HTTP 200 + `body.message="用户名或密码错误"`（由 `ApiResponse.error()` 抛错，未改变 HTTP 状态码）。
- **定位分析**：`AuthController.login` 用 `try/catch` 包裹并返回 `ApiResponse.error(e.getMessage())`，异常被吞入 HTTP 200，影响客户端语义化处理与接口监控。

### BUG-003　【预约 / 一般】
- **Bug标题**：预约状态处理接口可反复修改，缺乏状态机校验
- **前置条件**：存在一条 `status='待处理'` 的预约
- **重现步骤**
  1. 调用 `PUT /api/appointments/{id}/handle?status=已接受&reply=可以看房`；
  2. 再次调用 `PUT /api/appointments/{id}/handle?status=已拒绝&reply=改期`。
- **预期结果**：已处理的预约不应被再次修改。
- **实际结果**：`AppointmentService.handleAppointment()` 直接覆盖 status/reply，任意重复调用均成功，状态可被来回覆盖。
- **定位分析**：参照 `ReviewService.auditReview()` 已有「该评价已审核」守卫，建议对预约处理补充状态校验。

### BUG-004　【认证 / 轻微】
- **Bug标题**：注册接口缺少密码强度与长度校验
- **重现步骤**
  1. `POST /api/auth/register` 传入 `password='1'`；
  2. 观察是否成功注册。
- **预期结果**：密码应有最小长度/复杂度校验并给出明确提示。
- **实际结果**：`AuthController.register` 无密码校验，直接落库（仅加密），弱密码可通过。
- **备注**：可在 `RegisterRequest` 增加校验注解或在 `AuthController` 增加前置判断。

---

## 四、附件规范
- 截图统一存放：`test/evidence/<Bug编号>/`
- 命名规则：`<bug编号>_<步骤序号>_<描述>.png`
- 日志命名：`<bug编号>_<接口名>.log`
- 录制视频（可选）：`<bug编号>_<场景>.mp4`