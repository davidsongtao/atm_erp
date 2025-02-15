"""
Description: 修改保洁组信息页面

-*- Encoding: UTF-8 -*-
@File     ：modify_clean_team.py
@Author   ：King Songtao
@Time     ：2025/2/15 下午5:23
"""
import time
import pandas as pd
import streamlit as st
from utils.utils import navigation, check_login_state
from utils.db_operations_v2 import get_all_clean_teams, update_clean_team, connect_db
from utils.styles import apply_global_styles


def modify_clean_team():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()

    login_state, role = check_login_state()

    if login_state is True and role == "admin":
        navigation()
        st.title("✏️修改保洁组信息")
        st.divider()

        # 获取所有保洁组数据
        clean_teams_data, error_message = get_all_clean_teams()

        if error_message:
            st.error(error_message, icon="⚠️")
            return

        if clean_teams_data.empty:
            st.warning("暂无保洁组数据", icon="⚠️")
            if st.button("返回", use_container_width=True, type="secondary"):
                st.switch_page("pages/staff_acc.py")
            return

        # 过滤掉"暂未派单"选项
        valid_teams = clean_teams_data[clean_teams_data['保洁组名称'] != '暂未派单']

        st.info("请选择要修改的保洁组！", icon="ℹ️")
        # 选择要修改的保洁组
        selected_team = st.selectbox(
            "选择要修改的保洁组",
            options=["请选择保洁组..."] + valid_teams['保洁组名称'].tolist()
        )

        # 只有当选择了实际的保洁组时才显示修改表单
        if selected_team and selected_team != "请选择保洁组...":
            # 获取选中保洁组的当前信息
            team_info = valid_teams[valid_teams['保洁组名称'] == selected_team].iloc[0]

            st.divider()
            st.info("请填写要修改的信息！", icon="ℹ️")

            # 修改信息表单
            team_name = st.text_input("保洁组名称", value=team_info['保洁组名称'])
            contact_number = st.text_input("联系电话（选填）", value=team_info['联系电话'])

            # 当前ABN状态
            current_abn = bool(team_info['has_abn'])

            # 初始化新的ABN状态
            new_abn = st.checkbox("是否注册ABN", value=current_abn)

            # 如果新的ABN状态与当前状态不同，显示警告
            if new_abn != current_abn:
                status_change = "注册" if new_abn else "注销"
                st.warning(f"""
                您正在修改 **{team_name}** 的 ABN注册状态！

                请注意：修改 ABN 注册状态将导致该保洁组相关工单的总金额发生变化。
                - 已注册 ABN：工单转账收入金额将不计算 10% GST
                - 未注册 ABN：工单转账收入金额将计算 10% GST
                """, icon="⚠️")

            is_active = st.checkbox("是否在职", value=True if team_info['是否在职'] == '在职' else False)

            notes = st.text_area("备注", value=team_info['备注'] if pd.notna(team_info['备注']) else "")

            st.divider()
            st.info("请确保所有信息填写正确！", icon="ℹ️")

            # 确认复选框
            confirm_data = st.checkbox("我确认所有信息填写正确。", value=False)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("保存修改", use_container_width=True, type="primary"):
                    if not confirm_data:
                        st.error("请勾选确认信息！", icon="⚠️")
                    elif not team_name:
                        st.error("保洁组名称不能为空！", icon="⚠️")
                    else:
                        # 调用update_clean_team函数更新保洁组信息
                        # 首先获取team_id
                        team_id = valid_teams[valid_teams['保洁组名称'] == selected_team].iloc[0]['id']

                        # 调用更新函数
                        success, error_msg = update_clean_team(
                            team_id=team_id,
                            team_name=team_name,
                            contact_number=contact_number,
                            has_abn=new_abn,
                            is_active=is_active,
                            notes=notes
                        )

                        if success:
                            st.success("保存成功！3秒后页面将会刷新！", icon="✅")
                            time.sleep(3)
                            st.switch_page("pages/staff_acc.py")
                        else:
                            st.error(f"保存失败：{error_msg}", icon="⚠️")
            with col2:
                if st.button("取消", use_container_width=True, type="secondary"):
                    st.switch_page("pages/staff_acc.py")

        else:
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
        st.switch_page("app.py")


if __name__ == "__main__":
    modify_clean_team()