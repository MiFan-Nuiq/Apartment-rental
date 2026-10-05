# -*- coding: utf-8 -*-
"""
缴费模块接口自动化用例：/api/payments

覆盖点：
    1. test_create_payment_success
       正向：创建支付流水成功，金额与合同约定一致，数据库中存在对应记录
    2. test_pay_payment_and_query_status
       正向：执行"支付"动作（PUT status=已支付）后，通过详情/按合同查询接口读到支付状态
    3. test_duplicate_payment_rejected           【当前 xfail，缺陷 BUG-PAY-001】
       重复支付：同一合同重复创建支付流水，应返回非成功响应
    4. test_payment_amount_mismatch_rejected     【当前 xfail，缺陷 BUG-PAY-002】
       金额校验：支付金额与合同约定金额不一致时，应返回非成功响应
    5. test_contract_status_updated_after_payment【当前 xfail，缺陷 BUG-PAY-003】
       支付成功后校验：支付成功后合同状态应有联动更新

测试数据策略（静态打底 + 动态隔离）：
    - 静态种子数据（test/sql/data.sql）只提供登录账号等公共稳定数据；
    - 本文件的房源来自 temp_apartment（用例后自动删除），合同用合同模块的 API 动态创建，
      支付流水用本模块 API 动态创建，两者均通过 dynamic_data_cleaner 登记清理；
    - 清理顺序为后进先出：**先删支付流水 → 再删合同 → 最后删房源**，不会触发外键约束。

关于 3 个 xfail 用例（重要，实测结论）：
    后端 PaymentService.save 只做了一件事——自动生成缴费单号，**没有任何业务校验**，
    实测确认：同一合同重复创建流水返回 HTTP 200/code 200；
    支付金额与合同月租不一致（如 1 元 vs 2000 元）同样返回 HTTP 200/code 200；
    执行支付动作后合同状态也不会发生任何联动变化。
    因此这三条用例的断言**保持严格**（要求"必须失败"/"必须有联动"），
    按项目既有约定（参见 test_data_consistency.py 中 BUG-DATA-001 的处理方式）
    标记为 xfail，并已在 test/docs/Bug清单_实际发现.md 登记缺陷。
    后端修复后，这三条会自动转为 XPASS，提示把 xfail 标记去掉即可。

分层结构：
    testcases（本文） -> apis（接口层） -> utils（请求/断言/数据库工具）
"""

from decimal import Decimal

import allure
import pytest

from apis.contract_api import create_contract, delete_contract
from apis.payment_api import (
    create_payment,
    delete_payment,
    get_payment_by_id,
    get_payments,
    get_payments_by_contract,
    update_payment,
)
from utils.assert_util import (
    assert_business_error,
    assert_field_equal,
    assert_field_exists,
    assert_success,
)

# 租户/房东 id 统一取自 conftest 的静态配置（对应 data.sql 中 users.id=3 / users.id=2）
from conftest import LANDLORD_ID, TENANT_ID

# ==================== 业务常量（对齐后端真实取值） ====================
CONTRACT_STATUS_PENDING = "待确认"        # 临时合同的初始状态（对齐前端续租申请流）
CONTRACT_MONTHLY_RENT = 2000.00           # 合同月租：缴费用例的金额基准
CONTRACT_DEPOSIT = 2000.00                # 合同押金
PAYMENT_AMOUNT = CONTRACT_MONTHLY_RENT    # 与合同月租一致的支付金额
PAYMENT_STATUS_UNPAID = "待支付"          # 缴费状态：待支付
PAYMENT_STATUS_PAID = "已支付"            # 缴费状态：已支付
PAYMENT_TYPE_RENT = "租金"                # 缴费类型：租金
PAYMENT_DATE = "2026-10-05"               # 应缴日期（yyyy-MM-dd）
PAYMENT_TIME = "2026-10-05 12:00:00"      # 实际支付时间（yyyy-MM-dd HH:mm:ss）
# ====================================================================


def build_contract_payload(apartment_id: int, suffix: str) -> dict:
    """
    构造缴费用例所需的合同请求体（月租固定为 2000，便于做金额断言）。

    参数:
        apartment_id: 关联房源 id（通常来自 temp_apartment）
        suffix: 唯一后缀，写入 remark 便于事后检索残留数据
    返回:
        可直接传给 create_contract 的字典
    """
    return {
        "apartment": {"id": apartment_id},
        "tenant": {"id": TENANT_ID},
        "landlord": {"id": LANDLORD_ID},
        "startDate": "2027-01-01",
        "endDate": "2027-12-31",
        "monthlyRent": CONTRACT_MONTHLY_RENT,
        "deposit": CONTRACT_DEPOSIT,
        "paymentMethod": "月付",
        "status": CONTRACT_STATUS_PENDING,
        "remark": f"pytest 缴费模块自动化测试-合同（{suffix}）",
    }


def build_payment_payload(
    contract_id: int,
    suffix: str,
    amount: float = PAYMENT_AMOUNT,
    status: str = PAYMENT_STATUS_UNPAID,
) -> dict:
    """
    构造支付流水请求体（字段与后端 Payment 实体保持一致）。

    参数:
        contract_id: 关联合同 id
        suffix: 唯一后缀，写入 remark 便于事后检索残留数据
        amount: 支付金额，默认与合同月租一致（传其它值用于"金额不一致"用例）
        status: 缴费状态，默认"待支付"
    返回:
        可直接传给 create_payment 的字典
            注意：paymentNo 刻意不传，用于验证后端会自动生成缴费单号
    """
    return {
        # contract / tenant / landlord 均以嵌套对象传 id（JPA 多对一关联）
        "contract": {"id": contract_id},
        "tenant": {"id": TENANT_ID},
        "landlord": {"id": LANDLORD_ID},
        "paymentDate": PAYMENT_DATE,
        "amount": amount,
        "paymentType": PAYMENT_TYPE_RENT,
        "paymentMethod": "支付宝",
        "status": status,
        "remark": f"pytest 缴费模块自动化测试-流水（{suffix}）",
    }


def create_temp_contract(api_client, token: str, apartment_id: int, suffix: str, dynamic_data_cleaner) -> dict:
    """
    在临时房源上创建一条临时合同并登记清理（供缴费用例复用）。

    参数:
        api_client: 请求工具
        token: 登录 token
        apartment_id: 关联房源 id
        suffix: 唯一后缀
        dynamic_data_cleaner: 登记清理动作的 fixture
    返回:
        新建合同的 data 字典（含 id / contractNo / status）
    异常:
        AssertionError: 创建接口 HTTP 状态码或业务码异常、未返回 id
    清理逻辑:
        合同登记到 finalizer；支付流水会在其之后登记，finalizer 后进先出
        → 先删流水、再删合同、最后删房源
    """
    resp = create_contract(api_client, token, build_contract_payload(apartment_id, suffix))
    assert_success(resp)
    data = resp.json().get("data") or {}
    assert data.get("id"), f"创建临时合同未返回 id，响应：{resp.text}"
    dynamic_data_cleaner(delete_contract, data["id"], "临时合同")
    return data


def create_temp_payment(
    api_client,
    token: str,
    contract_id: int,
    suffix: str,
    dynamic_data_cleaner,
    amount: float = PAYMENT_AMOUNT,
):
    """
    创建一条临时支付流水，并在真正落库时登记清理。

    参数:
        api_client: 请求工具
        token: 登录 token
        contract_id: 关联合同 id
        suffix: 唯一后缀
        dynamic_data_cleaner: 登记清理动作的 fixture
        amount: 支付金额，默认与合同月租一致
    返回:
        (resp, payment_id)：响应对象与流水 id（未创建成功时 payment_id 为 None）
    说明:
        负向用例中后端可能并未按预期拒绝（当前即为该缺陷），
        所以只要真的生成了 id 就登记清理，避免脏数据残留。
    """
    resp = create_payment(api_client, token, build_payment_payload(contract_id, suffix, amount=amount))
    payment_id = None
    if resp.status_code == 200:
        payment_id = (resp.json().get("data") or {}).get("id")
    if payment_id:
        dynamic_data_cleaner(delete_payment, payment_id, "临时支付流水")
    return resp, payment_id


@allure.feature("缴费模块")
@allure.story("支付流水增查与支付状态")
@pytest.mark.api
@pytest.mark.regression
class TestPayment:
    """缴费模块接口测试类：覆盖创建、支付状态查询、重复支付、金额校验与合同状态联动。"""

    @allure.title("缴费：创建流水成功，金额与合同一致且数据库有记录")
    @pytest.mark.db
    def test_create_payment_success(
        self,
        api_client,
        auth_headers,
        temp_apartment,
        unique_suffix,
        dynamic_data_cleaner,
        db_connection,
    ):
        """
        验证创建支付流水成功，金额与合同约定一致，且数据库存在对应记录。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            temp_apartment: 用例级临时房源（合同与流水都必须挂在真实存在的数据上）
            unique_suffix: 唯一后缀（写入 remark，便于识别残留数据）
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具（校验落库）
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            流水与合同均由 dynamic_data_cleaner 登记删除（后进先出：先流水、后合同），
            temp_apartment 由 fixture 在用例结束后删除
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")

        # ---------- 步骤一：准备合同（金额基准） ----------
        with allure.step("动态创建临时合同（月租 2000，作为金额基准）"):
            contract = create_temp_contract(api_client, token, temp_apartment["id"], unique_suffix, dynamic_data_cleaner)
            assert_field_equal(contract, "monthlyRent", CONTRACT_MONTHLY_RENT)

        # ---------- 步骤二：创建支付流水 ----------
        with allure.step(f"在合同 id={contract['id']} 上创建支付流水（金额={PAYMENT_AMOUNT}）"):
            resp, payment_id = create_temp_payment(
                api_client, token, contract["id"], unique_suffix, dynamic_data_cleaner
            )
            assert_success(resp)

        data = resp.json().get("data")
        assert data is not None, "创建支付流水返回 data 为空"

        # ---------- 步骤三：校验关键返回字段与金额一致性 ----------
        with allure.step("校验流水返回字段（id / 缴费单号 / 金额 / 状态 / 关联合同）"):
            assert_field_exists(
                data,
                ["id", "paymentNo", "contract", "tenant", "landlord", "paymentDate", "amount", "status"],
            )
            # paymentNo 未传入，应由后端 PaymentService.save 自动生成（JF + yyyyMMdd + 4 位序号）
            assert data["paymentNo"].startswith("JF"), f"缴费单号格式异常：{data['paymentNo']}"
            assert_field_equal(data, "status", PAYMENT_STATUS_UNPAID)
            assert_field_equal(data["contract"], "id", contract["id"])
            assert_field_equal(data["tenant"], "id", TENANT_ID)
            assert_field_equal(data["landlord"], "id", LANDLORD_ID)

        with allure.step("校验支付金额与合同约定金额一致"):
            # 金额一致性是本用例的核心断言：流水金额必须等于合同月租
            assert float(data["amount"]) == float(contract["monthlyRent"]) == PAYMENT_AMOUNT, (
                f"支付金额 {data['amount']} 与合同月租 {contract['monthlyRent']} 不一致"
            )

        # ---------- 步骤四：查询接口校验 ----------
        with allure.step("详情接口校验：GET /api/payments/{id} 返回同一笔流水"):
            detail_resp = get_payment_by_id(api_client, token, data["id"])
            assert_success(detail_resp)
            detail = detail_resp.json().get("data") or {}
            assert_field_equal(detail, "id", data["id"])
            assert_field_equal(detail, "paymentNo", data["paymentNo"])

        with allure.step("按合同查询校验：GET /api/payments/contract/{id} 能查到该笔流水"):
            by_contract_resp = get_payments_by_contract(api_client, token, contract["id"])
            assert_success(by_contract_resp)
            payment_ids = {item.get("id") for item in (by_contract_resp.json().get("data") or [])}
            assert data["id"] in payment_ids, f"流水 id={data['id']} 未出现在合同 {contract['id']} 的缴费列表中"

        with allure.step("列表接口校验：新建流水出现在全量缴费列表中"):
            list_resp = get_payments(api_client, token)
            assert_success(list_resp)
            all_ids = {item.get("id") for item in (list_resp.json().get("data") or [])}
            assert data["id"] in all_ids, f"流水 id={data['id']} 未出现在缴费列表中"

        # ---------- 步骤五：数据库落库校验 ----------
        with allure.step("数据库校验：payments 表中记录与接口返回一致"):
            # 精确按 id 查询（而非"取最新一条"），避免与并发执行/其它用例的数据相互干扰
            row = db_connection.query_one(
                "SELECT id, payment_no, contract_id, tenant_id, landlord_id, amount, "
                "payment_type, status, pay_time, remark FROM payments WHERE id = %s",
                (payment_id,),
            )
            assert row is not None, f"payments 表未查询到 id={payment_id} 的记录，接口可能未真正落库"
            assert row["payment_no"] == data["paymentNo"], (
                f"数据库 payment_no={row['payment_no']} 与接口返回 {data['paymentNo']} 不一致"
            )
            assert row["contract_id"] == contract["id"], (
                f"数据库 contract_id={row['contract_id']} 与合同 {contract['id']} 不一致"
            )
            assert row["tenant_id"] == TENANT_ID, f"数据库 tenant_id={row['tenant_id']} 与提交的 {TENANT_ID} 不一致"
            assert row["landlord_id"] == LANDLORD_ID, (
                f"数据库 landlord_id={row['landlord_id']} 与提交的 {LANDLORD_ID} 不一致"
            )
            # 金额与合同约定一致（数据库侧复核，Decimal 精确比较）
            assert row["amount"] == Decimal(str(PAYMENT_AMOUNT)), (
                f"数据库 amount={row['amount']} 与合同约定金额 {PAYMENT_AMOUNT} 不一致"
            )
            assert row["payment_type"] == PAYMENT_TYPE_RENT, (
                f"数据库 payment_type={row['payment_type']} 与提交的 {PAYMENT_TYPE_RENT} 不一致"
            )
            assert row["status"] == PAYMENT_STATUS_UNPAID, (
                f"数据库缴费状态应为'{PAYMENT_STATUS_UNPAID}'，实际：{row['status']}"
            )
            assert row["pay_time"] is None, "未支付状态下 pay_time 应为空"
            assert unique_suffix in (row["remark"] or ""), (
                f"数据库 remark={row['remark']} 未包含本次用例的唯一后缀 {unique_suffix}"
            )

    @allure.title("缴费：执行支付动作后可通过接口查询到已支付状态")
    @pytest.mark.db
    def test_pay_payment_and_query_status(
        self,
        api_client,
        auth_headers,
        temp_apartment,
        unique_suffix,
        dynamic_data_cleaner,
        db_connection,
    ):
        """
        验证"支付"动作（PUT 置 status=已支付）执行成功后，支付状态可被查询到。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            temp_apartment: 用例级临时房源
            unique_suffix: 唯一后缀
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具（校验支付状态落库）
        返回:
            无；任一断言失败抛 AssertionError
        清理逻辑:
            流水与合同由 dynamic_data_cleaner 登记删除（先流水、后合同），
            temp_apartment 由 fixture 删除
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")

        with allure.step("准备：临时合同 + 一条待支付流水"):
            contract = create_temp_contract(api_client, token, temp_apartment["id"], unique_suffix, dynamic_data_cleaner)
            create_resp, payment_id = create_temp_payment(
                api_client, token, contract["id"], unique_suffix, dynamic_data_cleaner
            )
            assert_success(create_resp)
            assert payment_id, f"创建待支付流水未返回 id，响应：{create_resp.text}"

        # ---------- 步骤一：执行支付动作 ----------
        with allure.step(f"执行支付：PUT /api/payments/{payment_id} 置 status='{PAYMENT_STATUS_PAID}'"):
            # 后端 update 为整体覆盖，必填字段需一并提交
            pay_payload = build_payment_payload(
                contract["id"], unique_suffix, status=PAYMENT_STATUS_PAID
            )
            pay_payload["payTime"] = PAYMENT_TIME
            pay_resp = update_payment(api_client, token, payment_id, pay_payload)
            assert_success(pay_resp)

        paid = pay_resp.json().get("data") or {}
        with allure.step("校验支付接口返回：状态已支付且支付时间非空"):
            assert_field_equal(paid, "id", payment_id)
            assert_field_equal(paid, "status", PAYMENT_STATUS_PAID)
            # 缴费单号在更新时应沿用原值（后端从原记录取），不应被覆盖
            assert paid.get("paymentNo"), "更新后缴费单号不应为空"
            assert paid.get("payTime"), "支付成功后 payTime 不应为空"

        # ---------- 步骤二：查询支付状态 ----------
        with allure.step("详情接口校验：查询到支付状态为'已支付'"):
            detail_resp = get_payment_by_id(api_client, token, payment_id)
            assert_success(detail_resp)
            assert_field_equal(detail_resp.json().get("data") or {}, "status", PAYMENT_STATUS_PAID)

        with allure.step("按合同查询校验：该合同下的流水状态为'已支付'"):
            by_contract_resp = get_payments_by_contract(api_client, token, contract["id"])
            assert_success(by_contract_resp)
            rows = by_contract_resp.json().get("data") or []
            target = [item for item in rows if item.get("id") == payment_id]
            assert target, f"合同 {contract['id']} 下未查询到流水 id={payment_id}"
            assert_field_equal(target[0], "status", PAYMENT_STATUS_PAID)

        # ---------- 步骤三：数据库校验 ----------
        with allure.step("数据库校验：status='已支付' 且 pay_time 已写入"):
            row = db_connection.query_one("SELECT id, status, pay_time FROM payments WHERE id = %s", (payment_id,))
            assert row is not None, f"payments 表未查询到 id={payment_id} 的记录"
            assert row["status"] == PAYMENT_STATUS_PAID, (
                f"数据库缴费状态应为'{PAYMENT_STATUS_PAID}'，实际：{row['status']}"
            )
            assert row["pay_time"] is not None, "支付成功后数据库 pay_time 不应为空"

    @allure.title("缴费：同一合同重复创建支付流水应被拒绝")
    @pytest.mark.xfail(
        reason="BUG-PAY-001：后端 PaymentService.save 未做重复缴费校验，"
        "同一合同重复创建支付流水实测返回 HTTP 200/code 200",
        strict=False,
    )
    def test_duplicate_payment_rejected(
        self,
        api_client,
        auth_headers,
        temp_apartment,
        unique_suffix,
        dynamic_data_cleaner,
    ):
        """
        验证同一合同重复创建支付流水时，第二次必须被拒绝。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            temp_apartment: 用例级临时房源
            unique_suffix: 唯一后缀
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            两条流水（若都被创建成功）与合同均由 dynamic_data_cleaner 登记删除
        备注:
            断言保持严格（要求必须失败）。当前后端无重复缴费校验 → 用例 xfail（BUG-PAY-001），
            修复后会自动转为 XPASS。
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")

        with allure.step("准备：临时合同 + 第一条支付流水"):
            contract = create_temp_contract(api_client, token, temp_apartment["id"], unique_suffix, dynamic_data_cleaner)
            first_resp, first_id = create_temp_payment(
                api_client, token, contract["id"], unique_suffix, dynamic_data_cleaner
            )
            assert_success(first_resp)
            assert first_id, f"第一条流水创建失败：{first_resp.text}"

        with allure.step("对同一合同重复创建第二条支付流水"):
            # create_temp_payment 在"意外创建成功"时也会登记清理，避免脏数据残留
            second_resp, _ = create_temp_payment(api_client, token, contract["id"], unique_suffix, dynamic_data_cleaner)

        with allure.step("断言重复支付必须被拒绝"):
            assert_business_error(second_resp)

    @allure.title("缴费：支付金额与合同金额不一致时应被拒绝")
    @pytest.mark.xfail(
        reason="BUG-PAY-002：后端未校验支付金额与合同金额是否一致，"
        "实测金额 1 元 vs 合同 2000 元仍返回 HTTP 200/code 200",
        strict=False,
    )
    def test_payment_amount_mismatch_rejected(
        self,
        api_client,
        auth_headers,
        temp_apartment,
        unique_suffix,
        dynamic_data_cleaner,
    ):
        """
        验证支付金额与合同约定金额不一致时，必须被拒绝。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            temp_apartment: 用例级临时房源
            unique_suffix: 唯一后缀
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            流水（若被创建成功）与合同均由 dynamic_data_cleaner 登记删除
        备注:
            断言保持严格（要求必须失败）。当前后端无金额校验 → 用例 xfail（BUG-PAY-002），
            修复后会自动转为 XPASS。
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")

        with allure.step("准备：临时合同（月租 2000）"):
            contract = create_temp_contract(api_client, token, temp_apartment["id"], unique_suffix, dynamic_data_cleaner)

        # 刻意使用与合同月租不一致的极小金额
        mismatched_amount = 1.00
        with allure.step(f"创建金额为 {mismatched_amount} 的流水（合同月租为 {CONTRACT_MONTHLY_RENT}）"):
            resp, _ = create_temp_payment(
                api_client, token, contract["id"], unique_suffix, dynamic_data_cleaner, amount=mismatched_amount
            )

        with allure.step("断言金额不一致必须被拒绝"):
            assert_business_error(resp)

    @allure.title("缴费：支付成功后合同状态应有联动更新")
    @pytest.mark.db
    @pytest.mark.xfail(
        reason="BUG-PAY-003：PaymentService 与合同状态完全无联动，"
        "支付成功后合同状态仍停留在初始的'待确认'",
        strict=False,
    )
    def test_contract_status_updated_after_payment(
        self,
        api_client,
        auth_headers,
        temp_apartment,
        unique_suffix,
        dynamic_data_cleaner,
        db_connection,
    ):
        """
        验证支付成功后，合同状态应发生联动更新（不再停留在初始状态）。

        依赖:
            api_client / auth_headers: 请求工具与鉴权头
            temp_apartment: 用例级临时房源
            unique_suffix: 唯一后缀
            dynamic_data_cleaner: 登记用例内自建数据的清理动作
            db_connection: MySQL 直连工具（校验合同状态）
        返回:
            无；断言失败抛 AssertionError
        清理逻辑:
            流水与合同由 dynamic_data_cleaner 登记删除（先流水、后合同），
            temp_apartment 由 fixture 删除
        备注:
            断言保持严格（要求状态必须变化）。当前后端支付与合同状态无任何联动
            → 用例 xfail（BUG-PAY-003），修复后会自动转为 XPASS。
        """
        token = auth_headers["Authorization"].replace("Bearer ", "")

        with allure.step("准备：临时合同（初始状态'待确认'）+ 支付流水"):
            contract = create_temp_contract(api_client, token, temp_apartment["id"], unique_suffix, dynamic_data_cleaner)
            assert_field_equal(contract, "status", CONTRACT_STATUS_PENDING)
            create_resp, payment_id = create_temp_payment(
                api_client, token, contract["id"], unique_suffix, dynamic_data_cleaner
            )
            assert_success(create_resp)
            assert payment_id, f"创建流水失败：{create_resp.text}"

        with allure.step("执行支付动作，把流水置为'已支付'"):
            pay_payload = build_payment_payload(contract["id"], unique_suffix, status=PAYMENT_STATUS_PAID)
            pay_payload["payTime"] = PAYMENT_TIME
            pay_resp = update_payment(api_client, token, payment_id, pay_payload)
            assert_success(pay_resp)
            assert_field_equal(pay_resp.json().get("data") or {}, "status", PAYMENT_STATUS_PAID)

        with allure.step("数据库校验：合同状态应已被联动更新"):
            row = db_connection.query_one("SELECT id, status FROM contracts WHERE id = %s", (contract["id"],))
            assert row is not None, f"contracts 表未查询到 id={contract['id']} 的记录"
            # 核心断言：支付完成后合同状态不应还停留在初始的"待确认"
            assert row["status"] != CONTRACT_STATUS_PENDING, (
                f"支付成功后合同状态应有联动更新（如更新为'已到期'等），"
                f"实际仍为初始状态：{row['status']}"
            )