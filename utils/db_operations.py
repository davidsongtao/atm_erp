"""
Description: 数据库操作
    
-*- Encoding: UTF-8 -*-
@File     ：db_operations.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午9:05
@Contact  ：king.songtao@gmail.com
"""
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
        df = query_result[['id', 'username', 'password', 'role', 'name']]
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


def create_work_order(order_date, created_by, source, work_address, payment_method,
                      order_amount, basic_service, rooms, electricals, other_services,
                      custom_item, paperwork):
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
                payment_method, order_amount, total_amount, basic_service, rooms,
                electricals, other_services, custom_item, assigned_cleaner,
                payment_received, invoice_sent, receipt_sent, paperwork)
                VALUES 
                (:order_date, NULL, NULL, :created_by, :source, :work_address,
                :payment_method, :order_amount, :total_amount, :basic_service, :rooms,
                :electricals, :other_services, :custom_item, '暂未派单',
                FALSE, FALSE, FALSE, :paperwork)
                """),
                params={
                    'order_date': order_date,
                    'created_by': created_by,
                    'source': source,
                    'work_address': work_address,
                    'payment_method': payment_method,
                    'order_amount': order_amount,
                    'total_amount': total_amount,
                    'basic_service': basic_service_str,
                    'rooms': rooms_str,
                    'electricals': electricals_str,
                    'other_services': other_services_str,
                    'custom_item': custom_items_str,
                    'paperwork': paperwork  # 新增参数
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


def update_payment_status(order_id, payment_date):
    """
    更新工单的收款状态
    Args:
        order_id: 工单ID
        payment_date: 收款日期
    Returns:
        tuple: (是否成功, 错误信息)
    """
    try:
        conn = get_database_connection()
        cursor = conn.cursor()

        # 更新收款状态和收款日期
        sql = """
            UPDATE work_orders 
            SET payment_received = 1, 
                payment_date = %s,
                updated_at = NOW()
            WHERE id = %s
        """
        cursor.execute(sql, (payment_date, order_id))
        conn.commit()

        cursor.close()
        conn.close()
        return True, None

    except Exception as e:
        return False, str(e)
