# -*- coding: utf-8 -*-
"""
核心业务流程测试用例：登录 -> 房源查询 -> 预约提交

覆盖点（对应原 test/automation/test_core_flow.py 的 7 个用例 + 1 个动态数据演示用例）：
    1. 正确账号密码登录成功，返回 token 及用户信息
    2. 密码错误时返回业务提示
    3. 用户不存在时返回业务提示
    4. 携带 token 查询房源列表成功、字段完整（静态种子数据）
    5. 未携带 token 访问房源接口被拦截（HTTP 401/403）
    6. 携带 token 提交预约成功，状态为"待处理"（房源改用动态 temp_apartment）
    7. 端到端主流程连贯执行（查询用静态数据，预约用动态数据）
    8. 【新增】动态数据管理演示：临时房源 + 唯一后缀，用例后自动清理

分层结构：
    testcases（本文） -> apis（接口层） -> utils（请求/断言工具）
    登录 token 通过 conftest 的 auth_token / auth_headers fixture 复用。

测试数据策略：
    静态数据（test/sql/data.sql）负责登录账号与基础房源；
    业务操作产生的房源/预约数据一律使用 conftest 的动态 fixture（temp_apartment / temp_appointment），
    用例结束由 fixture 自动清理，保证用例之间互不污染。
"""

import allure
import pytest

from apis.apartment_api import get_apartments, get_apartments_without_token
from apis.appointment_api import create_appointment, delete_appointment
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

    @allure.title("预约：在动态临时房源上提交预约成功且状态为待处理")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.db
    def test_submit_appointment(
        self,
        api_client,
        auth_headers,
        appointment_data,
        temp_apartment,
        temp_appointment,
        dynamic_data_cleaner,
        db_connection,
    ):
        """
        验证携带 token 提交预约成功，且数据库落库记录与接口返回一致。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            appointment_data: 预约基础数据（租户/房东 id、预约时间）
            temp_apartment: 用例级临时房源（替代原写死的 apartment_id=3）
            temp_appointment: 用例级临时预约（验证动态数据存在时本用例仍互不干扰）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具（校验落库）
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例自建的预约由 dynamic_data_cleaner 登记删除；
            temp_appointment 与 temp_apartment 由 fixture 按"后进先出"自动删除
            （先删全部预约，再删房源，不会触发外键约束）
        """
        # 动态数据：本次预约挂到临时房源上，不再依赖 data.sql 中写死的 apartment_id=3
        apartment_id = temp_apartment["id"]

        with allure.step(
            f"动态数据准备：临时房源 id={apartment_id}（{temp_apartment['name']}）；"
            f"预置临时预约 id={temp_appointment['id']}（用例后自动清理）"
        ):
            # 确认 temp_appointment 确实挂在本次的临时房源上，体现用例间数据隔离
            assert temp_appointment["apartment_id"] == apartment_id, "预置临时预约未关联到本次临时房源"

        # 步骤一：调用提交预约接口
        with allure.step("提交预约请求（动态房源 id）"):
            resp = create_appointment(
                api_client,
                token=auth_headers["Authorization"].replace("Bearer ", ""),
                apartment_id=apartment_id,
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
            assert data["apartment"]["id"] == apartment_id, "预约返回的房源 id 与提交不一致"
            assert_field_equal(data, "status", "待处理")
            assert_field_equal(data, "remark", appointment_data["remark"])
            # 登记清理：本用例自建的预约必须先于临时房源被删除，否则房源删除会触发外键约束
            dynamic_data_cleaner(delete_appointment, data["id"], "临时预约")

        # 步骤三：数据库校验——按本次新建的预约 id 精确查询，与接口返回交叉比对
        with allure.step("数据库校验：appointments 表中本次记录与接口返回一致"):
            # 精确按 id 查询（而非"取最新一条"），避免同用例内预置数据/并发执行造成误判
            # 注意：appointments 表实际字段为 tenant_id / landlord_id，并无 user_id 列
            row = db_connection.query_one(
                "SELECT id, apartment_id, tenant_id, landlord_id, status, remark "
                "FROM appointments WHERE id = %s",
                (data["id"],),
            )
            assert row is not None, f"appointments 表未查询到 id={data['id']} 的记录，接口可能未真正落库"
            assert row["id"] == data["id"], f"数据库记录 id={row['id']} 与接口返回 id={data['id']} 不一致"
            assert row["apartment_id"] == apartment_id, (
                f"数据库 apartment_id={row['apartment_id']} 与提交的 {apartment_id} 不一致"
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

    @allure.title("端到端主流程：登录 -> 房源查询（静态） -> 提交预约（动态）")
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.slow
    def test_full_flow(self, api_client, auth_headers, appointment_data, temp_apartment, dynamic_data_cleaner):
        """
        端到端连贯执行房源查询与预约提交，验证 token 在链路中有效传递。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头（token 链路）
            appointment_data: 预约基础数据
            temp_apartment: 用例级临时房源（预约步骤使用动态数据，避免写死静态 id）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例自建的预约由 dynamic_data_cleaner 登记删除；
            临时房源由 temp_apartment fixture 在用例结束后自动删除
        """
        # 步骤一：房源查询（保留静态数据，验证基础数据可用）
        with allure.step("端到端步骤1：查询房源列表（静态种子数据，验证基础数据可用）"):
            resp = get_apartments(api_client, auth_headers["Authorization"].replace("Bearer ", ""))
            assert_status_code(resp, 200)
            apartments = resp.json().get("data")
            assert_list_not_empty(apartments, "房源列表为空")

        # 步骤二：在动态临时房源上提交预约
        with allure.step("端到端步骤2：在动态临时房源上提交预约"):
            # 校验新建的临时房源确实出现在列表中，避免用不存在的 ID 请求
            ids = {apt["id"] for apt in apartments}
            assert temp_apartment["id"] in ids, "新建的临时房源未出现在房源列表中"
            resp2 = create_appointment(
                api_client,
                token=auth_headers["Authorization"].replace("Bearer ", ""),
                apartment_id=temp_apartment["id"],
                tenant_id=appointment_data["tenant_id"],
                landlord_id=appointment_data["landlord_id"],
                appointment_time=appointment_data["appointment_time"],
                remark=appointment_data["remark"],
            )
            assert_status_code(resp2, 200)
            assert_field_equal(resp2.json().get("data") or {}, "status", "待处理")
            # 登记清理：自建的预约必须先删，避免临时房源删除时触发外键约束
            dynamic_data_cleaner(delete_appointment, resp2.json()["data"]["id"], "临时预约")

    @allure.title("预约：动态数据管理演示（临时房源 + 唯一后缀，用例后自动清理）")
    @allure.description(
        "演示「静态种子数据打底 + 动态 fixture 隔离」的数据管理策略："
        "用例通过 temp_apartment 创建带唯一后缀的临时房源，"
        "在其上提交预约并校验接口返回与数据库落库一致；"
        "用例结束后由 fixture 自动删除临时预约与临时房源，库中不留脏数据。"
    )
    @pytest.mark.api
    @pytest.mark.smoke
    @pytest.mark.db
    def test_submit_appointment_with_dynamic_data(
        self,
        api_client,
        auth_headers,
        appointment_data,
        temp_apartment,
        unique_suffix,
        dynamic_data_cleaner,
        db_connection,
    ):
        """
        验证动态数据管理策略：临时房源可创建、可预约、可校验、用例后自动清理。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            appointment_data: 预约基础数据（租户/房东 id、预约时间）
            temp_apartment: 用例级临时房源（由 fixture 动态创建，含唯一后缀）
            unique_suffix: 唯一后缀 fixture（演示用，校验数据标识唯一性）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例自建的预约由 dynamic_data_cleaner 登记删除；
            临时房源由 temp_apartment fixture 在用例结束后自动删除；
            清理成功后 GET /api/apartments/{id} 将查询不到该房源，
            该清理效果的验证见 testcases/test_data_isolation.py 中的清理校验用例。
        """
        # 步骤一：校验动态房源的数据标识带唯一后缀（避免与历史数据/其它用例撞车）
        with allure.step(f"校验动态房源标识唯一：唯一后缀={unique_suffix}"):
            assert temp_apartment["suffix"] == unique_suffix, "临时房源未使用本次用例的唯一后缀"
            assert unique_suffix in temp_apartment["name"], "临时房源标题未包含唯一后缀"
            assert temp_apartment["name"].startswith("自动化临时房源-"), (
                f"临时房源命名不符合约定：{temp_apartment['name']}"
            )
            assert temp_apartment["raw"].get("status") == "空置", "临时房源状态应为'空置'"
            assert temp_apartment["raw"].get("auditStatus") == "审核通过", "临时房源审核状态应为'审核通过'"

        # 步骤二：在动态房源上提交预约
        with allure.step("在动态临时房源上提交预约"):
            resp = create_appointment(
                api_client,
                token=auth_headers["Authorization"].replace("Bearer ", ""),
                apartment_id=temp_apartment["id"],
                tenant_id=appointment_data["tenant_id"],
                landlord_id=appointment_data["landlord_id"],
                appointment_time=appointment_data["appointment_time"],
                remark=appointment_data["remark"],
            )
            assert_status_code(resp, 200)
            assert_business_code(resp, 200)

        # 步骤三：断言预约创建成功（接口返回）
        with allure.step("断言预约创建成功且状态为待处理"):
            data = resp.json().get("data")
            assert data is not None, "提交预约返回 data 为空"
            assert data["apartment"]["id"] == temp_apartment["id"], "预约未关联到本次临时房源"
            assert_field_equal(data, "status", "待处理")
            # 登记清理：自建的预约必须先删，避免临时房源删除时触发外键约束
            dynamic_data_cleaner(delete_appointment, data["id"], "临时预约")

        # 步骤四：数据库落库校验（精确按 id 查询，证明动态数据真实入库）
        with allure.step("数据库校验：动态数据落库字段一致"):
            row = db_connection.query_one(
                "SELECT id, apartment_id, tenant_id, status FROM appointments WHERE id = %s",
                (data["id"],),
            )
            assert row is not None, "动态预约未落库"
            assert row["apartment_id"] == temp_apartment["id"], (
                f"数据库 apartment_id={row['apartment_id']} 与临时房源 {temp_apartment['id']} 不一致"
            )
            assert row["tenant_id"] == appointment_data["tenant_id"], "数据库 tenant_id 与提交不一致"
            assert row["status"] == "待处理", f"数据库预约状态应为'待处理'，实际：{row['status']}"