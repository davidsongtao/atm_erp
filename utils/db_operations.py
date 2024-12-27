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
        query_result = conn.query("SELECT password, role, name FROM users WHERE username = :username", params={'username': username}).to_dict()
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
        error_message = "用户名不存在"
        return False, None, error_message, None
