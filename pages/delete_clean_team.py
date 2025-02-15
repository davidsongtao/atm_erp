"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：delete_clean_team.py.py
@Author   ：King Songtao
@Time     ：2025/2/15 下午5:23
@Contact  ：king.songtao@gmail.com
"""
import time
import pandas as pd
import streamlit as st
from utils.utils import navigation, check_login_state
from utils.db_operations_v2 import get_all_clean_teams, delete_clean_team, connect_db
from utils.styles import apply_global_styles


def delete_clean_team_page():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()

    login_state, role = check_login_state()

    if login_state is True and role == "admin":
        navigation()
        st.title("❌删除保洁组")
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

        # 选择要删除的保洁组
        selected_team = st.selectbox(
            "选择要删除的保洁组",
            options=["请选择保洁组..."] + valid_teams['保洁组名称'].tolist()
        )

        # 只有当选择了实际的保洁组时才显示删除确认
        if selected_team and selected_team != "请选择保洁组...":
            st.divider()

            # 获取保洁组信息
            team_info = valid_teams[valid_teams['保洁组名称'] == selected_team].iloc[0]

            # 检查是否有关联工单
            conn = connect_db()
            related_orders = conn.query(
                """
                SELECT COUNT(*) as count 
                FROM work_orders 
                WHERE assigned_cleaner = :team_name
                """,
                params={'team_name': selected_team},
                ttl=0
            ).iloc[0]['count']

            # 显示保洁组信息
            st.info("保洁组信息", icon="ℹ️")
            st.write(f"**保洁组名称**: {team_info['保洁组名称']}")
            st.write(f"**联系电话**: {team_info['联系电话']}")
            st.write(f"**在职状态**: {team_info['是否在职']}")
            st.write(f"**ABN状态**: {'已注册' if team_info.get('has_abn', False) else '未注册'}")
            if pd.notna(team_info['备注']):
                st.write(f"**备注**: {team_info['备注']}")

            if related_orders > 0:
                st.error(
                    f"⚠️ 该保洁组有 {related_orders} 个关联工单，无法删除！\n\n"
                    "请先将工单重新分配给其他保洁组。",
                    icon="⚠️"
                )
            else:
                st.warning(
                    f"您正在删除保洁组：{selected_team}\n\n"
                    f"请输入 'delete{selected_team}' 确认删除操作。\n\n"
                    "**注意：此操作不可撤销！**",
                    icon="⚠️"
                )

                confirm_text = st.text_input(
                    "请输入指定内容以确认删除",
                    placeholder=f"请输入 'delete{selected_team}' 确认删除"
                )

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("删除保洁组", type="primary", use_container_width=True):
                        if confirm_text != f"delete{selected_team}":
                            st.error("确认文本输入错误！", icon="⚠️")
                        else:
                            success, error = delete_clean_team(team_info['id'])
                            if success:
                                st.success("保洁组删除成功！3秒后返回人员管理页面...", icon="✅")
                                time.sleep(3)
                                st.switch_page("pages/staff_acc.py")
                            else:
                                st.error(f"保洁组删除失败：{error}", icon="⚠️")
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
    delete_clean_team_page()
