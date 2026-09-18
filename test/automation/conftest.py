# -*- coding: utf-8 -*-
"""
conftest.py —— pytest 全局共享 fixture、配置与钩子

集中管理：
    - 配置常量：后端/前端地址、登录账号、业务数据 ID、数据库连接信息（均可环境变量覆盖）
    - 接口 fixture：base_url / api_client / auth_token / auth_headers / appointment_data
    - 数据库 fixture：db_connection（session 级，pymysql 直连 MySQL）
    - UI fixture：browser（module 级浏览器）/ ui_page（用例级页面，含 trace 录制）
    - 失败钩子：pytest_runtest_makereport —— UI 用例失败时自动截图并保存 Playwright trace

注意：登录账号、数据库密码等敏感/易变配置统一在此处集中管理，避免散落多个文件。
"""

import os
from pathlib import Path

import pytest

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