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
from utils.db_operations_v2 import get_all_staff_acc, update_account, login_auth
from utils.utils import logger
from utils.styles import apply_global_styles

def modify_acc():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')

    apply_global_styles()

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
            st.info("请填写要修改的信息！", icon="ℹ️")

            # 用户名（不可修改，只显示）
            st.text_input("登录账号", value=user_info['登录账号'], disabled=True)

            col1, col2 = st.columns(2)

            with col1:
                # 姓名
                new_name = st.text_input("用户名", value=user_info['用户名'])
            with col2:
            # 角色选择
                new_role = st.selectbox("账户权限",
                                        options=["staff", "admin"],
                                        index=0 if user_info['角色权限'] == "staff" else 1)

            # 添加是否修改密码的复选框
            change_password = st.checkbox("修改密码", value=False)

            # 密码修改部分，只在选中修改密码时显示
            passwords_match = True
            using_super_password = False
            final_new_password = None

            if change_password:
                password_tab, super_password_tab = st.tabs(["使用当前密码修改", "使用超级密码修改"])

                with password_tab:
                    # 当前密码验证
                    current_password = st.text_input("当前密码", type="password",
                                                     placeholder="请输入被修改账户的当前密码")

                    col1, col2 = st.columns(2)
                    with col1:
                        new_password = st.text_input("新密码", type="password",
                                                     placeholder="请输入新密码", key="normal_new_pass")
                    with col2:
                        confirm_password = st.text_input("确认新密码", type="password",
                                                         placeholder="请再次输入新密码", key="normal_confirm_pass")

                with super_password_tab:
                    # 超级密码验证
                    super_password = st.text_input("超级密码", type="password",
                                                   placeholder="请输入超级密码")

                    col1, col2 = st.columns(2)
                    with col1:
                        super_new_password = st.text_input("新密码", type="password",
                                                           placeholder="请输入新密码", key="super_new_pass")
                    with col2:
                        super_confirm_password = st.text_input("确认新密码", type="password",
                                                               placeholder="请再次输入新密码", key="super_confirm_pass")

                # 密码验证逻辑
                if new_password or confirm_password:
                    if new_password != confirm_password:
                        st.warning("两次输入的密码不一致！", icon="⚠️")
                        passwords_match = False
                    elif not current_password:
                        st.warning("请输入当前密码！", icon="⚠️")
                        passwords_match = False
                    else:
                        final_new_password = new_password

                if super_new_password or super_confirm_password:
                    if super_new_password != super_confirm_password:
                        st.warning("两次输入的密码不一致！", icon="⚠️")
                        passwords_match = False
                    elif super_password != "Dst881009...":
                        st.warning("超级密码错误！", icon="⚠️")
                        passwords_match = False
                    else:
                        final_new_password = super_new_password
                        using_super_password = True

            st.info("请确保所有信息填写正确，否则无法修改账户！", icon="ℹ️")

            confirm_data = st.checkbox("我确认所有信息填写正确。修改操作不可逆。", value=False)
            # 提交按钮
            # 提交按钮
            submit_change = st.button("保存修改", use_container_width=True, type="primary")
            if submit_change and confirm_data:
                success = False
                error_message = None

                if not new_name:
                    st.error("姓名不能为空！", icon="⚠️")
                elif change_password and not passwords_match:  # 只在选择修改密码时检查密码匹配
                    st.error("密码验证失败！", icon="⚠️")
                elif change_password and final_new_password:  # 如果要修改密码
                    if not using_super_password:  # 使用普通方式修改
                        if not current_password:  # 没有输入当前密码
                            st.error("请输入当前密码！", icon="⚠️")
                            return
                        # 添加日志
                        logger.info(f"验证密码 - 用户: {selected_user}, 输入的当前密码: {current_password}")

                        # 验证当前密码
                        login_state, _, error_message, _ = login_auth(selected_user, current_password)

                        # 添加验证结果日志
                        logger.info(f"密码验证结果 - 状态: {login_state}, 错误: {error_message}")

                        if not login_state:
                            st.error("当前密码错误！", icon="⚠️")
                            return

                    # 执行更新
                    success, error_message = update_account(
                        username=selected_user,
                        new_name=new_name,
                        new_password=final_new_password,
                        new_role=new_role
                    )
                else:  # 如果只修改其他信息，不修改密码
                    success, error_message = update_account(
                        username=selected_user,
                        new_name=new_name,
                        new_password=None,
                        new_role=new_role
                    )

                if success:
                    st.session_state.need_refresh = True

                    # 如果修改了密码，强制用户重新登录
                    if final_new_password:
                        st.session_state.clear()  # 清除所有会话状态
                        st.success("密码修改成功！请使用新密码重新登录...", icon="✅")
                        time.sleep(3)
                        st.switch_page("pages/login_page.py")
                    else:
                        st.success("账户修改成功！3秒后返回员工管理页面...", icon="✅")
                        time.sleep(3)
                        st.switch_page("pages/staff_acc.py")
                else:
                    if error_message:
                        st.error(f"账户修改失败：{error_message}", icon="⚠️")
                    else:
                        st.error("账户修改失败！", icon="⚠️")

            elif submit_change and not confirm_data:
                st.error("请勾选确认信息后进行提交！", icon="⚠️")

        if st.button("取消", use_container_width=True, type="secondary"):
            st.switch_page("pages/staff_acc.py")


if __name__ == '__main__':
    modify_acc()
