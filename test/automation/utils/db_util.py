# -*- coding: utf-8 -*-
"""
数据库工具模块：基于 pymysql 封装 MySQL 连接与常用查询/执行方法。

用途：
    - 为数据一致性校验用例（testcases/test_data_consistency.py）提供直连库查询能力；
    - 为接口用例提供“接口返回 vs 数据库落库”的交叉校验能力。

连接信息：
    统一从环境变量读取，默认值对齐后端 backend/src/main/resources/application.yml：
        host=localhost  port=3306  database=apartment_rental_db  user=apartment  password=123456

表名与字段说明（对齐后端 JPA 实体，驼峰转下划线命名）：
    appointments(id, apartment_id, tenant_id, landlord_id, appointment_time, status, remark, reply,
                 create_time, update_time)   —— 注意：本表没有 user_id 列，租户字段为 tenant_id
    contracts(id, contract_no, apartment_id, tenant_id, landlord_id, start_date, end_date,
              monthly_rent, deposit, status, contract_type, sublet_status, terminate_time, create_time, ...)
    payments(id, payment_no, contract_id, tenant_id, landlord_id, payment_date, amount,
             payment_type, status, pay_time, create_time, ...)
    users(id, username, real_name, role, phone, ...)
"""

import os

import pymysql
from pymysql.cursors import DictCursor


def default_db_config() -> dict:
    """
    构建默认数据库连接配置（环境变量优先，默认值取自后端 application.yml）。

    参数:
        无
    返回:
        dict：可直接传给 pymysql.connect 的连接参数字典
    异常:
        无（仅组装配置，不建立连接）
    """
    return {
        "host": os.getenv("DB_HOST", "localhost"),          # 数据库主机
        "port": int(os.getenv("DB_PORT", "3306")),          # 数据库端口
        "user": os.getenv("DB_USER", "apartment"),          # 数据库用户名
        "password": os.getenv("DB_PASSWORD", "123456"),     # 数据库密码
        "database": os.getenv("DB_NAME", "apartment_rental_db"),  # 库名
        "charset": "utf8mb4",                               # 支持中文与 emoji
    }


class DBUtil:
    """MySQL 数据库操作封装类（一个实例持有一个长连接，供 session 级 fixture 复用）。"""

    def __init__(self, config: dict = None):
        """
        初始化数据库工具并建立连接。

        参数:
            config: 连接配置字典；缺省时使用 default_db_config()（环境变量 + application.yml 默认值）
        返回:
            无
        异常:
            pymysql.MySQLError：连接失败（如库未启动、账号密码错误）时抛出，由调用方给出清晰报错
        """
        # 未显式传参时使用环境变量/default 配置，避免密码硬编码到多个文件
        self.config = config or default_db_config()
        # 使用 DictCursor，查询结果直接是 dict，便于按字段名断言
        self.conn = pymysql.connect(cursorclass=DictCursor, **self.config)

    def query_one(self, sql: str, params: tuple = None) -> dict:
        """
        查询单条记录（取结果集第一条）。

        参数:
            sql: 查询 SQL（建议使用 %s 占位符配合 params，避免拼接注入）
            params: SQL 参数元组，默认 None
        返回:
            dict：单条记录；无结果时返回 None
        异常:
            pymysql.MySQLError：SQL 执行异常
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)     # 参数化执行，防注入
            return cursor.fetchone()        # 无数据时返回 None

    def query_all(self, sql: str, params: tuple = None) -> list:
        """
        查询多条记录。

        参数:
            sql: 查询 SQL
            params: SQL 参数元组，默认 None
        返回:
            list[dict]：记录列表；无结果时返回空列表
        异常:
            pymysql.MySQLError：SQL 执行异常
        """
        with self.conn.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    def execute(self, sql: str, params: tuple = None) -> int:
        """
        执行写操作（INSERT/UPDATE/DELETE）。

        参数:
            sql: 写操作 SQL
            params: SQL 参数元组，默认 None
        返回:
            int：受影响行数
        异常:
            pymysql.MySQLError：SQL 执行异常
        """
        with self.conn.cursor() as cursor:
            rows = cursor.execute(sql, params)  # 返回受影响行数
        self.conn.commit()                      # 写操作显式提交事务
        return rows

    def close(self):
        """
        关闭数据库连接。

        参数:
            无
        返回:
            无
        异常:
            无（忽略已关闭情况）
        """
        if self.conn:
            self.conn.close()  # 释放连接，由 fixture 在 session 结束时调用