"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：login_page.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午9:57
@Contact  ：king.songtao@gmail.com
"""
import time

import time

import streamlit as st
from utils.utils import set_login_state, check_login_state, log_out, add_active_session
from utils.db_operations import login_auth


def login_page():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')

    # 添加CSS样式
    st.markdown(
        """
        <style>
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: #f0f2f6;
            padding: 10px 0;
            text-align: center;
            font-size: 14px;
            color: #666;
        }
        .footer a {
            color: #666;
            text-decoration: none;
        }
        .footer a:hover {
            color: #333;
            text-decoration: underline;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 清除可能存在的过期session
    if "logged_in_username" in st.session_state and st.session_state.login_state:
        # 重新验证用户是否存在
        username = st.session_state.get("logged_in_username")
        if username:
            check_state, _, error_message, _ = login_auth(username, None)
            if not check_state or error_message == "用户名不存在":
                # 如果用户不存在，清除登录状态
                st.session_state.clear()
                st.rerun()

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
        username = st.text_input("电子邮箱", key="username_input", placeholder="请输入用户名:your_name@email.com")
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
                if login_state:
                    # 存储完整的用户信息
                    st.session_state.logged_in_username = username
                    add_active_session(username)  # 添加活跃会话
                    set_login_state(True, role, name)

                    if role == "admin":
                        st.switch_page("pages/admin_page.py")
                    elif role == "customer_service":
                        st.switch_page("pages/customer_service_page.py")
                elif error_message == "用户名不存在":
                    st.error("用户名不存在！", icon="⚠️")
                elif error_message == "密码错误":
                    st.error("密码错误！", icon="⚠️")
                else:
                    st.error("未知错误！", icon="⚠️")

    # 添加ICP备案信息
    st.markdown(
        """
        <div class="footer">
            <span>Copy Right © 2025 ATM Cleaning Management PTY Ltd. 版权所有 | </span>
            <a href="https://beian.miit.gov.cn/" target="_blank">豫ICP备2025107955号</a>
            <span> | </span>
            <a href="https://beian.mps.gov.cn/#/query/webSearch?code=41010602000280" rel="noreferrer" target="_blank">豫公网安备41010602000280号</a>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    login_page()
