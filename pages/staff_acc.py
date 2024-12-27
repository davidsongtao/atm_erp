"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：staff_acc.py.py
@Author   ：King Songtao
@Time     ：2024/12/27 下午3:26
@Contact  ：king.songtao@gmail.com
"""
from utils.db_operations import get_all_staff_acc
from utils.utils import check_login_state
import streamlit as st


def staff_acc():
    st.title("📊员工管理")
    st.divider()
    login_state, role = check_login_state()

    if login_state is True and role == "admin":
        # 员工管理逻辑代码
        # 列出所有员工账户信息
        st.info("以下为所有员工账户信息！", icon="ℹ️")
        staff_acc_data, error_message = get_all_staff_acc()
        if error_message is None:
            st.dataframe(staff_acc_data)
        else:
            st.error(error_message, icon="⚠️")
    else:
        st.error("您没有权限访问该页面！5秒后跳转至登录页...", icon="⚠️")
        st.session_state["login_state"] = False
        st.switch_page("pages/login_page.py")


if __name__ == "__main__":
    staff_acc()
