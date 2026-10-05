# -*- coding: utf-8 -*-
"""
合同模块接口自动化用例：/api/contracts

覆盖点：
    1. test_create_contract_success
       正向：创建合同成功，返回合同 ID，数据库中存在对应记录（并校验详情/列表接口）
    2. test_create_contract_missing_required_field
       参数缺失：缺少房源 ID / 缺少租客 ID / 缺少合同起止日期，分别必须失败（参数化 3 组）
    3. test_create_contract_invalid_apartment
       无效房源 ID：用不存在的房源 ID 创建合同，必须失败，且数据库无残留
    4. test_contract_status_transition
       状态流转：创建合同 → 更新状态为"已终止" → 数据库校验状态已更新

测试数据策略（静态打底 + 动态隔离）：
    - 静态种子数据（test/sql/data.sql）只提供登录账号等公共稳定数据；
    - 本文件涉及的房源全部来自 temp_apartment（带唯一后缀、用例后自动删除），
      合同由用例动态创建并通过 dynamic_data_cleaner 登记清理，
      清理顺序为后进先出（先删合同、再删房源），不会触发外键约束。

关于"合同结束"状态的说明（以实际后端代码为准，未臆造枚举）：
    任务描述要求把状态更新为"已结束"，但项目中**不存在**"已结束"这一取值——
    后端 ContractService 与 schema.sql 中的合同状态真实枚举为
    **生效中 / 已到期 / 已终止**（另有前端续租申请流使用的初始状态"待确认"）。
    因此本用例用真实枚举 **"已终止"** 作为"合同结束"的状态值，语义与"已结束"一致。

分层结构：
    testcases（本文） -> apis（接口层） -> utils（请求/断言/数据库工具）
"""

import allure
import pytest

from apis.contract_api import (
    create_contract,
    delete_contract,
    get_contract_by_id,
    get_contracts,
    update_contract,
)
from utils.assert_util import (
    assert_business_error,
    assert_field_equal,
    assert_field_exists,
    assert_success,
)

# 租户/房东 id 统一取自 conftest 的静态配置（对应 data.sql 中 users.id=3 / users.id=2）
from conftest import LANDLORD_ID, TENANT_ID

# ==================== 合同状态常量（对齐后端真实枚举） ====================
CONTRACT_STATUS_PENDING = "待确认"        # 前端续租申请流创建合同时使用的初始状态
CONTRACT_STATUS_TERMINATED = "已终止"     # 合同结束状态（后端 terminate 与状态流转均使用该值）
# ======================================================================

# 合同的固定起止日期：取未来区间，避免被 ContractStatusScheduler 判定为"已到期"而干扰断言
CONTRACT_START_DATE = "2027-01-01"
CONTRACT_END_DATE = "2027-12-31"

# 参数缺失用例数据：(用例 id, 中文标题, 需要从请求体中移除的字段名列表)
MISSING_FIELD_CASES = [
    ("missing_apartment", "缺少房源 ID", ["apartment"]),
    ("missing_tenant", "缺少租客 ID", ["tenant"]),
    ("missing_date_range", "缺少合同起止日期", ["startDate", "endDate"]),
]


def build_contract_payload(apartment_id: int, suffix: str, status: str = CONTRACT_STATUS_PENDING) -> dict:
    """
    构造合同请求体（字段与后端 Contract 实体保持一致）。

    参数:
        apartment_id: 关联房源 id（通常是 temp_apartment 动态创建的房源）
        suffix: 唯一后缀，写入 remark 便于事后用 SQL 检索残留数据
        status: 合同状态，默认"待确认"（对齐前端续租申请流）
    返回:
        可直接传给 POST /api/contracts 的字典
            注意：contractNo 刻意不传，用于验证后端会自动生成合同编号
    """
    return {
        # apartment / tenant / landlord 均以嵌套对象传 id（JPA 多对一关联）
        "apartment": {"id": apartment_id},
        "tenant": {"id": TENANT_ID},
        "landlord": {"id": LANDLORD_ID},
        "startDate": CONTRACT_START_DATE,
        "endDate": CONTRACT_END_DATE,
        "monthlyRent": 2000.00,
        "deposit": 2000.00,
        "paymentMethod": "月付",
        "status": status,
        "remark": f"pytest 合同模块自动化测试（{suffix}）",
    }


@allure.feature("合同模块")
@allure.story("合同增查改与状态流转")
@pytest.mark.api
@pytest.mark.regression
class TestContract:
    """合同模块接口测试类：覆盖创建、参数校验、无效外键与状态流转。"""

    @allure.title("合同：创建成功且数据库存在对应记录")
    @pytest.mark.db
    def test_create_contract_success(
        self,
        api_client,
        auth_headers,
        temp_apartment,
        unique_suffix,
        dynamic_data_cleaner,
        db_connection,
    ):
        """
        验证携带 token 创建合同成功，返回合同 ID，且数据库落库记录与接口返回一致。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            temp_apartment: 用例级临时房源（合同必须挂在真实存在的房源上）
            unique_suffix: 唯一后缀（写入 remark，便于识别残留数据）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具（校验落库）
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            本用例创建的合同由 dynamic_data_cleaner 登记删除；
            temp_apartment 由 fixture 在用例结束后删除，finalizer 后进先出
            （先删合同、再删房源），不会触发外键约束
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")
        payload = build_contract_payload(temp_apartment["id"], unique_suffix)

        # ---------- 步骤一：创建合同 ----------
        with allure.step(f"在临时房源 id={temp_apartment['id']} 上创建合同"):
            resp = create_contract(api_client, token, payload)
            assert_success(resp)

        data = resp.json().get("data")
        assert data is not None, "创建合同返回 data 为空"

        # ---------- 步骤二：校验关键返回字段 ----------
        with allure.step("校验合同返回字段（id / 合同编号 / 状态 / 关联房源）"):
            assert_field_exists(
                data,
                ["id", "contractNo", "apartment", "tenant", "landlord", "startDate", "endDate", "status"],
            )
            # 合同 id 必须由数据库自增返回，用例后续据此查询与清理
            assert data["id"], f"创建合同成功但未返回合同 id，响应：{data}"
            # contractNo 未传入，应由后端 ContractService.save 自动生成（HT + yyyyMMdd + 4 位序号）
            assert data["contractNo"].startswith("HT"), f"合同编号格式异常：{data['contractNo']}"
            assert_field_equal(data, "status", CONTRACT_STATUS_PENDING)
            assert_field_equal(data["apartment"], "id", temp_apartment["id"])
            assert_field_equal(data["tenant"], "id", TENANT_ID)
            assert_field_equal(data["landlord"], "id", LANDLORD_ID)
            # 登记清理：自建的合同必须先于临时房源被删除，否则房源删除会触发外键约束
            dynamic_data_cleaner(delete_contract, data["id"], "临时合同")

        # ---------- 步骤三：详情接口校验 ----------
        with allure.step("详情接口校验：GET /api/contracts/{id} 返回同一份合同"):
            detail_resp = get_contract_by_id(api_client, token, data["id"])
            assert_success(detail_resp)
            detail = detail_resp.json().get("data") or {}
            assert_field_equal(detail, "id", data["id"])
            assert_field_equal(detail, "contractNo", data["contractNo"])

        # ---------- 步骤四：列表接口校验 ----------
        with allure.step("列表接口校验：新建合同出现在合同列表中"):
            list_resp = get_contracts(api_client, token)
            assert_success(list_resp)
            contract_ids = {item.get("id") for item in (list_resp.json().get("data") or [])}
            assert data["id"] in contract_ids, f"新建合同 id={data['id']} 未出现在合同列表中"

        # ---------- 步骤五：数据库落库校验 ----------
        with allure.step("数据库校验：contracts 表中记录与接口返回一致"):
            # 精确按 id 查询（而非"取最新一条"），避免与并发执行/其它用例的数据相互干扰
            row = db_connection.query_one(
                "SELECT id, contract_no, apartment_id, tenant_id, landlord_id, "
                "status, start_date, end_date, remark FROM contracts WHERE id = %s",
                (data["id"],),
            )
            assert row is not None, f"contracts 表未查询到 id={data['id']} 的记录，接口可能未真正落库"
            assert row["contract_no"] == data["contractNo"], (
                f"数据库 contract_no={row['contract_no']} 与接口返回 {data['contractNo']} 不一致"
            )
            assert row["apartment_id"] == temp_apartment["id"], (
                f"数据库 apartment_id={row['apartment_id']} 与临时房源 {temp_apartment['id']} 不一致"
            )
            assert row["tenant_id"] == TENANT_ID, f"数据库 tenant_id={row['tenant_id']} 与提交的 {TENANT_ID} 不一致"
            assert row["landlord_id"] == LANDLORD_ID, (
                f"数据库 landlord_id={row['landlord_id']} 与提交的 {LANDLORD_ID} 不一致"
            )
            assert row["status"] == CONTRACT_STATUS_PENDING, (
                f"数据库合同状态应为'{CONTRACT_STATUS_PENDING}'，实际：{row['status']}"
            )
            assert str(row["start_date"]) == CONTRACT_START_DATE, (
                f"数据库 start_date={row['start_date']} 与提交的 {CONTRACT_START_DATE} 不一致"
            )
            assert str(row["end_date"]) == CONTRACT_END_DATE, (
                f"数据库 end_date={row['end_date']} 与提交的 {CONTRACT_END_DATE} 不一致"
            )
            # remark 带唯一后缀：既证明这条记录属于本次用例，也便于事后检索残留
            assert unique_suffix in (row["remark"] or ""), (
                f"数据库 remark={row['remark']} 未包含本次用例的唯一后缀 {unique_suffix}"
            )

    @allure.title("合同：缺少必填字段时创建失败")
    @pytest.mark.parametrize(
        "case_id, case_title, removed_fields",
        MISSING_FIELD_CASES,
        ids=[case[0] for case in MISSING_FIELD_CASES],
    )
    def test_create_contract_missing_required_field(
        self,
        api_client,
        auth_headers,
        temp_apartment,
        unique_suffix,
        case_id,
        case_title,
        removed_fields,
    ):
        """
        验证缺少必填字段时合同创建必须失败（不做放宽，不接受成功响应）。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            temp_apartment: 用例级临时房源（保证"只有目标字段缺失"，失败原因不被其它因素污染）
            unique_suffix: 唯一后缀（写入 remark）
            case_id / case_title / removed_fields: 参数化传入的用例标识、标题与待移除字段
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            本用例不创建任何合同数据（请求均被后端拒绝），故无需清理；
            temp_apartment 由 fixture 在用例结束后自动删除
        """
        allure.dynamic.title(f"合同：创建失败（{case_title}）")
        token = auth_headers["Authorization"].replace("Bearer ", "")

        payload = build_contract_payload(temp_apartment["id"], unique_suffix)
        # 按参数化数据移除目标字段，构造"参数缺失"请求体
        for field in removed_fields:
            payload.pop(field, None)

        with allure.step(f"提交缺少 {case_title} 的合同请求"):
            resp = create_contract(api_client, token, payload)

        with allure.step(f"断言创建必须失败（{case_title}）"):
            assert_business_error(resp)

    @allure.title("合同：使用不存在的房源 ID 创建失败")
    @pytest.mark.db
    def test_create_contract_invalid_apartment(self, api_client, auth_headers, unique_suffix, db_connection):
        """
        验证使用不存在的房源 ID 创建合同时必须失败，且数据库无残留记录。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            unique_suffix: 唯一后缀（写入 remark，便于检索是否残留）
            db_connection: MySQL 直连工具（校验无残留）
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            本用例不会创建成功任何合同数据，故无需清理
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")
        # 该房源 id 在库中不存在（data.sql 仅种下 id=1/2/3）
        invalid_apartment_id = 999999
        payload = build_contract_payload(invalid_apartment_id, unique_suffix)

        with allure.step(f"使用不存在的房源 id={invalid_apartment_id} 创建合同"):
            resp = create_contract(api_client, token, payload)

        with allure.step("断言创建必须失败（外键约束由数据库拦截）"):
            assert_business_error(resp)

        with allure.step("数据库校验：contracts 表无该无效房源的残留记录"):
            row = db_connection.query_one(
                "SELECT id FROM contracts WHERE apartment_id = %s AND remark LIKE %s",
                (invalid_apartment_id, f"%{unique_suffix}%"),
            )
            assert row is None, f"无效房源 id={invalid_apartment_id} 的合同不应落库，实际查询到：{row}"

    @allure.title("合同：状态流转（创建 -> 已终止）并落库生效")
    @pytest.mark.db
    def test_contract_status_transition(
        self,
        api_client,
        auth_headers,
        temp_apartment,
        unique_suffix,
        dynamic_data_cleaner,
        db_connection,
    ):
        """
        验证合同状态可由初始状态流转为"已终止"，且数据库状态同步更新。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            temp_apartment: 用例级临时房源
            unique_suffix: 唯一后缀（写入 remark）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具（校验状态落库）
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            合同最终状态为"已终止"（非"生效中"，不会被后端拒绝删除），
            由 dynamic_data_cleaner 登记删除；temp_apartment 由 fixture 删除
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")
        payload = build_contract_payload(temp_apartment["id"], unique_suffix)

        # ---------- 步骤一：创建合同（初始状态"待确认"） ----------
        with allure.step(f"创建合同，初始状态为'{CONTRACT_STATUS_PENDING}'"):
            create_resp = create_contract(api_client, token, payload)
            assert_success(create_resp)
            created = create_resp.json().get("data") or {}
            contract_id = created.get("id")
            assert contract_id, f"创建合同未返回 id，响应：{create_resp.text}"
            assert_field_equal(created, "status", CONTRACT_STATUS_PENDING)
            # 登记清理，保证即使后续断言失败也不会残留
            dynamic_data_cleaner(delete_contract, contract_id, "临时合同")

        with allure.step("数据库校验：初始状态已落库"):
            before_row = db_connection.query_one("SELECT id, status FROM contracts WHERE id = %s", (contract_id,))
            assert before_row is not None, f"contracts 表未查询到 id={contract_id} 的记录"
            assert before_row["status"] == CONTRACT_STATUS_PENDING, (
                f"初始状态应为'{CONTRACT_STATUS_PENDING}'，实际：{before_row['status']}"
            )

        # ---------- 步骤二：更新状态为"已终止" ----------
        with allure.step(f"更新合同状态为'{CONTRACT_STATUS_TERMINATED}'（PUT /api/contracts/{contract_id}）"):
            # 注意：后端 update 为整体覆盖，必填字段需一并提交，否则会被置为 null 而违反 NOT NULL 约束
            update_payload = build_contract_payload(
                temp_apartment["id"], unique_suffix, status=CONTRACT_STATUS_TERMINATED
            )
            update_resp = update_contract(api_client, token, contract_id, update_payload)
            assert_success(update_resp)

        updated = update_resp.json().get("data") or {}
        with allure.step("校验更新接口返回"):
            assert_field_equal(updated, "id", contract_id)
            assert_field_equal(updated, "status", CONTRACT_STATUS_TERMINATED)
            # 合同编号在更新时应沿用原值（后端从原记录取），不应被覆盖
            assert updated.get("contractNo") == created.get("contractNo"), (
                f"更新后合同编号被改动：{updated.get('contractNo')} != {created.get('contractNo')}"
            )

        # ---------- 步骤三：数据库与详情接口双重校验 ----------
        with allure.step("数据库校验：合同状态已更新为'已终止'"):
            after_row = db_connection.query_one(
                "SELECT id, status, update_time FROM contracts WHERE id = %s", (contract_id,)
            )
            assert after_row is not None, f"contracts 表未查询到 id={contract_id} 的记录"
            assert after_row["status"] == CONTRACT_STATUS_TERMINATED, (
                f"数据库合同状态应为'{CONTRACT_STATUS_TERMINATED}'，实际：{after_row['status']}"
            )
            assert after_row["update_time"] is not None, "合同更新后 update_time 不应为空"

        with allure.step("详情接口校验：查询到的状态与数据库一致"):
            detail_resp = get_contract_by_id(api_client, token, contract_id)
            assert_success(detail_resp)
            assert_field_equal(detail_resp.json().get("data") or {}, "status", CONTRACT_STATUS_TERMINATED)