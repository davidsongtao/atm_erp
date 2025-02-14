import time
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from utils.db_operations import get_work_orders, get_work_orders_by_date_range, update_work_order, connect_db, delete_work_order
from utils.utils import navigation, check_login_state
from utils.styles import apply_global_styles


@st.dialog("删除工单")
def select_and_delete_order_dialog():
    """选择并删除工单的对话框"""
    # 获取所有工单
    orders_df, error = get_work_orders('year')  # 默认显示本年的工单

    if error:
        st.error(f"获取工单列表失败：{error}")
        return

    if orders_df is None or orders_df.empty:
        st.info("暂无可删除的工单")
        return

    # 创建工单选择列表
    order_options = []
    order_map = {}  # 用于存储地址到工单ID的映射

    for _, order in orders_df.iterrows():
        # 创建显示文本，包含地址和日期
        display_text = f"{order['work_address']} ({order['order_date'].strftime('%Y-%m-%d')})"
        order_options.append(display_text)
        order_map[display_text] = order

    # 工单选择下拉框
    selected_order_text = st.selectbox(
        "选择要删除的工单",
        options=order_options,
        format_func=lambda x: x,
        index=None,
        placeholder="请选择要删除的工单..."
    )

    if selected_order_text:
        selected_order = order_map[selected_order_text]

        # 显示选中工单的详细信息
        st.write(f"📍 工作地址：{selected_order['work_address']}")
        st.write(f"📅 创建日期：{selected_order['order_date'].strftime('%Y-%m-%d')}")
        if selected_order['assigned_cleaner'] != '暂未派单':
            st.write(f"👷 保洁小组：{selected_order['assigned_cleaner']}")
        if selected_order['work_date'] is not None:
            st.write(f"🕒 保洁时间：{selected_order['work_date'].strftime('%Y-%m-%d')} {selected_order['work_time']}")

        st.warning("确定要删除此工单吗？此操作不可恢复！", icon="⚠️")

        # 确认复选框
        confirm_checkbox = st.checkbox(
            "我已了解删除操作不可恢复，并确认删除此工单！",
            key=f"confirm_delete_checkbox_{selected_order['id']}"
        )

        # 操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button(
                    "确认删除",
                    use_container_width=True,
                    type="primary",
                    disabled=not confirm_checkbox
            ):
                success, error = delete_work_order(selected_order['id'])
                if success:
                    st.success("工单已成功删除！", icon="✅")
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"删除失败：{error}", icon="⚠️")

        with col2:
            if st.button("取消", use_container_width=True):
                st.rerun()


def generate_time_options():
    """生成时间选项列表，每15分钟一个间隔"""
    time_options = []

    # 上午时间选项 (8:00 - 11:45)
    for hour in range(8, 12):
        for minute in range(0, 60, 15):
            time_str = f"上午 {hour:02d}:{minute:02d}"
            time_options.append(time_str)

    # 下午时间选项 (12:00 - 21:45)
    for hour in range(12, 22):
        for minute in range(0, 60, 15):
            time_str = f"下午 {hour:02d}:{minute:02d}"
            time_options.append(time_str)

    return time_options


def init_session_state():
    """初始化session state变量"""
    if 'needs_reset' not in st.session_state:
        st.session_state.needs_reset = False

    # 强制设置默认时间范围为本月
    st.session_state.time_range = 'month'

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
    col1, col2, col3, col4 = st.columns(4)

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
            key='time_range'
        )

    with col2:
        cleaner_options = []
        if df is not None and not df.empty:
            cleaner_options = sorted([
                cleaner for cleaner in df['assigned_cleaner'].unique()
                if cleaner != '暂未派单' and pd.notna(cleaner)
            ])

        # 仅在选项发生变化时更新 session state
        if 'cleaner_filter' not in st.session_state:
            st.session_state.cleaner_filter = []

        # 验证现有的过滤器值是否在选项中
        st.session_state.cleaner_filter = [
            x for x in st.session_state.cleaner_filter
            if x in cleaner_options
        ]

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

        # 仅在选项发生变化时更新 session state
        if 'creator_filter' not in st.session_state:
            st.session_state.creator_filter = []

        # 验证现有的过滤器值是否在选项中
        st.session_state.creator_filter = [
            x for x in st.session_state.creator_filter
            if x in creator_options
        ]

        creator_filter = st.multiselect(
            "创建人",
            options=creator_options,
            key='creator_filter',
            placeholder="请选择..."
        )

    with col4:
        invoice_status = st.selectbox(
            "发票状态",
            options=["未开发票", "已开发票"],
            key='invoice_status_filter',
            index=None,
            placeholder="请选择..."
        )

    # 清空筛选按钮
    if st.button("清空筛选条件", type="primary"):
        st.session_state.needs_reset = True
        st.rerun()

    # 操作按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("新建工单", use_container_width=True, type="primary"):
            st.switch_page("pages/new_work_order.py")
    with col2:
        if st.button("删除工单", use_container_width=True, type="primary"):
            select_and_delete_order_dialog()
    with col3:
        if st.button("月度结算", use_container_width=True, type="primary"):
            st.switch_page("pages/monthly_review.py")

    return time_range


def show_work_orders_table(df):
    """显示工单详情表格"""
    filtered_df = df.copy()

    # 将所有的 NaN 和 None 值替换为空字符串
    filtered_df = filtered_df.fillna('')

    # 获取当前可用的保洁小组选项
    conn = connect_db()
    cleaner_options = conn.query("""
            SELECT team_name 
            FROM clean_teams 
            WHERE team_name != '暂未派单' AND is_active = 1
            ORDER BY team_name
        """, ttl=0)
    cleaner_options = cleaner_options['team_name'].tolist()

    # 获取所有用户名作为创建人选项
    creator_options = conn.query("""
        SELECT name 
        FROM users 
        ORDER BY name
    """, ttl=0)
    creator_options = creator_options['name'].tolist()

    # 处理收入1和收入2
    def calculate_income(row):
        if row['payment_method'] == 'cash':
            return str(row['order_amount']) if row['order_amount'] != 0 else "", ""
        elif row['payment_method'] == 'transfer':
            return "", str(row['total_amount']) if row['total_amount'] != 0 else ""
        return "", ""

    # 应用过滤器
    cleaner_filter = st.session_state.get('cleaner_filter', [])
    if cleaner_filter:
        filtered_df = filtered_df[filtered_df['assigned_cleaner'].isin(cleaner_filter)]

    creator_filter = st.session_state.get('creator_filter', [])
    if creator_filter:
        filtered_df = filtered_df[filtered_df['created_by'].isin(creator_filter)]

    # 应用发票状态筛选
    invoice_status_filter = st.session_state.get('invoice_status_filter')
    if invoice_status_filter:
        if invoice_status_filter == "未开发票":
            filtered_df = filtered_df[
                (filtered_df['paperwork'] == 0) & (filtered_df['invoice_sent'] == False)
                ]
        elif invoice_status_filter == "已开发票":
            filtered_df = filtered_df[
                (filtered_df['paperwork'] == 0) & (filtered_df['invoice_sent'] == True)
                ]

    display_df = filtered_df.copy()

    # 特殊处理 work_date 列，确保它是正确的日期格式或 None
    display_df['work_date'] = display_df['work_date'].apply(
        lambda x: pd.NaT if x == '' or pd.isna(x) else x
    )

    # 处理金额列的空值显示
    for col in ['subsidy', 'order_amount', 'total_amount']:
        display_df[col] = display_df[col].apply(lambda x: "" if pd.isna(x) or x == 0 else str(x))

    # 添加收入1和收入2列
    display_df[['income1', 'income2']] = display_df.apply(calculate_income, axis=1, result_type='expand')

    # 移除所有数值列中的'None'字符串
    for col in ['income1', 'income2', 'subsidy']:
        display_df[col] = display_df[col].replace({'None': '', 'nan': '', '0': ''})
        display_df[col] = display_df[col].apply(lambda x: '' if x in [None, 'None', 'nan', '0', 0] else x)

    # 处理发票状态显示
    def get_invoice_status_display(row):
        if row['paperwork'] == 0:  # 需要开发票
            return '已开发票' if row['invoice_sent'] else '未开发票'
        return '-'  # 不需要开发票或需要开收据

    display_df['invoice_status'] = filtered_df.apply(get_invoice_status_display, axis=1)

    # 选择要显示的列并重新排序
    columns_to_display = [
        'work_date',  # 保洁日期
        'work_time',  # 保洁时间
        'work_address',  # 工作地址
        'assigned_cleaner',  # 保洁小组
        'income1',  # 收入1（现金）
        'income2',  # 收入2（转账）
        'subsidy',  # 补贴
        'invoice_status',  # 发票状态
        'created_by',  # 创建人
        'source',  # 来源
        'remarks'  # 备注
    ]

    display_df = display_df[columns_to_display].copy()

    # 生成时间选项
    time_options = []
    for hour in range(8, 22):
        for minute in range(0, 60, 15):
            period = "上午" if hour < 12 else "下午"
            time_str = f"{period} {hour:02d}:{minute:02d}"
            time_options.append(time_str)

    # 设置列的编辑配置
    column_config = {
        "work_date": st.column_config.DateColumn(
            "保洁日期",
            format="YYYY-MM-DD",
            width="small",
            min_value=datetime(2020, 1, 1),  # 设置最小日期
            max_value=datetime(2030, 12, 31),  # 设置最大日期
            default=None,  # 允许空值
            required=False,  # 设置为非必填
        ),
        "work_time": st.column_config.SelectboxColumn(
            "保洁时间",
            width="small",
            options=[""] + time_options,
        ),
        "work_address": st.column_config.TextColumn(
            "工作地址",
            disabled=False,
            max_chars=200,
            help="点击单元格编辑地址",
            width="small"
        ),
        "assigned_cleaner": st.column_config.SelectboxColumn(
            "保洁小组",
            width="small",
            options=cleaner_options,
            required=False,
        ),
        "income1": st.column_config.NumberColumn(
            "收入1",
            help="现金收入",
            format="%.2f",
            width="small",
            min_value=0,
            step=0.01,
            default=None,
            required=False
        ),
        "income2": st.column_config.NumberColumn(
            "收入2",
            help="转账收入",
            format="%.2f",
            width="small",
            min_value=0,
            step=0.01,
            default=None,
            required=False
        ),
        "subsidy": st.column_config.NumberColumn(
            "补贴金额",
            format="%.2f",
            width="small",
            min_value=0,
            step=0.01,
            default=None,
            required=False
        ),
        "invoice_status": st.column_config.SelectboxColumn(
            "发票状态",
            width="small",
            options=['已开发票', '未开发票', '-'],
            help="需要开发票时可修改状态"
        ),
        "created_by": st.column_config.SelectboxColumn(
            "创建人",
            width="small",
            options=creator_options,
            required=True,
        ),
        "source": st.column_config.TextColumn(
            "来源",
            width="small"
        ),
        "remarks": st.column_config.TextColumn(
            "备注",
            width="medium",
            help="点击单元格编辑备注信息",
            max_chars=500,
        )
    }

    # 创建编辑器配置
    editor_disabled = {}
    for idx in display_df.index:
        if filtered_df.loc[idx, 'paperwork'] != 0:  # 如果不需要开发票
            if 'invoice_status' not in editor_disabled:
                editor_disabled['invoice_status'] = set()
            editor_disabled['invoice_status'].add(idx)

    # 保存编辑前的数据副本，用于比较
    pre_edit_df = display_df.copy()

    # 使用 st.data_editor 显示可编辑的数据表格
    edited_df = st.data_editor(
        display_df,
        column_config=column_config,
        hide_index=True,
        use_container_width=True,
        key="orders_table",
        disabled=editor_disabled
    )

    # 检测并处理数据更改
    if not pre_edit_df.equals(edited_df):
        # 找出实际发生变化的列
        changed_columns = []
        for col in edited_df.columns:
            if not (pre_edit_df[col].fillna('') == edited_df[col].fillna('')).all():
                changed_columns.append(col)

        # 重置索引，确保正确对应
        filtered_df_reset = filtered_df.reset_index(drop=True)
        edited_df_reset = edited_df.reset_index(drop=True)

        # 检查每一行是否有变化
        for idx, row in edited_df_reset.iterrows():
            order_id = filtered_df_reset.loc[idx, 'id']
            original_row = pre_edit_df.iloc[idx]

            # 检查这一行是否有实际变化
            has_changes = False
            update_data = {'id': order_id}

            for col in changed_columns:
                # 处理空值比较
                original_value = str(original_row[col]) if pd.notna(original_row[col]) else ''
                new_value = str(row[col]) if pd.notna(row[col]) else ''

                # 对于数值型列的特殊处理
                if col in ['income1', 'income2', 'subsidy']:
                    # 转换空字符串为0
                    original_num = float(original_value) if original_value.strip() != '' else 0
                    new_num = float(new_value) if new_value.strip() != '' else 0

                    if abs(original_num - new_num) > 0.01:  # 使用小数比较
                        has_changes = True
                        # 特殊处理收入字段
                        if col in ['income1', 'income2'] and new_num > 0:
                            if col == 'income1':
                                update_data['payment_method'] = 'cash'
                                update_data['order_amount'] = new_num
                                update_data['total_amount'] = new_num
                            else:
                                update_data['payment_method'] = 'transfer'
                                base_amount = new_num / 1.1  # 去除10% GST
                                update_data['order_amount'] = base_amount
                                update_data['total_amount'] = new_num
                        else:
                            update_data[col] = new_num

                # 特殊处理发票状态
                elif col == 'invoice_status':
                    if filtered_df_reset.loc[idx, 'paperwork'] == 0:
                        new_status = (new_value == '已开发票')
                        if new_status != (original_value == '已开发票'):
                            has_changes = True
                            update_data['invoice_sent'] = new_status
                # 处理其他列
                elif original_value != new_value:
                    has_changes = True
                    update_data[col] = new_value

            # 只有在有实际变化时才更新
            if has_changes:
                success, error = update_work_order(update_data)
                if success:
                    st.success(f"工单信息已成功更新", icon="✅")
                    st.session_state.table_updated = True
                    time.sleep(1)
                else:
                    st.error(f"更新工单失败: {error}")

    return edited_df


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

        st.title("📊 工单管理")
        st.divider()

        # 获取初始数据
        default_time_range = st.session_state.get('time_range', 'month')
        orders_df, error = get_work_orders(default_time_range)

        if error:
            st.error(f"获取数据失败：{error}")
            return

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
            # 显示工单详情
            edited_df = show_work_orders_table(orders_df)

            # 检查是否发生了更新
            if 'table_updated' in st.session_state and st.session_state.table_updated:
                # 清除更新标志
                st.session_state.table_updated = False
                st.rerun()
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
