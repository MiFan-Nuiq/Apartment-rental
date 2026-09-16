# -*- coding: utf-8 -*-
"""
房源查询接口封装模块：GET /api/apartments

接口说明：
    - 需携带 Authorization: Bearer <token>（除 /api/auth/** 与 /uploads/** 外均需鉴权）
    - 响应 data 为房源数组，元素含 id/name/address/monthlyRent/status/auditStatus 等字段
"""

from utils.request_util import RequestUtil


def get_apartments(client: RequestUtil, token: str):
    """
    携带 token 查询房源列表。

    参数:
        client: RequestUtil 请求工具实例
        token: 登录获取的 token
    返回:
        requests.Response 响应对象，可用 .json() 解析 ApiResponse
    异常:
        requests 相关异常（网络/超时）
    """
    # 携带统一鉴权头访问房源列表接口
    resp = client.get(
        "/api/apartments",
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp


def get_apartments_without_token(client: RequestUtil):
    """
    不带 token 访问房源列表（用于验证鉴权拦截）。

    参数:
        client: RequestUtil 请求工具实例
    返回:
        requests.Response 响应对象（预期被 Spring Security 拦截返回 401/403）
    异常:
        requests 相关异常（网络/超时）
    """
    # 故意不携带 Authorization 头，验证未认证访问是否被拦截
    resp = client.get("/api/apartments")
    return resp