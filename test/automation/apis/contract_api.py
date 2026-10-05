# -*- coding: utf-8 -*-
"""
合同接口封装模块：/api/contracts

接口清单（对齐 backend/.../controller/ContractController.java，未臆造任何路径）：
    - POST   /api/contracts             创建合同
    - GET    /api/contracts             查询合同列表
    - GET    /api/contracts/{id}        按 id 查询合同详情
    - PUT    /api/contracts/{id}        更新合同（含状态流转）
    - DELETE /api/contracts/{id}        删除合同（动态测试数据清理用）

接口说明：
    - 需携带 Authorization: Bearer <token>
    - 请求体结构（对齐 Contract 实体）：
        {apartment:{id}, tenant:{id}, landlord:{id}, startDate, endDate,
         monthlyRent, deposit, paymentMethod, status, remark}
      startDate / endDate 为 yyyy-MM-dd；apartment / tenant / landlord 以嵌套对象传 id
    - contractNo 不传时由后端 ContractService.save 自动生成（HT + yyyyMMdd + 4 位序号）
    - 业务规则：
        * apartment/tenant/landlord/startDate/endDate 在库中均为 NOT NULL 且有外键约束，
          缺字段或传不存在的 id 会触发数据库约束异常（后端无全局异常处理器，返回 HTTP 500）；
        * 更新时若该房源存在"生效中/待确认"合同且时间区间重叠，后端拦截并返回提示；
        * 只有"生效中"的合同才能删除，否则后端提示"生效中的合同不能删除，请先解约"。

重构说明：
    请求逻辑（拼路径、带 token、超时、日志）已上提到 apis/base_api.py 的 BaseApi，
    本模块只保留合同相关的接口方法；类外仍保留同名的模块级函数（签名与返回值不变）。
"""

from apis.base_api import BaseApi


class ContractApi(BaseApi):
    """合同接口类：封装 /api/contracts 下各接口的调用。"""

    def __init__(self, api_client, token: str = None):
        """
        初始化合同接口类。

        参数:
            api_client: 请求工具实例
            token: 登录 token
        返回:
            无
        """
        # 基础路径与后端 ContractController 的 @RequestMapping 保持一致
        super().__init__(api_client, "/api/contracts", token)

    def create_contract(self, payload: dict):
        """
        创建合同。

        接口路径: POST /api/contracts
        请求方法: POST
        参数:
            payload: 合同请求体字典，至少需要 apartment/tenant/landlord/startDate/endDate；
                     contractNo 可不传（后端自动生成）
        返回:
            requests.Response 响应对象，成功时 data 为新建合同（含自增 id、自动生成的 contractNo）
        异常:
            requests 相关异常（网络/超时）
        """
        return self.post(json=payload)

    def get_contracts(self):
        """
        查询合同列表。

        接口路径: GET /api/contracts
        请求方法: GET
        返回:
            requests.Response 响应对象，成功时 data 为合同数组
        异常:
            requests 相关异常（网络/超时）
        说明:
            后端查询合同前会先执行 checkAndUpdateExpiredContracts，
            可能顺带把到期合同置为"已到期"。
        """
        return self.get()

    def get_contract_by_id(self, contract_id: int):
        """
        按 id 查询合同详情。

        接口路径: GET /api/contracts/{id}
        请求方法: GET
        参数:
            contract_id: 合同 id
        返回:
            requests.Response 响应对象；合同存在时 data 为该合同对象，
            不存在时后端抛异常("合同不存在")，返回 HTTP 500（非 ApiResponse 结构）
        异常:
            requests 相关异常（网络/超时）
        """
        return self.get(contract_id)

    def update_contract(self, contract_id: int, payload: dict):
        """
        更新合同（用于状态流转等场景）。

        接口路径: PUT /api/contracts/{id}
        请求方法: PUT
        参数:
            contract_id: 待更新的合同 id
            payload: 合同请求体字典。
                     重要：后端 update 采用整体覆盖（contractRepository.save），
                     未传的字段会被置为 null 而可能违反 NOT NULL 约束，
                     因此除 contractNo/createTime（后端自动沿用原值）外，
                     apartment/tenant/landlord/startDate/endDate 等必填字段都需要带上
        返回:
            requests.Response 响应对象，成功时 data 为更新后的合同
        异常:
            requests 相关异常（网络/超时）
        """
        return self.put(contract_id, json=payload)

    def delete_contract(self, contract_id: int):
        """
        删除合同（供动态测试数据清理使用）。

        接口路径: DELETE /api/contracts/{id}
        请求方法: DELETE
        参数:
            contract_id: 待删除的合同 id
        返回:
            requests.Response 响应对象，成功时 message 为"删除成功"、data 为 null；
            合同为"生效中"时后端拒绝删除，返回业务错误提示
        异常:
            requests 相关异常（网络/超时）
        说明:
            后端 delete 会同时清理该合同关联的缴费记录。
        """
        return self.delete(contract_id)


# ==================== 模块级兼容函数（签名与返回值保持不变） ====================


def create_contract(client, token: str, payload: dict):
    """创建合同（兼容函数式调用，签名不变）。"""
    return ContractApi(client, token).create_contract(payload)


def get_contracts(client, token: str):
    """查询合同列表（兼容函数式调用，签名不变）。"""
    return ContractApi(client, token).get_contracts()


def get_contract_by_id(client, token: str, contract_id: int):
    """按 id 查询合同详情（兼容函数式调用，签名不变）。"""
    return ContractApi(client, token).get_contract_by_id(contract_id)


def update_contract(client, token: str, contract_id: int, payload: dict):
    """更新合同（兼容函数式调用，签名不变）。"""
    return ContractApi(client, token).update_contract(contract_id, payload)


def delete_contract(client, token: str, contract_id: int):
    """删除合同（兼容函数式调用，签名不变）。"""
    return ContractApi(client, token).delete_contract(contract_id)