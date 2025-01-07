"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：staff_acc.py.py
@Author   ：King Songtao
@Time     ：2024/12/27 下午3:26
@Contact  ：king.songtao@gmail.com
"""
import time

from utils.db_operations import get_all_staff_acc
from utils.utils import check_login_state, confirm_logout, formate_acc_info, navigation
import streamlit as st


def staff_acc():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    st.title("📊员工管理")
    st.divider()
    login_state, role = check_login_state()
    staff_acc_data, error_message = get_all_staff_acc()

    if login_state is True and role == "admin":
        navigation()
        # 列出所有员工账户信息
        if error_message is None:
            st.dataframe(staff_acc_data, use_container_width=True, on_select="ignore", selection_mode="single-row", hide_index=True)
        else:
            st.error(error_message, icon="⚠️")

        st.info("请选择您要进行的操作！", icon="ℹ️")

        # 创建新账户
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            create_acc = st.button("➕新建账户", use_container_width=True)
            if create_acc:
                st.switch_page("pages/add_acc.py")
        with col2:
            modify_acc = st.button("✏️修改账户信息", use_container_width=True)
            if modify_acc:
                st.switch_page("pages/modify_acc.py")
        with col3:
            delete_acc = st.button("❌删除账户", use_container_width=True)
            if delete_acc:
                st.switch_page("pages/delete_acc.py")
    else:
        error = st.error("您没有权限访问该页面！3秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您没有权限访问该页面！2秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您没有权限访问该页面！1秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)
        st.session_state["login_state"] = False
        st.switch_page("pages/login_page.py")


if __name__ == "__main__":
    staff_acc()
