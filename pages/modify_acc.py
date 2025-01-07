"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：modify_acc.py.py
@Author   ：King Songtao
@Time     ：2025/1/7 下午4:38
@Contact  ：king.songtao@gmail.com
"""
import time
import streamlit as st
from utils.utils import navigation, check_login_state, formate_acc_info
from utils.db_operations import get_all_staff_acc, update_account


def modify_acc():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    login_state, role = check_login_state()

    # 检查登录状态
    if login_state is True and role == "admin":
        navigation()
        st.title("✏️修改账户信息")
        st.divider()

        # 获取当前用户名
        current_user = st.session_state.get("username")

        # 获取所有用户数据
        staff_acc_data, error_message = get_all_staff_acc()

        if error_message:
            st.error(error_message, icon="⚠️")
            return

        # 过滤掉当前用户，因为不能修改自己的账户
        other_users = staff_acc_data[staff_acc_data['登录账号'] != current_user]

        st.info("请选择要修改的用户！登陆账号无法进行修改！", icon="ℹ️")
        # 选择要修改的用户
        selected_user = st.selectbox(
            "请在下来菜单中选择您要修改的账户",
            options=["请选择要修改的用户..."] + other_users['登录账号'].tolist(),
            format_func=lambda x: x if x == "请选择要修改的用户..." else f"{x} ({other_users[other_users['登录账号'] == x]['用户名'].iloc[0]})"
        )

        # 只有当用户选择了一个实际的账户时才显示修改表单
        if selected_user and selected_user != "请选择要修改的用户...":

            # 获取选中用户的当前信息
            user_info = other_users[other_users['登录账号'] == selected_user].iloc[0]

            # 修改信息表单
            st.info("请填写要修改的信息！若您不希望修改密码，留空即可！", icon="ℹ️")

            # 用户名（不可修改，只显示）
            st.text_input("登录账号", value=user_info['登录账号'], disabled=True)

            # 姓名
            new_name = st.text_input("用户名", value=user_info['用户名'])

            # 密码修改
            col1, col2 = st.columns(2)
            with col1:
                new_password = st.text_input("新密码", type="password",
                                             placeholder="留空表示不修改密码")
            with col2:
                confirm_password = st.text_input("确认新密码", type="password",
                                                 placeholder="留空表示不修改密码")

            # 密码验证
            passwords_match = True
            if new_password or confirm_password:
                if new_password != confirm_password:
                    st.warning("两次输入的密码不一致！", icon="⚠️")
                    passwords_match = False

            # 角色选择
            new_role = st.selectbox("角色",
                                    options=["staff", "admin"],
                                    index=0 if user_info['角色权限'] == "staff" else 1)

            st.info("请确保所有信息填写正确，否则无法修改账户！", icon="ℹ️")

            confirm_data = st.checkbox("我确认所有信息填写正确。修改操作不可逆。", value=False)
            # 提交按钮
            submit_change = st.button("保存修改", use_container_width=True, type="primary")
            if submit_change and confirm_data:
                if not new_name:
                    st.error("姓名不能为空！", icon="⚠️")
                elif not passwords_match:
                    st.error("两次输入的密码不一致！", icon="⚠️")
                else:
                    success, error_message = update_account(
                        username=selected_user,
                        new_name=new_name,
                        new_password=new_password if new_password else None,
                        new_role=new_role
                    )

                    if success:
                        st.session_state.need_refresh = True  # 设置刷新标志
                        st.success("账户修改成功！3秒后返回员工管理页面...", icon="✅")
                        time.sleep(3)
                        st.switch_page("pages/staff_acc.py")
                    else:
                        st.error(f"账户修改失败：{error_message}", icon="⚠️")
            elif submit_change and not confirm_data:
                st.error("请勾选确认信息后进行提交！", icon="⚠️")
            if st.button("取消", use_container_width=True, type="secondary"):
                st.switch_page("pages/staff_acc.py")
    else:
        st.error("您没有权限访问该页面！5秒后跳转至登录页...", icon="⚠️")
        st.session_state["login_state"] = False
        st.switch_page("pages/login_page.py")


if __name__ == '__main__':
    modify_acc()