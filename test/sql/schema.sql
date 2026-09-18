-- ============================================================================
-- schema.sql —— 自动化测试用数据库结构（建表脚本）
--
-- 用途：
--   1) 为 CI（GitHub Actions）提供确定的表结构，保证在启动后端之前就能导入种子数据；
--   2) 供本地复现 CI 环境使用：mysql -h127.0.0.1 -P3306 -uapartment -p apartment_rental_db < schema.sql
--
-- 字段与表名来源（未做任何臆造，全部对齐后端 JPA 实体）：
--   users        <- backend/src/main/java/com/rental/entity/User.java
--   apartments   <- backend/src/main/java/com/rental/entity/Apartment.java
--   appointments <- backend/src/main/java/com/rental/entity/Appointment.java
--   contracts    <- backend/src/main/java/com/rental/entity/Contract.java
--   payments     <- backend/src/main/java/com/rental/entity/Payment.java
--
-- 说明：
--   - 本脚本使用 CREATE TABLE IF NOT EXISTS，可重复执行，不会删除任何已有数据；
--   - 其余业务表（favorites/reviews/messages/repairs/complaints）由后端 JPA 的
--     ddl-auto=update 在服务启动时自动创建，测试用例未直接依赖，故不在此重复定义；
--   - 语句与 Hibernate 实际生成的 DDL 完全一致（含索引与约束名），
--     以便后端启动执行 update 时判定为“无需变更”，不会产生额外的 ALTER。
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 表 1：users —— 用户表（管理员 / 房东 / 租户）
-- 关键字段：
--   username 登录名（唯一）、password BCrypt 密文、role 角色枚举
--   role 取值：ADMIN / LANDLORD / TENANT
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
  `id` bigint NOT NULL AUTO_INCREMENT,                                  -- 主键，自增
  `create_time` datetime(6) NOT NULL,                                   -- 创建时间（JPA @PrePersist 写入）
  `password` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,          -- BCrypt 加密后的密码
  `phone` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,          -- 手机号
  `real_name` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,      -- 真实姓名
  `role` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,           -- 角色：ADMIN/LANDLORD/TENANT
  `update_time` datetime(6) DEFAULT NULL,                               -- 更新时间
  `username` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL,           -- 登录用户名（唯一）
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK_r43af9ap4edm43mmtq01oddj6` (`username`)                -- 用户名唯一约束（名称与 Hibernate 一致）
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 表 2：apartments —— 房源表
-- 关键字段：
--   status       房源状态，实测枚举为“空置”（后端 ApartmentService 默认值）
--   audit_status 审核状态：审核通过 / 待审核（ApartmentController#findAudited 使用“审核通过”）
--   landlord_id  外键 -> users.id（房源所属房东）
--   image_url    历史遗留列，仍存在于库中，保留以保证与后端一致
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `apartments` (
  `id` bigint NOT NULL AUTO_INCREMENT,                                  -- 主键，自增
  `address` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL,       -- 地址
  `area` decimal(10,2) DEFAULT NULL,                                    -- 面积（平方米）
  `building` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,       -- 楼栋
  `create_time` datetime(6) NOT NULL,                                   -- 创建时间
  `description` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,   -- 房源描述
  `floor` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,          -- 楼层
  `image_url` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,     -- 历史遗留图片列
  `monthly_rent` decimal(10,2) DEFAULT NULL,                            -- 月租金
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,              -- 房源名称
  `room_number` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,    -- 房间号
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,         -- 房源状态（空置/已出租）
  `unit` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,           -- 单元
  `update_time` datetime(6) DEFAULT NULL,                               -- 更新时间
  `landlord_id` bigint DEFAULT NULL,                                    -- 外键 -> users.id
  `audit_remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,  -- 审核备注
  `audit_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,   -- 审核状态
  `cover_image` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,   -- 封面图
  `detail_images` varchar(2000) COLLATE utf8mb4_unicode_ci DEFAULT NULL,-- 详情图（多张）
  PRIMARY KEY (`id`),
  KEY `FKlgxqx6iee69xapghocb02dltp` (`landlord_id`),
  CONSTRAINT `FKlgxqx6iee69xapghocb02dltp` FOREIGN KEY (`landlord_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 表 3：appointments —— 看房预约表
-- 关键字段：
--   apartment_id / tenant_id / landlord_id 三个外键均为 NOT NULL（外键约束失败即由此产生）
--   status 预约状态：待处理（后端 AppointmentService 默认值）/ 已接受
-- 注意：本表没有 user_id 列，租户字段名为 tenant_id（测试代码按真实字段校验）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `appointments` (
  `id` bigint NOT NULL AUTO_INCREMENT,                                  -- 主键，自增
  `appointment_time` datetime(6) NOT NULL,                              -- 预约看房时间
  `create_time` datetime(6) NOT NULL,                                   -- 创建时间
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,        -- 备注
  `reply` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,         -- 房东回复
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,         -- 预约状态：待处理/已接受
  `update_time` datetime(6) DEFAULT NULL,                               -- 更新时间
  `apartment_id` bigint NOT NULL,                                       -- 外键 -> apartments.id
  `landlord_id` bigint NOT NULL,                                        -- 外键 -> users.id
  `tenant_id` bigint NOT NULL,                                          -- 外键 -> users.id
  PRIMARY KEY (`id`),
  KEY `FKh3sjxls7carki9imrg82stkud` (`apartment_id`),
  KEY `FK73p89sb5fy751gn125154ltvm` (`landlord_id`),
  KEY `FKhpawwp308oijr2ox9mtcvwtuf` (`tenant_id`),
  CONSTRAINT `FK73p89sb5fy751gn125154ltvm` FOREIGN KEY (`landlord_id`) REFERENCES `users` (`id`),
  CONSTRAINT `FKh3sjxls7carki9imrg82stkud` FOREIGN KEY (`apartment_id`) REFERENCES `apartments` (`id`),
  CONSTRAINT `FKhpawwp308oijr2ox9mtcvwtuf` FOREIGN KEY (`tenant_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 表 4：contracts —— 租赁合同表
-- 关键字段：
--   status 合同状态：生效中 / 已到期 / 已终止（后端 ContractStatusScheduler 定时任务使用“生效中”“已到期”）
--   start_date / end_date 均为 NOT NULL，预约冲突校验（AppointmentService）依赖该区间
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `contracts` (
  `id` bigint NOT NULL AUTO_INCREMENT,                                  -- 主键，自增
  `contract_no` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,       -- 合同编号
  `create_time` datetime(6) NOT NULL,                                   -- 创建时间
  `deposit` decimal(10,2) DEFAULT NULL,                                 -- 押金
  `end_date` date NOT NULL,                                             -- 合同结束日期
  `monthly_rent` decimal(10,2) DEFAULT NULL,                            -- 月租金
  `payment_method` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL, -- 付款方式
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,        -- 备注
  `start_date` date NOT NULL,                                           -- 合同开始日期
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,         -- 合同状态
  `update_time` datetime(6) DEFAULT NULL,                               -- 更新时间
  `apartment_id` bigint NOT NULL,                                       -- 外键 -> apartments.id
  `landlord_id` bigint NOT NULL,                                        -- 外键 -> users.id
  `tenant_id` bigint NOT NULL,                                          -- 外键 -> users.id
  `contract_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,  -- 合同类型：新签/续签/转租
  `original_contract_id` bigint DEFAULT NULL,                           -- 原合同 id（续签/转租来源）
  `sublet_status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,  -- 转租状态：无/转租中
  `terminate_reason` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL, -- 终止原因
  `terminate_time` datetime(6) DEFAULT NULL,                            -- 终止时间
  `new_tenant_id` bigint DEFAULT NULL,                                  -- 新租户 id（转租后）
  PRIMARY KEY (`id`),
  KEY `FKq9jin1bxv13ve3ietjeetxagq` (`apartment_id`),
  KEY `FK3iuurga8k6kbqj65g6j2ule0x` (`landlord_id`),
  KEY `FKra7p26cb32ydditq6ab80pv6l` (`tenant_id`),
  KEY `FKmltu8fj9k4hs1ypsmnq0vv7y1` (`new_tenant_id`),
  CONSTRAINT `FK3iuurga8k6kbqj65g6j2ule0x` FOREIGN KEY (`landlord_id`) REFERENCES `users` (`id`),
  CONSTRAINT `FKmltu8fj9k4hs1ypsmnq0vv7y1` FOREIGN KEY (`new_tenant_id`) REFERENCES `users` (`id`),
  CONSTRAINT `FKq9jin1bxv13ve3ietjeetxagq` FOREIGN KEY (`apartment_id`) REFERENCES `apartments` (`id`),
  CONSTRAINT `FKra7p26cb32ydditq6ab80pv6l` FOREIGN KEY (`tenant_id`) REFERENCES `users` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ---------------------------------------------------------------------------
-- 表 5：payments —— 缴费流水表
-- 关键字段：
--   contract_id 外键 -> contracts.id（一致性校验用例依赖该关联）
--   status 缴费状态：已支付 / 待支付
--   payment_type 缴费类型：租金 / 押金 / 水电费
--   注意：本表无 payment_status 列，状态字段名为 status
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS `payments` (
  `id` bigint NOT NULL AUTO_INCREMENT,                                  -- 主键，自增
  `amount` decimal(10,2) DEFAULT NULL,                                  -- 缴费金额
  `create_time` datetime(6) NOT NULL,                                   -- 创建时间
  `payment_date` date NOT NULL,                                         -- 应缴日期
  `payment_method` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL, -- 支付方式
  `payment_no` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,        -- 缴费单号
  `payment_type` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,   -- 缴费类型：租金/押金/水电费
  `remark` varchar(500) COLLATE utf8mb4_unicode_ci DEFAULT NULL,        -- 备注
  `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,         -- 缴费状态：已支付/待支付
  `update_time` datetime(6) DEFAULT NULL,                               -- 更新时间
  `contract_id` bigint NOT NULL,                                        -- 外键 -> contracts.id
  `landlord_id` bigint NOT NULL,                                        -- 外键 -> users.id
  `tenant_id` bigint NOT NULL,                                          -- 外键 -> users.id
  `pay_time` datetime(6) DEFAULT NULL,                                  -- 实际支付时间
  `payment_voucher` varchar(200) COLLATE utf8mb4_unicode_ci DEFAULT NULL, -- 支付凭证图片
  PRIMARY KEY (`id`),
  KEY `FKqywegtqyijw241foqfkseq1l6` (`contract_id`),
  KEY `FK80vk9nv5gembkwiv9m18gaysl` (`landlord_id`),
  KEY `FK79d7r5jr8vll02xg5c6eih89s` (`tenant_id`),
  CONSTRAINT `FK79d7r5jr8vll02xg5c6eih89s` FOREIGN KEY (`tenant_id`) REFERENCES `users` (`id`),
  CONSTRAINT `FK80vk9nv5gembkwiv9m18gaysl` FOREIGN KEY (`landlord_id`) REFERENCES `users` (`id`),
  CONSTRAINT `FKqywegtqyijw241foqfkseq1l6` FOREIGN KEY (`contract_id`) REFERENCES `contracts` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;