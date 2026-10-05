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

重构说明：
    请求逻辑（拼路径、带 token、超时、日志）已上提到 apis/base_api.py 的 BaseApi，
    本模块只保留预约相关的接口方法；类外仍保留同名的模块级函数（签名与返回值不变）。
"""

from apis.base_api import BaseApi


class AppointmentApi(BaseApi):
    """预约接口类：封装 /api/appointments 下各接口的调用。"""

    def __init__(self, api_client, token: str = None):
        """
        初始化预约接口类。

        参数:
            api_client: 请求工具实例
            token: 登录 token
        返回:
            无
        """
        # 基础路径与后端 AppointmentController 的 @RequestMapping 保持一致
        super().__init__(api_client, "/api/appointments", token)

    def create_appointment(
        self,
        apartment_id: int,
        tenant_id: int,
        landlord_id: int,
        appointment_time: str,
        remark: str = "",
    ):
        """
        提交看房预约。

        接口路径: POST /api/appointments
        请求方法: POST
        参数:
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
        return self.post(json=body)

    def get_appointment_by_id(self, appointment_id: int):
        """
        按 id 查询单条预约。

        接口路径: GET /api/appointments/{id}
        请求方法: GET
        参数:
            appointment_id: 预约 id
        返回:
            requests.Response 响应对象；预约存在时 data 为预约对象，
            不存在时接口返回 HTTP 500（非 ApiResponse 结构）
        异常:
            requests 相关异常（网络/超时）
        """
        return self.get(appointment_id)

    def delete_appointment(self, appointment_id: int):
        """
        删除预约（供动态测试数据清理使用）。

        接口路径: DELETE /api/appointments/{id}
        请求方法: DELETE
        参数:
            appointment_id: 待删除的预约 id
        返回:
            requests.Response 响应对象，成功时 message 为"删除成功"、data 为 null
        异常:
            requests 相关异常（网络/超时）
        """
        return self.delete(appointment_id)


# ==================== 模块级兼容函数（签名与返回值保持不变） ====================


def create_appointment(
    client,
    token: str,
    apartment_id: int,
    tenant_id: int,
    landlord_id: int,
    appointment_time: str,
    remark: str = "",
):
    """携带 token 提交看房预约（兼容函数式调用，签名不变）。"""
    return AppointmentApi(client, token).create_appointment(
        apartment_id, tenant_id, landlord_id, appointment_time, remark
    )


def get_appointment_by_id(client, token: str, appointment_id: int):
    """按 id 查询单条预约（兼容函数式调用，签名不变）。"""
    return AppointmentApi(client, token).get_appointment_by_id(appointment_id)


def delete_appointment(client, token: str, appointment_id: int):
    """删除预约（兼容函数式调用，签名不变）。"""
    return AppointmentApi(client, token).delete_appointment(appointment_id)