"""
Description: 员工和保洁组管理页面

-*- Encoding: UTF-8 -*-
@File     ：staff_acc.py
@Author   ：King Songtao
@Time     ：2024/12/27 下午3:26
@Contact  ：king.songtao@gmail.com
"""
import time
import pandas as pd
import streamlit as st
from datetime import datetime
from utils.db_operations_v2 import get_all_staff_acc, delete_clean_team, get_all_clean_teams, create_clean_team, update_clean_team, get_active_clean_teams, get_team_monthly_orders
from utils.utils import check_login_state, navigation, get_theme_color
from utils.styles import apply_global_styles


@st.dialog("删除保洁组")
def show_clean_team_deletion_dialog():
    """删除保洁组的对话框"""
    st.markdown("""
        <style>
            .stDialog > div {
                border: none;
                border-radius: 0;
                padding: 2rem;
            }

            .stDialog > div > div {
                padding: 0;
            }
        </style>
    """, unsafe_allow_html=True)

    clean_teams_data, error_message = get_all_clean_teams()
    if error_message:
        st.error(error_message, icon="⚠️")
        return

    if clean_teams_data.empty:
        st.warning("暂无保洁组数据", icon="⚠️")
        return

    team_options = ["请选择保洁组"] + clean_teams_data['保洁组名称'].tolist()

    selected_team = st.selectbox(
        "选择要删除的保洁组",
        options=team_options,
        key="team_selector_delete"
    )

    if selected_team and selected_team != "请选择保洁组":
        selected_team_data = clean_teams_data[clean_teams_data['保洁组名称'] == selected_team].iloc[0]

        # 显示确认信息
        st.warning(
            f"确定要删除保洁组 **{selected_team}** 吗？此操作不可恢复！",
            icon="⚠️"
        )

        # # 显示保洁组当前信息
        # st.info("保洁组信息", icon="ℹ️")
        # st.write(f"保洁组名称: {selected_team_data['保洁组名称']}")
        # st.write(f"联系电话: {selected_team_data['联系电话']}")
        # st.write(f"在职状态: {selected_team_data['是否在职']}")
        # if pd.notna(selected_team_data['备注']):
        #     st.write(f"备注: {selected_team_data['备注']}")

        with st.form("delete_clean_team_form", border=False):
            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button(
                    "确认删除",
                    use_container_width=True,
                    type="primary"
                )
            with col2:
                if st.form_submit_button("取消", use_container_width=True):
                    st.rerun()

            if submitted:
                success, error = delete_clean_team(selected_team_data['id'])

                if success:
                    st.success("保洁组删除成功！", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"保洁组删除失败：{error}", icon="⚠️")


@st.dialog("更新保洁组信息")
def show_clean_team_update_dialog():
    """更新保洁组信息的对话框"""
    st.markdown("""
        <style>
            .stDialog > div {
                border: none;
                border-radius: 0;
                padding: 2rem;
            }

            .stDialog > div > div {
                padding: 0;
            }
        </style>
    """, unsafe_allow_html=True)

    clean_teams_data, error_message = get_all_clean_teams()
    if error_message:
        st.error(error_message, icon="⚠️")
        return

    if clean_teams_data.empty:
        st.warning("暂无保洁组数据", icon="⚠️")
        return

    team_options = ["请选择保洁组"] + clean_teams_data['保洁组名称'].tolist()

    selected_team = st.selectbox(
        "选择要更新的保洁组",
        options=team_options,
        key="team_selector"
    )

    if selected_team and selected_team != "请选择保洁组":
        selected_team_data = clean_teams_data[clean_teams_data['保洁组名称'] == selected_team].iloc[0]

        with st.form("update_clean_team_form", border=False):
            team_name = st.text_input("保洁组名称", value=selected_team_data['保洁组名称'])
            contact_number = st.text_input("联系电话（选填）", value=selected_team_data['联系电话'])
            has_abn = st.checkbox("是否注册ABN", value=bool(selected_team_data.get('has_abn', False)))
            is_active = st.checkbox("是否在职", value=True if selected_team_data['是否在职'] == '在职' else False)
            notes = st.text_area("备注", value=selected_team_data['备注'] if pd.notna(selected_team_data['备注']) else "")

            col1, col2 = st.columns(2)
            with col1:
                submitted = st.form_submit_button(
                    "确认更新",
                    use_container_width=True,
                    type="primary"
                )
            with col2:
                if st.form_submit_button("取消", use_container_width=True):
                    st.rerun()

            if submitted:
                if not team_name:
                    st.error("请填写保洁组名称！", icon="⚠️")
                    return

                success, error = update_clean_team(
                    selected_team_data['id'],
                    team_name,
                    contact_number or "",  # 如果为空则传入空字符串
                    has_abn,
                    is_active,
                    notes
                )

                if success:
                    st.success("保洁组信息更新成功！", icon="✅")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"保洁组信息更新失败：{error}", icon="⚠️")


@st.dialog("创建新保洁组")
def show_clean_team_creation_dialog():
    """创建保洁组的对话框"""
    st.markdown("""
        <style>
            .stDialog > div {
                border: none;
                border-radius: 0;
                padding: 2rem;
            }

            .stDialog > div > div {
                padding: 0;
            }
        </style>
    """, unsafe_allow_html=True)

    with st.form("create_clean_team_form", border=False):
        team_name = st.text_input("保洁组名称", placeholder="请输入保洁组名称")
        contact_number = st.text_input("联系电话（选填）", placeholder="请输入联系电话")
        has_abn = st.checkbox("是否注册ABN", value=False)
        notes = st.text_area("备注", placeholder="请输入备注信息（选填）")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("确认创建", use_container_width=True, type="primary")
        with col2:
            if st.form_submit_button("取消", use_container_width=True):
                st.rerun()

        if submitted:
            if not team_name:
                st.error("请填写保洁组名称！", icon="⚠️")
                return

            success, error = create_clean_team(
                team_name=team_name,
                contact_number=contact_number or "",  # 如果为空则传入空字符串
                has_abn=has_abn,
                notes=notes
            )

            if success:
                st.success("保洁组创建成功！", icon="✅")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"保洁组创建失败：{error}", icon="⚠️")


def select_clean_team():
    """选择要更新的保洁组"""
    clean_teams_data, error_message = get_all_clean_teams()
    if error_message:
        st.error(error_message, icon="⚠️")
        return None

    if clean_teams_data.empty:
        st.warning("暂无保洁组数据", icon="⚠️")
        return None

    # 提取保洁组名称列表
    team_options = clean_teams_data['保洁组名称'].tolist()

    selected_team = st.selectbox(
        "选择要更新的保洁组",
        options=team_options,
        key="team_selector"
    )

    if selected_team:
        # 获取对应的完整数据行
        selected_team_data = clean_teams_data[clean_teams_data['保洁组名称'] == selected_team]
        return selected_team_data
    return None


def show_clean_team_update(team_data):
    """显示更新保洁组信息的表单"""
    with st.form("update_clean_team_form"):
        st.subheader("更新保洁组信息")

        # 获取选中行的数据
        selected_team = team_data.iloc[0]

        team_name = st.text_input("保洁组名称", value=selected_team['保洁组名称'])
        contact_number = st.text_input("联系电话", value=selected_team['联系电话'])
        is_active = st.checkbox("是否在职", value=bool(selected_team['是否在职']))
        notes = st.text_area("备注", value=selected_team['备注'] if pd.notna(selected_team['备注']) else "")

        submitted = st.form_submit_button("确认更新", use_container_width=True, type="primary")

        if submitted:
            if not all([team_name, contact_number]):
                st.error("请填写所有必填信息！", icon="⚠️")
                return

            success, error = update_clean_team(
                selected_team['id'], team_name, contact_number, is_active, notes
            )

            if success:
                st.success("保洁组信息更新成功！", icon="✅")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"保洁组信息更新失败：{error}", icon="⚠️")


def show_monthly_settlement():
    """显示月度结算页面"""
    st.subheader("月度结算")

    # 获取当前年月
    current_date = datetime.now()

    # 年月选择
    col1, col2 = st.columns(2)
    with col1:
        selected_year = st.selectbox(
            "选择年份",
            options=range(2024, current_date.year + 1),
            index=current_date.year - 2024
        )
    with col2:
        selected_month = st.selectbox(
            "选择月份",
            options=range(1, 13),
            index=current_date.month - 1
        )

    # 获取所有在职保洁组
    active_teams, error = get_active_clean_teams()

    if error:
        st.error(f"获取保洁组失败：{error}", icon="⚠️")
        return

    if not active_teams:
        st.warning("当前没有在职的保洁组", icon="⚠️")
        return

    # 为每个保洁组显示月度工单统计
    for team in active_teams:
        with st.expander(f"🧹 {team['team_name']} - {team['leader_name']}"):
            orders, error = get_team_monthly_orders(
                team['id'], selected_year, selected_month
            )

            if error:
                st.error(f"获取工单统计失败：{error}", icon="⚠️")
                continue

            if orders.empty:
                st.info(f"{selected_year}年{selected_month}月暂无工单记录")
                continue

            # 显示工单明细
            st.dataframe(
                orders,
                use_container_width=True,
                hide_index=True
            )

            # 计算并显示统计信息
            total_orders = len(orders)
            total_amount = orders['total_amount'].sum()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("工单总数", f"{total_orders} 单")
            with col2:
                st.metric("总金额", f"${total_amount:.2f}")


def show_clean_teams_table(clean_teams_data):
    """显示保洁组列表，包含ABN状态"""
    # 需要显示的列
    display_columns = [
        '保洁组名称', '联系电话', '是否在职', '是否注册ABN', '备注'
    ]

    # 准备显示数据
    display_df = clean_teams_data.copy()

    # 添加ABN状态列
    display_df['是否注册ABN'] = display_df['has_abn'].apply(
        lambda x: '已注册' if x == 1 else '未注册'
    )

    # 筛选需要显示的列
    filtered_data = display_df[display_columns]

    # 显示处理后的数据
    st.dataframe(
        filtered_data,
        use_container_width=True,
        hide_index=True
    )


def staff_acc():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()

    # 动态设置 tab 样式
    theme_color = get_theme_color()
    st.markdown(f"""
            <style>
                .stTabs [data-baseweb="tab-list"] {{
                    gap: 2px;
                }}
                .stTabs [data-baseweb="tab"] {{
                    height: 50px;
                    background-color: #F0F2F6;
                    border-radius: 0px 0px 0px 0px;
                    padding-left: 15px;
                    padding-right: 15px;
                }}
                .stTabs [aria-selected="true"] {{
                    background-color: {theme_color} !important;
                    color: #FFFFFF !important;
                }}
            </style>""", unsafe_allow_html=True)

    login_state, role = check_login_state()

    if login_state is True and role == "admin":
        navigation()

        st.title("📊 人员管理")
        st.divider()

        # 创建三个标签页：员工管理、保洁组管理和月度结算
        tab1, tab2 = st.tabs(["👥 客服组管理", "🧹 保洁组管理"])

        with tab1:
            staff_acc_data, error_message = get_all_staff_acc()

            # 列出所有员工账户信息
            if error_message is None:
                st.dataframe(
                    staff_acc_data,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.error(error_message, icon="⚠️")

            st.info("请选择您要进行的操作！", icon="ℹ️")

            # 员工管理操作按钮
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("➕新建客服组", use_container_width=True, type="primary"):
                    st.switch_page("pages/add_acc.py")
            with col2:
                if st.button("✏️修改客服组", use_container_width=True, type="primary"):
                    st.switch_page("pages/modify_acc.py")
            with col3:
                if st.button("❌删除客服组", use_container_width=True, type="primary"):
                    st.switch_page("pages/delete_acc.py")

        # 在tab2中的相关代码需要这样修改：
        with tab2:
            # 获取保洁组数据
            clean_teams_data, error_message = get_all_clean_teams()

            if error_message is None:
                # 使用更新后的显示函数显示保洁组信息
                show_clean_teams_table(clean_teams_data)

                st.info("请选择您要进行的操作！", icon="ℹ️")

                # 保洁组管理操作
                col1, col2, col3 = st.columns(3)

                with col1:
                    if st.button("➕新建保洁组", use_container_width=True, type="primary"):
                        show_clean_team_creation_dialog()

                with col2:
                    if st.button("✏️修改保洁组", use_container_width=True, type="primary"):
                        show_clean_team_update_dialog()

                with col3:
                    if st.button("❌删除保洁组", use_container_width=True, type="primary"):
                        show_clean_team_deletion_dialog()


            else:
                st.error(error_message, icon="⚠️")
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
