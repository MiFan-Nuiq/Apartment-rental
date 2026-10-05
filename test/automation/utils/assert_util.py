# -*- coding: utf-8 -*-
"""
断言工具模块：封装常用断言，统一失败提示，便于用例复用与排错。

说明：
    项目后端统一返回结构 ApiResponse：{ code, message, data }
    - code=200 表示业务成功；
    - 鉴权失败由 Spring Security 返回 HTTP 401/403。

统一断言入口（正向 / 负向用例各一个，推荐优先使用）：
    - assert_success(resp)                     断言成功：HTTP 200 且业务码 200
    - assert_business_error(resp, expected_code) 断言失败：兼容"HTTP 200+业务码非 200"
                                                与"HTTP 500+Spring 默认错误页"两种形态
"""

import requests


def assert_success(resp: requests.Response):
    """
    断言接口调用成功（正向用例统一入口）。

    参数:
        resp: requests.Response 响应对象
    返回:
        无；断言失败时抛 AssertionError
    异常:
        AssertionError：HTTP 状态码非 200，或业务码非 200
    说明:
        项目后端成功时 HTTP 状态码恒为 200，响应体为
        {"code": 200, "message": "...", "data": ...}，因此两者都要校验。
    """
    # 先校验 HTTP 层，再校验业务层，失败信息各自带上完整响应便于定位
    assert resp.status_code == 200, (
        f"接口未返回 HTTP 200：实际 {resp.status_code}，响应体：{resp.text}"
    )
    payload = resp.json()
    assert payload.get("code") == 200, (
        f"业务码非 200：实际 {payload.get('code')}，响应体：{payload}"
    )


def assert_business_error(resp: requests.Response, expected_code: int = None):
    """
    断言接口调用失败（负向用例统一入口）。

    参数:
        resp: requests.Response 响应对象
        expected_code: 期望的业务码；传 None 时只要求"不是成功响应"
    返回:
        无；断言失败时抛 AssertionError
    异常:
        AssertionError：返回了成功响应，或状态码/业务码不符合预期
    兼容的两种失败形态（本项目后端两种都会出现）:
        ① 【业务错误】HTTP 200 + 业务码非 200：
           异常被后端 try/catch 捕获，以 ApiResponse.error 返回（业务码恒为 500）；
        ② 【HTTP 错误】HTTP 非 200（多为 500）：
           异常未被捕获，由 Spring 兜底返回默认错误页
           （{"timestamp":..., "status":500, "error":"Internal Server Error"}），
           该响应体**没有 code 字段**，无法比对业务码；
           此时按"HTTP 状态码 >= 400"判定失败，expected_code 仅在响应体确实带 code 时才比对。
    """
    # ---------- 形态①：HTTP 200，用业务码判定成功/失败 ----------
    if resp.status_code == 200:
        payload = resp.json()
        actual = payload.get("code")
        assert actual != 200, f"预期失败，但接口返回成功，响应体：{payload}"
        if expected_code is not None:
            assert actual == expected_code, (
                f"业务码不符：期望 {expected_code}，实际 {actual}，响应体：{payload}"
            )
        return

    # ---------- 形态②：HTTP 非 200，用状态码判定失败 ----------
    assert resp.status_code >= 400, (
        f"非预期的 HTTP 状态码：{resp.status_code}（预期失败时应 >= 400），响应体：{resp.text}"
    )
    if expected_code is not None:
        try:
            actual = resp.json().get("code")
        except ValueError:
            # 响应体不是合法 JSON，无法比对业务码
            actual = None
        # Spring 默认错误页不含 code 字段（actual 为 None），此时无从比对，跳过
        assert actual is None or actual == expected_code, (
            f"业务码不符：期望 {expected_code}，实际 {actual}，响应体：{resp.text}"
        )


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