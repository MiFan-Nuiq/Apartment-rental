# -*- coding: utf-8 -*-
"""
登录接口封装模块：POST /api/auth/login

接口说明：
    - 请求体：{username, password}
    - 成功响应 data 字段：token / username / realName / role / userId
    - 登录失败（密码错误/用户不存在）时后端以 message 返回业务提示

重构说明：
    请求逻辑（拼路径、超时、日志）已上提到 apis/base_api.py 的 BaseApi；
    登录接口属于公开接口（SecurityConfig 放行 /api/auth/**），因此**不带鉴权头**。
    类外仍保留同名的模块级函数（签名与返回值不变），
    以便 testcases 与 conftest 继续按原方式调用。
"""

from apis.base_api import BaseApi


class LoginApi(BaseApi):
    """登录接口类：封装 /api/auth 下的登录接口调用。"""

    def __init__(self, api_client):
        """
        初始化登录接口类。

        参数:
            api_client: 请求工具实例
        返回:
            无
        说明:
            登录接口无需鉴权，因此构造时 token 固定传 None。
        """
        # 基础路径与后端 AuthController 的 @RequestMapping 保持一致
        super().__init__(api_client, "/api/auth", None)

    def login(self, username: str, password: str):
        """
        调用登录接口获取 token。

        接口路径: POST /api/auth/login
        请求方法: POST
        参数:
            username: 登录用户名
            password: 登录密码
        返回:
            requests.Response 响应对象，可用 .json() 解析 ApiResponse
        异常:
            requests 相关异常（网络/超时）
        """
        return self.post("/login", json={"username": username, "password": password})

    def get_token(self, username: str, password: str) -> str:
        """
        登录并从响应 data.token 中提取 token（供 fixture 与多接口复用）。

        接口路径: POST /api/auth/login
        请求方法: POST
        参数:
            username: 登录用户名
            password: 登录密码
        返回:
            token 字符串
        异常:
            AssertionError: 登录失败（HTTP 状态码/业务码/字段缺失）
        """
        resp = self.login(username, password)
        # 登录失败给出清晰断言与错误信息，便于 fixture 定位
        assert resp.status_code == 200, f"登录接口 HTTP 状态异常：{resp.status_code}，响应：{resp.text}"
        payload = resp.json()
        assert payload.get("code") == 200, f"登录接口业务码异常，响应：{payload}"
        assert payload.get("message") == "登录成功", f"登录提示文案异常，响应：{payload}"
        data = payload.get("data") or {}
        assert data.get("token"), f"登录成功但未返回 token，响应：{payload}"
        return data["token"]


# ==================== 模块级兼容函数（签名与返回值保持不变） ====================


def login(client, username: str, password: str):
    """调用登录接口获取 token（兼容函数式调用，签名不变）。"""
    return LoginApi(client).login(username, password)


def get_token(client, username: str, password: str) -> str:
    """登录并提取 token（兼容函数式调用，签名不变）。"""
    return LoginApi(client).get_token(username, password)