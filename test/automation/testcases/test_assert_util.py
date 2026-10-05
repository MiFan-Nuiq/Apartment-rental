# -*- coding: utf-8 -*-
"""
断言工具自身的用例：验证 utils/assert_util.py 中 assert_business_error 对 expected_code 的处理。

覆盖点：
    test_assert_business_error_with_expected_code
        - 形态①【HTTP 200 + 业务码 500】：传 expected_code=500 应通过，传 404 应失败（抛 AssertionError）；
        - 形态②【HTTP 403 + Spring 默认错误页（响应体无 code 字段）】：
          此时无从比对业务码，传 expected_code 应跳过比对、不误报。

为什么要单独给断言工具写用例：
    assert_business_error 要同时兼容后端两种失败形态（业务错误被 try/catch 包住返回 HTTP 200 +
    业务码 500；未捕获异常由 Spring 兜底返回 HTTP 5xx 且响应体不含 code）。
    这两种形态下 expected_code 的处理逻辑不同，属于断言工具自身的分支逻辑，
    必须有用例覆盖，否则一旦改动容易悄悄失效（覆盖率报告里这两段正是未覆盖行）。

分层结构：
    testcases（本文） -> apis（接口层） -> utils（断言工具）
"""

import allure
import pytest

from apis.login_api import login
from utils.assert_util import assert_business_error

# 后端 AuthController 对"用户不存在"以 try/catch 返回业务错误（HTTP 200 + 业务码 500）
NON_EXIST_USERNAME = "no_such_user"
NON_EXIST_PASSWORD = "123456"
# 未携带 token 访问受保护接口时，Spring Security 直接返回 401/403（响应体是默认错误页，无 code 字段）
PROTECTED_ENDPOINT = "/api/users"


@allure.feature("测试工具")
@allure.story("断言工具 assert_business_error")
@pytest.mark.api
@pytest.mark.regression
class TestAssertBusinessError:
    """断言工具 assert_business_error 的 expected_code 分支用例。"""

    @allure.title("断言工具：expected_code 在两种失败形态下的处理")
    def test_assert_business_error_with_expected_code(self, api_client):
        """
        验证 assert_business_error(resp, expected_code) 在两种失败形态下的行为。

        依赖:
            api_client: 请求工具（用于构造真实的失败响应；本用例不新建任何业务数据）
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例只读不写，无需清理
        """
        # ---------- 形态①：HTTP 200 + 业务码 500 ----------
        with allure.step("构造形态①：登录不存在的用户 -> HTTP 200 + 业务码 500"):
            resp = login(api_client, NON_EXIST_USERNAME, NON_EXIST_PASSWORD)
            # 先确认响应确实是"HTTP 200 + 业务码 500"这一形态，避免用例前提不成立
            assert resp.status_code == 200, f"预期 HTTP 200，实际 {resp.status_code}，响应：{resp.text}"
            assert resp.json().get("code") == 500, f"预期业务码 500，响应：{resp.json()}"

        with allure.step("形态①：expected_code=500 时断言应通过"):
            # 不抛异常即为通过
            assert_business_error(resp, 500)

        with allure.step("形态①：expected_code=404 不符时断言应失败"):
            with pytest.raises(AssertionError):
                assert_business_error(resp, 404)

        # ---------- 形态②：HTTP 非 200 + 响应体无 code 字段 ----------
        with allure.step("构造形态②：未带 token 访问受保护接口 -> HTTP 401/403（无 code 字段）"):
            http_resp = api_client.get(PROTECTED_ENDPOINT)
            assert http_resp.status_code in (401, 403), (
                f"未登录访问应返回 401/403，实际：{http_resp.status_code}，响应：{http_resp.text}"
            )
            # Spring 默认错误页不含 code 字段，这正是"无从比对业务码"的前提
            assert http_resp.json().get("code") is None, f"预期响应体无 code 字段：{http_resp.text}"

        with allure.step("形态②：expected_code 无从比对时应跳过、不误报"):
            # 不抛异常即为通过：说明实现里对"无 code 字段"的情况做了跳过处理
            assert_business_error(http_resp, 500)