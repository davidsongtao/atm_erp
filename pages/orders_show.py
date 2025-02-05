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


def get_status_display(value, is_required):
    if not is_required:
        return '⚪'  # 浅灰色圆点表示不需要
    return '🟢' if value else '🔴'  # 绿色表示已完成，红色表示未完成


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

    # 定义支付方式映射
    payment_method_mapping = {
        'cash': '现金支付',
        'transfer': '银行转账'
    }

    # 创建反向映射（用于筛选）
    reverse_payment_mapping = {v: k for k, v in payment_method_mapping.items()}

    # 创建一个清空按钮
    clear_button = st.button("清空筛选条件", type="secondary")

    # 如果点击清空按钮，重置所有筛选条件
    if clear_button:
        st.session_state.payment_filter = []
        st.session_state.cleaner_filter = []
        st.session_state.creator_filter = []
        st.session_state.payment_status_filter = "全部"
        st.session_state.invoice_status_filter = "全部"
        st.session_state.receipt_status_filter = "全部"
        st.rerun()

    # 第一行筛选条件
    col1, col2, col3 = st.columns(3)

    with col1:
        # 将实际值映射为显示值
        display_options = [payment_method_mapping.get(method, method) for method in df['payment_method'].unique()]
        payment_filter = st.multiselect(
            "支付方式筛选",
            options=display_options,
            key='payment_filter'
        )
        # 将显示值转换回实际值用于筛选
        payment_filter_values = [reverse_payment_mapping.get(display, display) for display in payment_filter]

    with col2:
        # 过滤掉"暂未派单"选项并获取保洁员列表
        cleaner_options = [cleaner for cleaner in df['assigned_cleaner'].unique() if cleaner != '暂未派单']
        cleaner_filter = st.multiselect(
            "保洁小组筛选",
            options=cleaner_options,
            key='cleaner_filter'
        )

    with col3:
        creator_filter = st.multiselect(
            "创建人筛选",
            options=df['created_by'].unique(),
            key='creator_filter'
        )

    # 第二行筛选条件
    col4, col5, col6 = st.columns(3)

    with col4:
        payment_status_filter = st.selectbox(
            "收款状态",
            options=["全部", "已收款", "未收款"],
            key='payment_status_filter'
        )

    with col5:
        invoice_status_filter = st.selectbox(
            "开票状态",
            options=["全部", "已开票", "未开票"],
            key='invoice_status_filter'
        )

    with col6:
        receipt_status_filter = st.selectbox(
            "收据状态",
            options=["全部", "已开收据", "未开收据"],
            key='receipt_status_filter'
        )

    # 预处理数据类型
    filtered_df = df.copy()

    # 将paperwork转换为整数类型
    filtered_df['paperwork'] = pd.to_numeric(filtered_df['paperwork'], errors='coerce').fillna(0).astype(int)

    # 处理布尔值列
    bool_columns = ['payment_received', 'invoice_sent', 'receipt_sent']
    for col in bool_columns:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0).astype(bool)

    # 应用支付方式筛选
    if payment_filter_values:
        filtered_df = filtered_df[filtered_df['payment_method'].isin(payment_filter_values)]

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

    # 发票状态筛选逻辑
    if invoice_status_filter != "全部":
        # 只保留需要发票的订单
        filtered_df = filtered_df[filtered_df['paperwork'] == 0]
        if invoice_status_filter == "已开票":
            # 在需要发票的订单中筛选已开票的
            filtered_df = filtered_df[filtered_df['invoice_sent']]
        else:  # 未开票
            # 在需要发票的订单中筛选未开票的
            filtered_df = filtered_df[~filtered_df['invoice_sent']]

    # 收据状态筛选逻辑
    if receipt_status_filter != "全部":
        # 只保留需要收据的订单
        filtered_df = filtered_df[filtered_df['paperwork'] == 1]
        if receipt_status_filter == "已开收据":
            # 在需要收据的订单中筛选已开收据的
            filtered_df = filtered_df[filtered_df['receipt_sent']]
        else:  # 未开收据
            # 在需要收据的订单中筛选未开收据的
            filtered_df = filtered_df[~filtered_df['receipt_sent']]


    # 格式化日期时间列
    for col in ['order_date', 'work_date']:
        if col in filtered_df.columns:
            filtered_df[col] = pd.to_datetime(filtered_df[col]).dt.strftime('%Y-%m-%d')

    display_df = filtered_df.copy()

    # 合并工作日期和时间
    display_df['work_datetime'] = display_df['work_date'] + ' ' + display_df['work_time']

    # 创建服务内容列
    def combine_services(row):
        services = []

        # 检查并添加基础服务
        if pd.notna(row.get('basic_service')):
            services.append(str(row['basic_service']))

        # 检查并添加房间服务
        if pd.notna(row.get('rooms')):
            services.append(str(row['rooms']))

        # 检查并添加电器服务
        if pd.notna(row.get('electricals')):
            services.append(str(row['electricals']))

        # 检查并添加其他服务
        if pd.notna(row.get('other_services')):
            services.append(str(row['other_services']))

        # 检查并添加自定义项目
        if pd.notna(row.get('cuistom_item')):
            services.append(str(row['cuistom_item']))

        return ' ; '.join(filter(None, services))

    # 添加服务内容列
    display_df['service_content'] = display_df.apply(combine_services, axis=1)

    # 转换支付方式显示
    display_df['payment_method'] = display_df['payment_method'].map(payment_method_mapping).fillna(display_df['payment_method'])

    # 获取发票和收据的需求状态
    display_df['needs_invoice'] = display_df['paperwork'] == 0
    display_df['needs_receipt'] = display_df['paperwork'] == 1

    # 处理支付状态显示（支付状态总是需要显示）
    display_df['payment_received'] = display_df['payment_received'].map({
        True: '🟢',
        False: '🔴'
    }).fillna('❓')

    # 处理发票状态显示
    display_df['invoice_sent'] = display_df.apply(
        lambda row: get_status_display(row['invoice_sent'], row['needs_invoice']),
        axis=1
    )

    # 处理收据状态显示
    display_df['receipt_sent'] = display_df.apply(
        lambda row: get_status_display(row['receipt_sent'], row['needs_receipt']),
        axis=1
    )

    # 选择要显示的列并重新排序
    columns_to_display = [
        'work_datetime',
        'work_address',
        'payment_method',
        'order_amount',
        'total_amount',
        'assigned_cleaner',
        'payment_received',
        'invoice_sent',
        'receipt_sent',
        'created_by',
        'source',
        'service_content'
    ]

    display_df = display_df[columns_to_display]

    # 显示数据表格
    st.dataframe(
        display_df,
        column_config={
            "work_datetime": "工作日期时间",
            "work_address": "工作地址",
            "payment_method": "支付方式",
            "order_amount": "订单金额",
            "total_amount": "总金额",
            "assigned_cleaner": "保洁小组",
            "payment_received": "收款情况",
            "invoice_sent": "已开发票",
            "receipt_sent": "已开收据",
            "created_by": "创建人",
            "source": "来源",
            "service_content": "服务内容"
        },
        hide_index=True,
        use_container_width=True
    )


if __name__ == "__main__":
    work_order_statistics()
