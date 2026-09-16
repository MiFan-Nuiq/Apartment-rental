# -*- coding: utf-8 -*-
"""
请求工具模块：封装 requests.Session，统一 base_url、超时、日志与请求方法。

用途：
    - 复用同一个 requests.Session 连接池，减少握手开销、统一超时与日志；
    - 所有接口路径统一从 base_url 拼接，避免在多处硬编码完整 URL。
"""

import logging

import requests

# 模块级日志对象，供全工程统一打印请求/响应日志
logger = logging.getLogger(__name__)


class RequestUtil:
    """基于 requests.Session 的 HTTP 请求封装类。"""

    def __init__(self, base_url: str, timeout: int = 10):
        """
        初始化请求工具。

        参数:
            base_url: 后端服务基础地址，如 http://localhost:8080
            timeout: 请求超时时间（秒），默认 10 秒
        异常:
            无（仅保存配置）
        """
        self.base_url = base_url.rstrip("/")  # 去掉末尾斜杠，避免拼接时出现双斜杠
        self.timeout = timeout
        self.session = requests.Session()  # 复用会话，保持连接池与 cookie

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        发送请求的内部通用方法（get/post/put/delete 均经由该方法）。

        参数:
            method: HTTP 方法（小写，如 get/post/put/delete）
            path: 接口路径，如 /api/auth/login
            kwargs: 透传 requests 请求参数（json/headers/params 等）
        返回:
            requests.Response 响应对象
        异常:
            请求失败时抛出 requests 相关异常
        """
        # 从 base_url 拼接完整 URL，防止调用方自行写死完整地址
        url = f"{self.base_url}{path}"
        # 统一注入默认超时，调用方也可通过 kwargs 覆盖
        kwargs.setdefault("timeout", self.timeout)
        logger.info("请求 %s %s", method.upper(), url)
        resp = self.session.request(method, url, **kwargs)
        logger.info("响应 %s %s 状态码=%s", method.upper(), url, resp.status_code)
        return resp

    def get(self, path: str, **kwargs) -> requests.Response:
        """
        发送 GET 请求。

        参数:
            path: 接口路径，如 /api/apartments
            kwargs: 透传 requests 参数（headers/params 等）
        返回:
            requests.Response 响应对象
        异常:
            请求失败时抛出 requests 相关异常
        """
        return self._request("get", path, **kwargs)

    def post(self, path: str, **kwargs) -> requests.Response:
        """
        发送 POST 请求。

        参数:
            path: 接口路径，如 /api/auth/login
            kwargs: 透传 requests 参数（json/headers/params 等）
        返回:
            requests.Response 响应对象
        异常:
            请求失败时抛出 requests 相关异常
        """
        return self._request("post", path, **kwargs)

    def put(self, path: str, **kwargs) -> requests.Response:
        """
        发送 PUT 请求。

        参数:
            path: 接口路径
            kwargs: 透传 requests 参数（json/headers/params 等）
        返回:
            requests.Response 响应对象
        异常:
            请求失败时抛出 requests 相关异常
        """
        return self._request("put", path, **kwargs)

    def delete(self, path: str, **kwargs) -> requests.Response:
        """
        发送 DELETE 请求。

        参数:
            path: 接口路径
            kwargs: 透传 requests 参数（json/headers/params 等）
        返回:
            requests.Response 响应对象
        异常:
            请求失败时抛出 requests 相关异常
        """
        return self._request("delete", path, **kwargs)