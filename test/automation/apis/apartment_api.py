# -*- coding: utf-8 -*-
"""
房源接口封装模块：/api/apartments

接口清单（对齐 backend/.../controller/ApartmentController.java，未臆造任何路径）：
    - GET    /api/apartments            查询房源列表
    - GET    /api/apartments/{id}       按 id 查询单个房源
    - POST   /api/apartments            创建房源（动态测试数据用）
    - DELETE /api/apartments/{id}       删除房源（动态测试数据清理用）

通用说明：
    - 需携带 Authorization: Bearer <token>（除 /api/auth/** 与 /uploads/** 外均需鉴权）
    - 响应 data 为房源数组或单个房源，元素含 id/name/address/monthlyRent/status/auditStatus 等字段
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


def get_apartment_by_id(client: RequestUtil, token: str, apartment_id: int):
    """
    按 id 查询单个房源。

    参数:
        client: RequestUtil 请求工具实例
        token: 登录获取的 token
        apartment_id: 房源 id
    返回:
        requests.Response 响应对象；房源存在时 data 为该房源对象，
        房源不存在时后端 ApartmentService.findById 抛异常，接口返回 HTTP 500（非 ApiResponse 结构）
    异常:
        requests 相关异常（网络/超时）
    """
    # 用于校验动态数据清理结果：删除后再次查询应拿不到成功响应
    resp = client.get(
        f"/api/apartments/{apartment_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp


def create_apartment(client: RequestUtil, token: str, payload: dict):
    """
    创建房源（供动态测试数据 fixture 使用）。

    接口路径: POST /api/apartments
    请求方法: POST
    参数:
        client: RequestUtil 请求工具实例
        token: 登录获取的 token
        payload: 房源请求体字典，至少包含 name；
                 landlord 需以嵌套对象传入（如 {"id": 2}），
                 status / auditStatus 不传时后端默认为 空置 / 待审核
    返回:
        requests.Response 响应对象，成功时 data 为新建房源（含自增 id）
    异常:
        requests 相关异常（网络/超时）
    """
    # 与后端 ApartmentController#save(@RequestBody Apartment) 的实体字段保持一致
    resp = client.post(
        "/api/apartments",
        json=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    return resp


def delete_apartment(client: RequestUtil, token: str, apartment_id: int):
    """
    删除房源（供动态测试数据清理使用）。

    接口路径: DELETE /api/apartments/{id}
    请求方法: DELETE
    参数:
        client: RequestUtil 请求工具实例
        token: 登录获取的 token
        apartment_id: 待删除的房源 id
    返回:
        requests.Response 响应对象，成功时 message 为"删除成功"、data 为 null
    异常:
        requests 相关异常（网络/超时）
    """
    resp = client.delete(
        f"/api/apartments/{apartment_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp