# -*- coding: utf-8 -*-
"""
数据一致性校验用例：把 sql/contract_payment_consistency.sql 的 3 条校验 SQL 用例化。

对应关系：
    ① 合同状态为“生效中”但在 payments 表中无任何对应记录  -> test_active_contract_without_payment
    ② payments 表有记录但对应合同状态不是“生效中”          -> test_payment_exists_for_inactive_contract
    ③ 指定房东名下所有合同的租金/押金统计及其自一致性校验    -> test_landlord_contract_statistics_consistency

说明：
    - 校验口径与 SQL 脚本一致，状态枚举以业务代码为准（“生效中”，项目中不存在“已签约”）；
    - 直连 MySQL 查询，依赖 conftest 的 db_connection fixture；
    - 断言保持严格：命中不一致数据即判定失败（不做放宽）。
"""

from decimal import Decimal

import allure
import pytest

from conftest import LANDLORD_ID


@allure.feature("数据一致性校验")
@allure.story("合同-缴费一致性")
class TestContractPaymentConsistency:
    """合同状态与支付流水的一致性校验用例集。"""

    @allure.title("一致性①：生效中合同不应缺失缴费记录")
    @pytest.mark.db
    @pytest.mark.regression
    def test_active_contract_without_payment(self, db_connection):
        """校验所有“生效中”合同均存在对应缴费流水。"""
        with allure.step("查询生效中但无任何缴费记录的合同"):
            # LEFT JOIN 后用 p.id IS NULL 过滤出“无缴费记录”的生效合同
            rows = db_connection.query_all(
                "SELECT c.id, c.contract_no, c.status "
                "FROM contracts c "
                "LEFT JOIN payments p ON p.contract_id = c.id "
                "WHERE c.status = '生效中' AND p.id IS NULL"
            )
        with allure.step("断言查询结果为空（无不一致数据）"):
            # 业务口径：合同生效后会自动生成首月租金与押金流水，故此处不应有数据
            assert rows == [], (
                f"发现 {len(rows)} 条“生效中但无缴费记录”的合同（漏生成缴费）：{rows}"
            )

    @allure.title("一致性②：非生效中合同不应残留缴费记录")
    @pytest.mark.db
    @pytest.mark.regression
    @pytest.mark.xfail(
        strict=False,
        reason="已知缺陷 BUG-DATA-001：存在 1 条已终止合同仍残留缴费流水（合同ID=15，合同号 HT2026031600）",
    )
    def test_payment_exists_for_inactive_contract(self, db_connection):
        """校验非“生效中”合同（已终止/已到期）不再残留缴费流水。

        注：本条用例对应已知缺陷 BUG-DATA-001（见 test/docs/bug清单_实际发现.md），
        因此标记 xfail；断言本身仍然严格，若数据被修复后用例会转为 XPASS。
        """
        with allure.step("查询有缴费记录但合同状态非生效中的合同"):
            # 按合同聚合，统计异常流水条数与已支付金额，便于定位问题合同
            rows = db_connection.query_all(
                "SELECT p.contract_id, c.contract_no, c.status, "
                "       COUNT(p.id) AS payment_count, "
                "       SUM(CASE WHEN p.status = '已支付' THEN p.amount ELSE 0 END) AS paid_amount "
                "FROM payments p "
                "JOIN contracts c ON c.id = p.contract_id "
                "WHERE c.status NOT IN ('生效中') "
                "GROUP BY p.contract_id, c.contract_no, c.status"
            )
        with allure.step("断言查询结果为空（无失效合同残留流水）"):
            assert rows == [], (
                f"发现 {len(rows)} 条“非生效中合同却存在缴费记录”的数据：{rows}"
            )

    @allure.title("一致性③：房东名下合同租金押金统计与明细自一致")
    @pytest.mark.db
    @pytest.mark.regression
    def test_landlord_contract_statistics_consistency(self, db_connection):
        """校验按房东聚合的合同统计数据与其合同明细完全一致。"""
        with allure.step(f"查询房东(id={LANDLORD_ID})的合同汇总统计"):
            # 汇总口径：合同总数、生效中合同数、总月租金、总押金
            stat = db_connection.query_one(
                "SELECT c.landlord_id, u.username, "
                "       COUNT(c.id) AS contract_count, "
                "       COUNT(CASE WHEN c.status = '生效中' THEN 1 END) AS active_count, "
                "       COALESCE(SUM(c.monthly_rent), 0) AS total_rent, "
                "       COALESCE(SUM(c.deposit), 0) AS total_deposit "
                "FROM contracts c "
                "JOIN users u ON u.id = c.landlord_id "
                "WHERE c.landlord_id = %s "
                "GROUP BY c.landlord_id, u.username",
                (LANDLORD_ID,),
            )

        with allure.step(f"查询房东(id={LANDLORD_ID})的合同明细"):
            # 明细用于与汇总结果交叉校验，避免聚合计算错误
            details = db_connection.query_all(
                "SELECT id, status, monthly_rent, deposit FROM contracts WHERE landlord_id = %s",
                (LANDLORD_ID,),
            )

        with allure.step("断言汇总统计与明细一致"):
            if not details:
                # 无合同时，汇总查询也应无结果（GROUP BY 无行）
                assert stat is None, f"房东 {LANDLORD_ID} 无合同明细，但汇总查询却有结果：{stat}"
                return
            assert stat is not None, f"房东 {LANDLORD_ID} 有 {len(details)} 条合同，但汇总查询无结果"
            # 字段与明细逐一核对：数量、生效数、总月租金、总押金
            assert stat["contract_count"] == len(details), (
                f"合同总数不一致：汇总 {stat['contract_count']}，明细 {len(details)}"
            )
            expected_active = len([d for d in details if d["status"] == "生效中"])
            assert stat["active_count"] == expected_active, (
                f"生效中合同数不一致：汇总 {stat['active_count']}，明细 {expected_active}"
            )
            # 金额用 Decimal 比较，避免浮点误差
            expected_rent = sum(Decimal(str(d["monthly_rent"] or 0)) for d in details)
            expected_deposit = sum(Decimal(str(d["deposit"] or 0)) for d in details)
            assert Decimal(str(stat["total_rent"])) == expected_rent, (
                f"总月租金不一致：汇总 {stat['total_rent']}，明细合计 {expected_rent}"
            )
            assert Decimal(str(stat["total_deposit"])) == expected_deposit, (
                f"总押金不一致：汇总 {stat['total_deposit']}，明细合计 {expected_deposit}"
            )