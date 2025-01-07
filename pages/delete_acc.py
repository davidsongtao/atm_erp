"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：delete_acc.py.py
@Author   ：King Songtao
@Time     ：2025/1/7 下午8:51
@Contact  ：king.songtao@gmail.com
"""
import time
import streamlit as st
from utils.utils import navigation, check_login_state
from utils.db_operations import get_all_staff_acc, delete_account


def delete_acc():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    login_state, role = check_login_state()

    # 检查登录状态
    if login_state is True and role == "admin":
        navigation()
        st.title("❌删除账户")
        st.divider()

        # 获取当前用户名
        current_user = st.session_state.get("logged_in_username")

        # 获取所有用户数据
        staff_acc_data, error_message = get_all_staff_acc()

        if error_message:
            st.error(error_message, icon="⚠️")
            return

        # 过滤掉当前用户，因为不能删除自己的账户
        other_users = staff_acc_data[staff_acc_data['登录账号'] != current_user].copy()  # 使用copy避免视图警告

        if other_users.empty:
            st.warning("没有可以删除的账户！", icon="⚠️")
            if st.button("返回", use_container_width=True, type="secondary"):
                st.switch_page("pages/staff_acc.py")
            return

        # 选择要删除的用户
        selected_user = st.selectbox(
            "选择要删除的用户",
            options=["请选择要删除的用户..."] + other_users['登录账号'].tolist(),
            format_func=lambda x: x if x == "请选择要删除的用户..." else f"{x} ({other_users[other_users['登录账号'] == x]['用户名'].iloc[0]})"
        )

        # 只有当用户选择了一个实际的账户时才显示删除确认
        if selected_user and selected_user != "请选择要删除的用户...":
            st.divider()

            # 再次验证不是当前用户
            if selected_user == current_user:
                st.error("不能删除自己的账户！", icon="⚠️")
                return

            st.warning(
                f"您正在删除账户：{selected_user}\n\n"
                f"请输入 'delete{selected_user}' 确认删除操作。\n\n"
                "**注意：此操作不可撤销！**",
                icon="⚠️"
            )

            confirm_text = st.text_input("请输入指定内容以确认删除", placeholder=f"请输入 'delete{selected_user}' 确认删除")

            if st.button("删除账户", type="primary", use_container_width=True):
                if confirm_text != f"delete{selected_user}":
                    st.error("确认文本输入错误！", icon="⚠️")
                elif selected_user == current_user:  # 最后一次验证
                    st.error("不能删除自己的账户！", icon="⚠️")
                else:
                    success, error_message = delete_account(selected_user)
                    if success:
                        st.session_state.need_refresh = True
                        success = st.success("账户删除成功！3秒后返回员工管理页面...", icon="✅")
                        time.sleep(1)
                        success.empty()
                        success = st.success("账户删除成功！2秒后返回员工管理页面...", icon="✅")
                        time.sleep(1)
                        success.empty()
                        st.success("账户删除成功！1秒后返回员工管理页面...", icon="✅")
                        time.sleep(1)
                        st.switch_page("pages/staff_acc.py")
                    else:
                        st.error(f"账户删除失败：{error_message}", icon="⚠️")

        if st.button("取消", use_container_width=True, type="secondary"):
            st.switch_page("pages/staff_acc.py")
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


if __name__ == '__main__':
    delete_acc()
