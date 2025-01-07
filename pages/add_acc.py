"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：add_acc.py.py
@Author   ：King Songtao
@Time     ：2025/1/6 上午11:39
@Contact  ：king.songtao@gmail.com
"""
import time
import streamlit as st
from utils.utils import navigation, check_login_state
from utils.db_operations import create_new_account


def add_acc():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')

    login_state, role = check_login_state()

    # 检查登录状态
    if login_state is True and role == "admin":
        navigation()
        st.title("➕新建账户")
        st.divider()

        # 基本信息输入
        username = st.text_input("用户名", placeholder="请输入用户名")

        # 密码输入
        col1, col2 = st.columns(2)
        with col1:
            if "password" not in st.session_state:
                st.session_state.password = ""
            password = st.text_input("密码", placeholder="请输入密码", type="password", key="password")

        with col2:
            if "confirm_password" not in st.session_state:
                st.session_state.confirm_password = ""
            confirm_password = st.text_input("确认密码", placeholder="请再次输入密码", type="password", key="confirm_password")

        # 即时密码验证
        passwords_match = True
        if confirm_password:
            if password != confirm_password:
                st.error("两次输入的密码不一致！请检查", icon="⚠️")
                passwords_match = False

        name = st.text_input("姓名", placeholder="请输入姓名")

        # 角色选择
        role = st.selectbox("角色", options=["admin", "customer_service"], index=None, placeholder="请选择角色")

        st.info("请确保所有信息填写正确，否则无法创建账户！", icon="ℹ️")
        # 提交按钮
        if st.button("创建账户", use_container_width=True, type="primary"):
            if not username or not password or not name:
                st.error("请填写所有必填项！", icon="⚠️")
            elif not passwords_match:
                st.error("两次输入的密码不一致！", icon="⚠️")
            else:
                # 调用创建账户的数据库操作
                success, error_message = create_new_account(username, password, name, role)
                if success:
                    st.session_state.need_refresh = True
                    success = st.success("账户创建成功！3秒后返回员工管理页面...", icon="✅")
                    time.sleep(1)
                    success.empty()
                    success = st.success("账户创建成功！2秒后返回员工管理页面...", icon="✅")
                    time.sleep(1)
                    success.empty()
                    st.success("账户创建成功！1秒后返回员工管理页面...", icon="✅")
                    time.sleep(1)
                    st.switch_page("pages/staff_acc.py")
                else:
                    st.error(f"账户创建失败：{error_message}", icon="⚠️")

        if st.button("取消", use_container_width=True, type="secondary"):
            st.switch_page("pages/staff_acc.py")

    else:
        error = st.error("您还没有登录！3秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您还没有登录！2秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您还没有登录！1秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)

        st.session_state["login_state"] = False
        st.switch_page("pages/login_page.py")


if __name__ == '__main__':
    add_acc()
