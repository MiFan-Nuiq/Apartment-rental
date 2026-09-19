# -*- coding: utf-8 -*-
"""
看房预约接口封装模块：/api/appointments

接口清单（对齐 backend/.../controller/AppointmentController.java，未臆造任何路径）：
    - POST   /api/appointments          提交预约
    - GET    /api/appointments/{id}     按 id 查询预约
    - DELETE /api/appointments/{id}     删除预约（动态测试数据清理用）

接口说明：
    - 需携带 Authorization: Bearer <token>
    - 请求体结构：{apartment:{id}, tenant:{id}, landlord:{id}, appointmentTime, remark}
    - 成功响应 data 含 id/status（默认"待处理"）等字段
    - 业务规则：若预约时间与该房源"生效中"合同时间段冲突，后端会拦截并返回提示
"""

from utils.request_util import RequestUtil


def create_appointment(
    client: RequestUtil,
    token: str,
    apartment_id: int,
    tenant_id: int,
    landlord_id: int,
    appointment_time: str,
    remark: str = "",
):
    """
    携带 token 提交看房预约。

    参数:
        client: RequestUtil 请求工具实例
        token: 登录获取的 token
        apartment_id: 目标房源 id
        tenant_id: 租户用户 id
        landlord_id: 房东用户 id
        appointment_time: 预约时间，格式 yyyy-MM-dd HH:mm:ss
        remark: 预约备注，默认空字符串
    返回:
        requests.Response 响应对象，可用 .json() 解析 ApiResponse
    异常:
        requests 相关异常（网络/超时）
    """
    # 预约请求体结构与后端 Appointment 实体关联字段保持一致
    body = {
        "apartment": {"id": apartment_id},
        "tenant": {"id": tenant_id},
        "landlord": {"id": landlord_id},
        "appointmentTime": appointment_time,
        "remark": remark,
    }
    resp = client.post(
        "/api/appointments",
        json=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    return resp


def get_appointment_by_id(client: RequestUtil, token: str, appointment_id: int):
    """
    按 id 查询单条预约。

    接口路径: GET /api/appointments/{id}
    请求方法: GET
    参数:
        client: RequestUtil 请求工具实例
        token: 登录获取的 token
        appointment_id: 预约 id
    返回:
        requests.Response 响应对象；预约存在时 data 为预约对象，
        不存在时后端 AppointmentService.findById 抛异常，接口返回 HTTP 500（非 ApiResponse 结构）
    异常:
        requests 相关异常（网络/超时）
    """
    # 用于校验动态预约数据清理结果
    resp = client.get(
        f"/api/appointments/{appointment_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp


def delete_appointment(client: RequestUtil, token: str, appointment_id: int):
    """
    删除预约（供动态测试数据清理使用）。

    接口路径: DELETE /api/appointments/{id}
    请求方法: DELETE
    参数:
        client: RequestUtil 请求工具实例
        token: 登录获取的 token
        appointment_id: 待删除的预约 id
    返回:
        requests.Response 响应对象，成功时 message 为"删除成功"、data 为 null
    异常:
        requests 相关异常（网络/超时）
    """
    # 与 AppointmentController#delete 一致：DELETE /api/appointments/{id}
    resp = client.delete(
        f"/api/appointments/{appointment_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    return resp