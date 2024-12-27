"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：staff_acc.py.py
@Author   ：King Songtao
@Time     ：2024/12/27 下午3:26
@Contact  ：king.songtao@gmail.com
"""
from utils.db_operations import get_all_staff_acc
from utils.utils import check_login_state, confirm_logout, formate_acc_info, navigation
import streamlit as st


def staff_acc():
    st.title("📊员工管理")
    st.divider()
    login_state, role = check_login_state()

    if login_state is True and role == "admin":

        navigation()

        # 员工管理逻辑代码
        # 列出所有员工账户信息
        st.info("以下为所有员工账户信息！", icon="ℹ️")
        staff_acc_data, error_message = get_all_staff_acc()
        if error_message is None:
            st.dataframe(staff_acc_data, use_container_width=True, on_select="ignore", selection_mode="single-row", hide_index=True)
        else:
            st.error(error_message, icon="⚠️")

        # 修改员工信息
        with st.expander("✏️修改员工信息", expanded=False):
            # st.warning("暂未开放修改员工信息功能！请联系系统管理员！", icon="⚠️")
            acc_data = staff_acc_data.to_dict()
            acc_edit = st.selectbox("选择要修改的员工账户:", options=formate_acc_info(acc_data), index=0)

        # 添加新账户
        with st.expander("➕添加新账户", expanded=False):
            st.warning("暂未开放添加新账户功能！请联系系统管理员！", icon="⚠️")

        # 添加新账户
        with st.expander("❌删除员工账户", expanded=False):
            st.warning("暂未开放添加新账户功能！请联系系统管理员！", icon="⚠️")
    else:
        st.error("您没有权限访问该页面！5秒后跳转至登录页...", icon="⚠️")
        st.session_state["login_state"] = False
        st.switch_page("pages/login_page.py")


if __name__ == "__main__":
    staff_acc()
