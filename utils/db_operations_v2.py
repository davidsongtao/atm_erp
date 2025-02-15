"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：db_operations_v2.py
@Author   ：King Songtao
@Time     ：2025/2/15 上午11:42
@Contact  ：king.songtao@gmail.com
"""
import streamlit as st
from datetime import datetime
from sqlalchemy import text
from configs.settings import *


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
    """创建新工单

    Args:
        order_date: 登记日期
        created_by: 创建人
        source: 来源
        work_address: 工作地址
        income1: 现金收入
        income2: 转账收入
        work_date: 工作日期(可选)
        work_time: 工作时间(可选)
        assigned_cleaner: 保洁组(默认暂未派单)
        subsidy: 补贴金额(可选)
        remarks: 备注(可选)
    """
    try:
        # 计算订单金额和总金额
        order_amount = income1 + income2
        total_amount = income1 + (income2 * 1.1)  # 转账收入加10% GST

        conn = connect_db()
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

        # 防止更新total_amount
        if 'total_amount' in data:
            del data['total_amount']

        # 如果更新了income1或income2,需要重新计算order_amount和total_amount
        if 'income1' in data or 'income2' in data:
            # 获取当前的income值
            current = conn.query(
                "SELECT income1, income2 FROM work_orders WHERE id = :id",
                params={'id': data['id']},
                ttl=0
            ).iloc[0]

            income1 = float(data.get('income1', current['income1']) or 0)
            income2 = float(data.get('income2', current['income2']) or 0)

            # 计算新的金额
            data['order_amount'] = income1 + income2
            data['total_amount'] = income1 + (income2 * 1.1)

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
