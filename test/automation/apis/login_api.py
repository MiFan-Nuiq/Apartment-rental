# -*- coding: utf-8 -*-
"""
登录接口封装模块：POST /api/auth/login

接口说明：
    - 请求体：{username, password}
    - 成功响应 data 字段：token / username / realName / role / userId
    - 登录失败（密码错误/用户不存在）时后端以 message 返回业务提示
"""

from utils.request_util import RequestUtil


def login(client: RequestUtil, username: str, password: str):
    """
    调用登录接口获取 token。

    参数:
        client: RequestUtil 请求工具实例（base_url 已在其中配置）
        username: 登录用户名
        password: 登录密码
    返回:
        requests.Response 响应对象，可用 .json() 解析 ApiResponse
    异常:
        requests 相关异常（网络/超时）
    """
    # 登录认证接口属于公开接口（SecurityConfig 放行 /api/auth/**），无需携带 token
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    return resp


def get_token(client: RequestUtil, username: str, password: str) -> str:
    """
    登录并从响应 data.token 中提取 token（供 fixture 与多接口复用）。

    参数:
        client: RequestUtil 请求工具实例
        username: 登录用户名
        password: 登录密码
    返回:
        token 字符串
    异常:
        AssertionError: 登录失败（HTTP 状态码/业务码/字段缺失）
    """
    resp = login(client, username, password)
    # 登录失败给出清晰断言与错误信息，便于 fixture 定位
    assert resp.status_code == 200, f"登录接口 HTTP 状态异常：{resp.status_code}，响应：{resp.text}"
    payload = resp.json()
    assert payload.get("code") == 200, f"登录接口业务码异常，响应：{payload}"
    assert payload.get("message") == "登录成功", f"登录提示文案异常，响应：{payload}"
    data = payload.get("data") or {}
    assert data.get("token"), f"登录成功但未返回 token，响应：{payload}"
    return data["token"]