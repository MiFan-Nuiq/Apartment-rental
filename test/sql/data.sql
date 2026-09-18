-- ============================================================================
-- data.sql —— 自动化测试种子数据（幂等，可重复执行）
--
-- 用途：
--   解决 CI（GitHub Actions）中“数据库为空”导致的用例失败：
--     - test_query_apartments / test_full_flow 失败：房源列表为空
--     - test_submit_appointment 失败：apartment_id=3 不存在，外键约束失败
--
-- 与测试代码的对应关系（务必保持一致，见 test/automation/conftest.py）：
--   USERNAME=tenant / PASSWORD=123456   -> users.id = 3
--   LANDLORD_ID = 2                     -> users.id = 2（房东）
--   TENANT_ID   = 3                     -> users.id = 3（租户）
--   APARTMENT_ID= 3                     -> apartments.id = 3（必须存在，否则预约外键失败）
--   APPOINTMENT_TIME 默认 2026-10-01     -> apartments.id=3 上不能有“生效中”合同，
--                                          否则 AppointmentService 会拦截预约（提示已被预订）
--
-- 幂等性说明：
--   全部使用 INSERT ... ON DUPLICATE KEY UPDATE（按主键），重复执行不会报错；
--   在已存在同 id 数据的库上执行时，会将该行的关键字段规范化为种子值，
--   以保证测试前置条件稳定（CI 为全新库，等价于纯插入）。
--
-- 执行方式：mysql -h127.0.0.1 -P3306 -uapartment -p apartment_rental_db < data.sql
-- ============================================================================

-- ---------------------------------------------------------------------------
-- ① 用户数据：与后端 DataInitializer 初始化出的账号完全一致
--    password 为 BCrypt("123456") 的密文，直接取自本项目后端
--    BCryptPasswordEncoder 生成的结果（非手写，保证登录接口校验通过）
--    说明：users 表若已有数据，后端 DataInitializer 的 count()==0 判断会跳过初始化，
--          因此这里必须把登录账号一并种下，否则登录用例会失败。
-- ---------------------------------------------------------------------------
INSERT INTO `users` (`id`, `username`, `password`, `real_name`, `phone`, `role`, `create_time`, `update_time`) VALUES
  (1, 'admin',    '$2a$10$ciZ2htni/HqazRxVlTD11.EKta54TCPxeZqlKkHIhnPU0vw7VLP1K', '系统管理员', '13800138000', 'ADMIN',    NOW(), NOW()),
  (2, 'landlord', '$2a$10$ciZ2htni/HqazRxVlTD11.EKta54TCPxeZqlKkHIhnPU0vw7VLP1K', '张房东',     '13800138001', 'LANDLORD', NOW(), NOW()),
  (3, 'tenant',   '$2a$10$ciZ2htni/HqazRxVlTD11.EKta54TCPxeZqlKkHIhnPU0vw7VLP1K', '李租户',     '13800138002', 'TENANT',   NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `username`  = VALUES(`username`),   -- 用户名规范化
  `password`  = VALUES(`password`),   -- 密码统一重置为 123456 的密文，保证登录用例可复现
  `real_name` = VALUES(`real_name`),
  `phone`     = VALUES(`phone`),
  `role`      = VALUES(`role`),
  `update_time` = NOW();

-- ---------------------------------------------------------------------------
-- ② 房源数据：至少 3 条，id 固定为 1、2、3
--    status='空置'        后端 ApartmentService 的默认房源状态（项目中不存在“可预约”枚举）
--    audit_status='审核通过' 与 ApartmentController#findAudited 使用同一枚举值
--    landlord_id=2        必须指向已存在的房东用户，否则外键约束失败
--    其中 id=3 的字段与本地真实数据保持一致，避免覆盖本地已有房源信息
-- ---------------------------------------------------------------------------
INSERT INTO `apartments` (`id`, `name`, `address`, `building`, `unit`, `room_number`, `floor`, `area`, `monthly_rent`, `status`, `audit_status`, `description`, `landlord_id`, `create_time`, `update_time`) VALUES
  (1, '阳光花园A座101', '北京市朝阳区阳光路1号', 'A座', '1单元', '101', '1', 68.50, 3200.00, '空置', '审核通过', '自动化测试种子房源：一室一厅，采光良好', 2, NOW(), NOW()),
  (2, '阳光花园A座202', '北京市朝阳区阳光路2号', 'A座', '2单元', '202', '2', 89.00, 4200.00, '空置', '审核通过', '自动化测试种子房源：两室一厅，近地铁', 2, NOW(), NOW()),
  (3, '北京苑',         '北京市',               NULL,  NULL,   NULL,  NULL,  NULL, 3500.00, '空置', '审核通过', '自动化测试种子房源：预约用例目标房源', 2, NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `name`         = VALUES(`name`),
  `address`      = VALUES(`address`),
  `monthly_rent` = VALUES(`monthly_rent`),
  `status`       = VALUES(`status`),        -- 保证房源状态可用于查询
  `audit_status` = VALUES(`audit_status`),  -- 保证审核状态字段非空（字段完整性断言依赖）
  `landlord_id`  = VALUES(`landlord_id`),
  `update_time`  = NOW();

-- ---------------------------------------------------------------------------
-- ③ 合同数据：为一致性校验用例准备“干净”的数据基线
--    id=1：生效中合同（apartment 1），end_date 设为未来日期，
--          避免被 ContractStatusScheduler 定时任务（每天 0 点）改成“已到期”
--    id=2：已终止合同（apartment 2），且不生成任何缴费流水，
--          使一致性用例②（非生效中合同残留流水）在全新库上可正常通过
--    注意：合同的 apartment_id 不能是 3 —— 否则预约时间落在合同区间内时，
--          AppointmentService#checkAppointmentTimeConflict 会拦截预约提交
-- ---------------------------------------------------------------------------
INSERT INTO `contracts` (`id`, `contract_no`, `apartment_id`, `tenant_id`, `landlord_id`, `start_date`, `end_date`, `monthly_rent`, `deposit`, `payment_method`, `status`, `contract_type`, `sublet_status`, `create_time`, `update_time`) VALUES
  (1, 'HT-CI-0001', 1, 3, 2, '2026-01-01', '2027-12-31', 3200.00, 3200.00, '月付', '生效中', '新签', '无', NOW(), NOW()),
  (2, 'HT-CI-0002', 2, 3, 2, '2025-01-01', '2025-12-31', 4200.00, 4200.00, '月付', '已终止', '新签', '无', NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `contract_no`  = VALUES(`contract_no`),
  `apartment_id` = VALUES(`apartment_id`),
  `tenant_id`    = VALUES(`tenant_id`),
  `landlord_id`  = VALUES(`landlord_id`),
  `start_date`   = VALUES(`start_date`),
  `end_date`     = VALUES(`end_date`),
  `monthly_rent` = VALUES(`monthly_rent`),
  `deposit`      = VALUES(`deposit`),
  `status`       = VALUES(`status`),
  `update_time`  = NOW();

-- ---------------------------------------------------------------------------
-- ④ 缴费流水：只为“生效中”的合同 1 生成租金与押金流水
--    对应一致性用例①：生效中合同不应缺失缴费记录
--    对应一致性用例②：非生效中合同（合同 2）不得有流水
--    status='已支付'、payment_type 取值为“租金/押金/水电费”（与后端枚举一致）
-- ---------------------------------------------------------------------------
INSERT INTO `payments` (`id`, `payment_no`, `contract_id`, `tenant_id`, `landlord_id`, `payment_date`, `pay_time`, `amount`, `payment_type`, `payment_method`, `status`, `remark`, `create_time`, `update_time`) VALUES
  (1, 'JF-CI-0001', 1, 3, 2, '2026-01-01', '2026-01-01 09:00:00', 3200.00, '租金', '月付', '已支付', '自动化测试种子流水：首月租金', NOW(), NOW()),
  (2, 'JF-CI-0002', 1, 3, 2, '2026-01-01', '2026-01-01 09:00:00', 3200.00, '押金', '月付', '已支付', '自动化测试种子流水：押金',     NOW(), NOW())
ON DUPLICATE KEY UPDATE
  `payment_no`  = VALUES(`payment_no`),
  `contract_id` = VALUES(`contract_id`),
  `amount`      = VALUES(`amount`),
  `status`      = VALUES(`status`),
  `update_time` = NOW();

-- ---------------------------------------------------------------------------
-- ⑤ 预约数据：1 条历史预约，用于验证预约列表/落库查询
--    apartment_id=2（无生效中合同，不会触发预约时间冲突校验）
--    ON DUPLICATE KEY UPDATE 使用空更新（id=id），已存在时不改动，避免覆盖本地已有预约
--    注意：自动化用例断言的是 id 最大的最新记录，本行 id=1 不会被误判为目标记录
-- ---------------------------------------------------------------------------
INSERT INTO `appointments` (`id`, `apartment_id`, `tenant_id`, `landlord_id`, `appointment_time`, `status`, `remark`, `create_time`, `update_time`) VALUES
  (1, 2, 3, 2, '2026-09-25 14:00:00', '待处理', '自动化测试种子预约：历史看房预约', NOW(), NOW())
ON DUPLICATE KEY UPDATE `id` = `id`;