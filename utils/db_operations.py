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


def create_work_order(
        order_date, created_by, source, work_address,
        income1=0, income2=0,  # 修改为收入1和收入2参数
        work_date=None, work_time=None,
        assigned_cleaner="暂未派单",
        subsidy=None, remarks=None,
        paperwork=None, invoice_sent=False, receipt_sent=False
):
    """创建新工单"""
    try:
        # 计算订单金额和总金额
        order_amount, total_amount, payment_method = calculate_order_amounts(
            income1, income2, assigned_cleaner
        )

        conn = connect_db()
        with conn.session as session:
            session.execute(
                text("""
                INSERT INTO work_orders (
                    order_date, work_date, work_time, created_by, source,
                    work_address, assigned_cleaner, payment_method,
                    order_amount, total_amount, subsidy, remarks,
                    paperwork, invoice_sent, receipt_sent
                )
                VALUES (
                    :order_date, :work_date, :work_time, :created_by, :source,
                    :work_address, :assigned_cleaner, :payment_method,
                    :order_amount, :total_amount, :subsidy, :remarks,
                    :paperwork, :invoice_sent, :receipt_sent
                )
                """),
                params={
                    'order_date': order_date,
                    'work_date': work_date,
                    'work_time': work_time,
                    'created_by': created_by,
                    'source': source,
                    'work_address': work_address,
                    'assigned_cleaner': assigned_cleaner,
                    'payment_method': payment_method,
                    'order_amount': order_amount,
                    'total_amount': total_amount,
                    'subsidy': subsidy,
                    'remarks': remarks,
                    'paperwork': paperwork,
                    'invoice_sent': invoice_sent,
                    'receipt_sent': receipt_sent
                }
            )
            session.commit()

        logger.success("工单创建成功")
        return True, None
    except Exception as e:
        logger.error(f"创建工单失败：{e}")
        return False, str(e)


def update_work_order_amounts(order_id: int, income1: float, income2: float):
    """更新工单金额信息"""
    try:
        conn = connect_db()

        # 获取工单信息
        order_info = conn.query(
            "SELECT assigned_cleaner FROM work_orders WHERE id = :order_id",
            params={'order_id': order_id},
            ttl=0
        ).iloc[0]

        # 计算新的金额
        order_amount, total_amount, payment_method = calculate_order_amounts(
            income1, income2, order_info['assigned_cleaner']
        )

        # 更新工单
        with conn.session as session:
            session.execute(
                text("""
                    UPDATE work_orders 
                    SET order_amount = :order_amount,
                        total_amount = :total_amount,
                        payment_method = :payment_method
                    WHERE id = :order_id
                """),
                params={
                    'order_id': order_id,
                    'order_amount': order_amount,
                    'total_amount': total_amount,
                    'payment_method': payment_method
                }
            )
            session.commit()

        return True, None

    except Exception as e:
        logger.error(f"更新工单金额失败：{e}")
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
                order_date DESC,
                CASE WHEN work_date IS NULL THEN 1 ELSE 0 END,
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
                order_date DESC,
                CASE WHEN work_date IS NULL THEN 1 ELSE 0 END,
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
    """获取所有保洁组信息,包含ABN状态"""
    try:
        conn = connect_db()

        df = conn.query("""
            SELECT 
                id, 
                team_name AS '保洁组名称',
                contact_number AS '联系电话',
                CASE 
                    WHEN is_active = 1 THEN '在职'
                    ELSE '离职'
                END AS '是否在职',
                has_abn,  -- 直接获取has_abn列
                notes AS '备注',
                created_at AS '创建时间',
                updated_at AS '更新时间'
            FROM clean_teams 
            WHERE team_name != '暂未派单'
            ORDER BY is_active DESC, team_name ASC
        """, ttl=0)

        return df, None

    except Exception as e:
        logger.error(f"获取保洁组信息失败：{e}")
        return None, str(e)


def create_clean_team(team_name: str, contact_number: str, has_abn: bool = False, notes: str = None) -> tuple[bool, str]:
    """创建新保洁组"""
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
                INSERT INTO clean_teams (team_name, contact_number, has_abn, notes)
                VALUES (:team_name, :contact_number, :has_abn, :notes)
                """),
                params={
                    'team_name': team_name,
                    'contact_number': contact_number,
                    'has_abn': 1 if has_abn else 0,  # 转换为整数
                    'notes': notes
                }
            )
            session.commit()

        return True, ""

    except Exception as e:
        return False, str(e)


def calculate_total_amount(order_amount: float, payment_method: str, has_abn: bool) -> float:
    """计算订单总金额（含GST）"""
    if not order_amount or payment_method == 'blank':
        return 0

    if payment_method == 'cash':
        return order_amount

    if has_abn:
        return order_amount

    # 对于没有ABN的保洁组，转账部分需要加上GST
    if payment_method == 'transfer':
        return round(order_amount * 1.1, 2)

    if payment_method == 'both':
        # 假设order_amount已经是现金和转账的总和
        # 需要将转账部分加上GST
        # 这里需要从原始的income1和income2重新计算
        raise ValueError("both类型的支付需要提供现金和转账的具体金额")

    return order_amount  # 默认返回原始金额


def calculate_order_amounts(income1: float, income2: float, assigned_cleaner: str) -> tuple[float, float, str]:
    """
    计算订单金额、总金额和支付方式

    Args:
        income1: 现金收入
        income2: 转账收入
        assigned_cleaner: 保洁组名称

    Returns:
        tuple: (order_amount, total_amount, payment_method)
    """
    try:
        conn = connect_db()

        # 获取保洁组的ABN状态
        has_abn = False
        if assigned_cleaner and assigned_cleaner != "暂未派单":
            result = conn.query(
                "SELECT has_abn FROM clean_teams WHERE team_name = :team_name",
                params={'team_name': assigned_cleaner},
                ttl=0
            )
            if not result.empty:
                has_abn = bool(result.iloc[0]['has_abn'])

        # 根据不同情况计算金额
        if income1 == 0 and income2 == 0:
            return 0, 0, 'blank'

        if income1 > 0 and income2 == 0:
            return income1, income1, 'cash'

        if income1 == 0 and income2 > 0:
            if has_abn:
                return income2, income2, 'transfer'
            else:
                return income2, round(income2 * 1.1, 2), 'transfer'

        if income1 > 0 and income2 > 0:
            if has_abn:
                order_amount = income1 + income2
                return order_amount, order_amount, 'both'
            else:
                order_amount = income1 + income2
                total_amount = income1 + round(income2 * 1.1, 2)
                return order_amount, total_amount, 'both'

        return 0, 0, 'blank'

    except Exception as e:
        logger.error(f"计算订单金额失败：{e}")
        raise e


def update_orders_for_team(session, team_name: str, has_abn: bool):
    """更新指定保洁组的所有工单金额"""
    try:
        # 获取该保洁组的所有工单
        orders = session.execute(
            text("""
                SELECT id, payment_method, order_amount
                FROM work_orders
                WHERE assigned_cleaner = :team_name
                AND payment_method IN ('transfer', 'both')
            """),
            {'team_name': team_name}
        ).fetchall()

        for order in orders:
            # 确保转换为浮点数
            order_amount = float(order.order_amount or 0)
            total_amount = order_amount

            # 如果未注册ABN且付款方式为转账或混合，需要加GST
            if not has_abn and order.payment_method in ('transfer', 'both'):
                # 对于转账或混合付款方式，加10% GST
                if order.payment_method == 'transfer':
                    total_amount = round(order_amount * 1.1, 2)
                elif order.payment_method == 'both':
                    # 假设 order_amount 已经包含现金部分
                    # 只对转账部分加GST
                    cash_part = order_amount / 2  # 简单地平分
                    transfer_part = order_amount / 2
                    total_amount = cash_part + round(transfer_part * 1.1, 2)

            session.execute(
                text("""
                    UPDATE work_orders
                    SET total_amount = :total_amount
                    WHERE id = :order_id
                """),
                {
                    'total_amount': total_amount,
                    'order_id': order.id
                }
            )

    except Exception as e:
        logger.error(f"更新工单金额失败：{e}")
        raise e


def update_clean_team(team_id: int, team_name: str, contact_number: str, has_abn: bool, is_active: bool = True, notes: str = None) -> tuple[bool, str]:
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

        # 获取旧的ABN状态
        old_abn_status = conn.query(
            "SELECT has_abn FROM clean_teams WHERE id = :team_id",
            params={'team_id': team_id},
            ttl=0
        ).iloc[0]['has_abn']

        # 更新保洁组信息
        with conn.session as session:
            session.execute(
                text("""
                UPDATE clean_teams 
                SET team_name = :team_name,
                    contact_number = :contact_number,
                    has_abn = :has_abn,
                    is_active = :is_active,
                    notes = :notes,
                    updated_at = NOW()
                WHERE id = :team_id
                """),
                params={
                    'team_name': team_name,
                    'contact_number': contact_number,
                    'has_abn': 1 if has_abn else 0,  # 确保转换为整数
                    'is_active': 1 if is_active else 0,  # 确保转换为整数
                    'notes': notes,
                    'team_id': team_id
                }
            )

            # 如果ABN状态发生变化，更新相关工单的total_amount
            if old_abn_status != (1 if has_abn else 0):
                update_orders_for_team(session, team_name, has_abn)

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
                wo.payment_method,
                wo.subsidy  # 添加这一行
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
    """删除工单及其关联的所有图片

    Args:
        order_id: 工单ID

    Returns:
        tuple[bool, str]: (是否成功, 错误信息)
    """
    try:
        conn = connect_db()
        with conn.session as session:
            try:
                # 首先删除工单关联的所有图片
                session.execute(
                    text("""
                        DELETE FROM work_order_images 
                        WHERE order_id = :order_id
                    """),
                    params={'order_id': order_id}
                )

                # 然后删除工单本身
                session.execute(
                    text("""
                        DELETE FROM work_orders 
                        WHERE id = :order_id
                    """),
                    params={'order_id': order_id}
                )

                # 提交事务
                session.commit()
                logger.success(f"工单 {order_id} 及其关联图片删除成功")
                return True, None

            except Exception as e:
                # 如果发生错误，回滚事务
                session.rollback()
                raise e

    except Exception as e:
        error_msg = f"删除工单失败：{e}"
        logger.error(error_msg)
        return False, error_msg


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
                # 处理日期和时间字段
                if key in ['work_date', 'work_time', 'cleaning_completed_at']:
                    if value == '' or value is None:
                        update_fields.append(f"{key} = NULL")
                        continue

                # 常规字段处理
                update_fields.append(f"{key} = :{key}")
                params[key] = value

        # 如果没有需要更新的字段，返回成功
        if not update_fields:
            return True, None

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
        logger.error(f"更新工单失败：{str(e)}")
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
def update_receipt_status(order_id, receipt_date=None, cancel=False):
    """更新收据状态
    Args:
        order_id (int): 工单ID
        receipt_date (datetime): 收据签发日期 (注意改为 receipt_date)
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
                    SET receipt_sent = false, receipt_date = NULL 
                    WHERE id = :order_id
                """)
                session.execute(query, {'order_id': order_id})
            else:
                query = text("""
                    UPDATE work_orders 
                    SET receipt_sent = true, receipt_date = :receipt_date 
                    WHERE id = :order_id
                """)
                session.execute(query, {
                    'receipt_date': receipt_date,
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


def check_order_has_images(order_id):
    """检查工单是否有图片"""
    conn = connect_db()
    if not conn:
        return False

    try:
        query_result = conn.query(
            "SELECT COUNT(*) as count FROM work_order_images WHERE order_id = :order_id",
            params={'order_id': order_id},
            ttl=0
        ).to_dict()
        return query_result['count'][0] > 0
    except Exception as e:
        logger.error(f"检查工单图片失败: {e}")
        return False


def get_order_images(order_id):
    conn = connect_db()
    if not conn:
        return None

    try:
        # 查询包含缩略图数据
        query_result = conn.query("""
            SELECT i.id, i.image_data, i.thumbnail_data,
                   CONCAT(wo.work_address, '_', DATE_FORMAT(i.created_at, '%Y%m%d%H%i%s')) as image_name
            FROM work_order_images i
            JOIN work_orders wo ON i.order_id = wo.id
            WHERE i.order_id = :order_id
        """, params={'order_id': order_id}, ttl=0).to_dict('records')
        return query_result
    except Exception as e:
        logger.error(f"获取工单图片失败: {e}")
        return None


from PIL import Image
import io


def create_thumbnail(image_data, size=(400, 400)):
    """创建缩略图
    尺寸设为400x400以保证清晰度
    使用高质量的缩放和压缩参数
    """
    try:
        # 将二进制数据转换为图片对象
        image = Image.open(io.BytesIO(image_data))

        # 计算等比例缩放尺寸
        original_size = image.size
        ratio = min(size[0] / original_size[0], size[1] / original_size[1])
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))

        # 使用LANCZOS重采样进行高质量缩放
        resized_image = image.resize(new_size, Image.Resampling.LANCZOS)

        # 转换回二进制，使用较高的质量参数
        thumb_io = io.BytesIO()

        # 根据图片格式选择最佳保存参数
        if image.format == 'JPEG':
            resized_image.save(thumb_io, format='JPEG', quality=85, optimize=True)
        elif image.format == 'PNG':
            resized_image.save(thumb_io, format='PNG', optimize=True)
        else:
            # 默认使用JPEG
            resized_image.save(thumb_io, format='JPEG', quality=85, optimize=True)

        return thumb_io.getvalue()
    except Exception as e:
        logger.error(f"创建缩略图失败: {e}")
        return None


def upload_order_images(order_id, work_address, image_files):
    """上传工单图片"""
    conn = connect_db()
    if not conn:
        return False

    try:
        with conn.session as session:
            for idx, file in enumerate(image_files):
                # 读取原图数据
                image_data = file.read()
                # 创建缩略图
                thumbnail_data = create_thumbnail(image_data)

                # 构建图片名称
                image_name = f"{work_address}_{idx + 1}"

                session.execute(
                    text("""
                        INSERT INTO work_order_images 
                        (order_id, image_name, image_data, thumbnail_data) 
                        VALUES (:order_id, :image_name, :image_data, :thumbnail_data)
                    """),
                    {
                        'order_id': order_id,
                        'image_name': image_name,
                        'image_data': image_data,
                        'thumbnail_data': thumbnail_data
                    }
                )
            session.commit()
        return True
    except Exception as e:
        logger.error(f"上传工单图片失败: {e}")
        return False


def delete_order_image(image_id):
    """删除工单图片"""
    conn = connect_db()
    if not conn:
        return False

    try:
        with conn.session as session:
            session.execute(
                text("DELETE FROM work_order_images WHERE id = :image_id"),
                {'image_id': image_id}
            )
            session.commit()
        return True
    except Exception as e:
        logger.error(f"删除工单图片失败: {e}")
        return False


def handle_order_amounts(income1: float, income2: float, assigned_cleaner: str) -> dict:
    """
    处理工单金额逻辑

    Args:
        income1: 现金收入
        income2: 转账收入
        assigned_cleaner: 保洁组名称

    Returns:
        dict: 包含order_amount, total_amount和payment_method的字典
    """
    try:
        # 先获取保洁组的ABN状态
        conn = connect_db()
        has_abn = False

        if assigned_cleaner and assigned_cleaner != "暂未派单":
            result = conn.query(
                "SELECT has_abn FROM clean_teams WHERE team_name = :team_name",
                params={'team_name': assigned_cleaner},
                ttl=0
            )
            if not result.empty:
                has_abn = bool(result.iloc[0]['has_abn'])

        # 处理不同的收入情况
        order_amount = 0
        total_amount = 0
        payment_method = 'blank'

        if income1 == 0 and income2 == 0:
            return {
                'order_amount': 0,
                'total_amount': 0,
                'payment_method': 'blank'
            }

        if income1 > 0 and income2 == 0:
            # 只有现金收入
            return {
                'order_amount': income1,
                'total_amount': income1,
                'payment_method': 'cash'
            }

        if income1 == 0 and income2 > 0:
            # 只有转账收入
            if has_abn:
                # 有ABN，不需要加GST
                return {
                    'order_amount': income2,
                    'total_amount': income2,
                    'payment_method': 'transfer'
                }
            else:
                # 无ABN，需要加GST
                return {
                    'order_amount': income2,
                    'total_amount': round(income2 * 1.1, 2),
                    'payment_method': 'transfer'
                }

        if income1 > 0 and income2 > 0:
            # 同时有现金和转账收入
            if has_abn:
                # 有ABN，直接相加
                order_amount = income1 + income2
                return {
                    'order_amount': order_amount,
                    'total_amount': order_amount,
                    'payment_method': 'both'
                }
            else:
                # 无ABN，转账部分需要加GST
                order_amount = income1 + income2
                total_amount = income1 + round(income2 * 1.1, 2)
                return {
                    'order_amount': order_amount,
                    'total_amount': total_amount,
                    'payment_method': 'both'
                }

    except Exception as e:
        logger.error(f"处理工单金额失败：{e}")
        raise e


def update_order_total_amount(order_id: int):
    """
    更新工单的total_amount
    当保洁组的ABN状态改变时调用此函数
    """
    try:
        conn = connect_db()

        # 获取工单信息
        order_info = conn.query("""
            SELECT wo.id, wo.order_amount, wo.payment_method, 
                   wo.assigned_cleaner, ct.has_abn
            FROM work_orders wo
            LEFT JOIN clean_teams ct ON wo.assigned_cleaner = ct.team_name
            WHERE wo.id = :order_id
        """, params={'order_id': order_id}, ttl=0).iloc[0]

        # 如果是转账或混合支付，且保洁组没有ABN，需要计算GST
        if order_info['payment_method'] in ('transfer', 'both') and not order_info['has_abn']:
            total_amount = round(order_info['order_amount'] * 1.1, 2)
        else:
            total_amount = order_info['order_amount']

        # 更新工单
        with conn.session as session:
            session.execute(
                text("""
                    UPDATE work_orders 
                    SET total_amount = :total_amount
                    WHERE id = :order_id
                """),
                {
                    'order_id': order_id,
                    'total_amount': total_amount
                }
            )
            session.commit()

        return True, None

    except Exception as e:
        logger.error(f"更新工单总金额失败：{e}")
        return False, str(e)


def extract_income_values(payment_method: str, order_amount: float) -> tuple[float, float]:
    """
    从支付方式和订单金额中提取现金和转账收入
    """
    if payment_method == 'cash':
        return order_amount, 0
    elif payment_method == 'transfer':
        return 0, order_amount
    elif payment_method == 'both':
        # 这里需要从数据库中获取原始的income1和income2
        # 暂时简单处理，假设对半分（实际应该从数据库获取原始值）
        return order_amount / 2, order_amount / 2
    else:
        return 0, 0


def get_income_values(order_id: int, conn) -> tuple[float, float]:
    """
    从数据库获取工单的收入信息
    """
    try:
        result = conn.query("""
            SELECT payment_method, order_amount
            FROM work_orders 
            WHERE id = :order_id
        """, params={'order_id': order_id}, ttl=0)

        if result.empty:
            return 0, 0

        payment_method = result.iloc[0]['payment_method']
        order_amount = float(result.iloc[0]['order_amount'] or 0)

        if payment_method == 'cash':
            return order_amount, 0
        elif payment_method == 'transfer':
            return 0, order_amount
        elif payment_method == 'both':
            # 由于both类型的收入已经合并，这里需要获取原始的income1和income2
            income_result = conn.query("""
                SELECT income1, income2
                FROM work_orders 
                WHERE id = :order_id
            """, params={'order_id': order_id}, ttl=0)

            if not income_result.empty:
                income1 = float(income_result.iloc[0].get('income1', 0) or 0)
                income2 = float(income_result.iloc[0].get('income2', 0) or 0)
                return income1, income2

            # 如果无法获取具体值，假设平分
            return order_amount / 2, order_amount / 2

        return 0, 0

    except Exception as e:
        logger.error(f"获取收入信息失败：{e}")
        return 0, 0


def get_payment_info(order_id: int, conn) -> tuple[float, float, str]:
    """
    从数据库获取工单的支付信息
    """
    try:
        result = conn.query("""
            SELECT payment_method, order_amount
            FROM work_orders 
            WHERE id = :order_id
        """, params={'order_id': order_id}, ttl=0)

        if result.empty:
            return 0, 0, 'blank'

        payment_method = result.iloc[0]['payment_method']
        order_amount = float(result.iloc[0]['order_amount'] or 0)

        if payment_method == 'cash':
            return order_amount, 0, payment_method
        elif payment_method == 'transfer':
            return 0, order_amount, payment_method
        elif payment_method == 'both':
            # 如果是both类型，假设现金和转账各占一半
            # 实际应用中可能需要更复杂的逻辑
            half_amount = order_amount / 2
            return half_amount, half_amount, payment_method

        return 0, 0, 'blank'

    except Exception as e:
        logger.error(f"获取支付信息失败：{e}")
        return 0, 0, 'blank'


def get_payment_info(order_id: int, conn) -> tuple[float, float, str]:
    """
    从数据库获取工单的支付信息
    """
    try:
        result = conn.query("""
            SELECT payment_method, order_amount
            FROM work_orders 
            WHERE id = :order_id
        """, params={'order_id': order_id}, ttl=0)

        if result.empty:
            return 0, 0, 'blank'

        payment_method = result.iloc[0]['payment_method']
        order_amount = float(result.iloc[0]['order_amount'] or 0)

        if payment_method == 'cash':
            return order_amount, 0, payment_method
        elif payment_method == 'transfer':
            return 0, order_amount, payment_method
        elif payment_method == 'both':
            # 如果是both类型，假设现金和转账各占一半
            # 实际应用中可能需要更复杂的逻辑
            half_amount = order_amount / 2
            return half_amount, half_amount, payment_method

        return 0, 0, 'blank'

    except Exception as e:
        logger.error(f"获取支付信息失败：{e}")
        return 0, 0, 'blank'


def update_order_amounts_for_cleaner_change(order_id: int, new_cleaner: str) -> tuple[bool, str]:
    """
    当保洁组变更时重新计算订单金额

    Args:
        order_id: 工单ID
        new_cleaner: 新的保洁组名称（空值时会设为"暂未派单"）
    """
    try:
        conn = connect_db()

        # 处理空值情况
        if not new_cleaner or new_cleaner.strip() == '':
            new_cleaner = "暂未派单"

        # 获取原始支付数据
        cash_amount, transfer_amount, current_payment_method = get_payment_info(order_id, conn)

        # 获取保洁组的ABN状态
        has_abn = False
        if new_cleaner != "暂未派单":
            result = conn.query(
                "SELECT has_abn FROM clean_teams WHERE team_name = :team_name",
                params={'team_name': new_cleaner},
                ttl=0
            )
            if not result.empty:
                has_abn = bool(result.iloc[0]['has_abn'])

        # 计算新的金额
        if cash_amount == 0 and transfer_amount == 0:
            order_amount = 0
            total_amount = 0
            payment_method = 'blank'
        elif cash_amount > 0 and transfer_amount == 0:
            order_amount = cash_amount
            total_amount = cash_amount
            payment_method = 'cash'
        elif cash_amount == 0 and transfer_amount > 0:
            order_amount = transfer_amount
            if has_abn:
                total_amount = transfer_amount  # 有ABN时不加GST
            else:
                total_amount = round(transfer_amount * 1.1, 2)  # 无ABN时加10% GST
            payment_method = 'transfer'
        else:  # cash_amount > 0 and transfer_amount > 0
            order_amount = cash_amount + transfer_amount
            if has_abn:
                total_amount = order_amount  # 有ABN时不加GST
            else:
                total_amount = cash_amount + round(transfer_amount * 1.1, 2)  # 只对转账部分加GST
            payment_method = 'both'

        # 更新工单
        with conn.session as session:
            session.execute(
                text("""
                    UPDATE work_orders 
                    SET assigned_cleaner = :assigned_cleaner,
                        order_amount = :order_amount,
                        total_amount = :total_amount,
                        payment_method = :payment_method,
                        updated_at = NOW()
                    WHERE id = :order_id
                """),
                {
                    'order_id': order_id,
                    'assigned_cleaner': new_cleaner,
                    'order_amount': order_amount,
                    'total_amount': total_amount,
                    'payment_method': payment_method
                }
            )
            session.commit()

        return True, None

    except Exception as e:
        logger.error(f"更新工单金额失败：{e}")
        return False, str(e)