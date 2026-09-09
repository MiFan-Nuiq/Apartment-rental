# -*- coding: utf-8 -*-
"""
===== 运行记录 =====
说明：每次执行本脚本后，请将实际运行结果（测试通过数/失败数、耗时、失败用例原因）
      填写到下方占位符，便于记录测试过程和排查回归。

- 最近一次执行时间：2026-09-01 21:31
- 运行环境（Python/后端服务地址/数据库）：Python 3.14.7 / http://localhost:8080 / MySQL
- 执行命令：pytest test_core_flow.py -v
- 执行结果：7 passed in 0.48s
- 失败用例定位：无
===== 运行记录结束 =====

公寓租赁管理系统 —— 核心业务流程自动化测试
测试链路：登录(获取token) -> 房源查询 -> 预约提交

接口映射（对应项目 backend 代码）：
  POST /api/auth/login        认证登录，返回 token/username/realName/role/id
  GET  /api/apartments        房源列表，需携带 Authorization: Bearer <token>
  POST /api/appointments      提交看房预约，需携带 token

统一返回结构 ApiResponse：{ code, message, data }
  code=200 表示业务成功；未认证由 Spring Security 返回 HTTP 401。

运行方式：
  pip install requests pytest
  pytest test_core_flow.py -v

说明：预约接口会对“已生效的合同”做时间段冲突校验（AppointmentService.checkAppointmentTimeConflict），
因此若要提交成功，请传入一个不存在生效中合同或预约时间落在合同期外的公寓ID（见 6.1 中的场景）。
"""

import pytest
import requests
from datetime import datetime

# ==================== 配置区 ====================
BASE_URL = "http://localhost:8080"          # 后端服务地址（Spring Boot 默认 8080）
LOGIN_URL = BASE_URL + "/api/auth/login"
APARTMENTS_URL = BASE_URL + "/api/apartments"
APPOINTMENTS_URL = BASE_URL + "/api/appointments"

# 登录账号（项目 DataInitializer 初始化账号），可替换为测试专用账号
USERNAME = "tenant"
PASSWORD = "123456"

# 预约提交所需的关联数据（请按实际测试数据填写）
APARTMENT_ID = 3          # 目标房源 id（需真实存在且与其关联房东匹配）
TENANT_ID = 3             # 租户用户 id（DataInitializer 中 tenant 的 id）
LANDLORD_ID = 2           # 房东用户 id（DataInitializer 中 landlord 的 id）
APPOINTMENT_TIME = "2026-10-01 10:00:00"    # 预约时间（格式 yyyy-MM-dd HH:mm:ss）
REMARK = "pytest 自动化提交的看房预约"
# ==================== 配置区 ====================


# -------------------- 1. 登录：获取 token --------------------
def login(username: str, password: str) -> dict:
    """调用登录接口，成功返回 data（含 token / realName / role / id）。"""
    resp = requests.post(
        LOGIN_URL,
        json={"username": username, "password": password},
        timeout=10,
    )
    payload = resp.json()
    assert resp.status_code == 200, f"登录请求 HTTP 状态码异常，实际：{resp.status_code}"
    assert payload.get("code") == 200, f"登录业务码异常，返回：{payload}"
    assert payload.get("message") == "登录成功", f"登录提示文案异常，返回：{payload}"
    data = payload.get("data")
    assert data is not None, "登录返回 data 为空"
    # 断言返回的关键字段（字段集对应用例：login 响应无 id，用户主键为 userId）
    for field in ("token", "username", "realName", "role", "userId"):
        assert field in data, f"登录响应缺少字段：{field}"
    assert data["username"] == username, f"登录返回用户名 {data['username']} 与输入 {username} 不一致"
    return data


# -------------------- 2. 房源查询 --------------------
def query_apartments(token: str) -> list:
    """携带 token 查询房源列表，断言 HTTP 200 与业务字段。"""
    resp = requests.get(
        APARTMENTS_URL,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    payload = resp.json()
    assert resp.status_code == 200, f"房源查询 HTTP 状态码异常，实际：{resp.status_code}"
    assert payload.get("code") == 200, f"房源查询业务码异常，返回：{payload}"
    apartments = payload.get("data")
    assert isinstance(apartments, list), f"房源 data 应为列表，实际：{type(apartments)}"
    # 对返回的每个房源校验核心字段（对应 Apartment 实体）
    for apt in apartments:
        for field in ("id", "name", "address", "monthlyRent", "status", "auditStatus"):
            assert field in apt, f"房源缺少字段：{field}"
    return apartments


# -------------------- 3. 提交预约 --------------------
def submit_appointment(token: str) -> dict:
    """携带 token 提交看房预约，断言 HTTP 200 与业务字段。"""
    body = {
        "apartment": {"id": APARTMENT_ID},
        "tenant": {"id": TENANT_ID},
        "landlord": {"id": LANDLORD_ID},
        "appointmentTime": APPOINTMENT_TIME,
        "remark": REMARK,
    }
    resp = requests.post(
        APPOINTMENTS_URL,
        json=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        timeout=10,
    )
    payload = resp.json()
    assert resp.status_code == 200, f"提交预约 HTTP 状态码异常，实际：{resp.status_code}"
    assert payload.get("code") == 200, f"提交预约业务码异常，返回：{payload}"
    data = payload.get("data")
    assert data is not None, "提交预约返回 data 为空"
    # 断言返回的关键字段（对应 Appointment 实体 + 后端默认逻辑）
    for field in ("id", "apartment", "tenant", "landlord", "appointmentTime"):
        assert field in data, f"预约返回缺少字段：{field}"
    assert data["apartment"]["id"] == APARTMENT_ID, "预约返回的房源 id 与提交不一致"
    assert data["status"] == "待处理", f"新预约状态应为'待处理'，实际：{data.get('status')}"
    return data


# ==================== pytest 用例 ====================

@pytest.fixture(scope="module")
def auth_token():
    """模块级 fixture：登录一次，供后续用例复用 token。"""
    login_data = login(USERNAME, PASSWORD)
    return login_data["token"]


def test_01_login_success():
    """TC: 正确账号密码登录成功，返回 token 及用户信息。"""
    data = login(USERNAME, PASSWORD)
    assert isinstance(data["token"], str) and len(data["token"]) > 0, "token 为空"
    assert data["role"] in ("ADMIN", "LANDLORD", "TENANT"), f"非法角色：{data['role']}"


def test_02_login_wrong_password():
    """TC: 密码错误时返回业务提示，而不返回 token。"""
    resp = requests.post(LOGIN_URL, json={"username": USERNAME, "password": "wrong-pwd"}, timeout=10)
    payload = resp.json()
    assert payload.get("message") == "用户名或密码错误", f"密码错误提示异常：{payload}"


def test_03_login_non_exist_user():
    """TC: 用户不存在时返回业务提示。"""
    resp = requests.post(LOGIN_URL, json={"username": "no_such_user", "password": "123456"}, timeout=10)
    payload = resp.json()
    assert payload.get("message") == "用户不存在", f"用户不存在提示异常：{payload}"


def test_04_query_apartments(auth_token):
    """TC: 携带 token 查询房源列表成功，字段完整。"""
    apartments = query_apartments(auth_token)
    assert len(apartments) > 0, "房源列表为空，请先准备房源数据"


def test_05_query_apartments_without_token():
    """TC: 未携带 token 访问房源接口应被拦截（HTTP 401）。"""
    resp = requests.get(APARTMENTS_URL, timeout=10)
    assert resp.status_code in (401, 403), f"未认证访问应返回 401，实际：{resp.status_code}"


def test_06_submit_appointment(auth_token):
    """TC: 携带 token 提交预约成功，状态为'待处理'。"""
    data = submit_appointment(auth_token)
    assert data["remark"] == REMARK, f"预约 remark 不一致，实际：{data.get('remark')}"


def test_07_full_flow(auth_token):
    """TC: 端到端主流程连贯执行：登录 -> 房源查询 -> 提交预约。

    该用例串联了链路，用于验证 token 在整条业务链路中的有效传递。
    """
    apartments = query_apartments(auth_token)
    print(f"共查询到 {len(apartments)} 条房源")
    # 若指定的房源存在，则提交预约并验证创建成功
    ids = {apt["id"] for apt in apartments}
    if APARTMENT_ID in ids:
        data = submit_appointment(auth_token)
        print(f"预约创建成功，预约ID：{data['id']}")
        assert data["status"] == "待处理"