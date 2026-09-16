# -*- coding: utf-8 -*-
"""
断言工具模块：封装常用断言，统一失败提示，便于用例复用与排错。

说明：
    项目后端统一返回结构 ApiResponse：{ code, message, data }
    - code=200 表示业务成功；
    - 鉴权失败由 Spring Security 返回 HTTP 401/403。
"""

import requests


def assert_status_code(resp: requests.Response, expected: int = 200):
    """
    断言 HTTP 状态码。

    参数:
        resp: requests.Response 响应对象
        expected: 期望的 HTTP 状态码，默认 200
    返回:
        无；断言失败时抛 AssertionError
    异常:
        AssertionError：实际状态码与期望不符
    """
    # 失败时附带完整响应体便于定位
    assert resp.status_code == expected, (
        f"HTTP 状态码错误：期望 {expected}，实际 {resp.status_code}，响应体：{resp.text}"
    )


def assert_business_code(resp: requests.Response, expected_code: int = 200):
    """
    断言业务返回码（resp.json() 中的 code 字段）。

    参数:
        resp: requests.Response 响应对象
        expected_code: 期望的业务 code，默认 200
    返回:
        无；断言失败时抛 AssertionError
    异常:
        AssertionError：实际业务码与期望不符
    """
    payload = resp.json()
    actual = payload.get("code")
    assert actual == expected_code, (
        f"业务码错误：期望 {expected_code}，实际 {actual}，响应体：{payload}"
    )


def assert_field_exists(data: dict, fields: list):
    """
    断言字典中必须存在指定字段。

    参数:
        data: 接口返回的业务数据（dict）
        fields: 需要校验存在的字段名列表
    返回:
        无；断言失败时抛 AssertionError
    异常:
        AssertionError：存在缺失字段
    """
    for field in fields:
        # 缺失字段精确到字段名，便于快速定位
        assert field in data, f"响应数据缺少字段 {field}，当前字段：{list(data.keys())}"


def assert_field_equal(data: dict, field: str, expected):
    """
    断言字典指定字段值等于期望值。

    参数:
        data: 接口返回的业务数据（dict）
        field: 字段名
        expected: 期望值
    返回:
        无；断言失败时抛 AssertionError
    异常:
        AssertionError：字段实际值与期望值不符
    """
    actual = data.get(field)
    assert actual == expected, f"字段 {field} 值错误：期望 {expected}，实际 {actual}"


def assert_list_not_empty(data_list: list, message: str = "列表为空"):
    """
    断言列表非空。

    参数:
        data_list: 接口返回的列表数据
        message: 失败时的自定义提示，默认"列表为空"
    返回:
        无；断言失败时抛 AssertionError
    异常:
        AssertionError：列表为空
    """
    assert isinstance(data_list, list) and len(data_list) > 0, message