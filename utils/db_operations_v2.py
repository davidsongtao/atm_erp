"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：db_operations_v2.py
@Author   ：King Songtao
@Time     ：2025/2/15 上午11:42
@Contact  ：king.songtao@gmail.com
"""
import pandas as pd
import streamlit as st
from datetime import datetime
from sqlalchemy import text
from configs.settings import *
from utils.amount_calculator import calculate_total_amount
from utils.utils import remove_active_session


def connect_db():
    """连接数据库"""
    try:
        conn = st.connection('mysql', type='sql')
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败，错误信息：{e}")
        return None


def create_work_order(
        order_date, created_by, source, work_address,
        income1=0, income2=0,
        work_date=None, work_time=None,
        assigned_cleaner="暂未派单",
        subsidy=None, remarks=None
):
    """创建新工单"""
    try:
        conn = connect_db()

        # 使用工具函数计算金额
        order_amount, total_amount = calculate_total_amount(
            income1, income2, assigned_cleaner, conn
        )

        with conn.session as session:
            session.execute(
                text("""
                INSERT INTO work_orders (
                    order_date, work_date, work_time, created_by, source,
                    work_address, assigned_cleaner, order_amount, total_amount, 
                    subsidy, remarks, income1, income2
                )
                VALUES (
                    :order_date, :work_date, :work_time, :created_by, :source,
                    :work_address, :assigned_cleaner, :order_amount, :total_amount,
                    :subsidy, :remarks, :income1, :income2
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
                    'order_amount': order_amount,
                    'total_amount': total_amount,
                    'subsidy': subsidy,
                    'remarks': remarks,
                    'income1': income1,
                    'income2': income2
                }
            )
            session.commit()

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
            SELECT 
                id, order_date, work_date, work_time, created_by,
                source, work_address, assigned_cleaner, 
                income1, income2, order_amount, total_amount,
                subsidy, remarks
            FROM work_orders 
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
            SELECT 
                id, order_date, work_date, work_time, created_by,
                source, work_address, assigned_cleaner, 
                income1, income2, order_amount, total_amount,
                subsidy, remarks
            FROM work_orders 
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


def update_work_order(data):
    """更新工单信息"""
    if 'assigned_cleaner' in data and not data['assigned_cleaner']:
        data['assigned_cleaner'] = '暂未派单'

    try:
        conn = connect_db()

        # 构建 UPDATE 语句
        update_fields = []
        params = {'order_id': data['id']}

        # 防止更新total_amount
        if 'total_amount' in data:
            del data['total_amount']

        # 如果更新了income1、income2或assigned_cleaner，需要重新计算金额
        if 'income1' in data or 'income2' in data or 'assigned_cleaner' in data:
            # 获取当前的值
            current = conn.query(
                """
                SELECT income1, income2, assigned_cleaner 
                FROM work_orders 
                WHERE id = :id
                """,
                params={'id': data['id']},
                ttl=0
            ).iloc[0]

            income1 = float(data.get('income1', current['income1']) or 0)
            income2 = float(data.get('income2', current['income2']) or 0)
            assigned_cleaner = data.get('assigned_cleaner', current['assigned_cleaner'])

            # 计算新的金额
            order_amount, total_amount = calculate_total_amount(
                income1, income2, assigned_cleaner, conn
            )

            data['order_amount'] = order_amount
            data['total_amount'] = total_amount

        for key, value in data.items():
            if key != 'id':  # 排除id字段
                if key in ['work_date', 'work_time']:
                    if value == '' or value is None:
                        update_fields.append(f"{key} = NULL")
                        continue
                update_fields.append(f"{key} = :{key}")
                params[key] = value

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


def delete_work_order(order_id: int) -> tuple[bool, str]:
    """删除工单

    Args:
        order_id: 工单ID
    Returns:
        tuple[bool, str]: (成功状态, 错误信息)
    """
    try:
        conn = connect_db()
        with conn.session as session:
            session.execute(
                text("DELETE FROM work_orders WHERE id = :order_id"),
                params={'order_id': order_id}
            )
            session.commit()
            return True, None
    except Exception as e:
        error_msg = f"删除工单失败：{e}"
        logger.error(error_msg)
        return False, error_msg


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


def get_active_clean_teams():
    """获取所有活跃的保洁组信息

    Returns:
        tuple: (清洁组列表, 错误信息)
    """
    try:
        conn = connect_db()
        if not conn:
            return None, "数据库连接失败"

        result = conn.query("""
            SELECT 
                id,
                team_name,
                contact_number,
                has_abn,
                notes
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


def get_team_monthly_orders(team_id, year, month):
    """获取指定保洁组的月度工单统计

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
                wo.income1,
                wo.income2,
                wo.order_amount,
                wo.total_amount,
                wo.subsidy
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


def update_clean_team(team_id: int, team_name: str, contact_number: str, has_abn: bool, is_active: bool = True, notes: str = None) -> tuple[bool, str]:
    try:
        conn = connect_db()

        # 检查是否存在相同名称的其他保洁组
        check_result = conn.query(
            """
            SELECT id, team_name, has_abn FROM clean_teams 
            WHERE id = :team_id
            """,
            params={'team_id': team_id},
            ttl=0
        )

        if check_result.empty:
            return False, "保洁组不存在"

        old_team_name = check_result.iloc[0]['team_name']
        old_has_abn = bool(check_result.iloc[0]['has_abn'])

        # 如果ABN状态发生改变，需要更新相关工单的总金额
        if has_abn != old_has_abn:
            # 获取该保洁组的所有工单
            orders = conn.query(
                """
                SELECT id, income1, income2 
                FROM work_orders 
                WHERE assigned_cleaner = :team_name
                """,
                params={'team_name': old_team_name},
                ttl=0
            )

            # 更新保洁组信息
            with conn.session as s1:
                s1.execute(
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
                        'has_abn': 1 if has_abn else 0,
                        'is_active': 1 if is_active else 0,
                        'notes': notes,
                        'team_id': team_id
                    }
                )
                s1.commit()

            # 更新所有相关工单的总金额
            if not orders.empty:
                with conn.session as s2:
                    for _, order in orders.iterrows():
                        # 计算新的金额
                        order_amount, total_amount = calculate_total_amount(
                            float(order['income1']),
                            float(order['income2']),
                            team_name,
                            conn
                        )

                        # 更新工单金额
                        s2.execute(
                            text("""
                            UPDATE work_orders 
                            SET order_amount = :order_amount,
                                total_amount = :total_amount,
                                assigned_cleaner = :new_team_name
                            WHERE id = :order_id
                            """),
                            params={
                                'order_amount': order_amount,
                                'total_amount': total_amount,
                                'new_team_name': team_name,
                                'order_id': order['id']
                            }
                        )
                    s2.commit()

                # 记录日志
                logger.info(f"已更新 {len(orders)} 个工单的金额")
        else:
            # 如果ABN状态没有改变，只更新保洁组信息
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
                        'has_abn': 1 if has_abn else 0,
                        'is_active': 1 if is_active else 0,
                        'notes': notes,
                        'team_id': team_id
                    }
                )

                # 如果team_name发生改变，更新工单表中的保洁组名称
                if team_name != old_team_name:
                    session.execute(
                        text("""
                        UPDATE work_orders 
                        SET assigned_cleaner = :new_team_name
                        WHERE assigned_cleaner = :old_team_name
                        """),
                        params={
                            'new_team_name': team_name,
                            'old_team_name': old_team_name
                        }
                    )
                session.commit()

        return True, ""

    except Exception as e:
        logger.error(f"更新保洁组信息失败：{e}")
        return False, str(e)
