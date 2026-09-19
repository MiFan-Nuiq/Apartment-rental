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