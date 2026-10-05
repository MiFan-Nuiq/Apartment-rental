# -*- coding: utf-8 -*-
"""
权限隔离接口自动化用例：验证不同角色对受保护接口的访问边界

覆盖点：
    1. test_admin_can_access_admin_endpoint
       正向：admin 的 token 调用管理员专属接口（用户管理 /api/users），返回成功
    2. test_landlord_cannot_access_admin_endpoint   【当前 xfail，缺陷 BUG-PERM-001】
       landlord 的 token 调用管理员专属接口，应被拒绝
    3. test_tenant_cannot_access_admin_endpoint     【当前 xfail，缺陷 BUG-PERM-002】
       tenant 的 token 调用管理员专属接口，应被拒绝
    4. test_tenant_cannot_publish_apartment         【当前 xfail，缺陷 BUG-PERM-003】
       tenant 的 token 调用房东专属接口（房源发布 POST /api/apartments），应被拒绝
    5. test_no_token_cannot_access_protected_endpoint
       正向：未登录（无 token）调用任意受保护接口，返回 401/403
    6. test_user_endpoint_does_not_leak_password    【当前 xfail，缺陷 BUG-PERM-004】
       敏感数据保护：用户管理接口（列表与详情）的响应体不得包含 password 字段

关于角色账号：
    login_api.login / get_token 本身已支持传入任意 username/password，
    因此**无需改动 login_api.py**；本文件在其之上补了一层"角色 → 鉴权头"映射
    （module 级 fixture role_headers），并顺带校验账号角色与预期一致。

关于 4 个 xfail 用例（重要，实测结论）：
    后端 SecurityConfig 的授权规则只有 `.antMatchers("/api/**").authenticated()`，
    **全项目没有任何基于角色的授权**（无 hasRole/hasAuthority，也无 @PreAuthorize），
    且 JwtAuthenticationFilter 在构建认证信息时传入的是空权限集合（new ArrayList<>()），
    也就是说：只要登录了，任何角色都能调用任何 /api/** 接口。
    实测确认：landlord / tenant 调用 /api/users 均返回 HTTP 200/code 200，
    tenant 调用房源发布接口甚至真的创建出了房源。
    另外实测发现 /api/users 的响应体会直接带出用户的 BCrypt 密码哈希（BUG-PERM-004）。
    因此这四条用例的断言**保持严格**（要求"必须被拒绝"/"必须不泄露"），按项目既有约定
    （参见 test_data_consistency.py 中 BUG-DATA-001、test_payment.py 中 BUG-PAY-* 的处理方式）
    标记为 xfail，并已在 test/docs/Bug清单_实际发现.md 登记缺陷。
    后端修复后，这四条会自动转为 XPASS，提示去掉 xfail 标记即可。

分层结构：
    testcases（本文） -> apis（接口层） -> utils（请求/断言工具）
"""

import allure
import pytest

from apis.apartment_api import create_apartment, delete_apartment
from apis.login_api import login
from utils.assert_util import (
    assert_business_code,
    assert_list_not_empty,
    assert_status_code,
)

# 临时房源请求体构造器与房东 id 统一取自 conftest，保证与其它模块口径一致
from conftest import build_temp_apartment_payload

# ==================== 角色账号与专属接口（对齐真实代码，未臆造） ====================
# 账号来自后端 DataInitializer / test/sql/data.sql：1=ADMIN、2=LANDLORD、3=TENANT
ROLE_ACCOUNTS = {
    "admin": ("admin", "123456"),
    "landlord": ("landlord", "123456"),
    "tenant": ("tenant", "123456"),
}

# 管理员专属接口：用户管理（backend/.../controller/AuthController.java 内的 UserController）
ADMIN_ONLY_ENDPOINT = "/api/users"
# 房东专属动作：房源发布（ApartmentController#save，前端在房东端"房源管理"中使用）
LANDLORD_ONLY_ENDPOINT = "/api/apartments"
# ================================================================================


@pytest.fixture(scope="module")
def role_headers(api_client) -> dict:
    """
    module 级 fixture：用三种角色账号分别登录，返回 {角色: 鉴权请求头}。

    依赖:
        api_client: conftest 中 session 级的请求工具
    返回:
        dict，形如 {"admin": {"Authorization": "Bearer xxx"}, "landlord": {...}, "tenant": {...}}
    说明:
        login_api.login 已支持传入任意 username/password，本 fixture 只在其之上
        补一层"角色 → 鉴权头"的映射，供权限隔离用例复用（module 级只登录一次）；
        登录时顺带断言返回的 role 与账号预期一致，
        避免账号数据被改动后用例结论失真（例如 tenant 账号被改成了房东角色）。
    异常:
        AssertionError: 登录失败，或账号实际角色与预期不符
    """
    headers = {}
    for role, (username, password) in ROLE_ACCOUNTS.items():
        resp = login(api_client, username, password)
        assert resp.status_code == 200, f"{role} 账号登录失败：HTTP {resp.status_code}，响应：{resp.text}"
        body = resp.json()
        assert body.get("code") == 200, f"{role} 账号登录失败：{body}"
        data = body.get("data") or {}
        # 角色自检：确保该账号真的是预期角色，否则权限结论不可信
        assert data.get("role") == role.upper(), (
            f"{username} 账号角色应为 {role.upper()}，实际：{data.get('role')}"
        )
        headers[role] = {"Authorization": f"Bearer {data['token']}"}
    return headers


def assert_access_denied(resp, case_title: str):
    """
    断言"越权访问必须被拒绝"（负向断言风格与 test_contract.py / test_payment.py 一致）。

    参数:
        resp: 接口返回的响应对象
        case_title: 中文用例标题，用于失败提示
    返回:
        无；断言失败时抛 AssertionError
    说明:
        HTTP≠200 时要求 ≥400；HTTP=200 时业务码必须非 200（不接受成功响应）。
    """
    if resp.status_code == 200:
        body = resp.json()
        assert body.get("code") != 200, f"{case_title}：预期被拒绝，但接口返回成功，响应：{body}"
    else:
        assert resp.status_code >= 400, f"{case_title}：非预期的状态码 {resp.status_code}，响应：{resp.text}"


@allure.feature("权限隔离")
@allure.story("角色访问控制")
@pytest.mark.api
@pytest.mark.regression
class TestPermission:
    """权限隔离测试类：覆盖管理员专属接口、房东专属接口与未登录访问的边界。"""

    @allure.title("权限：管理员可正常访问管理员专属接口（用户管理）")
    def test_admin_can_access_admin_endpoint(self, api_client, role_headers):
        """
        验证 admin 的 token 可以正常调用管理员专属接口（用户管理）。

        依赖:
            api_client: 请求工具
            role_headers: 三角色鉴权头（本用例使用 admin）
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例只读不写，无需清理
        """
        with allure.step(f"用 admin 的 token 调用 {ADMIN_ONLY_ENDPOINT}"):
            resp = api_client.get(ADMIN_ONLY_ENDPOINT, headers=role_headers["admin"])
            assert_status_code(resp, 200)
            assert_business_code(resp, 200)

        with allure.step("校验用户列表返回结构与三种角色数据"):
            users = resp.json().get("data")
            assert_list_not_empty(users, "用户管理接口返回的用户列表为空")
            # 关键字段完整性
            for user in users:
                assert "id" in user, f"用户记录缺少 id 字段：{user}"
                assert "username" in user, f"用户记录缺少 username 字段：{user}"
                assert "role" in user, f"用户记录缺少 role 字段：{user}"
            # 种子数据中应同时存在三种角色，证明该接口返回的是完整用户数据
            roles = {user.get("role") for user in users}
            assert {"ADMIN", "LANDLORD", "TENANT"} <= roles, f"用户列表缺少预期角色，实际角色集合：{roles}"

    @allure.title("权限：房东访问管理员专属接口应被拒绝")
    @pytest.mark.xfail(
        reason="BUG-PERM-001：后端无任何基于角色的授权（SecurityConfig 仅 authenticated()，"
        "JwtAuthenticationFilter 传入空权限集合），landlord 调用 /api/users 实测返回 HTTP 200/code 200",
        strict=False,
    )
    def test_landlord_cannot_access_admin_endpoint(self, api_client, role_headers):
        """
        验证 landlord 的 token 调用管理员专属接口时必须被拒绝。

        依赖:
            api_client: 请求工具
            role_headers: 三角色鉴权头（本用例使用 landlord）
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            本用例只读不写，无需清理
        备注:
            断言保持严格（要求必须被拒绝）。当前后端无角色鉴权 → 用例 xfail（BUG-PERM-001），
            后端补齐后会自动转为 XPASS。
        """
        with allure.step(f"用 landlord 的 token 调用管理员专属接口 {ADMIN_ONLY_ENDPOINT}"):
            resp = api_client.get(ADMIN_ONLY_ENDPOINT, headers=role_headers["landlord"])

        with allure.step("断言房东越权访问被拒绝"):
            assert_access_denied(resp, "房东访问管理员专属接口")

    @allure.title("权限：租客访问管理员专属接口应被拒绝")
    @pytest.mark.xfail(
        reason="BUG-PERM-002：后端无任何基于角色的授权，tenant 调用 /api/users 实测返回 HTTP 200/code 200",
        strict=False,
    )
    def test_tenant_cannot_access_admin_endpoint(self, api_client, role_headers):
        """
        验证 tenant 的 token 调用管理员专属接口时必须被拒绝。

        依赖:
            api_client: 请求工具
            role_headers: 三角色鉴权头（本用例使用 tenant）
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            本用例只读不写，无需清理
        备注:
            断言保持严格（要求必须被拒绝）。当前后端无角色鉴权 → 用例 xfail（BUG-PERM-002），
            后端补齐后会自动转为 XPASS。
        """
        with allure.step(f"用 tenant 的 token 调用管理员专属接口 {ADMIN_ONLY_ENDPOINT}"):
            resp = api_client.get(ADMIN_ONLY_ENDPOINT, headers=role_headers["tenant"])

        with allure.step("断言租客越权访问被拒绝"):
            assert_access_denied(resp, "租客访问管理员专属接口")

    @allure.title("权限：租客发布房源（房东专属动作）应被拒绝")
    @pytest.mark.xfail(
        reason="BUG-PERM-003：后端无任何基于角色的授权，tenant 调用 POST /api/apartments 实测返回 "
        "HTTP 200/code 200 并真实创建出房源",
        strict=False,
    )
    def test_tenant_cannot_publish_apartment(
        self,
        api_client,
        role_headers,
        unique_suffix,
        dynamic_data_cleaner,
    ):
        """
        验证 tenant 的 token 调用房东专属接口（房源发布）时必须被拒绝。

        依赖:
            api_client: 请求工具
            role_headers: 三角色鉴权头（本用例使用 tenant）
            unique_suffix: 唯一后缀（房源命名，便于识别残留数据）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            若越权创建"意外成功"（当前即为该缺陷），会立即登记删除该房源，
            保证用例结束（含失败）后不残留脏数据
        备注:
            断言保持严格（要求必须被拒绝）。当前后端无角色鉴权 → 用例 xfail（BUG-PERM-003），
            后端补齐后会自动转为 XPASS。
        """
        name = f"自动化临时房源-{unique_suffix}-perm"
        payload = build_temp_apartment_payload(name)
        token = role_headers["tenant"]["Authorization"].replace("Bearer ", "")

        with allure.step(f"用 tenant 的 token 调用房东专属接口 {LANDLORD_ONLY_ENDPOINT}（房源发布）"):
            resp = create_apartment(api_client, token, payload)

        # 只要真的创建成功（当前缺陷场景）就登记清理，避免脏数据残留
        created_id = None
        if resp.status_code == 200:
            created_id = (resp.json().get("data") or {}).get("id")
        if created_id:
            dynamic_data_cleaner(delete_apartment, created_id, "临时房源")

        with allure.step("断言租客越权发布房源被拒绝"):
            assert_access_denied(resp, "租客发布房源（房东专属动作）")

    @allure.title("权限：未登录访问受保护接口返回 401/403")
    def test_no_token_cannot_access_protected_endpoint(self, api_client):
        """
        验证未携带 token 访问受保护接口时被 Spring Security 拦截，返回 401 或 403。

        依赖:
            api_client: 请求工具（本用例刻意不传鉴权头）
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例只读不写，无需清理
        说明:
            认证失败由 Spring Security 直接返回默认错误结构（非 ApiResponse，没有 code 字段），
            因此这里显式校验 HTTP 状态码与响应体中的 error 文案，做到"明确检查权限错误码或错误信息"。
        """
        with allure.step(f"不携带任何 token 调用受保护接口 {ADMIN_ONLY_ENDPOINT}"):
            resp = api_client.get(ADMIN_ONLY_ENDPOINT)

        with allure.step("断言返回 401 或 403"):
            assert resp.status_code in (401, 403), (
                f"未登录访问应返回 401/403，实际：{resp.status_code}，响应：{resp.text}"
            )

        with allure.step("断言响应体中的权限错误码与错误信息"):
            body = resp.json()
            assert body.get("status") in (401, 403), f"响应体中的 status 异常：{body}"
            assert body.get("error") in ("Unauthorized", "Forbidden"), f"响应体中的 error 文案异常：{body}"
            # 认证失败不应返回业务成功码
            assert body.get("code") != 200, f"未登录访问不应返回业务成功：{body}"


@allure.feature("权限隔离")
@allure.story("敏感数据保护")
@pytest.mark.api
@pytest.mark.regression
class TestSensitiveDataProtection:
    """敏感数据保护测试类：验证接口响应体不泄露密码等敏感字段。"""

    @allure.title("敏感数据：用户管理接口响应体不应包含 password 字段")
    @pytest.mark.xfail(
        reason="BUG-PERM-004：UserController 直接返回 JPA 实体 User，password 字段既无 @JsonIgnore "
        "也未走 DTO 转换，实测 /api/users 的列表与详情响应都带出 BCrypt 密码哈希",
        strict=False,
    )
    def test_user_endpoint_does_not_leak_password(self, api_client, role_headers):
        """
        验证用户管理接口（列表 + 详情）的响应体不包含 password 字段。

        依赖:
            api_client: 请求工具
            role_headers: 三角色鉴权头（本用例走 admin 的**合法**访问路径，
                          强调"即便权限正确也不应返回密码字段"）
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例只读不写，无需清理
        备注:
            断言保持严格（要求响应体必须不含 password）。
            当前后端直接序列化 User 实体 → 用例 xfail（BUG-PERM-004），修复后会自动转为 XPASS。
        """
        # ---------- 步骤一：用户列表 ----------
        with allure.step(f"用 admin 的 token 调用 {ADMIN_ONLY_ENDPOINT} 获取用户列表"):
            resp = api_client.get(ADMIN_ONLY_ENDPOINT, headers=role_headers["admin"])
            assert_status_code(resp, 200)
            assert_business_code(resp, 200)

        users = resp.json().get("data")
        assert_list_not_empty(users, "用户管理接口返回的用户列表为空")

        with allure.step("断言列表响应中任何用户对象都不携带 password 字段"):
            # 核心断言：逐个用户检查，并列出泄露涉及的账号便于定位
            # 注意：断言信息里只回显账号名，不打印哈希值本身，避免把敏感数据再写进测试日志
            leaked = [user.get("username") for user in users if "password" in user]
            assert leaked == [], (
                f"用户列表接口泄露了 password 字段，涉及账号：{leaked}；"
                f"应通过 @JsonIgnore 注解或在 DTO 中剔除该字段"
            )

        # ---------- 步骤二：用户详情 ----------
        user_id = users[0].get("id")
        with allure.step(f"用 admin 的 token 调用 {ADMIN_ONLY_ENDPOINT}/{user_id} 获取用户详情"):
            detail_resp = api_client.get(f"{ADMIN_ONLY_ENDPOINT}/{user_id}", headers=role_headers["admin"])
            assert_status_code(detail_resp, 200)
            assert_business_code(detail_resp, 200)

        with allure.step("断言详情响应同样不携带 password 字段"):
            detail = detail_resp.json().get("data") or {}
            # 同样只回显账号名，不回显哈希值
            assert "password" not in detail, (
                f"用户详情接口泄露了 password 字段（账号：{detail.get('username')}）"
            )