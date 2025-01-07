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
        logger.success(f"连接数据库成功！")
        return conn
    except Exception as e:
        logger.error(f"数据库连接失败，错误信息：{e}")
        return None


# 根据用户名查询用户密码
def login_auth(username, password):
    """
    验证用户登录是否合法
    :param username: 用户输入的用户名
    :param password: 用户输入的密码
    :return: 用户登录状态，用户权限
    """
    try:
        conn = connect_db()
        logger.info(f"开始验证用户: {username}")  # 添加日志

        # 如果是仅检查用户存在性（password为None）
        if password is None:
            check_query = conn.query(
                "SELECT COUNT(*) as count FROM users WHERE username = :username",
                params={'username': username}
            ).to_dict()
            exists = check_query['count'][0] > 0
            logger.info(f"检查用户存在性: {exists}")  # 添加日志
            return exists, None, None if exists else "用户名不存在", None

        # 验证用户名和密码
        query_result = conn.query(
            "SELECT password, role, name FROM users WHERE username = :username",
            params={'username': username}
        ).to_dict()

        logger.info(f"查询结果: {query_result}")  # 添加日志

        if not query_result or len(query_result['password']) == 0:
            logger.error(f"用户 {username} 不存在")  # 添加日志
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
            logger.error(f"用户 {username} 登录失败！")

        return logging_status, role, error_message, name

    except Exception as e:
        logger.error(f"数据库验证失败，错误信息：{e}")
        error_message = "数据库验证失败"  # 修改错误信息，使其更具体
        return False, None, error_message, None


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
    """
    更新用户账户信息
    :param username: 要修改的用户名
    :param new_name: 新姓名
    :param new_password: 新密码（可选）
    :param new_role: 新角色（可选）
    :return: 更新状态，错误信息
    """
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
