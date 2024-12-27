"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：staff_acc.py.py
@Author   ：King Songtao
@Time     ：2024/12/27 下午3:26
@Contact  ：king.songtao@gmail.com
"""
from utils.db_operations import get_all_staff_acc
from utils.utils import check_login_state, log_out, formate_acc_info
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
            st.dataframe(staff_acc_data, use_container_width=True, on_select="ignore", selection_mode="single-row", hide_index=True)
        else:
            st.error(error_message, icon="⚠️")

        # 修改员工信息
        with st.expander("修改员工信息", expanded=False):
            # st.warning("暂未开放修改员工信息功能！请联系系统管理员！", icon="⚠️")
            acc_data = staff_acc_data.to_dict()
            acc_edit = st.selectbox("选择要修改的员工账户:", options=formate_acc_info(acc_data), index=0)

        # 添加新账户
        with st.expander("添加新账户", expanded=False):
            st.warning("暂未开放添加新账户功能！请联系系统管理员！", icon="⚠️")

        if st.button("返回控制台", use_container_width=True, type="primary"):
            st.switch_page("pages/admin_page.py")
        # 退出登录模块
        st.session_state["logout_button_disabled"] = False
        logout_check = st.checkbox("我希望退出登录！")
        if logout_check:
            if st.button("🛏️退出登录", key="logout_button", use_container_width=True, disabled=st.session_state["logout_button_disabled"]):
                log_out()
        else:
            st.session_state["logout_button_disabled"] = True
            st.button("🛏️退出登录", key="logout_button", use_container_width=True, disabled=st.session_state["logout_button_disabled"])
    else:
        st.error("您没有权限访问该页面！5秒后跳转至登录页...", icon="⚠️")
        st.session_state["login_state"] = False
        st.switch_page("pages/login_page.py")


if __name__ == "__main__":
    staff_acc()
