# -*- coding: utf-8 -*-
"""
核心业务流程测试用例：登录 -> 房源查询 -> 预约提交

覆盖点（对应原 test/automation/test_core_flow.py 的 7 个用例）：
    1. 正确账号密码登录成功，返回 token 及用户信息
    2. 密码错误时返回业务提示
    3. 用户不存在时返回业务提示
    4. 携带 token 查询房源列表成功、字段完整
    5. 未携带 token 访问房源接口被拦截（HTTP 401/403）
    6. 携带 token 提交预约成功，状态为"待处理"
    7. 端到端主流程连贯执行

分层结构：
    testcases（本文） -> apis（接口层） -> utils（请求/断言工具）
    登录 token 通过 conftest 的 auth_token / auth_headers fixture 复用。
"""

import allure
import pytest

from apis.apartment_api import get_apartments, get_apartments_without_token
from apis.appointment_api import create_appointment
from apis.login_api import login
from utils.assert_util import (
    assert_business_code,
    assert_field_equal,
    assert_field_exists,
    assert_list_not_empty,
    assert_status_code,
)

# 登录账号统一取自 conftest 环境变量配置（避免散落硬编码）
from conftest import PASSWORD, USERNAME


@allure.feature("核心流程")
@allure.story("登录-房源-预约")
class TestCoreFlow:
    """核心业务链路测试类：登录、房源查询、预约提交。"""

    @allure.title("登录：正确账号密码登录成功并返回 token")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_login_success(self, api_client):
        """验证正确账号密码登录成功，token 与角色字段完整。"""
        # 步骤一：调用登录接口
        with allure.step("调用登录接口"):
            resp = login(api_client, USERNAME, PASSWORD)
            assert_status_code(resp, 200)
            assert_business_code(resp, 200)
            assert_field_equal(resp.json(), "message", "登录成功")

        # 步骤二：校验返回的业务数据字段
        with allure.step("校验登录返回 token 与用户信息"):
            data = resp.json().get("data")
            assert data is not None, "登录返回 data 为空"
            # 登录响应字段集（后端 LoginResponse：无 id，用户主键为 userId）
            assert_field_exists(data, ["token", "username", "realName", "role", "userId"])
            assert isinstance(data["token"], str) and len(data["token"]) > 0, "token 为空"
            assert data["role"] in ("ADMIN", "LANDLORD", "TENANT"), f"非法角色：{data['role']}"

    @allure.title("登录：密码错误返回业务提示")
    @pytest.mark.api
    @pytest.mark.regression
    def test_login_wrong_password(self, api_client):
        """验证密码错误时后端返回业务提示而非 token。"""
        with allure.step("使用错误密码调用登录接口"):
            resp = login(api_client, USERNAME, "wrong-pwd")
            assert_status_code(resp, 200)
            payload = resp.json()
        # 后端业务提示文案断言（AuthController 对密码错误统一返回该文案）
        with allure.step("断言错误提示文案"):
            assert_field_equal(payload, "message", "用户名或密码错误")

    @allure.title("登录：用户不存在返回业务提示")
    @pytest.mark.api
    @pytest.mark.regression
    def test_login_non_exist_user(self, api_client):
        """验证不存在的用户名登录时返回业务提示。"""
        with allure.step("使用不存在的用户名调用登录接口"):
            resp = login(api_client, "no_such_user", "123456")
            assert_status_code(resp, 200)
            payload = resp.json()
        with allure.step("断言用户不存在提示文案"):
            assert_field_equal(payload, "message", "用户不存在")

    @allure.title("房源：携带 token 查询房源列表成功且字段完整")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_query_apartments(self, api_client, auth_headers):
        """验证携带 token 查询房源列表，返回数据为列表且字段完整。"""
        # 步骤一：携带鉴权头查询房源
        with allure.step("携带 token 调用房源列表接口"):
            resp = get_apartments(api_client, auth_headers["Authorization"].replace("Bearer ", ""))
            assert_status_code(resp, 200)
            assert_business_code(resp, 200)

        # 步骤二：断言房源列表非空且关键字段完整
        with allure.step("校验房源列表字段"):
            apartments = resp.json().get("data")
            assert_list_not_empty(apartments, "房源列表为空，请先准备房源数据")
            for apt in apartments:
                assert_field_exists(apt, ["id", "name", "address", "monthlyRent", "status", "auditStatus"])

    @allure.title("房源：未携带 token 访问被拦截")
    @pytest.mark.api
    @pytest.mark.smoke
    def test_query_apartments_without_token(self, api_client):
        """验证未携带 token 访问房源接口被 Spring Security 拦截。"""
        with allure.step("不携带 token 调用房源列表接口"):
            resp = get_apartments_without_token(api_client)
        with allure.step("断言返回 401 或 403"):
            assert resp.status_code in (401, 403), f"未认证访问应返回 401/403，实际：{resp.status_code}"

    @allure.title("预约：携带 token 提交预约成功且状态为待处理")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.db
    def test_submit_appointment(self, api_client, auth_headers, appointment_data, db_connection):
        """验证携带 token 提交预约成功，且数据库落库记录与接口返回一致。"""
        # 步骤一：调用提交预约接口
        with allure.step("提交预约请求"):
            resp = create_appointment(
                api_client,
                token=auth_headers["Authorization"].replace("Bearer ", ""),
                apartment_id=appointment_data["apartment_id"],
                tenant_id=appointment_data["tenant_id"],
                landlord_id=appointment_data["landlord_id"],
                appointment_time=appointment_data["appointment_time"],
                remark=appointment_data["remark"],
            )
            assert_status_code(resp, 200)
            assert_business_code(resp, 200)

        # 步骤二：校验预约创建结果（接口返回）
        with allure.step("校验预约返回字段与状态"):
            data = resp.json().get("data")
            assert data is not None, "提交预约返回 data 为空"
            assert_field_exists(data, ["id", "apartment", "tenant", "landlord", "appointmentTime"])
            assert data["apartment"]["id"] == appointment_data["apartment_id"], "预约返回的房源 id 与提交不一致"
            assert_field_equal(data, "status", "待处理")
            assert_field_equal(data, "remark", appointment_data["remark"])

        # 步骤三：数据库校验——查询 appointments 表最新记录，与接口返回交叉比对
        with allure.step("数据库校验：appointments 表最新记录与接口返回一致"):
            # 取最新一条记录（id 自增，最大 id 即本次接口新建的记录）
            # 注意：appointments 表实际字段为 tenant_id / landlord_id，并无 user_id 列
            row = db_connection.query_one(
                "SELECT id, apartment_id, tenant_id, landlord_id, status, remark "
                "FROM appointments ORDER BY id DESC LIMIT 1"
            )
            assert row is not None, "appointments 表未查询到任何记录，接口可能未真正落库"
            assert row["id"] == data["id"], f"数据库最新记录 id={row['id']} 与接口返回 id={data['id']} 不一致"
            assert row["apartment_id"] == appointment_data["apartment_id"], (
                f"数据库 apartment_id={row['apartment_id']} 与提交的 {appointment_data['apartment_id']} 不一致"
            )
            assert row["tenant_id"] == appointment_data["tenant_id"], (
                f"数据库 tenant_id={row['tenant_id']} 与提交的 {appointment_data['tenant_id']} 不一致"
            )
            assert row["landlord_id"] == appointment_data["landlord_id"], (
                f"数据库 landlord_id={row['landlord_id']} 与提交的 {appointment_data['landlord_id']} 不一致"
            )
            assert row["status"] == "待处理", f"数据库预约状态应为'待处理'，实际：{row['status']}"
            assert row["remark"] == appointment_data["remark"], (
                f"数据库 remark={row['remark']} 与提交的 {appointment_data['remark']} 不一致"
            )

    @allure.title("端到端主流程：登录 -> 房源查询 -> 提交预约")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.slow
    def test_full_flow(self, api_client, auth_headers, appointment_data):
        """端到端连贯执行登录、房源查询、预约提交，验证 token 在链路中有效传递。"""
        # 步骤一：房源查询
        with allure.step("端到端步骤1：查询房源列表"):
            resp = get_apartments(api_client, auth_headers["Authorization"].replace("Bearer ", ""))
            assert_status_code(resp, 200)
            apartments = resp.json().get("data")
            assert_list_not_empty(apartments, "房源列表为空")

        # 步骤二：若目标房源存在则提交预约
        with allure.step("端到端步骤2：提交预约"):
            # 校验目标房源在列表中，避免用不存在的 ID 请求
            ids = {apt["id"] for apt in apartments}
            assert appointment_data["apartment_id"] in ids, "目标房源不存在于房源列表"
            resp2 = create_appointment(
                api_client,
                token=auth_headers["Authorization"].replace("Bearer ", ""),
                apartment_id=appointment_data["apartment_id"],
                tenant_id=appointment_data["tenant_id"],
                landlord_id=appointment_data["landlord_id"],
                appointment_time=appointment_data["appointment_time"],
                remark=appointment_data["remark"],
            )
            assert_status_code(resp2, 200)
            assert_field_equal(resp2.json().get("data") or {}, "status", "待处理")