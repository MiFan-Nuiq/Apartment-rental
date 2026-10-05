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

重构说明：
    请求逻辑（拼路径、带 token、超时、日志）已上提到 apis/base_api.py 的 BaseApi，
    本模块只保留房源相关的接口方法；类外仍保留同名的模块级函数（签名与返回值不变），
    以便 testcases 与 conftest 继续按原方式调用。
"""

from apis.base_api import BaseApi


class ApartmentApi(BaseApi):
    """房源接口类：封装 /api/apartments 下各接口的调用。"""

    def __init__(self, api_client, token: str = None):
        """
        初始化房源接口类。

        参数:
            api_client: 请求工具实例
            token: 登录 token；传 None 表示不带鉴权头（用于未登录访问的用例）
        返回:
            无
        """
        # 基础路径与后端 ApartmentController 的 @RequestMapping 保持一致
        super().__init__(api_client, "/api/apartments", token)

    def get_apartments(self):
        """
        查询房源列表。

        接口路径: GET /api/apartments
        请求方法: GET
        返回:
            requests.Response 响应对象，可用 .json() 解析 ApiResponse
        异常:
            requests 相关异常（网络/超时）
        """
        return self.get()

    def get_apartment_by_id(self, apartment_id: int):
        """
        按 id 查询单个房源。

        接口路径: GET /api/apartments/{id}
        请求方法: GET
        参数:
            apartment_id: 房源 id
        返回:
            requests.Response 响应对象；房源存在时 data 为该房源对象，
            房源不存在时后端抛异常，接口返回 HTTP 500（非 ApiResponse 结构）
        异常:
            requests 相关异常（网络/超时）
        """
        return self.get(apartment_id)

    def create_apartment(self, payload: dict):
        """
        创建房源（供动态测试数据 fixture 使用）。

        接口路径: POST /api/apartments
        请求方法: POST
        参数:
            payload: 房源请求体字典，至少包含 name；
                     landlord 需以嵌套对象传入（如 {"id": 2}），
                     status / auditStatus 不传时后端默认为 空置 / 待审核
        返回:
            requests.Response 响应对象，成功时 data 为新建房源（含自增 id）
        异常:
            requests 相关异常（网络/超时）
        """
        return self.post(json=payload)

    def delete_apartment(self, apartment_id: int):
        """
        删除房源（供动态测试数据清理使用）。

        接口路径: DELETE /api/apartments/{id}
        请求方法: DELETE
        参数:
            apartment_id: 待删除的房源 id
        返回:
            requests.Response 响应对象，成功时 message 为"删除成功"、data 为 null
        异常:
            requests 相关异常（网络/超时）
        """
        return self.delete(apartment_id)


# ==================== 模块级兼容函数（签名与返回值保持不变） ====================
# 保留这些函数是为了让 testcases / conftest 无需修改即可继续使用；
# 每个函数只负责构造 ApartmentApi 并转调对应方法。


def get_apartments(client, token: str):
    """携带 token 查询房源列表（兼容函数式调用，签名不变）。"""
    return ApartmentApi(client, token).get_apartments()


def get_apartments_without_token(client):
    """不带 token 访问房源列表（用于验证鉴权拦截；兼容函数式调用，签名不变）。"""
    # 不传 token：BaseApi 不会附加 Authorization 头
    return ApartmentApi(client, None).get_apartments()


def get_apartment_by_id(client, token: str, apartment_id: int):
    """按 id 查询单个房源（兼容函数式调用，签名不变）。"""
    return ApartmentApi(client, token).get_apartment_by_id(apartment_id)


def create_apartment(client, token: str, payload: dict):
    """创建房源（兼容函数式调用，签名不变）。"""
    return ApartmentApi(client, token).create_apartment(payload)


def delete_apartment(client, token: str, apartment_id: int):
    """删除房源（兼容函数式调用，签名不变）。"""
    return ApartmentApi(client, token).delete_apartment(apartment_id)