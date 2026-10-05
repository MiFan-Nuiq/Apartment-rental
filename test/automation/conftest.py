# -*- coding: utf-8 -*-
"""
conftest.py —— pytest 全局共享 fixture、配置与钩子

集中管理：
    - 配置常量：后端/前端地址、登录账号、业务数据 ID、数据库连接信息（均可环境变量覆盖）
    - 接口 fixture：base_url / api_client / auth_token / auth_headers / appointment_data
    - 动态数据 fixture：unique_suffix / temp_apartment / temp_appointment（用例级隔离 + 自动清理）
    - 数据库 fixture：db_connection（session 级，pymysql 直连 MySQL）
    - UI fixture：browser（module 级浏览器）/ ui_page（用例级页面，含 trace 录制）
    - 失败钩子：pytest_runtest_makereport —— UI 用例失败时自动截图并保存 Playwright trace
    - 清理钩子：pytest_sessionstart / pytest_sessionfinish —— 会话开始与结束时各兜底清理一次
      残留的动态测试数据（应对"用例中途崩溃 / 进程被 kill，最终器来不及执行"导致的脏数据）

测试数据管理策略（静态打底 + 动态隔离）：
    - 静态种子数据（test/sql/data.sql）：登录账号、基础房源（id=1/2/3）、合同/流水等公共稳定数据；
    - 动态 fixture（本文件）：用例运行期通过接口临时创建的房源与预约，用例结束立即清理。
      这样用例之间互不依赖、互不污染，也不会给数据库留下脏数据。

注意：登录账号、数据库密码等敏感/易变配置统一在此处集中管理，避免散落多个文件。
"""

import os
import uuid
from datetime import datetime
from pathlib import Path

import pytest

from apis.apartment_api import create_apartment, delete_apartment
from apis.appointment_api import create_appointment, delete_appointment
from apis.login_api import get_token
from utils.db_util import DBUtil
from utils.request_util import RequestUtil

# ==================== 目录常量 ====================
AUTOMATION_DIR = Path(__file__).resolve().parent       # 工程根目录 test/automation
SCREENSHOTS_DIR = AUTOMATION_DIR / "screenshots"        # UI 失败截图输出目录
TRACES_DIR = AUTOMATION_DIR / "traces"                  # Playwright trace 输出目录

# ==================== 全局配置（可通过环境变量覆盖） ====================
BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")          # 后端服务基础地址
UI_BASE_URL = os.getenv("UI_BASE_URL", "http://localhost:5173")    # 前端页面基础地址
USERNAME = os.getenv("TEST_USERNAME", "tenant")       # 登录用户名（DataInitializer 初始化账号）
PASSWORD = os.getenv("TEST_PASSWORD", "123456")       # 登录密码
APARTMENT_ID = int(os.getenv("APARTMENT_ID", "3"))    # 目标房源 id（需真实存在且与房东匹配）
TENANT_ID = int(os.getenv("TENANT_ID", "3"))          # 租户用户 id（tenant 账号对应 userId）
LANDLORD_ID = int(os.getenv("LANDLORD_ID", "2"))      # 房东用户 id（landlord 账号对应 userId）
APPOINTMENT_TIME = os.getenv("APPOINTMENT_TIME", "2026-10-01 10:00:00")  # 预约时间
REMARK = os.getenv("APPOINTMENT_REMARK", "pytest 自动化提交的看房预约")   # 预约备注
# ======================================================================


# ==================== UI 运行时状态（供失败钩子读取） ====================
# 记录当前用例的 Playwright page/context 与 trace 落盘状态，钩子据此截图与保存 trace
_UI_STATE: dict = {}


@pytest.fixture(scope="session")
def base_url() -> str:
    """
    session 级 fixture：后端服务基础地址。

    依赖:
        无
    返回:
        后端基础地址字符串（取模块常量 BASE_URL，可用环境变量 BASE_URL 覆盖）
    """
    return BASE_URL


@pytest.fixture(scope="session")
def ui_base_url() -> str:
    """
    session 级 fixture：前端页面基础地址（供 UI 用例使用）。

    依赖:
        无
    返回:
        前端基础地址字符串（取模块常量 UI_BASE_URL，可用环境变量 UI_BASE_URL 覆盖）
    """
    return UI_BASE_URL


@pytest.fixture(scope="session")
def api_client(base_url: str) -> RequestUtil:
    """
    session 级 fixture：全局共享的 HTTP 请求工具。

    依赖:
        base_url: 后端基础地址
    返回:
        RequestUtil 实例，内部复用 requests.Session（长连接）
    """
    # 全工程共用同一个请求会话，接口层通过该实例拼接 URL
    return RequestUtil(base_url)


@pytest.fixture(scope="session")
def auth_token(api_client: RequestUtil) -> str:
    """
    session 级 fixture：登录 token。

    依赖:
        api_client: 请求工具
    返回:
        登录成功返回的 token 字符串
    异常:
        AssertionError: 登录失败（HTTP 状态码/业务码/缺失 token 均会触发清晰报错）
    """
    # 登录失败时 get_token 内部断言会给出明确错误信息，便于快速定位环境问题
    return get_token(api_client, USERNAME, PASSWORD)


@pytest.fixture(scope="session")
def auth_headers(auth_token: str) -> dict:
    """
    session 级 fixture：携带 Bearer token 的鉴权请求头。

    依赖:
        auth_token: 登录 token
    返回:
        形如 {"Authorization": "Bearer <token>"} 的请求头字典
    """
    # 统一封装鉴权头，接口层直接作为 headers 传入 requests
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="session")
def appointment_data() -> dict:
    """
    session 级 fixture：提交预约所需的关联业务数据。

    依赖:
        无
    返回:
        包含预约时间、备注及房源/租户/房东 ID 的字典
    """
    # 数据统一在此维护，测试用例直接引用，便于批量调整测试数据
    return {
        "apartment_id": APARTMENT_ID,
        "tenant_id": TENANT_ID,
        "landlord_id": LANDLORD_ID,
        "appointment_time": APPOINTMENT_TIME,
        "remark": REMARK,
    }


# ==================== 动态测试数据 fixture（用例级隔离 + 用例后自动清理） ====================
# 设计思路：
#   静态种子数据（test/sql/data.sql）负责"公共、稳定"的数据（登录账号、基础房源、权限）；
#   业务操作产生的"会变化"的数据（临时房源、临时预约）一律由下面的 fixture 动态创建，
#   并在用例结束后立即清理，从而做到：用例之间数据隔离、互不污染、库里不留脏数据。


def safe_delete(delete_func, client: RequestUtil, token: str, record_id: int, label: str):
    """
    安全删除辅助函数：删除失败只打印中文警告，不抛异常。

    用途:
        供 fixture 与用例的 finalizer 复用，保证动态数据被清理，
        且清理失败不会掩盖原始断言错误（避免连锁失败）。

    参数:
        delete_func: 删除接口函数（delete_apartment / delete_appointment）
        client: RequestUtil 请求工具实例
        token: 登录 token
        record_id: 待删除记录 id
        label: 中文标签，用于日志（如"临时房源"/"临时预约"）
    返回:
        无
    """
    try:
        resp = delete_func(client, token, record_id)
        body = resp.json() if resp.status_code == 200 else {}
        if resp.status_code != 200 or body.get("code") != 200:
            # 常见原因：该房源下仍挂着预约（外键约束），提示人工确认是否有残留
            print(f"[警告] 清理{label} id={record_id} 失败：HTTP {resp.status_code}，响应：{resp.text}")
    except Exception as e:
        # 绝不静默吞掉：打印警告提示人工确认数据库是否残留该条动态数据
        print(f"[警告] 清理{label} id={record_id} 异常：{e}，请人工确认该数据是否残留")


@pytest.fixture(scope="function")
def dynamic_data_cleaner(request, api_client: RequestUtil, auth_headers: dict):
    """
    用例级 fixture：返回"登记动态数据清理"的函数，供用例清理自己创建的数据。

    依赖:
        request: pytest 内置 fixture（用于注册 finalizer）
        api_client: 请求工具
        auth_headers: 携带 Bearer token 的鉴权头
    返回:
        register(delete_func, record_id, label) -> None
        调用后该记录会在用例结束（含失败）时被删除
    说明:
        为什么需要它：用例体内自己创建的预约并不属于任何 fixture，
        若不登记清理，会在 temp_apartment 删除房源时触发外键约束（HTTP 500），
        导致房源与预约双双残留。finalizer 的执行顺序为后进先出，
        因此"用例创建的预约"会先于"fixture 的临时房源"被删除。
    """
    token = auth_headers["Authorization"].replace("Bearer ", "")

    def register(delete_func, record_id: int, label: str):
        """
        登记一条动态数据的清理动作。

        参数:
            delete_func: 删除接口函数（delete_apartment / delete_appointment）
            record_id: 待删除记录 id
            label: 中文标签，用于日志
        返回:
            无
        """
        # 使用 finalizer 而非 finally：断言失败时同样会执行清理
        request.addfinalizer(lambda: safe_delete(delete_func, api_client, token, record_id, label))

    return register


def build_temp_apartment_payload(name: str) -> dict:
    """
    构造临时房源的请求体（字段与后端 Apartment 实体保持一致）。

    用途:
        供 temp_apartment fixture 与"需要按需自建临时房源"的用例（如数据驱动用例）复用，
        保证动态房源的字段口径统一。

    参数:
        name: 房源名称（需自带唯一后缀）
    返回:
        可直接传给 POST /api/apartments 的字典
    """
    return {
        "name": name,
        "address": f"自动化测试虚拟地址-{name}",
        "building": "自动化A座",
        "unit": "1单元",
        "floor": "1",
        "area": 60.00,
        "monthlyRent": 1999.00,
        # 项目真实房源状态枚举为"空置"（不存在"可预约"）
        "status": "空置",
        "auditStatus": "审核通过",
        "description": f"pytest 动态数据，用例结束自动清理（标识：{name}）",
        # landlord 以嵌套对象传入（JPA 多对一关联），房东 id 取自静态数据
        "landlord": {"id": LANDLORD_ID},
    }


@pytest.fixture(scope="function")
def unique_suffix() -> str:
    """
    用例级 fixture：生成不重复的测试数据标识后缀。

    依赖:
        无
    返回:
        形如 "20260919103000-3f9a1c2b" 的唯一字符串（时间戳 + 8 位短 uuid）
    说明:
        时间戳便于人工判断数据产生时间，短 uuid 保证同一秒内并发执行（pytest-xdist）也不重复；
        用于拼接临时房源标题、备注等，避免与历史数据或其它用例的数据撞车。
    """
    # 时间戳（可读、可排序） + uuid4 前 8 位（并发下仍唯一）
    return f"{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def temp_apartment(api_client: RequestUtil, auth_headers: dict, unique_suffix: str) -> dict:
    """
    用例级 fixture：动态创建一条临时房源，用例结束后自动清理。

    依赖:
        api_client: 请求工具
        auth_headers: 携带 Bearer token 的鉴权头
        unique_suffix: 唯一后缀（保证房源标题不重复）
    返回:
        dict，包含:
            - id: 新建房源的主键 id（用例据此提交预约、校验落库）
            - name: 新建房源名称（含唯一后缀，便于识别残留数据）
            - landlord_id: 关联的房东用户 id（取自静态数据的 LANDLORD_ID）
            - suffix: 本次数据的唯一后缀
            - raw: 创建接口返回的原始房源数据
    清理逻辑:
        用例结束（含失败）后调用 DELETE /api/apartments/{id} 删除该房源；
        清理失败不抛异常（避免连锁失败），但会打印中文警告，提示人工确认残留数据。
    异常:
        AssertionError: 创建接口 HTTP 状态码 / 业务码异常，或未返回房源 id
    """
    # 从统一鉴权头中取出裸 token（接口层签名要求传 token 字符串）
    token = auth_headers["Authorization"].replace("Bearer ", "")

    # 标题与描述均带唯一后缀：既避免重名，也便于事后用 SQL 检索是否残留
    name = f"自动化临时房源-{unique_suffix}"
    # 请求体字段与后端 Apartment 实体保持一致（统一由 build_temp_apartment_payload 构造）
    payload = build_temp_apartment_payload(name)

    # ---------- 用例前：创建临时房源 ----------
    resp = create_apartment(api_client, token, payload)
    assert resp.status_code == 200, f"创建临时房源失败：HTTP {resp.status_code}，响应：{resp.text}"
    body = resp.json()
    assert body.get("code") == 200, f"创建临时房源失败：{body}"
    data = body.get("data") or {}
    apartment_id = data.get("id")
    assert apartment_id, f"创建临时房源成功但未返回 id，响应：{body}"

    # 交给用例使用
    yield {
        "id": apartment_id,
        "name": name,
        "landlord_id": LANDLORD_ID,
        "suffix": unique_suffix,
        "raw": data,
    }

    # ---------- 用例后：清理临时房源 ----------
    # 清理失败只打印中文警告，不抛异常（避免连锁失败）
    safe_delete(delete_apartment, api_client, token, apartment_id, "临时房源")


@pytest.fixture(scope="function")
def temp_appointment(
    api_client: RequestUtil,
    auth_headers: dict,
    appointment_data: dict,
    temp_apartment: dict,
) -> dict:
    """
    用例级 fixture：在临时房源上动态创建一条临时预约，用例结束后自动清理。

    依赖:
        api_client: 请求工具
        auth_headers: 携带 Bearer token 的鉴权头
        appointment_data: 会话级预约基础数据（租户/房东 id、预约时间）
        temp_apartment: 用例级临时房源，预约必须挂在这条房源上（避免使用静态 id）
    返回:
        dict，包含:
            - id: 新建预约的主键 id
            - apartment_id: 关联的临时房源 id
            - tenant_id / landlord_id / appointment_time: 本次预约的业务字段
            - remark: 本次预约备注（含唯一后缀，便于识别残留数据）
            - raw: 创建接口返回的原始预约数据
    清理逻辑:
        用例结束（含失败）后调用 DELETE /api/appointments/{id} 删除该预约；
        由于 fixture 清理顺序为后进先出，预约先于临时房源被删除，不会触发外键约束；
        清理失败同样只打印中文警告，不抛异常。
    异常:
        AssertionError: 创建预约接口 HTTP 状态码 / 业务码异常，或未返回预约 id
    """
    token = auth_headers["Authorization"].replace("Bearer ", "")
    # 备注追加唯一后缀，便于定位本次用例产生的预约数据
    remark = f"{appointment_data['remark']}（{temp_apartment['suffix']}）"

    # ---------- 用例前：创建临时预约（挂在临时房源的 apartment_id 上） ----------
    resp = create_appointment(
        api_client,
        token=token,
        apartment_id=temp_apartment["id"],
        tenant_id=appointment_data["tenant_id"],
        landlord_id=appointment_data["landlord_id"],
        appointment_time=appointment_data["appointment_time"],
        remark=remark,
    )
    assert resp.status_code == 200, f"创建临时预约失败：HTTP {resp.status_code}，响应：{resp.text}"
    body = resp.json()
    assert body.get("code") == 200, f"创建临时预约失败：{body}"
    data = body.get("data") or {}
    appointment_id = data.get("id")
    assert appointment_id, f"创建临时预约成功但未返回 id，响应：{body}"

    yield {
        "id": appointment_id,
        "apartment_id": temp_apartment["id"],
        "tenant_id": appointment_data["tenant_id"],
        "landlord_id": appointment_data["landlord_id"],
        "appointment_time": appointment_data["appointment_time"],
        "remark": remark,
        "raw": data,
    }

    # ---------- 用例后：清理临时预约 ----------
    # 清理失败只打印中文警告，不抛异常（避免连锁失败）
    safe_delete(delete_appointment, api_client, token, appointment_id, "临时预约")


@pytest.fixture(scope="session")
def db_connection() -> DBUtil:
    """
    session 级 fixture：MySQL 数据库连接工具（供数据库校验用例使用）。

    依赖:
        无（连接信息来自环境变量，默认值对齐后端 application.yml）
    返回:
        DBUtil 实例，session 内复用同一长连接
    异常:
        pytest.fail：数据库连接失败时给出明确提示（提示需启动 MySQL 或配置 DB_* 环境变量）
    """
    try:
        # 建立数据库连接（默认 localhost:3306/apartment_rental_db）
        db = DBUtil()
    except Exception as e:
        # 连接失败直接 fail，并提示配置方式，避免用例因“连不上库”而含糊失败
        pytest.fail(
            f"数据库连接失败：{e}\n"
            f"请确认 MySQL 已启动，或通过环境变量 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME 覆盖连接信息"
        )
    yield db          # 交给用例使用
    db.close()         # session 结束后统一释放连接


@pytest.fixture(scope="module")
def browser():
    """
    module 级 fixture：启动一个 Playwright 浏览器实例，供本模块全部 UI 用例复用。

    依赖:
        需已安装 playwright（pip install playwright）并执行 playwright install chromium
    返回:
        Playwright Browser 对象
    异常:
        未安装 playwright 时跳过用例（Skipped）
    """
    # 延迟导入：未安装 playwright 时仅跳过 UI 用例，不影响接口/数据库用例的收集与执行
    pytest.importorskip("playwright", reason="未安装 playwright，跳过 UI 用例")
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        # HEADLESS=true 时无头运行（CI 场景），默认有头便于本地观察
        b = p.chromium.launch(headless=os.getenv("HEADLESS", "false").lower() == "true")
        yield b
        b.close()


@pytest.fixture
def ui_page(browser):
    """
    用例级 fixture：创建一个带 trace 录制的浏览器页面。

    依赖:
        browser: module 级浏览器实例
    返回:
        Playwright Page 对象（页面级隔离，避免用例间互相影响）
    异常:
        playwright.sync_api.Error：创建上下文或页面失败
    """
    # 每个用例独立 context，实现页面级隔离
    context = browser.new_context()
    # 开启 trace 录制（含截图与 DOM 快照），用例失败时由钩子落盘
    context.tracing.start(screenshots=True, snapshots=True, sources=True)
    page = context.new_page()
    # 注册到全局状态，供失败钩子读取当前用例的页面
    _UI_STATE["page"] = page
    _UI_STATE["context"] = context
    _UI_STATE["trace_saved"] = False
    yield page
    # 用例结束清理：关闭上下文并清空状态（trace 已在钩子中或此处结束）
    try:
        if not _UI_STATE.get("trace_saved"):
            # 用例成功时正常结束 trace（不落盘），避免残留录制状态
            context.tracing.stop()
        context.close()
    finally:
        _UI_STATE.clear()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    pytest 钩子：用例失败时自动截图并保存 Playwright trace。

    作用:
        - 仅处理用例主体（call 阶段）的失败，避免 setup/teardown 误触发；
        - UI 用例失败：把当前页面截图保存到 screenshots/，trace 保存到 traces/；
        - 截图与 trace 路径会追加到报告 sections，便于在终端与 Allure 中定位。
    参数:
        item: 当前测试项
        call: 当前执行阶段（setup/call/teardown）
    返回:
        无（hookwrapper 通过 yield 获取结果）
    异常:
        无（内部捕获异常，不影响原始测试结果）
    """
    outcome = yield
    report = outcome.get_result()

    # 只关注用例执行阶段（call）的失败，且必须存在已注册的 UI 页面
    if report.when != "call" or not report.failed:
        return
    page = _UI_STATE.get("page")
    context = _UI_STATE.get("context")
    if page is None or context is None:
        return  # 非 UI 用例，无需截图/trace

    # 生成安全文件名（基于用例名，替换掉路径分隔符）
    safe_name = item.name.replace("/", "_").replace("::", "_").replace("[", "_").replace("]", "")

    # ---------- 失败截图 ----------
    try:
        SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        shot_path = SCREENSHOTS_DIR / f"{safe_name}.png"
        page.screenshot(path=str(shot_path))
        report.sections.append(("UI 失败截图", str(shot_path)))
    except Exception as e:
        report.sections.append(("UI 失败截图", f"截图失败：{e}"))

    # ---------- Playwright trace ----------
    try:
        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        trace_path = TRACES_DIR / f"{safe_name}.zip"
        context.tracing.stop(path=str(trace_path))
        _UI_STATE["trace_saved"] = True  # 标记已结束，避免 fixture 重复 stop
        report.sections.append(("Playwright Trace", str(trace_path)))
    except Exception as e:
        report.sections.append(("Playwright Trace", f"trace 保存失败：{e}"))


# ==================== 会话结束兜底清理（防脏数据残留） ====================
# 背景（为什么需要它）：
#   temp_apartment / temp_appointment 等动态数据依赖 fixture 的 yield 之后代码清理，
#   用例体内自建的数据依赖 request.addfinalizer（后进先出）清理。
#   但这两条路径都要求「Python 进程还活着」——如果用例中途把解释器搞崩、进程被 kill、
#   或 setup 阶段直接段错误，最终器就来不及执行，数据会永久残留在数据库里。
#   因此再加一道「会话开始 / 会话结束各按标记兜底清理一次」的保险：
#     - pytest_sessionstart：会话一开始就清掉上一次崩溃留下的残留，
#       这样本次会话期间数据库就是干净的（不必等到跑完）；
#     - pytest_sessionfinish：会话结束时再清一次，兜住本次会话自己产生的残留。
#
# 重要认知（避免误解）：
#   这两个钩子都**无法**替"正在被 kill 的那一次会话"清理（进程已经没了）；
#   它们的作用是：进程被杀之后，**下一次** pytest 会话一开始（sessionstart）
#   就会把历史残留清掉，从而不会长期积累脏数据。
#
# 标记方式说明（unique_suffix 的两种落地位置，均在此处识别）：
#   ① 房源：写入 apartments.name，形如「自动化临时房源-20261005203118-075794c1」
#      （另有 -B / -ddt / -perm / -cleanup 等后缀变体，正则前缀匹配即可覆盖）
#   ② 合同 / 缴费 / 预约：写入各自 remark，形如「...（20261005203118-075794c1）」
#   注意：contracts.contract_no 与 payments.payment_no 是**后端自动生成**的
#      （HT+日期+序号 / JF+日期+序号），不含 unique_suffix，不能作为标记字段；
#      appointments 中 test_login_ddt 的预约 remark 也不含标记——
#      这类"自身无标记"的数据通过「以临时房源为根、按外键级联」的路径清理。

# unique_suffix 的格式正则（与 unique_suffix fixture 的生成规则一一对应）：
#   %Y%m%d%H%M%S -> 14 位数字；uuid4().hex[:8] -> 8 位小写十六进制
# 刻意使用 [0-9]{14} 而非 \d{14}，避免不同 MySQL/ICU 版本对 \d 支持差异
_TEMP_SUFFIX_PATTERN = "[0-9]{14}-[0-9a-f]{8}"
# 临时房源名称前缀 + 标记（覆盖 自动化临时房源-<suffix> 及其所有变体）
_TEMP_APARTMENT_NAME_PATTERN = f"自动化临时房源-{_TEMP_SUFFIX_PATTERN}"


# 本清理逻辑涉及的全部业务表（用于一次性探测"当前库里实际存在哪些表"）
_CLEANUP_TABLES = (
    "payments",
    "reviews",
    "repairs",
    "contracts",
    "appointments",
    "favorites",
    "complaints",
    "apartments",
    "users",
)


def _existing_tables(db, tables: tuple) -> set:
    """
    查询当前数据库中实际存在的表名集合。

    参数:
        db: DBUtil 实例
        tables: 待探测的表名元组
    返回:
        set：存在的表名集合
    说明:
        为什么需要它：favorites / reviews / repairs / complaints 这四张表由后端 JPA
        （ddl-auto=update）自动创建，**不在 test/sql/schema.sql 里**。
        若后端从未启动过（例如只跑了不含 DB 的用例），这些表可能不存在，
        此时直接 DELETE 会抛 "Table doesn't exist" 并中断整段清理，
        连本来能清的表也一起清不掉。因此先探测存在性，不存在的表直接跳过。
    """
    placeholders = ", ".join(["%s"] * len(tables))
    rows = db.query_all(
        "SELECT table_name AS t FROM information_schema.tables "
        f"WHERE table_schema = DATABASE() AND table_name IN ({placeholders})",
        tuple(tables),
    )
    return {row["t"] for row in rows}


def _delete_where_in(db, existing_tables: set, table: str, column: str, ids: list) -> int:
    """
    按主键/外键列表批量删除（参数化 IN，空列表或表不存在时直接跳过）。

    参数:
        db: DBUtil 实例
        existing_tables: _existing_tables 返回的存在表集合
        table: 表名（仅使用本文件内的常量，不来自外部输入）
        column: 条件列名
        ids: 待删除的 id 列表
    返回:
        int：受影响行数；ids 为空或表不存在时返回 0
    异常:
        pymysql.MySQLError：SQL 执行异常（由调用方统一捕获并打印警告）
    """
    if not ids or table not in existing_tables:
        # 空列表不能拼出 "IN ()"（SQL 语法错误）；表不存在则跳过
        return 0
    placeholders = ", ".join(["%s"] * len(ids))
    return db.execute(f"DELETE FROM {table} WHERE {column} IN ({placeholders})", tuple(ids))


def _delete_where_marked(db, existing_tables: set, table: str, column: str) -> int:
    """
    按「字段内容包含 unique_suffix 标记」批量删除。

    参数:
        db: DBUtil 实例
        existing_tables: _existing_tables 返回的存在表集合
        table: 表名（仅使用本文件内的常量）
        column: 待匹配的列名（remark / username 等）
    返回:
        int：受影响行数；表不存在时返回 0
    异常:
        pymysql.MySQLError：SQL 执行异常（由调用方统一捕获并打印警告）
    """
    if table not in existing_tables:
        return 0
    # 只删除"字段内容明确带有 unique_suffix 标记"的行，种子数据不含该格式，不会被误删
    return db.execute(f"DELETE FROM {table} WHERE {column} REGEXP %s", (_TEMP_SUFFIX_PATTERN,))


def cleanup_residual_temp_data(db) -> dict:
    """
    清理数据库中所有残留的动态测试数据（会话开始 / 结束时兜底）。

    参数:
        db: DBUtil 实例（由调用方创建并负责关闭）
    返回:
        dict：各表删除条数，形如
              {"payments": 3, "reviews": 1, "repairs": 0, "contracts": 2,
               "appointments": 1, "favorites": 1, "complaints": 0, "apartments": 2, "users": 0}
    异常:
        pymysql.MySQLError：SQL 执行异常（由调用方统一捕获并打印警告）
    清理策略:
        以「临时房源」为根，按外键反向级联删除子表，再删父表，避免外键约束报错。
        除级联路径外，再按各表自身的 unique_suffix 标记做补充扫描，
        以覆盖"父记录不是临时房源、但自身带标记"的漏网数据。

        实际删除顺序（务必保持，全部来自 information_schema 的真实外键）：
          缴费流水 -> 评价/报修(按 contract_id) -> 合同 -> 预约
          -> 收藏/评价/报修/投诉(按 apartment_id) -> 房源 -> 用户
        其中"评价/报修(按 contract_id)"必须排在删除合同之前：
        reviews.contract_id（可空）与 repairs.contract_id（非空）都外键指向 contracts，
        若先删合同会被外键约束拦下。
    """
    # 先探测一次"当前库里实际存在哪些表"，避免在不存在的表上执行 DELETE 中断整段清理
    existing_tables = _existing_tables(db, _CLEANUP_TABLES)

    # ---------- 第一步：找出所有带标记的临时数据（自身带标记 or 挂在临时房源下） ----------
    apartment_rows = db.query_all(
        "SELECT id FROM apartments WHERE name REGEXP %s", (_TEMP_APARTMENT_NAME_PATTERN,)
    )
    temp_apartment_ids = [row["id"] for row in apartment_rows]

    # 合同：既包含"挂在临时房源下"的，也包含"remark 自身带标记"的
    contract_rows = db.query_all(
        "SELECT id FROM contracts WHERE remark REGEXP %s", (_TEMP_SUFFIX_PATTERN,)
    )
    temp_contract_ids = {row["id"] for row in contract_rows}
    if temp_apartment_ids:
        placeholders = ", ".join(["%s"] * len(temp_apartment_ids))
        rows = db.query_all(
            f"SELECT id FROM contracts WHERE apartment_id IN ({placeholders})", tuple(temp_apartment_ids)
        )
        temp_contract_ids.update(row["id"] for row in rows)
    temp_contract_ids = sorted(temp_contract_ids)

    deleted = {}

    # ---------- 第二步：按外键顺序删除（先子后父，避免外键约束报错） ----------
    # ① 缴费流水：删除挂在临时合同下的 + 自身 remark 带标记的
    deleted["payments"] = _delete_where_in(db, existing_tables, "payments", "contract_id", temp_contract_ids)
    deleted["payments"] += _delete_where_marked(db, existing_tables, "payments", "remark")

    # ② 评价 / 报修（按 contract_id）：二者都外键指向 contracts，必须先于合同删除
    deleted["reviews"] = _delete_where_in(db, existing_tables, "reviews", "contract_id", temp_contract_ids)
    deleted["repairs"] = _delete_where_in(db, existing_tables, "repairs", "contract_id", temp_contract_ids)

    # ③ 合同：此时缴费流水、评价、报修都已解除引用，可以安全删除
    deleted["contracts"] = _delete_where_in(db, existing_tables, "contracts", "id", temp_contract_ids)

    # ④ 预约：删除挂在临时房源下的 + 自身 remark 带标记的
    #    （test_login_ddt 的预约 remark 不含标记，靠前者覆盖）
    deleted["appointments"] = _delete_where_in(db, existing_tables, "appointments", "apartment_id", temp_apartment_ids)
    deleted["appointments"] += _delete_where_marked(db, existing_tables, "appointments", "remark")

    # ⑤ 收藏 / 评价 / 报修 / 投诉（按 apartment_id）：都外键指向 apartments，必须先于房源删除
    #    评价/报修这里再兜一次：可能"挂在临时房源下、但关联合同不在临时合同范围内"
    deleted["favorites"] = _delete_where_in(db, existing_tables, "favorites", "apartment_id", temp_apartment_ids)
    deleted["reviews"] += _delete_where_in(db, existing_tables, "reviews", "apartment_id", temp_apartment_ids)
    deleted["repairs"] += _delete_where_in(db, existing_tables, "repairs", "apartment_id", temp_apartment_ids)
    deleted["complaints"] = _delete_where_in(db, existing_tables, "complaints", "apartment_id", temp_apartment_ids)

    # ⑥ 房源：以上引用它的子表均已清理，可以安全删除
    deleted["apartments"] = _delete_where_in(db, existing_tables, "apartments", "id", temp_apartment_ids)

    # ⑦ 用户：当前没有任何 fixture/用例动态创建用户，这里是防御性清理
    #    （只匹配用户名里带 unique_suffix 标记的，不会命中 admin/landlord/tenant 种子账号）
    deleted["users"] = _delete_where_marked(db, existing_tables, "users", "username")

    return deleted


def _log_to_terminal(session, message: str):
    """
    统一的日志输出出口：优先走 terminalreporter，保证输出不被 pytest 捕获而看不到。

    参数:
        session: pytest 会话对象
        message: 待输出的中文日志
    返回:
        无
    """
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(message)
    else:
        print(message)


def _run_residual_cleanup(session, phase: str):
    """
    执行一次「残留动态数据兜底清理」并输出中文日志（sessionstart / sessionfinish 共用）。

    参数:
        session: pytest 会话对象（用于取 terminalreporter 输出日志）
        phase: 阶段名称，用于日志文案（"会话开始" / "会话结束"）
    返回:
        无
    异常:
        无（数据库连不上或 SQL 异常均被捕获并打印警告，不改变测试退出码）
    """
    try:
        # 说明：不能复用 db_connection fixture —— 它是 session 级，
        # 在 sessionstart 时尚未创建、在 sessionfinish 时已被关闭，因此这里单独建连接
        db = DBUtil()
    except Exception as e:
        _log_to_terminal(session, f"[警告] {phase}兜底清理已跳过：数据库连接失败（{e}）")
        return

    try:
        deleted = cleanup_residual_temp_data(db)
    except Exception as e:
        # 绝不静默吞掉：提示人工确认，避免残留数据被忽视
        _log_to_terminal(
            session, f"[警告] {phase}兜底清理异常：{e}，请人工确认数据库中是否残留临时数据"
        )
        return
    finally:
        db.close()

    total = sum(deleted.values())
    if total:
        # 只在"确实清掉东西"时输出，正常干净的会话保持安静
        detail = "、".join(f"{table} {count} 条" for table, count in deleted.items() if count)
        _log_to_terminal(session, f"[清理] {phase}兜底清理残留动态数据，共 {total} 条：{detail}")


def pytest_sessionstart(session):
    """
    pytest 钩子：会话开始前，先清理上一次会话可能残留的动态测试数据。

    作用:
        - 上一次会话若在用例中途崩溃 / 进程被 kill，fixture 与 finalizer 都来不及执行，
          数据会残留在数据库；本钩子在本次会话**一开始**就统一清掉，
          这样整个会话期间数据库都是干净的（不必等到会话结束才清）；
        - 只删除"明确带 unique_suffix 标记"或"挂在临时房源下"的数据，
          种子数据（admin/landlord/tenant、id=1/2/3 的房源与合同等）不会被误删；
        - 清理失败只打印中文警告，**不改变测试退出码**。
    参数:
        session: pytest 会话对象（用于获取 terminalreporter 输出日志）
    返回:
        无
    异常:
        无（数据库连不上或 SQL 异常均被捕获并打印警告）
    """
    _run_residual_cleanup(session, "会话开始")


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """
    pytest 钩子：整个测试会话结束后，兜底清理残留的动态测试数据。

    作用:
        - 用例中途崩溃 / 进程被 kill 时，fixture 与 finalizer 都来不及执行，
          动态数据会残留在数据库；本钩子在会话结束时再清一次；
        - 只删除"明确带 unique_suffix 标记"或"挂在临时房源下"的数据，
          种子数据（admin/landlord/tenant、id=1/2/3 的房源与合同等）不会被误删；
        - 清理失败只打印中文警告，**不改变测试结果**（退出码仍由用例本身决定）。
    参数:
        session: pytest 会话对象（用于获取 terminalreporter 输出日志）
        exitstatus: 会话退出码（本钩子不使用）
    返回:
        无
    异常:
        无（数据库连不上或 SQL 异常均被捕获并打印警告）
    """
    _run_residual_cleanup(session, "会话结束")