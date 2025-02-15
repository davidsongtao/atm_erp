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
from utils.db_operations_v2 import get_work_orders, get_work_orders_by_date_range, update_work_order, get_active_clean_teams
from utils.utils import navigation, check_login_state
from utils.styles import apply_global_styles


# 首先在文件顶部添加对话框函数
@st.dialog("更新成功")
def show_update_dialog():
    st.write("数据已更新成功！请点击刷新按钮，以获取最新的数据。")
    if st.button("刷新表格", type="primary"):
        st.rerun()


@st.dialog("更新失败")
def show_error_dialog(error_msg):
    st.error("数据更新失败！您的数据没有被更新！")
    st.write(f"错误原因：{error_msg}")
    st.write("请修改后重试。")
    if st.button("确定", type="primary"):
        st.rerun()


def show_filters(df=None):
    """显示筛选条件"""
    col1, col2, col3 = st.columns(3)

    with col1:
        options = ["year", "quarter", "month", "week", "day"]
        default_index = options.index('month')

        # 如果没有时间范围状态，设置默认值
        if 'time_range' not in st.session_state:
            st.session_state.time_range = 'month'

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

        # 从 session_state 获取当前的筛选值，如果不存在则为空列表
        current_cleaner_filter = st.session_state.get('cleaner_filter', [])

        cleaner_filter = st.multiselect(
            "保洁小组",
            options=cleaner_options,
            default=current_cleaner_filter,
            key='cleaner_filter',
            placeholder="请选择..."
        )

    with col3:
        creator_options = []
        if df is not None and not df.empty:
            creator_options = sorted(df['created_by'].unique().tolist())

        # 从 session_state 获取当前的筛选值，如果不存在则为空列表
        current_creator_filter = st.session_state.get('creator_filter', [])

        creator_filter = st.multiselect(
            "创建人",
            options=creator_options,
            default=current_creator_filter,
            key='creator_filter',
            placeholder="请选择..."
        )

    # 清空筛选按钮
    def clear_filters():
        # 清除筛选器的状态
        if 'cleaner_filter' in st.session_state:
            del st.session_state['cleaner_filter']
        if 'creator_filter' in st.session_state:
            del st.session_state['creator_filter']

    if st.button("清空筛选条件", type="primary"):
        clear_filters()
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

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "收入1总额",
            f"${total_income1:.2f}",
            help="所有工单的收入1总和"
        )

    with col2:
        st.metric(
            "收入2总额",
            f"${total_income2:.2f}",
            help="所有工单的收入2总和（不含GST）"
        )

    with col3:
        st.metric(
            "补贴总额",
            f"${total_subsidy:.2f}",
            help="所有工单的补贴总和（如果有）"
        )


def show_work_orders_table(df, cleaner_options):
    """显示工单详情表格
    Args:
        df: 工单数据DataFrame
        cleaner_options: 保洁组选项列表
    """
    filtered_df = df.copy()

    # 将所有的 NaN 和 None 值替换为空字符串
    filtered_df = filtered_df.fillna('')

    # 处理日期排序：保持work_date为日期类型，将空值替换为NaT
    filtered_df['work_date'] = pd.to_datetime(filtered_df['work_date'], errors='coerce').dt.date

    # 按日期升序排序，将NaT值排在最后
    filtered_df = filtered_df.sort_values(
        by='work_date',
        ascending=True,
        na_position='last'
    )

    # 获取保洁组选项
    cleaner_options = sorted([
        cleaner for cleaner in filtered_df['assigned_cleaner'].unique()
        if cleaner != '暂未派单' and pd.notna(cleaner) and cleaner != ''
    ])

    # 应用过滤器
    cleaner_filter = st.session_state.get('cleaner_filter', [])
    if cleaner_filter:
        filtered_df = filtered_df[filtered_df['assigned_cleaner'].isin(cleaner_filter)]

    creator_filter = st.session_state.get('creator_filter', [])
    if creator_filter:
        filtered_df = filtered_df[filtered_df['created_by'].isin(creator_filter)]

    # 重置索引，以确保索引连续
    filtered_df = filtered_df.reset_index(drop=True)

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
        'remarks',  # 备注
        'assigned_cleaner',  # 保洁小组
        'total_amount',  # 总金额
        'income1',  # 现金收入
        'income2',  # 转账收入
        'subsidy',  # 补贴
        'created_by',  # 创建人
        'source',  # 来源
    ]

    display_df = display_df[columns_to_display].copy()

    # 重命名列
    column_labels = {
        'work_date': '日期',
        'work_time': '时间',
        'work_address': '地址',
        'income1': '收入1',
        'income2': '收入2',
        'total_amount': '总金额',
        'assigned_cleaner': '保洁组',
        'subsidy': '补贴',
        'created_by': '创建人',
        'source': '来源',
        'remarks': '备注'
    }
    display_df = display_df.rename(columns=column_labels)

    # 生成时间选项（从上午6:00到下午10:00，每半小时一个选项）
    time_options = []
    for hour in range(6, 23):  # 6:00 到 22:00
        for minute in [0, 30]:
            period = "上午" if hour < 12 else "下午"
            # 转换为12小时制
            display_hour = hour if hour <= 12 else hour - 12
            time_str = f"{period} {display_hour:02d}:{minute:02d}"
            time_options.append(time_str)

    # 使用传入的 cleaner_options
    edited_df = st.data_editor(
        display_df,
        key='work_orders_editor',
        use_container_width=True,
        hide_index=True,
        column_config={
            "日期": st.column_config.DateColumn(
                "日期",
                help="保洁日期",
                format="YYYY-MM-DD",
                step=1,
                width="small",
            ),
            "时间": st.column_config.SelectboxColumn(  # 改为SelectboxColumn
                "时间",
                help="保洁时间",
                width="small",
                options=[""] + time_options,  # 添加空选项
            ),
            "地址": st.column_config.TextColumn(
                "地址",
                help="工作地址",
                width="medium",
            ),
            "保洁组": st.column_config.SelectboxColumn(
                "保洁组",
                help="保洁小组",
                width="small",
                options=["暂未派单"] + cleaner_options,
            ),
            "收入1": st.column_config.NumberColumn(
                "收入1",
                help="现金收入",
                min_value=0,
                width="small",
                format="$%.2f",
            ),
            "收入2": st.column_config.NumberColumn(
                "收入2",
                help="转账收入",
                min_value=0,
                width="small",
                format="$%.2f",
            ),
            "补贴": st.column_config.NumberColumn(
                "补贴",
                help="补贴金额",
                min_value=0,
                width="small",
                format="$%.2f",
            ),
            "总金额": st.column_config.NumberColumn(
                "总金额",
                help="总金额(含GST)",
                min_value=0,
                format="$%.2f",
                width="small",
                disabled=True,
            ),
            "备注": st.column_config.TextColumn(
                "备注",
                help="工单备注",
                width="small",
            ),
            "创建人": st.column_config.TextColumn(
                "创建人",
                help="工单创建人",
                width="small",
                disabled=True,
            ),
            "来源": st.column_config.TextColumn(
                "来源",
                help="工单来源",
                width="small",
            ),
        }
    )

    # 在 show_work_orders_table 函数中的更新逻辑部分
    if st.session_state.get('show_work_orders_table', None) != edited_df.to_dict():
        st.session_state['show_work_orders_table'] = edited_df.to_dict()

        # 获取原始数据用于对比
        original_df = display_df.copy()

        # 比较并处理修改过的行
        for index, row in edited_df.iterrows():
            original_row = original_df.iloc[index]
            if not row.equals(original_row):
                # 准备更新数据
                update_data = {
                    'id': filtered_df.iloc[index]['id'],
                    'work_date': row['日期'] if pd.notna(row['日期']) else None,
                    'work_time': row['时间'],
                    'work_address': row['地址'],
                    'assigned_cleaner': row['保洁组'],
                    'income1': float(row['收入1'].replace('$', '').replace(',', '')) if row['收入1'] else 0,
                    'income2': float(row['收入2'].replace('$', '').replace(',', '')) if row['收入2'] else 0,
                    'subsidy': float(row['补贴'].replace('$', '').replace(',', '')) if row['补贴'] else 0,
                    'source': row['来源'],
                    'remarks': row['备注']
                }

                # 调用更新函数
                success, error = update_work_order(update_data)

                if success:
                    # 显示更新成功对话框
                    show_update_dialog()
                else:
                    # 显示更新失败对话框
                    show_error_dialog(error)

    return filtered_df  # 返回过滤后的数据用于统计


def work_order_statistics():
    """工单统计主页面"""
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png', layout='wide')
    apply_global_styles()
    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("📊 工单管理")
        st.divider()

        # # 操作按钮
        # col1, col2, col3 = st.columns([1, 1, 1])
        # with col1:
        #     if st.button("新建工单", use_container_width=True, type="primary"):
        #         st.switch_page("pages/new_work_order_v2.py")
        # with col3:
        #     if st.button("创建收据", use_container_width=True, type="primary"):
        #         st.switch_page("pages/receipt_page.py")
        # with col2:
        #     if st.button("月度结算", use_container_width=True, type="primary"):
        #         st.switch_page("pages/monthly_review.py")

        # 获取初始数据
        default_time_range = st.session_state.get('time_range', 'month')
        orders_df, error = get_work_orders(default_time_range)

        # 获取活跃的保洁组
        teams, teams_error = get_active_clean_teams()
        if teams_error:
            st.error(f"获取保洁组信息失败：{teams_error}")
            return

        # 提取保洁组名称列表
        cleaner_options = [team['team_name'] for team in teams]

        if error:
            st.error(f"获取数据失败：{error}")
            return

        # 检查是否有数据需要显示
        if orders_df is not None and not orders_df.empty:
            # 显示统计信息
            show_statistics(orders_df)
            st.divider()

            # 显示筛选条件
            selected_time_range = show_filters(orders_df)

            st.info("您可以直接在下面的表格中修改数据", icon="ℹ️")

            # 只有当时间范围发生变化时才重新获取数据
            if selected_time_range != default_time_range:
                orders_df, error = get_work_orders(selected_time_range)
                if error:
                    st.error(f"获取数据失败：{error}")
                    return

            # 显示工单表格
            filtered_df = show_work_orders_table(orders_df, cleaner_options)
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
        st.switch_page("app.py")


if __name__ == "__main__":
    work_order_statistics()
