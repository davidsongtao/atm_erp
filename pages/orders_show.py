import time
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.db_operations import get_work_orders, get_work_orders_by_date_range, update_work_order
from utils.utils import navigation, check_login_state
from utils.styles import apply_global_styles


def init_session_state():
    """初始化session state变量"""
    # 初始化重置标志
    if 'needs_reset' not in st.session_state:
        st.session_state.needs_reset = False

    # 如果需要重置，设置所有值为默认值
    if st.session_state.needs_reset:
        if 'time_range' in st.session_state:
            del st.session_state.time_range
        if 'cleaner_filter' in st.session_state:
            del st.session_state.cleaner_filter
        if 'creator_filter' in st.session_state:
            del st.session_state.creator_filter
        if 'payment_status_filter' in st.session_state:
            del st.session_state.payment_status_filter
        if 'invoice_status_filter' in st.session_state:
            del st.session_state.invoice_status_filter
        if 'receipt_status_filter' in st.session_state:
            del st.session_state.receipt_status_filter
        st.session_state.needs_reset = False


def get_status_display(value, is_required):
    if not is_required:
        return '⚪'  # 浅灰色圆点表示不需要
    return '🟢' if value else '🔴'  # 绿色表示已完成，红色表示未完成


def show_filters(df=None):
    """显示筛选条件，即使没有数据也显示基本的筛选选项"""
    # 第一行筛选条件
    col1, col2, col3 = st.columns(3)

    with col1:
        time_range = st.selectbox(
            "时间范围",
            options=["year", "quarter", "month", "week", "day"],
            format_func=lambda x: {
                "day": "今日",
                "week": "本周",
                "month": "本月",
                "quarter": "本季度",
                "year": "今年"
            }[x],
            key='time_range',
            index=0  # 设置默认选项为第一个（即"year"）
        )

    with col2:
        # 如果有数据，显示保洁员选项，否则显示空列表
        cleaner_options = []
        if df is not None and not df.empty:
            cleaner_options = sorted([
                cleaner for cleaner in df['assigned_cleaner'].unique()
                if cleaner != '暂未派单' and pd.notna(cleaner)
            ])

        cleaner_filter = st.multiselect(
            "保洁小组筛选",
            options=cleaner_options,
            default=[],
            key='cleaner_filter'
        )

    with col3:
        # 如果有数据，显示创建人选项，否则显示空列表
        creator_options = []
        if df is not None and not df.empty:
            creator_options = sorted(df['created_by'].unique().tolist())

        creator_filter = st.multiselect(
            "创建人筛选",
            options=creator_options,
            default=[],
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

    # 创建一个清空按钮，放在所有筛选条件下方
    if st.button("清空筛选条件", type="primary"):
        st.session_state.needs_reset = True
        st.rerun()

    return time_range


def show_work_orders_table(df):
    """显示工单详情表格"""
    # 预处理数据类型
    filtered_df = df.copy()

    # 保存原始数据的副本，用于检测更改
    original_df = filtered_df.copy()

    # 将paperwork转换为整数类型
    filtered_df['paperwork'] = pd.to_numeric(filtered_df['paperwork'], errors='coerce').fillna(0).astype(int)

    # 处理布尔值列
    bool_columns = ['payment_received', 'invoice_sent', 'receipt_sent']
    for col in bool_columns:
        filtered_df[col] = pd.to_numeric(filtered_df[col], errors='coerce').fillna(0).astype(bool)

    # 应用保洁员筛选
    cleaner_filter = st.session_state.get('cleaner_filter', [])
    if cleaner_filter:
        filtered_df = filtered_df[filtered_df['assigned_cleaner'].isin(cleaner_filter)]

    # 应用创建人筛选
    creator_filter = st.session_state.get('creator_filter', [])
    if creator_filter:
        filtered_df = filtered_df[filtered_df['created_by'].isin(creator_filter)]

    # 应用收款状态筛选
    if st.session_state.payment_status_filter != "全部":
        is_paid = st.session_state.payment_status_filter == "已收款"
        filtered_df = filtered_df[filtered_df['payment_received'] == is_paid]

    # 发票状态筛选逻辑
    if st.session_state.invoice_status_filter != "全部":
        filtered_df = filtered_df[filtered_df['paperwork'] == 0]
        if st.session_state.invoice_status_filter == "已开票":
            filtered_df = filtered_df[filtered_df['invoice_sent']]
        else:
            filtered_df = filtered_df[~filtered_df['invoice_sent']]

    # 收据状态筛选逻辑
    if st.session_state.receipt_status_filter != "全部":
        filtered_df = filtered_df[filtered_df['paperwork'] == 1]
        if st.session_state.receipt_status_filter == "已开收据":
            filtered_df = filtered_df[filtered_df['receipt_sent']]
        else:
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
        if pd.notna(row.get('basic_service')): services.append(str(row['basic_service']))
        if pd.notna(row.get('rooms')): services.append(str(row['rooms']))
        if pd.notna(row.get('electricals')): services.append(str(row['electricals']))
        if pd.notna(row.get('other_services')): services.append(str(row['other_services']))
        if pd.notna(row.get('cuistom_item')): services.append(str(row['cuistom_item']))
        return ' ; '.join(filter(None, services))

    # 添加服务内容列
    display_df['service_content'] = display_df.apply(combine_services, axis=1)

    # 获取发票和收据的需求状态
    display_df['needs_invoice'] = display_df['paperwork'] == 0
    display_df['needs_receipt'] = display_df['paperwork'] == 1

    # 处理支付状态显示
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
        'id',  # 添加ID列用于数据更新
        'work_datetime',
        'work_address',
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

    # 设置列的编辑配置
    column_config = {
        "id": st.column_config.NumberColumn(
            "ID",
            disabled=True,
            help="工单ID"
        ),
        "work_datetime": st.column_config.TextColumn(
            "工作日期时间",
            disabled=True,
        ),
        "work_address": st.column_config.TextColumn(
            "工作地址",
            disabled=False,  # 允许编辑
            max_chars=200,
            help="点击单元格编辑地址"
        ),
        "order_amount": st.column_config.NumberColumn(
            "订单金额",
            disabled=True,
            format="%.2f",
        ),
        "total_amount": st.column_config.NumberColumn(
            "总金额",
            disabled=True,
            format="%.2f",
        ),
        "assigned_cleaner": st.column_config.TextColumn(
            "保洁小组",
            disabled=True,
        ),
        "payment_received": st.column_config.TextColumn(
            "收款情况",
            disabled=True,
        ),
        "invoice_sent": st.column_config.TextColumn(
            "已开发票",
            disabled=True,
        ),
        "receipt_sent": st.column_config.TextColumn(
            "已开收据",
            disabled=True,
        ),
        "created_by": st.column_config.TextColumn(
            "创建人",
            disabled=True,
        ),
        "source": st.column_config.TextColumn(
            "来源",
            disabled=True,
        ),
        "service_content": st.column_config.TextColumn(
            "服务内容",
            disabled=True,
            width="large",
        ),
    }

    # 使用 st.data_editor 显示可编辑的数据表格
    edited_df = st.data_editor(
        display_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        disabled=["id"],  # 禁用 ID 列编辑
        key="orders_table"
    )

    # 检测并处理数据更改
    if not display_df.equals(edited_df):
        # 找出发生更改的行
        changed_mask = display_df != edited_df
        changed_rows_idx = changed_mask.any(axis=1)

        # 获取发生变化的行
        original_rows = display_df[changed_rows_idx]
        edited_rows = edited_df[changed_rows_idx]

        # 逐行处理更改
        for idx in original_rows.index:
            # 确保 ID 是有效的数字
            order_id = original_rows.loc[idx, 'id']
            if pd.isna(order_id):
                st.error(f"无效的工单ID：{order_id}")
                continue

            # 转换 ID 为整数
            try:
                order_id = int(order_id)
            except (ValueError, TypeError):
                st.error(f"无效的工单ID格式：{order_id}")
                continue

            # 获取新的地址值
            new_address = edited_rows.loc[idx, 'work_address']
            if pd.isna(new_address):
                st.error("地址不能为空")
                continue

            # 构造更新数据
            update_data = {
                'id': order_id,
                'work_address': str(new_address).strip()  # 确保地址是字符串类型
            }

            # 调用更新函数
            success, error = update_work_order(update_data)

            if success:
                st.success(f"成功更新工单 {order_id} 的地址信息")
            else:
                st.error(f"更新工单 {order_id} 失败: {error}")

    return edited_df  # 返回编辑后的数据框


def work_order_statistics():
    # 设置页面配置
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png', layout="wide")
    apply_global_styles()

    # 初始化session state
    init_session_state()

    # 检查登录状态
    login_state, role = check_login_state()

    if login_state:
        # 显示导航栏
        navigation()

        st.title("📊 工单统计")
        st.divider()
        st.subheader("工单详情")

        # 获取数据
        default_time_range = st.session_state.get('time_range', 'year')
        orders_df, error = get_work_orders(default_time_range)

        if error:
            st.error(f"获取数据失败：{error}")
            return

        if orders_df is not None and not orders_df.empty:
            # 显示筛选条件
            selected_time_range = show_filters(orders_df)

            # 如果时间范围发生变化，重新获取数据
            if selected_time_range != default_time_range:
                orders_df, error = get_work_orders(selected_time_range)
                if error:
                    st.error(f"获取数据失败：{error}")
                    return

            # 显示工单详情
            if orders_df is not None and not orders_df.empty:
                show_work_orders_table(orders_df)
            else:
                st.info("暂无工单数据")
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
        st.error("您还没有登录！1秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)
        st.switch_page("pages/login_page.py")


if __name__ == "__main__":
    work_order_statistics()
