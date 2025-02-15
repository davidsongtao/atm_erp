"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：orders_statistics.py
@Author   ：King Songtao
@Time     ：2025/2/15 上午11:44
@Contact  ：king.songtao@gmail.com
"""
import time
import streamlit as st
import pandas as pd
from utils.db_operations_v2 import get_work_orders, get_work_orders_by_date_range
from utils.utils import navigation, check_login_state
from utils.styles import apply_global_styles


def show_filters(df=None):
    """显示筛选条件"""
    col1, col2, col3 = st.columns(3)

    with col1:
        options = ["year", "quarter", "month", "week", "day"]
        default_index = options.index('month')
        time_range = st.selectbox(
            "时间范围",
            options=options,
            format_func=lambda x: {
                "day": "今日",
                "week": "本周",
                "month": "本月",
                "quarter": "本季度",
                "year": "今年"
            }[x],
            key='time_range',
            index=default_index
        )

    with col2:
        cleaner_options = []
        if df is not None and not df.empty:
            cleaner_options = sorted([
                cleaner for cleaner in df['assigned_cleaner'].unique()
                if cleaner != '暂未派单' and pd.notna(cleaner)
            ])

        cleaner_filter = st.multiselect(
            "保洁小组",
            options=cleaner_options,
            key='cleaner_filter',
            placeholder="请选择..."
        )

    with col3:
        creator_options = []
        if df is not None and not df.empty:
            creator_options = sorted(df['created_by'].unique().tolist())

        creator_filter = st.multiselect(
            "创建人",
            options=creator_options,
            key='creator_filter',
            placeholder="请选择..."
        )

    # 清空筛选按钮
    def clear_filters():
        st.session_state.time_range = 'month'
        if 'cleaner_filter' in st.session_state:
            del st.session_state['cleaner_filter']
        if 'creator_filter' in st.session_state:
            del st.session_state['creator_filter']
        return True

    if st.button("清空筛选条件", type="primary", on_click=clear_filters):
        st.rerun()

    return time_range


def show_statistics(filtered_df):
    """显示统计信息"""
    # 计算统计信息 - 使用原始的filtered_df进行计算
    total_income1 = pd.to_numeric(filtered_df['income1'], errors='coerce').fillna(0).sum()
    total_income2 = pd.to_numeric(filtered_df['income2'], errors='coerce').fillna(0).sum()
    total_subsidy = pd.to_numeric(filtered_df['subsidy'], errors='coerce').fillna(0).sum()
    total_order_amount = pd.to_numeric(filtered_df['order_amount'], errors='coerce').fillna(0).sum()
    total_amount = pd.to_numeric(filtered_df['total_amount'], errors='coerce').fillna(0).sum()

    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "现金收入总额",
            f"${total_income1:.2f}",
            help="所有工单的现金收入总和"
        )

    with col2:
        st.metric(
            "转账收入总额",
            f"${total_income2:.2f}",
            help="所有工单的转账收入总和（不含GST）"
        )

    with col3:
        st.metric(
            "补贴总额",
            f"${total_subsidy:.2f}",
            help="所有工单的补贴总和"
        )

    with col4:
        st.metric(
            "订单总额",
            f"${total_order_amount:.2f}",
            help="所有工单的订单金额总和（不含GST）"
        )

    with col5:
        st.metric(
            "总金额(含GST)",
            f"${total_amount:.2f}",
            help="所有工单的总金额（含GST）"
        )


def show_work_orders_table(df):
    """显示工单详情表格"""
    filtered_df = df.copy()

    # 将所有的 NaN 和 None 值替换为空字符串
    filtered_df = filtered_df.fillna('')

    # 处理日期排序：保持work_date为日期类型，将空值替换为NaT
    filtered_df['work_date'] = pd.to_datetime(filtered_df['work_date'], errors='coerce')

    # 按日期升序排序，将NaT值排在最后
    filtered_df = filtered_df.sort_values(
        by='work_date',
        ascending=True,
        na_position='last'
    )

    # 应用过滤器
    cleaner_filter = st.session_state.get('cleaner_filter', [])
    if cleaner_filter:
        filtered_df = filtered_df[filtered_df['assigned_cleaner'].isin(cleaner_filter)]

    creator_filter = st.session_state.get('creator_filter', [])
    if creator_filter:
        filtered_df = filtered_df[filtered_df['created_by'].isin(creator_filter)]

    display_df = filtered_df.copy()

    # 特殊处理 work_date 列
    display_df['work_date'] = display_df['work_date'].apply(
        lambda x: pd.NaT if x == '' or pd.isna(x) else x
    )

    # 处理金额列的空值显示
    for col in ['subsidy', 'income1', 'income2', 'order_amount', 'total_amount']:
        # 先确保列中的值是数值类型
        display_df[col] = pd.to_numeric(display_df[col], errors='coerce')
        # 然后格式化为货币显示
        display_df[col] = display_df[col].apply(
            lambda x: "" if pd.isna(x) or x == 0 else f"${x:.2f}"
        )

    # 选择要显示的列并重新排序
    columns_to_display = [
        'work_date',  # 保洁日期
        'work_time',  # 保洁时间
        'work_address',  # 工作地址
        'assigned_cleaner',  # 保洁小组
        'income1',  # 现金收入
        'income2',  # 转账收入
        'total_amount',  # 总金额
        'subsidy',  # 补贴
        'created_by',  # 创建人
        'source',  # 来源
        'remarks',  # 备注
    ]

    display_df = display_df[columns_to_display].copy()

    # 重命名列
    column_labels = {
        'work_date': '日期',
        'work_time': '时间',
        'work_address': '地址',
        'assigned_cleaner': '保洁组',
        'income1': '现金收入',
        'income2': '转账收入',
        'total_amount': '总金额',
        'subsidy': '补贴',
        'created_by': '创建人',
        'source': '来源',
        'remarks': '备注'
    }
    display_df = display_df.rename(columns=column_labels)

    # 显示表格
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    return filtered_df  # 返回过滤后的数据用于统计


def work_order_statistics():
    """工单统计主页面"""
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("📊 工单统计")
        st.divider()

        # 获取初始数据
        default_time_range = st.session_state.get('time_range', 'month')
        orders_df, error = get_work_orders(default_time_range)

        if error:
            st.error(f"获取数据失败：{error}")
            return

        if orders_df is not None and not orders_df.empty:
            # 先显示统计信息
            show_statistics(orders_df)
            st.divider()

        # 操作按钮
        col1, col3 = st.columns([1, 1])
        with col1:
            if st.button("新建工单", use_container_width=True, type="primary"):
                st.switch_page("pages/new_work_order_v2.py")
        # with col2:
        #     if st.button("工单管理", use_container_width=True, type="primary"):
        #         st.switch_page("pages/work_orders_v2.py")
        with col3:
            if st.button("月度结算", use_container_width=True, type="primary"):
                st.switch_page("pages/monthly_review.py")

        # 显示筛选条件
        selected_time_range = show_filters(orders_df)

        # 只有当时间范围发生变化时才重新获取数据
        if selected_time_range != default_time_range:
            new_orders_df, error = get_work_orders(selected_time_range)
            if error:
                st.error(f"获取数据失败：{error}")
                return
            orders_df = new_orders_df

        # 检查是否有数据需要显示
        if orders_df is not None and not orders_df.empty:
            filtered_df = show_work_orders_table(orders_df)
        else:
            st.info("暂无工单数据")

    else:
        error = st.error("您还没有登录！3秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您还没有登录！2秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您还没有登录！1秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        st.switch_page("pages/login_page.py")


if __name__ == "__main__":
    work_order_statistics()
