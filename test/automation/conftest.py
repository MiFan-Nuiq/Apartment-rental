# -*- coding: utf-8 -*-
"""
conftest.py —— pytest 全局共享 fixture 与配置

集中管理：
    - base_url：后端/前端地址，支持环境变量覆盖
    - api_client：全局共享的 HTTP 请求工具（requests.Session 封装）
    - auth_token / auth_headers：登录 token 及鉴权头，全工程复用
    - 预约测试数据：预约所需的房源/租户/房东 ID 与时间等

注意：登录账号、业务数据 ID 等凭据资源统一在此处管理，避免散落多个文件。
"""

import os

import pytest

from apis.login_api import get_token
from utils.request_util import RequestUtil

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