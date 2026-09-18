# -*- coding: utf-8 -*-
"""
数据驱动（DDT）测试用例：登录接口 + 预约接口

数据来源（data/ 目录下的 YAML）：
    - data/login_data.yaml       登录接口的 正常/密码错误/用户不存在 三组数据
    - data/appointment_data.yaml 预约接口的 正常/缺失字段/无效房源 三组数据

实现方式：
    - 使用 @pytest.mark.parametrize + yaml.safe_load 驱动，实现“数据与脚本分离”；
    - 每条数据的 id 作为 parametrize 用例 id，title 写入 Allure 动态标题；
    - 负向用例不做放宽：仅断言“未成功”，并要求业务码非 200。
"""

from pathlib import Path

import allure
import pytest
import yaml

from apis.login_api import login

# 数据目录：test/automation/data（本文件位于 testcases/ 下，故向上取一级）
DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def load_yaml(filename: str) -> dict:
    """
    读取 data 目录下的 YAML 数据文件。

    参数:
        filename: YAML 文件名（如 login_data.yaml）
    返回:
        dict：解析后的数据字典
    异常:
        FileNotFoundError：文件不存在
        yaml.YAMLError：YAML 格式错误
    """
    # 统一使用 utf-8 读取，保证中文用例标题正常解析
    with open(DATA_DIR / filename, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# 模块加载时读取用例数据（读取失败会直接暴露，避免静默跳过）
LOGIN_CASES = load_yaml("login_data.yaml")["cases"]
APPOINTMENT_CASES = load_yaml("appointment_data.yaml")["cases"]


@allure.feature("数据驱动测试")
@allure.story("登录接口")
@pytest.mark.api
@pytest.mark.regression
class TestLoginDDT:
    """登录接口数据驱动用例集（覆盖正常与异常场景）。"""

    @pytest.mark.parametrize("case", LOGIN_CASES, ids=[c["id"] for c in LOGIN_CASES])
    def test_login_by_data(self, api_client, case):
        """按 YAML 数据驱动校验登录接口的返回码、提示文案与 token 返回情况。"""
        # 用数据中的 title 作为 Allure 动态标题，报告中可读性更好
        allure.dynamic.title(f"数据驱动-登录：{case['title']}")

        with allure.step(f"调用登录接口（用户名={case['username']}）"):
            resp = login(api_client, case["username"], case["password"])
            # 后端接口的 HTTP 状态码恒为 200，业务结果由 body 的 code/message 表达
            assert resp.status_code == 200, f"HTTP 状态码异常：{resp.status_code}"
            payload = resp.json()

        with allure.step("断言业务码与提示文案"):
            assert payload.get("code") == case["expected_code"], (
                f"业务码不符：期望 {case['expected_code']}，实际 {payload.get('code')}，响应：{payload}"
            )
            assert payload.get("message") == case["expected_message"], (
                f"提示文案不符：期望 {case['expected_message']}，实际 {payload.get('message')}"
            )

        with allure.step("断言 token 返回情况"):
            data = payload.get("data")
            if case["expect_token"]:
                # 正常登录：必须返回非空 token
                assert data is not None, f"期望返回 data，实际为空：{payload}"
                assert data.get("token"), f"期望返回 token，实际为空：{payload}"
            else:
                # 异常登录：不应返回 token
                assert not (data and data.get("token")), f"异常场景不应返回 token：{payload}"


@allure.feature("数据驱动测试")
@allure.story("预约接口")
@pytest.mark.api
@pytest.mark.regression
class TestAppointmentDDT:
    """看房预约接口数据驱动用例集（覆盖正常与异常场景）。"""

    @pytest.mark.parametrize("case", APPOINTMENT_CASES, ids=[c["id"] for c in APPOINTMENT_CASES])
    def test_appointment_by_data(self, api_client, auth_headers, case):
        """按 YAML 数据驱动校验预约提交的成功/失败结果。"""
        allure.dynamic.title(f"数据驱动-预约：{case['title']}")
        payload = case["payload"]

        with allure.step("组装预约请求体（映射为后端要求的驼峰结构）"):
            # 后端请求体结构：apartment/tenant/landlord 为对象，appointmentTime 为 yyyy-MM-dd HH:mm:ss
            body = {
                "apartment": {"id": payload.get("apartment_id")},
                "tenant": {"id": payload.get("tenant_id")},
                "landlord": {"id": payload.get("landlord_id")},
                "appointmentTime": payload.get("appointment_time"),  # 缺失字段场景下为 None
                "remark": payload.get("remark", ""),
            }

        with allure.step("携带 token 提交预约"):
            resp = api_client.post("/api/appointments", json=body, headers=auth_headers)

        if case["expect_success"]:
            with allure.step("正向断言：提交成功且状态为待处理"):
                assert resp.status_code == 200, f"HTTP 状态码异常：{resp.status_code}"
                result = resp.json()
                assert result.get("code") == 200, f"预约提交失败：{result}"
                assert result["data"]["status"] == "待处理", (
                    f"新预约状态应为'待处理'，实际：{result['data'].get('status')}"
                )
        else:
            with allure.step("负向断言：提交必须失败（不接受成功）"):
                # 负向场景：缺失必填字段/无效外键，后端可能返回业务码 500 或 HTTP 5xx 异常
                if resp.status_code == 200:
                    result = resp.json()
                    assert result.get("code") != 200, f"预期失败，但预约提交成功了：{result}"
                else:
                    assert resp.status_code >= 400, f"非预期的状态码：{resp.status_code}"