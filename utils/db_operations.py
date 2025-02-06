"""
Description: 数据库操作

-*- Encoding: UTF-8 -*-
@File     ：db_operations.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午9:05
@Contact  ：king.songtao@gmail.com
"""
from datetime import date, datetime

import pandas as pd
import streamlit as st
from configs.settings import *
from sqlalchemy import text
from utils.utils import remove_active_session


# 连接数据库
def connect_db():
    try:
        conn = st.connection('mysql', type='sql')
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败，错误信息：{e}")
        return None


# 根据用户名查询用户密码
def login_auth(username, password):
    try:
        conn = connect_db()
        query_result = conn.query(
            "SELECT password, role, name FROM users WHERE username = :username",
            params={'username': username},
            ttl=0  # 禁用缓存
        ).to_dict()
        if not query_result or len(query_result['password']) == 0:
            logger.error(f"用户 {username} 不存在")
            return False, None, "用户名不存在", None

        db_password = query_result['password'][0]

        if db_password == password:
            role = query_result['role'][0]
            name = query_result['name'][0]
            logging_status = True
            error_message = None
            logger.success(f"用户 {username} 登录成功！")
        else:
            logging_status = False
            role = None
            name = None
            error_message = "密码错误"
            logger.error(f"用户 {username} 登录失败！密码不匹配")

        return logging_status, role, error_message, name

    except Exception as e:
        logger.error(f"数据库验证失败，错误信息：{e}")
        return False, None, str(e), None


def get_all_staff_acc():
    try:
        conn = connect_db()
        # 将 ttl 设置为 0 以禁用缓存
        query_result = conn.query("SELECT *  FROM users", ttl=0)
        # 移除 id 列，只选择其他需要的列
        df = query_result[['username', 'password', 'role', 'name']]
        df['password'] = "********"
        df = df.rename(columns=BaseConfig().CUSTOM_HEADER)
        return df, None
    except Exception as e:
        logger.error(f"获取所有员工信息失败！错误信息：{e}")
        error_message = "获取所有员工信息失败!"
        return None, error_message


def create_new_account(username, password, name, role):
    """
    创建新的用户账户
    :param username: 用户名
    :param password: 密码
    :param name: 姓名
    :param role: 角色
    :return: 创建状态，错误信息
    """
    try:
        conn = connect_db()

        # 首先检查用户名是否已存在
        check_query = conn.query(
            "SELECT COUNT(*) as count FROM users WHERE username = :username",
            params={'username': username}
        ).to_dict()

        if check_query['count'][0] > 0:
            return False, "用户名已存在"

        # 使用 text() 函数包装 SQL 语句
        with conn.session as session:
            session.execute(
                text("""
                INSERT INTO users (username, password, name, role) 
                VALUES (:username, :password, :name, :role)
                """),
                params={
                    'username': username,
                    'password': password,
                    'name': name,
                    'role': role
                }
            )
            session.commit()

        logger.success(f"成功创建新用户：{username}")
        return True, None

    except Exception as e:
        logger.error(f"创建新用户失败，错误信息：{e}")
        return False, str(e)


def update_account(username, new_name, new_password=None, new_role=None):
    try:
        conn = connect_db()

        # 构建UPDATE语句
        update_fields = []
        params = {'username': username, 'new_name': new_name}

        update_fields.append("name = :new_name")

        if new_password:
            update_fields.append("password = :new_password")
            params['new_password'] = new_password

        if new_role:
            update_fields.append("role = :new_role")
            params['new_role'] = new_role

        update_sql = f"""
            UPDATE users 
            SET {', '.join(update_fields)}
            WHERE username = :username
        """

        # 使用session执行更新
        with conn.session as session:
            session.execute(text(update_sql), params)
            session.commit()

        # 获取新的数据库连接来验证更新
        verify_conn = connect_db()

        if new_password:
            verify_query = verify_conn.query(
                "SELECT password FROM users WHERE username = :username",
                params={'username': username},
                ttl=0
            ).to_dict()
            actual_password = verify_query['password'][0]
            logger.info(f"更新后验证 - 数据库中的新密码: {actual_password}")

            if actual_password != new_password:
                raise Exception("密码更新验证失败")

            remove_active_session(username)
            logger.info(f"已移除用户 {username} 的活跃会话")

        logger.success(f"成功更新用户信息：{username}")
        return True, None

    except Exception as e:
        logger.error(f"更新用户信息失败，错误信息：{e}")
        return False, str(e)


def delete_account(username):
    """
    删除用户账户
    :param username: 要删除的用户名
    :return: 删除状态，错误信息
    """
    try:
        # 检查是否是当前登录用户
        current_user = st.session_state.get("logged_in_username")
        if username == current_user:
            return False, "不能删除自己的账户"

        conn = connect_db()

        # 使用session执行删除
        with conn.session as session:
            session.execute(
                text("DELETE FROM users WHERE username = :username"),
                params={'username': username}
            )
            session.commit()

        # 只清除被删除用户的会话
        remove_active_session(username)

        logger.success(f"成功删除用户账户：{username}")
        return True, None

    except Exception as e:
        logger.error(f"删除用户账户失败，错误信息：{e}")
        return False, str(e)


def create_work_order(order_date, created_by, source, work_address, room_type, payment_method,
                      order_amount, remarks, basic_service, rooms, electricals, other_services,
                      custom_item, paperwork):
    """创建新工单
    Args:
        ...新增room_type和remarks参数...
    """
    try:
        conn = connect_db()

        # 计算总金额
        total_amount = order_amount * 1.1 if payment_method == 'transfer' else order_amount

        # 将列表转换为字符串存储
        basic_service_str = "|".join(basic_service) if basic_service else ""
        rooms_str = "|".join(rooms) if rooms else ""
        electricals_str = "|".join(electricals) if electricals else ""
        other_services_str = "|".join(other_services) if other_services else ""
        custom_items_str = "|".join(custom_item) if custom_item else ""

        with conn.session as session:
            session.execute(
                text("""
                INSERT INTO work_orders 
                (order_date, work_date, work_time, created_by, source, work_address, 
                room_type, payment_method, order_amount, total_amount, remarks, 
                basic_service, rooms, electricals, other_services, custom_item, 
                assigned_cleaner, cleaning_status, payment_received, invoice_sent, 
                receipt_sent, paperwork)
                VALUES 
                (:order_date, NULL, NULL, :created_by, :source, :work_address,
                :room_type, :payment_method, :order_amount, :total_amount, :remarks,
                :basic_service, :rooms, :electricals, :other_services, :custom_item,
                '暂未派单', 0, FALSE, FALSE, FALSE, :paperwork)
                """),
                params={
                    'order_date': order_date,
                    'created_by': created_by,
                    'source': source,
                    'work_address': work_address,
                    'room_type': room_type,
                    'payment_method': payment_method,
                    'order_amount': order_amount,
                    'total_amount': total_amount,
                    'remarks': remarks,
                    'basic_service': basic_service_str,
                    'rooms': rooms_str,
                    'electricals': electricals_str,
                    'other_services': other_services_str,
                    'custom_item': custom_items_str,
                    'paperwork': paperwork
                }
            )
            session.commit()

        logger.success("工单创建成功")
        return True, None
    except Exception as e:
        logger.error(f"创建工单失败：{e}")
        return False, str(e)


def get_work_orders(time_range='week'):
    """获取工单列表"""
    try:
        conn = connect_db()

        # 根据时间范围构建查询条件
        time_filters = {
            'day': 'DATE(work_date) = CURDATE() OR work_date IS NULL',
            'week': 'YEARWEEK(work_date) = YEARWEEK(CURDATE()) OR work_date IS NULL',
            'month': '(YEAR(work_date) = YEAR(CURDATE()) AND MONTH(work_date) = MONTH(CURDATE())) OR work_date IS NULL',
            'quarter': '(YEAR(work_date) = YEAR(CURDATE()) AND QUARTER(work_date) = QUARTER(CURDATE())) OR work_date IS NULL',
            'year': 'YEAR(work_date) = YEAR(CURDATE()) OR work_date IS NULL'
        }

        time_filter = time_filters.get(time_range, time_filters['week'])

        query = f"""
            SELECT * FROM work_orders 
            WHERE {time_filter}
            ORDER BY 
                CASE WHEN work_date IS NULL THEN 0 ELSE 1 END,  -- NULL值排在前面
                order_date DESC,  -- 未派单的按创建日期倒序排
                work_date ASC,
                CASE WHEN work_time IS NULL THEN 1 ELSE 0 END,
                work_time ASC
        """

        result = conn.query(query, ttl=0)
        return result, None
    except Exception as e:
        logger.error(f"获取工单列表失败：{e}")
        return None, str(e)


def get_work_orders_by_date_range(start_date, end_date):
    """根据日期范围获取工单列表"""
    try:
        conn = connect_db()

        query = """
            SELECT * FROM work_orders 
            WHERE work_date BETWEEN :start_date AND :end_date
               OR work_date IS NULL
            ORDER BY 
                CASE WHEN work_date IS NULL THEN 0 ELSE 1 END,  -- NULL值排在前面
                order_date DESC,  -- 未派单的按创建日期倒序排
                work_date ASC,
                CASE WHEN work_time IS NULL THEN 1 ELSE 0 END,
                work_time ASC
        """

        result = conn.query(
            query,
            params={'start_date': start_date, 'end_date': end_date},
            ttl=0
        )
        return result, None
    except Exception as e:
        logger.error(f"获取工单列表失败：{e}")
        return None, str(e)


def get_all_clean_teams():
    """获取所有保洁组信息

    Returns:
        tuple: (DataFrame or None, error_message)
    """
    try:
        conn = connect_db()

        # 使用 conn.query 替代 read_sql，同时修改SQL查询
        df = conn.query("""
            SELECT 
                id, 
                team_name AS '保洁组名称',
                contact_number AS '联系电话',
                CASE 
                    WHEN is_active = 1 THEN '在职'
                    ELSE '离职'
                END AS '是否在职',
                notes AS '备注',
                created_at AS '创建时间',
                updated_at AS '更新时间'
            FROM clean_teams 
            WHERE team_name != '暂未派单'
            ORDER BY is_active DESC, team_name ASC
        """, ttl=0)  # 禁用缓存

        return df, None

    except Exception as e:
        logger.error(f"获取保洁组信息失败：{e}")
        return None, str(e)


def create_clean_team(team_name: str, contact_number: str, notes: str = None) -> tuple[bool, str]:
    try:
        conn = connect_db()

        # 检查名称是否存在
        check_result = conn.query(
            "SELECT id FROM clean_teams WHERE team_name = :team_name",
            params={'team_name': team_name},
            ttl=0
        )

        if not check_result.empty:
            return False, "保洁组名称已存在"

        # 插入新记录
        with conn.session as session:
            session.execute(
                text("""
                INSERT INTO clean_teams (team_name, contact_number, notes)
                VALUES (:team_name, :contact_number, :notes)
                """),
                params={
                    'team_name': team_name,
                    'contact_number': contact_number,
                    'notes': notes
                }
            )
            session.commit()

        return True, ""

    except Exception as e:
        return False, str(e)


def update_clean_team(team_id: int, team_name: str, contact_number: str, is_active: bool = True, notes: str = None) -> tuple[bool, str]:
    """更新保洁组信息

    Args:
        team_id (int): 保洁组ID
        team_name (str): 保洁组名称
        contact_number (str): 联系电话
        is_active (bool): 是否在职
        notes (str, optional): 备注信息

    Returns:
        tuple[bool, str]: (是否成功, 错误信息)
    """
    try:
        conn = connect_db()

        # 检查是否存在相同名称的其他保洁组
        check_result = conn.query(
            """
            SELECT id FROM clean_teams 
            WHERE team_name = :team_name AND id != :team_id
            """,
            params={
                'team_name': team_name,
                'team_id': team_id
            },
            ttl=0
        )

        if not check_result.empty:
            return False, "保洁组名称已存在"

        # 更新保洁组信息
        with conn.session as session:
            session.execute(
                text("""
                UPDATE clean_teams 
                SET team_name = :team_name,
                    contact_number = :contact_number,
                    is_active = :is_active,
                    notes = :notes,
                    updated_at = NOW()
                WHERE id = :team_id
                """),
                params={
                    'team_name': team_name,
                    'contact_number': contact_number,
                    'is_active': is_active,
                    'notes': notes,
                    'team_id': team_id
                }
            )
            session.commit()

        return True, ""

    except Exception as e:
        logger.error(f"更新保洁组信息失败：{e}")
        return False, str(e)


def get_active_clean_teams():
    """获取所有在职的保洁组

    Returns:
        tuple: (DataFrame, error_message)
    """
    try:
        conn = connect_db()

        result = conn.query("""
            SELECT 
                id,
                team_name,
                contact_number
            FROM clean_teams 
            WHERE is_active = 1
            ORDER BY team_name ASC
        """, ttl=0)

        # 转换为字典列表格式
        teams = result.to_dict('records')
        return teams, None

    except Exception as e:
        logger.error(f"获取在职保洁组失败：{e}")
        return None, str(e)


def delete_clean_team(team_id: int) -> tuple[bool, str]:
    """删除保洁组

    Args:
        team_id (int): 保洁组ID

    Returns:
        tuple[bool, str]: (是否成功, 错误信息)
    """
    try:
        conn = connect_db()

        # 检查是否有关联的工单
        check_result = conn.query(
            """
            SELECT COUNT(*) as count 
            FROM work_orders wo 
            JOIN clean_teams ct ON wo.assigned_cleaner = ct.team_name 
            WHERE ct.id = :team_id
            """,
            params={'team_id': team_id},
            ttl=0
        ).to_dict()

        if check_result['count'][0] > 0:
            return False, "该保洁组有关联的工单,无法删除"

        # 执行删除操作
        with conn.session as session:
            session.execute(
                text("DELETE FROM clean_teams WHERE id = :team_id"),
                params={'team_id': team_id}
            )
            session.commit()

        return True, ""

    except Exception as e:
        logger.error(f"删除保洁组失败：{e}")
        return False, str(e)


def get_team_monthly_orders(team_id, year, month):
    """
    获取指定保洁组的月度工单统计
    Args:
        team_id: 保洁组ID
        year: 年份
        month: 月份
    Returns:
        tuple: (DataFrame, error_message)
    """
    try:
        conn = connect_db()
        query_result = conn.query("""
            SELECT 
                wo.work_date,
                wo.work_time,
                wo.work_address,
                wo.order_amount,
                wo.total_amount,
                wo.payment_method
            FROM work_orders wo
            WHERE wo.assigned_cleaner = (
                SELECT team_name 
                FROM clean_teams 
                WHERE id = :team_id
            )
            AND YEAR(wo.work_date) = :year
            AND MONTH(wo.work_date) = :month
            ORDER BY wo.work_date ASC, wo.work_time ASC
        """, params={
            'team_id': team_id,
            'year': year,
            'month': month
        }, ttl=0)

        return query_result, None
    except Exception as e:
        logger.error(f"获取保洁组月度工单统计失败！错误信息：{e}")
        return pd.DataFrame(), f"获取保洁组月度工单统计失败：{str(e)}"


def assign_work_order(order_id: int, team_name: str, work_date: date, work_time: str) -> tuple[bool, str]:
    """更新工单的派单信息

    Args:
        order_id (int): 工单ID
        team_name (str): 保洁组名称
        work_date (date): 保洁日期
        work_time (str): 保洁时间

    Returns:
        tuple[bool, str]: (是否成功, 错误信息)
    """
    try:
        conn = connect_db()

        # 使用 session 执行更新
        with conn.session as session:
            session.execute(
                text("""
                    UPDATE work_orders 
                    SET assigned_cleaner = :team_name,
                        work_date = :work_date,
                        work_time = :work_time,
                        cleaning_status = 1,  -- 设置为进行中
                        updated_at = NOW()
                    WHERE id = :order_id
                """),
                params={
                    'order_id': order_id,
                    'team_name': team_name,
                    'work_date': work_date,
                    'work_time': work_time
                }
            )
            session.commit()

        logger.success(f"工单 {order_id} 派单成功")
        return True, None

    except Exception as e:
        logger.error(f"派单失败：{e}")
        return False, str(e)


def update_remarks(order_id: int, remarks: str) -> tuple[bool, str]:
    """更新工单备注信息

    Args:
        order_id (int): 工单ID
        remarks (str): 新的备注内容

    Returns:
        tuple[bool, str]: (成功状态, 错误信息)
    """
    try:
        conn = connect_db()
        with conn.session as session:
            session.execute(
                text("""
                    UPDATE work_orders 
                    SET remarks = :remarks,
                        updated_at = NOW()
                    WHERE id = :order_id
                """),
                params={
                    'order_id': order_id,
                    'remarks': remarks
                }
            )
            session.commit()

        logger.success(f"工单 {order_id} 备注更新成功")
        return True, None
    except Exception as e:
        logger.error(f"更新备注失败：{e}")
        return False, str(e)


def delete_work_order(order_id: int) -> tuple[bool, str]:
    """删除工单

    Args:
        order_id: 工单ID

    Returns:
        tuple[bool, str]: (是否成功, 错误信息)
    """
    try:
        conn = connect_db()
        with conn.session as session:
            session.execute(
                text("""
                    DELETE FROM work_orders 
                    WHERE id = :order_id
                """),
                params={'order_id': order_id}
            )
            session.commit()

        logger.success(f"工单 {order_id} 删除成功")
        return True, None

    except Exception as e:
        logger.error(f"删除工单失败：{e}")
        return False, str(e)


def update_work_order(data):
    """更新工单信息
    Args:
        data (dict): 工单更新数据
    Returns:
        tuple: (success, error)
    """
    try:
        conn = connect_db()

        # 构建 UPDATE 语句
        update_fields = []
        params = {'order_id': data['id']}

        for key, value in data.items():
            if key != 'id':  # 排除id字段
                update_fields.append(f"{key} = :{key}")
                params[key] = value

        query = text(f"""
            UPDATE work_orders 
            SET {', '.join(update_fields)}
            WHERE id = :order_id
        """)

        with conn.session as session:
            result = session.execute(query, params)
            session.commit()

        success = result.rowcount > 0
        error = None if success else "未找到要更新的工单"

        return success, error

    except Exception as e:
        return False, str(e)


def update_cleaning_status(order_id, status, completed_at=None, cancel=False):
    """更新清洁状态"""
    try:
        conn = connect_db()

        with conn.session as session:
            if cancel:
                query = text("""
                    UPDATE work_orders 
                    SET cleaning_status = 1,
                        cleaning_completed_at = NULL
                    WHERE id = :order_id
                """)
                session.execute(query, {'order_id': order_id})
            else:
                query = text("""
                    UPDATE work_orders 
                    SET cleaning_status = :status,
                        cleaning_completed_at = :completed_at
                    WHERE id = :order_id
                """)
                session.execute(query, {
                    'status': status,
                    'completed_at': completed_at,
                    'order_id': order_id
                })

            session.commit()

        success = conn.query(
            "SELECT COUNT(*) as count FROM work_orders WHERE id = :order_id",
            params={'order_id': order_id}
        )['count'][0] > 0

        error = None if success else "未找到要更新的工单"

        return success, error

    except Exception as e:
        return False, str(e)


# 修改收款状态更新函数，添加撤销功能
def update_payment_status(order_id, payment_time=None, cancel=False):
    """更新收款状态
    Args:
        order_id (int): 工单ID
        payment_time (datetime): 收款时间
        cancel (bool): 是否为撤销操作
    Returns:
        tuple: (success, error)
    """
    try:
        conn = connect_db()

        with conn.session as session:
            if cancel:
                query = text("""
                    UPDATE work_orders 
                    SET payment_received = false, payment_time = NULL 
                    WHERE id = :order_id
                """)
                session.execute(query, {'order_id': order_id})
            else:
                query = text("""
                    UPDATE work_orders 
                    SET payment_received = true, payment_time = :payment_time 
                    WHERE id = :order_id
                """)
                session.execute(query, {
                    'payment_time': payment_time,
                    'order_id': order_id
                })

            session.commit()

        # 检查是否有影响的行
        success = conn.query(
            "SELECT COUNT(*) as count FROM work_orders WHERE id = :order_id",
            params={'order_id': order_id}
        )['count'][0] > 0

        error = None if success else "未找到要更新的工单"

        return success, error

    except Exception as e:
        return False, str(e)


# 修改发票状态更新函数，添加撤销功能
def update_invoice_status(order_id, invoice_date=None, cancel=False):
    """更新发票状态
    Args:
        order_id (int): 工单ID
        invoice_date (datetime): 发票签发日期
        cancel (bool): 是否为撤销操作
    Returns:
        tuple: (success, error)
    """
    try:
        conn = connect_db()

        with conn.session as session:
            if cancel:
                query = text("""
                    UPDATE work_orders 
                    SET invoice_sent = false, invoice_date = NULL 
                    WHERE id = :order_id
                """)
                session.execute(query, {'order_id': order_id})
            else:
                query = text("""
                    UPDATE work_orders 
                    SET invoice_sent = true, invoice_date = :invoice_date 
                    WHERE id = :order_id
                """)
                session.execute(query, {
                    'invoice_date': invoice_date,
                    'order_id': order_id
                })

            session.commit()

        # 检查是否有影响的行
        success = conn.query(
            "SELECT COUNT(*) as count FROM work_orders WHERE id = :order_id",
            params={'order_id': order_id}
        )['count'][0] > 0

        error = None if success else "未找到要更新的工单"

        return success, error

    except Exception as e:
        return False, str(e)


# 修改收据状态更新函数，添加撤销功能
def update_receipt_status(order_id, receipt_time=None, cancel=False):
    """更新收据状态
    Args:
        order_id (int): 工单ID
        receipt_time (datetime): 收据签发时间
        cancel (bool): 是否为撤销操作
    Returns:
        tuple: (success, error)
    """
    try:
        conn = connect_db()

        with conn.session as session:
            if cancel:
                query = text("""
                    UPDATE work_orders 
                    SET receipt_sent = false, receipt_time = NULL 
                    WHERE id = :order_id
                """)
                session.execute(query, {'order_id': order_id})
            else:
                query = text("""
                    UPDATE work_orders 
                    SET receipt_sent = true, receipt_time = :receipt_time 
                    WHERE id = :order_id
                """)
                session.execute(query, {
                    'receipt_time': receipt_time,
                    'order_id': order_id
                })

            session.commit()

        # 检查是否有影响的行
        success = conn.query(
            "SELECT COUNT(*) as count FROM work_orders WHERE id = :order_id",
            params={'order_id': order_id}
        )['count'][0] > 0

        error = None if success else "未找到要更新的工单"

        return success, error

    except Exception as e:
        return False, str(e)


# 添加撤销派单函数
def cancel_assignment(order_id):
    """撤销派单
    Args:
        order_id (int): 工单ID
    Returns:
        tuple: (success, error)
    """
    try:
        conn = connect_db()

        # 如果连接失败，返回 False 和错误消息
        if conn is None:
            logger.error("数据库连接失败")
            return False, "数据库连接失败"

        # 确保 order_id 是整数类型
        order_id = int(order_id)

        with conn.session as session:
            query = text("""
                UPDATE work_orders 
                SET assigned_cleaner = '暂未派单',
                    work_date = NULL,
                    work_time = NULL,
                    cleaning_status = 0,
                    cleaning_completed_at = NULL
                WHERE id = :order_id
            """)
            result = session.execute(query, {'order_id': order_id})
            session.commit()

        # 检查是否有影响的行
        affected_rows = conn.query(
            "SELECT COUNT(*) as count FROM work_orders WHERE id = :order_id",
            params={'order_id': order_id}
        )['count'][0]

        success = result.rowcount > 0
        error = None if success else "未找到要更新的工单"

        return success, error

    except Exception as e:
        logger.error(f"撤销派单失败：{e}")
        # 确保总是返回一个元组
        return False, str(e)
