"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：login_page.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午9:57
@Contact  ：king.songtao@gmail.com
"""
import time

import streamlit as st
from utils.utils import set_login_state, check_login_state, log_out
from utils.db_operations import login_auth


def login_page():

    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    login_state, role = check_login_state()
    if login_state:
        st.success("您已登录，无需重新登录！", icon="👋")
        if role == "admin":
            if st.button("跳转至管理员控制台", key="admin_button", use_container_width=True):
                st.switch_page("pages/admin_page.py")
        elif role == "customer_service":
            if st.button("跳转至客服控制台", key="customer_service_button", use_container_width=True, type="primary"):
                st.switch_page("pages/customer_service_page.py")
            if st.button("退出登录", key="logout_button", use_container_width=True):
                log_out()

    else:
        st.title("👋ATM-Cleaning 办公管理系统")
        st.divider()
        username = st.text_input("电子邮箱", key="username", placeholder="请输入用户名:your_name@email.com")
        password = st.text_input("登录密码", key="password", type="password")

        col1, col2 = st.columns(2)
        with col1:
            login_button = st.button("登录", key="login_button", use_container_width=True, type="primary")
        with col2:
            register_button = st.button("注册", key="register_button", use_container_width=True)

        if login_button:
            if not username:
                st.error("请输入您的用户名！", icon="⚠️")
            elif not password:
                st.error("请输入您的密码！", icon="⚠️")
            else:
                login_state, role, error_message, name = login_auth(username, password)
                if "current_user" not in st.session_state:
                    st.session_state["current_user"] = name
                if login_state and role == "admin":
                    set_login_state(True, role, name)
                    st.switch_page("pages/admin_page.py")
                if login_state and role == "customer_service":
                    set_login_state(True, role, name)
                    st.switch_page("pages/customer_service_page.py")
                elif error_message == "用户名不存在":
                    st.error("用户名不存在！", icon="⚠️")
                elif error_message == "密码错误":
                    st.error("密码错误！", icon="⚠️")
                else:
                    st.error("未知错误！", icon="⚠️")
        if register_button:
            st.warning("暂未开放注册功能！请联系系统管理员获取您的账户信息！", icon="⚠️")


if __name__ == '__main__':
    login_page()
