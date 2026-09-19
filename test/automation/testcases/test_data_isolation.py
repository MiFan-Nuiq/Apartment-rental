# -*- coding: utf-8 -*-
"""
动态测试数据隔离用例：验证「静态种子数据打底 + 动态 fixture 隔离」策略的有效性

覆盖点：
    1. test_two_apartments_do_not_conflict
       同一用例内创建两条临时房源，验证 id 不同、数据互不影响
    2. test_appointment_data_isolated
       在同一临时房源上连续创建两条预约，验证第二条不受第一条影响
    3. test_deleted_apartment_not_found
       验证清理策略真实生效：删除后的房源查询不到、数据库中无残留

设计说明：
    - 静态数据（test/sql/data.sql）只提供登录账号与基础房源等公共稳定数据；
    - 本文件所需房源全部通过接口动态创建（带唯一后缀，避免唯一约束/命名冲突），
      用例结束由 fixture 或 finalizer 清理，绝不依赖也不污染静态数据；
    - 断言全部为正向强断言，不做放宽、不做跳过。

分层结构：
    testcases（本文） -> apis（接口层） -> utils（请求/断言工具）
"""

import allure
import pytest

from apis.apartment_api import (
    create_apartment,
    delete_apartment,
    get_apartment_by_id,
    get_apartments,
)
from apis.appointment_api import create_appointment, delete_appointment

# 房东 id 与"临时房源请求体构造器"统一取自 conftest：
#   - LANDLORD_ID 对应 data.sql 中 users.id=2（静态种子数据里的房东账号）
#   - build_temp_apartment_payload 保证本文件与 fixture 的房源字段口径完全一致（避免两处维护）
from conftest import LANDLORD_ID, build_temp_apartment_payload


@allure.feature("测试数据管理")
@allure.story("动态数据隔离")
class TestDataIsolation:
    """动态测试数据隔离测试类：验证用例间数据互不污染、清理真实生效。"""

    @allure.title("数据隔离：同时创建两条临时房源，id 不同且互不影响")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.db
    def test_two_apartments_do_not_conflict(
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
        验证同一用例内的两条临时房源彼此独立，互不干扰。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            appointment_data: 预约基础数据（租户 id）
            temp_apartment: 用例级临时房源（第 1 条）
            unique_suffix: 唯一后缀（第 2 条房源据此命名）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            第 1 条由 temp_apartment fixture 用例后自动删除；
            第 2 条房源与用例内自建的预约由 dynamic_data_cleaner 登记删除，断言失败也会执行
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")

        # ---------- 步骤一：动态创建第 2 条临时房源 ----------
        with allure.step("动态创建第 2 条临时房源（第 1 条来自 temp_apartment fixture）"):
            # 名称带同一唯一后缀但加 -B 区分，保证两条数据可独立识别
            name_b = f"自动化临时房源-{unique_suffix}-B"
            resp_b = create_apartment(api_client, token, build_temp_apartment_payload(name_b))
            assert resp_b.status_code == 200, f"创建第 2 条临时房源失败：HTTP {resp_b.status_code}"
            body_b = resp_b.json()
            assert body_b.get("code") == 200, f"创建第 2 条临时房源失败：{body_b}"
            apt_b = body_b["data"]
            # 登记清理，保证即使后续断言失败也不会残留
            dynamic_data_cleaner(delete_apartment, apt_b["id"], "临时房源")

        apt_a = temp_apartment

        # ---------- 步骤二：断言两条房源完全独立 ----------
        with allure.step("断言两条临时房源 id、名称均不同"):
            assert apt_a["id"] != apt_b["id"], f"两条动态房源 id 重复：{apt_a['id']}"
            assert apt_a["name"] != apt_b["name"], "两条动态房源名称重复"
            assert apt_b["name"].endswith("-B"), f"第 2 条房源命名异常：{apt_b['name']}"

        with allure.step("数据库校验：两条房源各自独立存在且字段互不覆盖"):
            row_a = db_connection.query_one(
                "SELECT id, name, status, landlord_id FROM apartments WHERE id = %s", (apt_a["id"],)
            )
            row_b = db_connection.query_one(
                "SELECT id, name, status, landlord_id FROM apartments WHERE id = %s", (apt_b["id"],)
            )
            assert row_a is not None, "第 1 条临时房源未落库"
            assert row_b is not None, "第 2 条临时房源未落库"
            # 两条记录的 name 必须各自对应，证明创建第二条没有覆盖第一条
            assert row_a["name"] == apt_a["name"], f"房源 A 名称被覆盖：{row_a['name']} != {apt_a['name']}"
            assert row_b["name"] == apt_b["name"], f"房源 B 名称被覆盖：{row_b['name']} != {apt_b['name']}"
            assert row_a["landlord_id"] == LANDLORD_ID, "房源 A 房东 id 异常"
            assert row_b["landlord_id"] == LANDLORD_ID, "房源 B 房东 id 异常"

        with allure.step("接口校验：两条房源同时出现在房源列表中"):
            resp_list = get_apartments(api_client, token)
            assert resp_list.status_code == 200, f"查询房源列表失败：HTTP {resp_list.status_code}"
            ids = {apt["id"] for apt in resp_list.json().get("data") or []}
            assert apt_a["id"] in ids, "第 1 条临时房源未出现在房源列表"
            assert apt_b["id"] in ids, "第 2 条临时房源未出现在房源列表"

        # ---------- 步骤三：验证业务数据互不影响 ----------
        with allure.step("业务校验：在房源 A 上创建预约，房源 B 不产生任何预约数据"):
            resp_appt = create_appointment(
                api_client,
                token=token,
                apartment_id=apt_a["id"],
                tenant_id=appointment_data["tenant_id"],
                landlord_id=LANDLORD_ID,
                appointment_time="2026-11-11 09:00:00",
                remark=f"数据隔离验证：仅作用于房源 A（{unique_suffix}）",
            )
            assert resp_appt.status_code == 200, f"在房源 A 上创建预约失败：HTTP {resp_appt.status_code}"
            appt_a_id = (resp_appt.json().get("data") or {}).get("id")
            assert appt_a_id, f"房源 A 的预约未返回 id：{resp_appt.text}"
            # 登记预约清理（必须先于房源删除，避免外键约束导致房源清理失败）
            dynamic_data_cleaner(delete_appointment, appt_a_id, "临时预约")

            # 房源 B 上不应有任何预约记录，证明两条房源的数据完全隔离
            rows_b = db_connection.query_all(
                "SELECT id FROM appointments WHERE apartment_id = %s", (apt_b["id"],)
            )
            assert rows_b == [], f"房源 B 不应存在预约数据，实际查询到 {rows_b}"

    @allure.title("数据隔离：连续创建两条预约，第二条不受第一条影响")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.db
    def test_appointment_data_isolated(
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
        验证在同一临时房源上连续创建的两条预约彼此独立。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            appointment_data: 预约基础数据（租户/房东 id）
            temp_apartment: 用例级临时房源（两条预约共用，验证预约维度隔离）
            unique_suffix: 唯一后缀（用于生成两条各自可识别的备注）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            两条预约由 dynamic_data_cleaner 登记删除；临时房源由 temp_apartment fixture 删除
            （预约先删、房源后删，不会触发外键约束）
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")

        # ---------- 步骤一：连续创建两条预约 ----------
        with allure.step("连续创建两条预约（备注带唯一后缀区分）"):
            remark_1 = f"数据隔离验证-第1条（{unique_suffix}）"
            resp_1 = create_appointment(
                api_client,
                token=token,
                apartment_id=temp_apartment["id"],
                tenant_id=appointment_data["tenant_id"],
                landlord_id=appointment_data["landlord_id"],
                appointment_time=appointment_data["appointment_time"],
                remark=remark_1,
            )
            assert resp_1.status_code == 200, f"创建第 1 条预约失败：HTTP {resp_1.status_code}"
            data_1 = resp_1.json().get("data") or {}
            assert data_1.get("id"), f"第 1 条预约未返回 id：{resp_1.text}"
            dynamic_data_cleaner(delete_appointment, data_1["id"], "临时预约")

            remark_2 = f"数据隔离验证-第2条（{unique_suffix}）"
            resp_2 = create_appointment(
                api_client,
                token=token,
                apartment_id=temp_apartment["id"],
                tenant_id=appointment_data["tenant_id"],
                landlord_id=appointment_data["landlord_id"],
                appointment_time=appointment_data["appointment_time"],
                remark=remark_2,
            )
            assert resp_2.status_code == 200, f"创建第 2 条预约失败：HTTP {resp_2.status_code}"
            data_2 = resp_2.json().get("data") or {}
            assert data_2.get("id"), f"第 2 条预约未返回 id：{resp_2.text}"
            dynamic_data_cleaner(delete_appointment, data_2["id"], "临时预约")

        # ---------- 步骤二：断言两条预约互相独立 ----------
        with allure.step("断言两条预约 id 不同、备注各自独立"):
            assert data_1["id"] != data_2["id"], f"两条预约 id 重复：{data_1['id']}"
            assert data_1["remark"] == remark_1, "第 1 条预约备注被改写"
            assert data_2["remark"] == remark_2, "第 2 条预约备注被改写"
            assert data_1["status"] == "待处理" and data_2["status"] == "待处理", (
                f"预约状态异常：{data_1['status']} / {data_2['status']}"
            )

        with allure.step("数据库校验：两条预约都落库且第一条内容未被第二条影响"):
            row_1 = db_connection.query_one(
                "SELECT id, apartment_id, status, remark FROM appointments WHERE id = %s",
                (data_1["id"],),
            )
            row_2 = db_connection.query_one(
                "SELECT id, apartment_id, status, remark FROM appointments WHERE id = %s",
                (data_2["id"],),
            )
            assert row_1 is not None, "第 1 条预约未落库"
            assert row_2 is not None, "第 2 条预约未落库"
            # 第一条记录的 remark 必须仍是最初写入的值，证明创建第二条不会串改第一条
            assert row_1["remark"] == remark_1, f"第 1 条预约 remark 被影响：{row_1['remark']}"
            assert row_2["remark"] == remark_2, f"第 2 条预约 remark 异常：{row_2['remark']}"
            assert row_1["apartment_id"] == temp_apartment["id"], "第 1 条预约关联房源异常"
            assert row_2["apartment_id"] == temp_apartment["id"], "第 2 条预约关联房源异常"

        with allure.step("数据库校验：该临时房源下恰好存在本次创建的两条预约"):
            rows = db_connection.query_all(
                "SELECT id FROM appointments WHERE apartment_id = %s AND remark IN (%s, %s)",
                (temp_apartment["id"], remark_1, remark_2),
            )
            assert len(rows) == 2, f"该房源下本次动态预约数量应为 2，实际：{rows}"

    @allure.title("数据清理：删除后的临时房源查询不到且无数据库残留")
    @pytest.mark.api
    @pytest.mark.regression
    @pytest.mark.db
    def test_deleted_apartment_not_found(
        self,
        api_client,
        auth_headers,
        unique_suffix,
        db_connection,
    ):
        """
        验证清理策略真实生效（与 temp_apartment fixture 使用完全相同的删除接口）。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            unique_suffix: 唯一后缀（构造可识别的临时房源名）
            db_connection: MySQL 直连工具
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例在用例体内自行创建并删除，不依赖 fixture；
            若删除失败，用例会直接失败并暴露出清理问题，便于定位数据残留
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")

        # ---------- 步骤一：动态创建一条临时房源 ----------
        with allure.step("动态创建临时房源"):
            name = f"自动化临时房源-{unique_suffix}-cleanup"
            resp = create_apartment(api_client, token, build_temp_apartment_payload(name))
            assert resp.status_code == 200, f"创建临时房源失败：HTTP {resp.status_code}，响应：{resp.text}"
            apartment_id = (resp.json().get("data") or {}).get("id")
            assert apartment_id, f"创建临时房源未返回 id：{resp.text}"

            # 创建成功即可查询到，证明前置条件成立
            before = get_apartment_by_id(api_client, token, apartment_id)
            assert before.status_code == 200, f"新建房源查询失败：HTTP {before.status_code}"
            assert (before.json() or {}).get("code") == 200, f"新建房源查询业务码异常：{before.text}"

        # ---------- 步骤二：调用与 fixture 相同的删除接口 ----------
        with allure.step(f"调用 DELETE /api/apartments/{apartment_id} 清理临时房源"):
            del_resp = delete_apartment(api_client, token, apartment_id)
            assert del_resp.status_code == 200, (
                f"删除临时房源失败：HTTP {del_resp.status_code}，响应：{del_resp.text}"
            )
            assert (del_resp.json() or {}).get("code") == 200, f"删除临时房源业务码异常：{del_resp.text}"

        # ---------- 步骤三：验证清理结果 ----------
        with allure.step("接口校验：该房源已查询不到"):
            # 后端 findById 找不到时抛异常，接口返回 HTTP 500；此处只要求"拿不到成功响应"
            after = get_apartment_by_id(api_client, token, apartment_id)
            payload = after.json() if after.headers.get("Content-Type", "").startswith("application/json") else {}
            assert not (after.status_code == 200 and payload.get("code") == 200), (
                f"已删除的房源仍可查询到：HTTP {after.status_code}，响应：{after.text}"
            )

        with allure.step("数据库校验：apartments 表无该房源残留"):
            row = db_connection.query_one("SELECT id FROM apartments WHERE id = %s", (apartment_id,))
            assert row is None, f"apartments 表仍残留已删除的房源：{row}"