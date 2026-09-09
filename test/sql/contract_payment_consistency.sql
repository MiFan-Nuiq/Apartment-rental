-- =====================================================================
-- 公寓租赁管理系统 —— 合同状态与支付流水数据一致性验证脚本
-- 数据模型说明（对应后端实体 / JPA 驼峰转下划线命名）：
--   contracts 合同表：id, contract_no(合同编号), apartment_id, tenant_id, landlord_id,
--            start_date, end_date, monthly_rent(月租金), deposit(押金), status,
--            contract_type(新签/转租), sublet_status, ...
--   payments  缴费表：id, payment_no(缴费编号), contract_id, tenant_id, landlord_id,
--            payment_date, amount(金额), payment_type(租金/押金), status(待支付/已支付), ...
--   users     用户表：id, username, real_name, role(ADMIN/LANDLORD/TENANT)
--
-- 注意：合同状态枚举值以业务代码为准：
--   ContractService 中"生效中""已终止""已到期"，不存在"已签约"，故下述均用"生效中"。
--   若你的环境确实存在"已签约"取值，请自行将 status 条件替换为 '已签约'。
-- =====================================================================


-- ---------------------------------------------------------------------
-- ① 合同状态为"生效中"但在支付表里没有任何对应记录的合同
--    业务口径：正常合同生效后（ContractService.update 生效流程）会自动生成首月租金、押金两条待支付流水，
--    若生效合同却查不到任何 payments 记录，说明存在“漏生成缴费”的数据一致性问题。
-- ---------------------------------------------------------------------
SELECT
    c.id                              AS 合同ID,
    c.contract_no                     AS 合同编号,
    c.apartment_id                    AS 房源ID,
    c.tenant_id                       AS 租户ID,
    c.landlord_id                     AS 房东ID,
    c.start_date                      AS 开始日期,
    c.end_date                        AS 结束日期,
    c.monthly_rent                    AS 月租金,
    c.deposit                         AS 押金,
    c.status                          AS 合同状态,
    c.create_time                     AS 合同创建时间
FROM contracts c
LEFT JOIN payments p
       ON p.contract_id = c.id
WHERE c.status = '生效中'
  AND p.id IS NULL;          -- 过滤掉有缴费记录的合同，仅保留无任何缴费的生效合同


-- ---------------------------------------------------------------------
-- ② 支付表有记录，但对应合同状态不是"生效中"的合同
--    业务口径：合同解约/到期后不应再产生有效业务流水，若 payments 中仍存在指向
--    "已终止/已到期"合同的记录，说明存在“合同已失效但缴费流水未清理”的一致性问题。
--    为避免重复，这里按 p.contract_id 去重，仅展示首个异常流水。
-- ---------------------------------------------------------------------
SELECT
    p.contract_id                     AS 合同ID,
    c.contract_no                     AS 合同编号,
    c.status                          AS 合同状态,
    c.terminate_time                  AS 解约时间,
    COUNT(p.id)                       AS 异常流水条数,
    SUM(CASE WHEN p.status = '已支付' THEN p.amount ELSE 0 END) AS 已支付异常金额
FROM payments p
LEFT JOIN contracts c
       ON c.id = p.contract_id
WHERE c.status NOT IN ('生效中')      -- 生效中之外：已终止 / 已到期 / 待确认 等
GROUP BY p.contract_id, c.contract_no, c.status, c.terminate_time;


-- ---------------------------------------------------------------------
-- ③ 某个房东(landlord_id 替换为实际ID)名下所有合同的总租金、总押金统计
--    业务口径：按合同统计金额（不以支付流水统计，体现“合同应收口径”），
--    并可顺带输出名下有效合同数，便于与房东端统计页面核对 rentalRate/收入。
-- ---------------------------------------------------------------------
SELECT
    c.landlord_id                     AS 房东ID,
    u.username                        AS 房东用户名,
    u.real_name                       AS 房东姓名,
    COUNT(c.id)                       AS 合同总数,
    COUNT(CASE WHEN c.status = '生效中' THEN 1 END) AS 生效中合同数,
    COALESCE(SUM(c.monthly_rent), 0)  AS 总月租金,
    COALESCE(SUM(c.deposit), 0)       AS 总押金
FROM contracts c
JOIN users u
  ON u.id = c.landlord_id
WHERE c.landlord_id = 2               -- ← 请替换为你要统计的房东ID
GROUP BY c.landlord_id, u.username, u.real_name;


-- =====================================================================
-- ===== 执行结果摘要 =====
-- 说明：执行上述 ① ② ③ 三条查询后，请将实际结果填写到下方占位符，
--      已发现的数据一致性问题建议关联登记到 Bug清单。
--      建议同时记录：执行时间、数据库版本、数据量级，便于问题定位与追溯。
-- =====================================================================

-- 【执行时间】：[请在此处填写实际执行时间]

-- ① 生效中合同但无任何缴费记录：
--     返回行数：[请在此处填写实际查询结果，如：0 行 / 1 行 - 合同HT202609090001]
--     初步结论：[请在此处填写，如：数据一致 / 存在漏生成缴费的生效合同]

-- ② 存在缴费记录但合同状态非生效中：
--     返回行数：[请在此处填写实际查询结果，如：0 行 / 1 行 - 合同ID=5]
--     异常合同ID列表：[请在此处填写实际查询结果]

-- ③ 房东(landlord_id=2)名下合同租金统计：
--     合同总数 / 生效中合同数 / 总月租金 / 总押金：
--     [请在此处填写实际查询结果]

-- 补充说明：
--   [请在此处填写，例如：第②项发现的 2 条异常流水是否已人工核实/修复]