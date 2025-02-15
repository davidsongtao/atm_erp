"""
Description: 月度结算页面

-*- Encoding: UTF-8 -*-
@File     ：monthly_review.py
@Author   ：King Songtao
@Time     ：2025/2/6 下午4:15
@Contact  ：king.songtao@gmail.com
"""
import time
import pandas as pd
import streamlit as st
from datetime import datetime

from pages.work_orders import get_theme_color
from utils.styles import apply_global_styles
from utils.utils import check_login_state, navigation
from utils.db_operations_v2 import get_active_clean_teams, get_team_monthly_orders


def process_orders_data(orders_df):
    """处理工单数据,添加收入列"""
    if orders_df.empty:
        return orders_df

    # 重命名列
    columns_mapping = {
        'work_date': '工作日期',
        'work_time': '工作时间',
        'work_address': '工作地址'
    }

    df = orders_df.rename(columns=columns_mapping)

    # 处理收入列
    def calculate_incomes(row):
        income1 = float(row.get('income1', 0) or 0)  # 现金收入
        income2 = float(row.get('income2', 0) or 0)  # 转账收入
        subsidy = float(row.get('subsidy', 0) or 0)  # 补贴

        return pd.Series({
            '现金收入': f"${income1:.2f}" if income1 > 0 else '',
            '转账收入': f"${income2:.2f}" if income2 > 0 else '',
            '补贴': f"${subsidy:.2f}" if subsidy > 0 else ''
        })

    # 添加收入和补贴列
    income_df = orders_df.apply(calculate_incomes, axis=1)
    df = pd.concat([df, income_df], axis=1)

    # 处理时间格式
    df['工作日期'] = pd.to_datetime(df['工作日期']).dt.strftime('%Y-%m-%d')

    # 选择要显示的列
    display_columns = [
        '工作日期', '工作时间', '工作地址',
        '现金收入', '转账收入', '补贴'
    ]

    return df[display_columns]


def show_team_monthly_stats(team, selected_year, selected_month):
    """显示单个保洁组的月度统计信息"""
    # 获取工单数据
    orders, error = get_team_monthly_orders(
        team['id'], selected_year, selected_month
    )

    if error:
        st.error(f"获取工单统计失败：{error}", icon="⚠️")
        return

    if orders.empty:
        st.info(f"{selected_year}年{selected_month}月暂无工单记录")
        return

    # 确保添加 'subsidy' 列，如果不存在
    if 'subsidy' not in orders.columns:
        orders['subsidy'] = 0

    # 处理数据用于显示
    display_df = process_orders_data(orders)

    # 显示工单明细
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    # 计算统计信息
    income1 = pd.to_numeric(orders['income1'], errors='coerce').fillna(0).sum()  # 现金收入
    income2 = pd.to_numeric(orders['income2'], errors='coerce').fillna(0).sum()  # 转账收入
    total_amount = pd.to_numeric(orders['total_amount'], errors='coerce').fillna(0).sum()  # 总金额(含GST)
    subsidy = pd.to_numeric(orders['subsidy'], errors='coerce').fillna(0).sum()  # 补贴

    # 计算逻辑：
    # 1. 保洁组总佣金 = 现金收入×70% + 转账收入×70% + 补贴
    team_total_income = income1 * 0.7 + income2 * 0.7 + subsidy

    # 2. 保洁组待缴 = 现金收入×30% - 补贴（如果为负数则为0）
    team_payment = max(0, income1 * 0.3 - subsidy)

    # 3. ATM待付保洁组 =
    #    如果保洁组待缴为0: 转账收入×70% + abs(现金收入×30% - 补贴)
    #    否则: 转账收入×70%
    if team_payment == 0:
        atm_pending = income2 * 0.7 + abs(income1 * 0.3 - subsidy)
    else:
        atm_pending = income2 * 0.7

    # 显示统计信息
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("现金收入合计", f"${income1:.2f}", help="统计月所有工单现金收入总额")
    with col2:
        st.metric("转账收入合计", f"${income2:.2f}", help="统计月所有工单转账收入总额(不含GST)")
    with col3:
        st.metric("补贴总额", f"${subsidy:.2f}", help="统计月所有补贴总额")

    col4, col5, col6 = st.columns(3)
    with col4:
        st.metric("保洁组总佣金", f"${team_total_income:.2f}",
                  help="计算公式：现金收入×70% + 转账收入×70% + 补贴")
    with col5:
        st.metric("保洁组待缴", f"${team_payment:.2f}",
                  help="计算公式：现金收入×30% - 补贴（如果为负数则为0）")
    with col6:
        st.metric("ATM待付保洁组", f"${atm_pending:.2f}",
                  help="计算公式：\n如果保洁组待缴为0:\n  转账收入×70% + abs(现金收入×30% - 补贴)\n否则:\n  转账收入×70%")

    # 创建包含统计信息的CSV字符串
    csv_data = display_df.to_csv(index=False)
    csv_data += f"\n\n统计信息\n"
    csv_data += f"现金收入,${income1:.2f}\n"
    csv_data += f"转账收入,${income2:.2f}\n"
    csv_data += f"补贴总额,${subsidy:.2f}\n"
    csv_data += f"总金额(含GST),${total_amount:.2f}\n"
    csv_data += f"保洁组总佣金,${team_total_income:.2f}\n"
    csv_data += f"保洁组待缴,${team_payment:.2f}\n"
    csv_data += f"ATM待付保洁组,${atm_pending:.2f}\n"

    # 添加月度报表下载按钮
    st.download_button(
        label="📥 下载月度报表",
        data=csv_data.encode('utf-8'),
        file_name=f"{team['team_name']}_{selected_year}_{selected_month}_月度报表.csv",
        mime='text/csv',
        type="primary",
        help="点击下载月度报表，将显示在浏览器的下载列表中。",
        use_container_width=True
    )


def monthly_review():
    """月度结算主页面"""
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

        st.title("📊 月度结算")
        st.divider()

        # 年月选择
        col1, col2 = st.columns(2)
        with col1:
            selected_year = st.selectbox(
                "选择年份",
                options=range(2024, datetime.now().year + 1),
                index=datetime.now().year - 2024
            )
        with col2:
            selected_month = st.selectbox(
                "选择月份",
                options=range(1, 13),
                index=datetime.now().month - 1
            )

        # 获取所有在职保洁组
        active_teams, error = get_active_clean_teams()

        if error:
            st.error(f"获取保洁组失败：{error}", icon="⚠️")
            return

        if not active_teams:
            st.warning("当前没有在职的保洁组", icon="⚠️")
            return

        # 过滤掉"暂未派单"的保洁组
        active_teams = [team for team in active_teams if team['team_name'] != '暂未派单']

        if not active_teams:
            st.warning("当前没有可显示的保洁组", icon="⚠️")
            return

        # 创建标签页
        tabs = st.tabs([f"{team['team_name']}" for team in active_teams])

        # 在每个标签页中显示对应保洁组的统计信息
        for tab, team in zip(tabs, active_teams):
            with tab:
                show_team_monthly_stats(team, selected_year, selected_month)

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
    monthly_review()
