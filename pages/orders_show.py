"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：orders_show.py.py
@Author   ：King Songtao
@Time     ：2025/2/5 下午2:29
@Contact  ：king.songtao@gmail.com
"""
import time
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.db_operations import get_work_orders, get_work_orders_by_date_range
from utils.utils import navigation, check_login_state
from utils.styles import apply_global_styles


def work_order_statistics():
    # 设置页面配置
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png', layout="wide")
    apply_global_styles()

    # 检查登录状态
    login_state, role = check_login_state()

    if login_state:
        # 显示导航栏
        navigation()

        st.title("📊 工单统计")
        st.divider()

        # 时间范围选择，默认选择"year"（本年）
        col1, col2 = st.columns(2)
        with col1:
            time_range = st.selectbox(
                "选择时间范围",
                options=["year", "quarter", "month", "week", "day"],
                format_func=lambda x: {
                    "day": "今日",
                    "week": "本周",
                    "month": "本月",
                    "quarter": "本季度",
                    "year": "本年"
                }[x],
                index=0  # 设置默认选项为第一个（即"year"）
            )

        # 获取工单数据
        orders_df, error = get_work_orders(time_range)

        if error:
            st.error(f"获取数据失败：{error}")
            return

        if orders_df is not None and not orders_df.empty:
            # 显示统计指标
            show_statistics(orders_df)

            # 显示工单详情
            show_work_orders_table(orders_df)
        else:
            st.info("暂无工单数据")
    else:
        # 未登录状态处理
        error = st.error("您还没有登录！3秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您还没有登录！2秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您还没有登录！1秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        st.switch_page("pages/login_page.py")


def show_statistics(df):
    """显示统计指标"""
    st.subheader("统计指标")

    # 统计数据计算
    total_orders = len(df)
    total_amount = df['total_amount'].sum()
    unassigned_orders = len(df[df['assigned_cleaner'] == '暂未派单'])
    unpaid_orders = len(df[df['payment_received'] == False])

    # 发票相关统计
    invoice_needed = len(df[df['paperwork'] == '0'])  # 需要发票的订单
    invoice_pending = len(df[(df['paperwork'] == '0') & (df['invoice_sent'] == False)])  # 待开发票

    # 收据相关统计
    receipt_needed = len(df[df['paperwork'] == '1'])  # 需要收据的订单
    receipt_pending = len(df[(df['paperwork'] == '1') & (df['receipt_sent'] == False)])  # 待开收据

    # 第一行指标
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "总工单数",
            f"{total_orders}",
            border=True
        )

    with col2:
        st.metric(
            "总工单金额",
            f"${total_amount:,.2f}",
            border=True
        )

    with col3:
        st.metric(
            "待派单工单数",
            f"{unassigned_orders}",
            border=True
        )

    # 第二行指标
    col4, col5, col6 = st.columns(3)

    with col4:
        st.metric(
            "待收款工单数",
            f"{unpaid_orders}",
            border=True
        )

    with col5:
        st.metric(
            "待开发票工单数",
            f"{invoice_pending}",
            border=True
        )

    with col6:
        st.metric(
            "待开收据工单数",
            f"{receipt_pending}",
            border=True
        )


def show_work_orders_table(df):
    """显示工单详情表格"""
    st.subheader("工单详情")

    # 添加筛选器 - 使用两行布局
    col1, col2, col3 = st.columns(3)

    # 第一行筛选条件
    with col1:
        payment_filter = st.multiselect(
            "支付方式筛选",
            options=df['payment_method'].unique(),
            default=[]
        )

    with col2:
        cleaner_filter = st.multiselect(
            "保洁员筛选",
            options=df['assigned_cleaner'].unique(),
            default=[]
        )

    with col3:
        creator_filter = st.multiselect(
            "创建人筛选",
            options=df['created_by'].unique(),
            default=[]
        )

    # 第二行筛选条件
    col4, col5, col6 = st.columns(3)

    with col4:
        payment_status_filter = st.selectbox(
            "收款状态",
            options=["全部", "已收款", "未收款"],
            index=0
        )

    with col5:
        invoice_status_filter = st.selectbox(
            "开票状态",
            options=["全部", "已开票", "未开票"],
            index=0
        )

    with col6:
        receipt_status_filter = st.selectbox(
            "收据状态",
            options=["全部", "已开收据", "未开收据"],
            index=0
        )

    # 应用筛选
    filtered_df = df.copy()

    # 应用支付方式筛选
    if payment_filter:
        filtered_df = filtered_df[filtered_df['payment_method'].isin(payment_filter)]

    # 应用保洁员筛选
    if cleaner_filter:
        filtered_df = filtered_df[filtered_df['assigned_cleaner'].isin(cleaner_filter)]

    # 应用创建人筛选
    if creator_filter:
        filtered_df = filtered_df[filtered_df['created_by'].isin(creator_filter)]

    # 应用收款状态筛选
    if payment_status_filter != "全部":
        is_paid = payment_status_filter == "已收款"
        filtered_df = filtered_df[filtered_df['payment_received'] == is_paid]

    # 应用开票状态筛选
    if invoice_status_filter != "全部":
        is_invoice_sent = invoice_status_filter == "已开票"
        filtered_df = filtered_df[filtered_df['invoice_sent'] == is_invoice_sent]

    # 应用收据状态筛选
    if receipt_status_filter != "全部":
        is_receipt_sent = receipt_status_filter == "已开收据"
        filtered_df = filtered_df[filtered_df['receipt_sent'] == is_receipt_sent]

    # 格式化日期时间列
    for col in ['order_date', 'work_date']:
        if col in filtered_df.columns:
            filtered_df[col] = pd.to_datetime(filtered_df[col]).dt.strftime('%Y-%m-%d')

    # 显示数据表格
    st.dataframe(
        filtered_df,
        column_config={
            "order_date": "创建日期",
            "work_date": "工作日期",
            "work_time": "工作时间",
            "created_by": "创建人",
            "source": "来源",
            "work_address": "工作地址",
            "payment_method": "支付方式",
            "order_amount": "订单金额",
            "total_amount": "总金额",
            "assigned_cleaner": "保洁员",
            "payment_received": "已收款",
            "invoice_sent": "已开票",
            "receipt_sent": "已开收据"
        },
        hide_index=True
    )


if __name__ == "__main__":
    work_order_statistics()
