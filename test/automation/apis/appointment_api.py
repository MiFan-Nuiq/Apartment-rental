# -*- coding: utf-8 -*-
"""
看房预约提交接口封装模块：POST /api/appointments

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