# -*- coding: utf-8 -*-
"""
缴费接口封装模块：/api/payments

接口清单（对齐 backend/.../controller/PaymentController.java，未臆造任何路径）：
    - POST   /api/payments                       创建支付流水
    - GET    /api/payments                       查询支付流水列表
    - GET    /api/payments/{id}                  按 id 查询支付流水（含支付状态）
    - GET    /api/payments/contract/{contractId} 按合同查询支付流水（含支付状态）
    - PUT    /api/payments/{id}                  更新支付流水（"支付"动作：置 status=已支付、写 payTime）
    - DELETE /api/payments/{id}                  删除支付流水（动态测试数据清理用）

接口说明：
    - 需携带 Authorization: Bearer <token>
    - 请求体结构（对齐 Payment 实体）：
        {contract:{id}, tenant:{id}, landlord:{id}, paymentDate, amount,
         paymentType, paymentMethod, status, remark, paymentVoucher, payTime}
      paymentDate 为 yyyy-MM-dd；payTime 为 yyyy-MM-dd HH:mm:ss；
      contract / tenant / landlord 以嵌套对象传 id
    - paymentNo 不传时由后端 PaymentService.save 自动生成（JF + yyyyMMdd + 4 位序号）
    - 真实的"支付"动作不是新增接口，而是前端调用 PUT /api/payments/{id}，
      把 status 置为"已支付"并写入 paymentMethod / paymentVoucher / payTime
    - 业务现状（实测确认，详见 testcases/test_payment.py 与 Bug 清单）：
      后端 PaymentService.save 只生成单号，**没有任何业务校验**——
      不拦截同一合同的重复缴费、不校验金额与合同是否一致、也不联动变更合同状态。

重构说明：
    请求逻辑（拼路径、带 token、超时、日志）已上提到 apis/base_api.py 的 BaseApi，
    本模块只保留缴费相关的接口方法；类外仍保留同名的模块级函数（签名与返回值不变）。
"""

from apis.base_api import BaseApi


class PaymentApi(BaseApi):
    """缴费接口类：封装 /api/payments 下各接口的调用。"""

    def __init__(self, api_client, token: str = None):
        """
        初始化缴费接口类。

        参数:
            api_client: 请求工具实例
            token: 登录 token
        返回:
            无
        """
        # 基础路径与后端 PaymentController 的 @RequestMapping 保持一致
        super().__init__(api_client, "/api/payments", token)

    def create_payment(self, payload: dict):
        """
        创建支付流水。

        接口路径: POST /api/payments
        请求方法: POST
        参数:
            payload: 支付流水请求体字典，必填项为 contract/tenant/landlord/paymentDate；
                     paymentNo 可不传（后端自动生成）
        返回:
            requests.Response 响应对象，成功时 data 为新建流水（含自增 id、自动生成的 paymentNo）
        异常:
            requests 相关异常（网络/超时）
        """
        return self.post(json=payload)

    def get_payments(self):
        """
        查询支付流水列表。

        接口路径: GET /api/payments
        请求方法: GET
        返回:
            requests.Response 响应对象，成功时 data 为支付流水数组
        异常:
            requests 相关异常（网络/超时）
        """
        return self.get()

    def get_payment_by_id(self, payment_id: int):
        """
        按 id 查询支付流水（可读取其支付状态 status 与 payTime）。

        接口路径: GET /api/payments/{id}
        请求方法: GET
        参数:
            payment_id: 支付流水 id
        返回:
            requests.Response 响应对象；流水存在时 data 为该流水对象，
            不存在时后端抛异常("缴费记录不存在")，返回 HTTP 500（非 ApiResponse 结构）
        异常:
            requests 相关异常（网络/超时）
        """
        return self.get(payment_id)

    def get_payments_by_contract(self, contract_id: int):
        """
        按合同 id 查询该合同下的全部支付流水（用于核对"同一合同是否被重复缴费"）。

        接口路径: GET /api/payments/contract/{contractId}
        请求方法: GET
        参数:
            contract_id: 合同 id
        返回:
            requests.Response 响应对象，成功时 data 为该合同下的流水数组（无数据时为空数组）
        异常:
            requests 相关异常（网络/超时）
        """
        return self.get(f"/contract/{contract_id}")

    def update_payment(self, payment_id: int, payload: dict):
        """
        更新支付流水（对应前端的"支付"动作）。

        接口路径: PUT /api/payments/{id}
        请求方法: PUT
        参数:
            payment_id: 待更新的支付流水 id
            payload: 流水请求体字典。
                     重要：后端 update 采用整体覆盖（paymentRepository.save），
                     未传字段会被置为 null 而可能违反 NOT NULL 约束，
                     因此除 paymentNo/createTime（后端自动沿用原值）外，
                     contract/tenant/landlord/paymentDate 等必填字段都需要带上；
                     执行"支付"时需传 status="已支付" 与 payTime
        返回:
            requests.Response 响应对象，成功时 data 为更新后的流水
        异常:
            requests 相关异常（网络/超时）
        """
        return self.put(payment_id, json=payload)

    def delete_payment(self, payment_id: int):
        """
        删除支付流水（供动态测试数据清理使用）。

        接口路径: DELETE /api/payments/{id}
        请求方法: DELETE
        参数:
            payment_id: 待删除的支付流水 id
        返回:
            requests.Response 响应对象，成功时 message 为"删除成功"、data 为 null
        异常:
            requests 相关异常（网络/超时）
        """
        return self.delete(payment_id)


# ==================== 模块级兼容函数（签名与返回值保持不变） ====================


def create_payment(client, token: str, payload: dict):
    """创建支付流水（兼容函数式调用，签名不变）。"""
    return PaymentApi(client, token).create_payment(payload)


def get_payments(client, token: str):
    """查询支付流水列表（兼容函数式调用，签名不变）。"""
    return PaymentApi(client, token).get_payments()


def get_payment_by_id(client, token: str, payment_id: int):
    """按 id 查询支付流水（兼容函数式调用，签名不变）。"""
    return PaymentApi(client, token).get_payment_by_id(payment_id)


def get_payments_by_contract(client, token: str, contract_id: int):
    """按合同查询支付流水（兼容函数式调用，签名不变）。"""
    return PaymentApi(client, token).get_payments_by_contract(contract_id)


def update_payment(client, token: str, payment_id: int, payload: dict):
    """更新支付流水（兼容函数式调用，签名不变）。"""
    return PaymentApi(client, token).update_payment(payment_id, payload)


def delete_payment(client, token: str, payment_id: int):
    """删除支付流水（兼容函数式调用，签名不变）。"""
    return PaymentApi(client, token).delete_payment(payment_id)