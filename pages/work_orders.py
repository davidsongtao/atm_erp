"""
Description: 工单管理页面

-*- Encoding: UTF-8 -*-
@File     ：work_orders.py
@Author   ：King Songtao
@Time     ：2025/1/8
@Contact  ：king.songtao@gmail.com
"""
import os
import time
import toml
import streamlit as st
from datetime import datetime, date, timedelta
from utils.utils import navigation, check_login_state
from utils.db_operations import get_work_orders, get_work_orders_by_date_range, update_payment_status, update_receipt_status, update_invoice_status, assign_work_order, get_active_clean_teams
import pandas as pd
from utils.styles import apply_global_styles


@st.dialog("派单信息")
def show_assign_order_dialog(order_data):
    """派单对话框
    Args:
        order_data (pd.Series): 工单数据
    """
    st.write(f"📍 工单地址：{order_data['work_address']}")

    # 获取在职保洁组列表
    active_teams, error = get_active_clean_teams()
    if error:
        st.error(f"获取保洁组列表失败：{error}", icon="⚠️")
        return

    if not active_teams:
        st.warning("当前没有在职的保洁组", icon="⚠️")
        return

    # 过滤掉"暂未派单"选项
    active_teams = [team for team in active_teams if team['team_name'] != '暂未派单']

    # 选择保洁组
    selected_team = st.selectbox(
        "选择保洁组",
        options=[team['team_name'] for team in active_teams],
        placeholder="请选择保洁组",
        index=None
    )

    # 选择保洁日期
    min_date = datetime.now().date()
    work_date = st.date_input(
        "保洁日期",
        value=min_date,
        min_value=min_date
    )

    # 生成时间选项
    time_options = []
    for hour in range(7, 23):  # 7 AM to 10 PM
        period = "AM" if hour < 12 else "PM"
        display_hour = hour if hour <= 12 else hour - 12
        time_options.append(f"{display_hour}:00 {period}")

    # 选择保洁时间
    work_time = st.selectbox(
        "保洁时间",
        options=time_options,
        placeholder="请选择保洁时间",
        index=None
    )

    # 确认复选框
    confirm_checkbox = st.checkbox(
        "我已确认以上信息无误，并确认派单！",
        key=f"confirm_assign_checkbox_{order_data['id']}"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
                "确认派单",
                use_container_width=True,
                type="primary",
                disabled=not confirm_checkbox or not selected_team
        ):
            # 更新数据库中的派单状态
            success, error = assign_work_order(
                order_data['id'],
                selected_team,
                work_date,
                work_time
            )
            if success:
                st.success("派单成功！", icon="✅")
                time.sleep(2)  # 显示2秒成功消息
                st.rerun()  # 重新加载页面
            else:
                st.error(f"派单失败：{error}", icon="⚠️")

    with col2:
        if st.button("取消", use_container_width=True):
            st.rerun()


# 修改后的发票签发对话框函数
@st.dialog("签发发票")
def issue_invoice_dialog(order_data):
    """发票签发对话框

    Args:
        order_data (pd.Series): 工单数据
    """
    st.write(f"📍 工单地址：{order_data['work_address']}")
    st.number_input("工单总金额", value=order_data['total_amount'], disabled=True)

    # 添加确认checkbox
    confirm_checkbox = st.checkbox(
        "我已确认以上信息无误，并确认签发该发票！",
        key=f"confirm_invoice_checkbox_{order_data['id']}"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
                "确认已签发",
                use_container_width=True,
                type="primary",
                disabled=not confirm_checkbox  # 根据checkbox状态禁用确认按钮
        ):
            # 更新数据库中的发票状态
            success, error = update_invoice_status(order_data['id'], datetime.now())
            if success:
                st.success("发票状态已更新！", icon="✅")
                time.sleep(2)  # 显示2秒成功消息
                st.rerun()  # 重新加载页面
            else:
                st.error(f"发票状态更新失败：{error}", icon="⚠️")

    with col2:
        if st.button("取消", use_container_width=True):
            st.rerun()


# 修改后的收据签发对话框函数
@st.dialog("签发收据")
def issue_receipt_dialog(order_data):
    """收据签发对话框

    Args:
        order_data (pd.Series): 工单数据
    """
    st.write(f"📍 工单地址：{order_data['work_address']}")
    st.number_input("工单总金额", value=order_data['total_amount'], disabled=True)

    # 添加确认checkbox
    confirm_checkbox = st.checkbox(
        "我已确认以上信息无误，并确认签发该收据！",
        key=f"confirm_receipt_checkbox_{order_data['id']}"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button(
                "收据已签发",
                use_container_width=True,
                type="primary",
                disabled=not confirm_checkbox  # 根据checkbox状态禁用确认按钮
        ):
            # 更新数据库中的收据状态
            success, error = update_receipt_status(order_data['id'], datetime.now())
            if success:
                st.success("收据状态已更新！", icon="✅")
                time.sleep(2)  # 显示2秒成功消息
                st.rerun()  # 重新加载页面
            else:
                st.error(f"收据状态更新失败：{error}", icon="⚠️")

    with col2:
        if st.button(
                "前往创建收据页面",
                use_container_width=True,
                disabled=not confirm_checkbox  # 根据checkbox状态禁用按钮
        ):
            # 构建初始化数据
            receipt_data = {
                "address": order_data['work_address'],
                "selected_date": datetime.now().date(),
                "amount": float(order_data['total_amount']),
                "basic_service": order_data['basic_service'].split('|') if order_data['basic_service'] else [],
                "rooms": order_data['rooms'].split('|') if order_data['rooms'] else [],
                "electrical": order_data['electricals'].split('|') if order_data['electricals'] else [],
                "other": order_data['other_services'].split('|') if order_data['other_services'] else [],
                "custom_notes": order_data['custom_item'].split('|') if order_data['custom_item'] else [],
                "custom_notes_enabled": bool(order_data['custom_item']),
                "excluded_enabled": False,
                "custom_excluded_enabled": False,
                "manual_excluded_selection": [],
                "custom_excluded_items": [],
                "order_id": order_data['id']  # 保存工单ID以便后续更新状态
            }

            # 存储到session state
            st.session_state['previous_form_data'] = receipt_data

            # 跳转到收据页面
            st.switch_page("pages/receipt_page.py")


# 修改后的确认收款对话框函数
@st.dialog("确认收款")
def confirm_payment_dialog(order_id, work_address, total_amount, payment_method):  # 添加payment_method参数
    st.write(f"📍 工单地址：{work_address}")

    # 使用columns布局来并排显示收款金额和付款方式
    col1, col2 = st.columns(2)

    with col1:
        # 添加收款金额输入框，默认值为工单总额
        payment_amount = st.number_input(
            "收款金额",
            min_value=0.0,
            value=float(total_amount),
            step=0.1,
            format="%.2f",
            disabled=True,
        )

    with col2:
        # 显示付款方式
        payment_text = "转账(含GST)" if payment_method == 'transfer' else "现金"
        st.text_input("付款方式", value=payment_text, disabled=True)

    # 添加确认checkbox
    confirm_checkbox = st.checkbox("我已确认以上信息无误，并已收到相应款项", key=f"confirm_checkbox_{order_id}")

    # 添加确认和取消按钮
    col1, col2 = st.columns(2)

    with col1:
        if st.button(
                "确认",
                type="primary",
                use_container_width=True,
                disabled=not confirm_checkbox  # 根据checkbox状态禁用确认按钮
        ):
            # 更新数据库中的收款状态
            success, error = update_payment_status(order_id, datetime.now())
            if success:
                st.success("收款确认成功！", icon="✅")
                time.sleep(2)  # 显示2秒成功消息
                st.rerun()  # 重新加载页面
            else:
                st.error(f"收款确认失败：{error}", icon="⚠️")

    with col2:
        if st.button("取消", type="secondary", use_container_width=True):
            st.rerun()


def get_theme_color():
    """
    从 .streamlit/config.toml 读取主题色
    Returns:
        str: 主题色（十六进制颜色代码）
    """
    config_path = ".streamlit/config.toml"
    default_color = "#FF4B4B"

    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding='utf-8') as f:
                config = toml.load(f)
                return config.get("theme", {}).get("primaryColor", default_color)
        return default_color
    except Exception:
        return default_color


def display_orders(orders, tab_name):
    """显示工单列表

    Args:
        orders: 工单数据 DataFrame
        tab_name: 标签页名称，用于生成唯一的按钮 key
    """
    for _, order in orders.iterrows():
        with st.container():
            st.write(f"📍 工单地址： {order['work_address']}")
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                if order['assigned_cleaner'] == '暂未派单':
                    st.markdown(f"👷 保洁小组：<span style='color:red'>⭕ 暂未确认</span>", unsafe_allow_html=True)
                    st.markdown(f"📆 保洁日期：<span style='color:red'>⭕ 暂未确认</span>", unsafe_allow_html=True)
                    st.markdown(f"🕒 保洁时间：<span style='color:red'>⭕ 暂未确认</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"👷 保洁小组：<span style='color:green'>✅ {order['assigned_cleaner']}</span>", unsafe_allow_html=True)
                    st.markdown(f"📆 保洁日期：<span style='color:green'>✅ {order['work_date'].strftime('%Y-%m-%d')}</span>", unsafe_allow_html=True)
                    st.markdown(f"🕒 保洁时间：<span style='color:green'>✅ {order['work_time']}</span>", unsafe_allow_html=True)
            with col2:
                # 根据收款状态决定高亮颜色
                if order['payment_received']:
                    # 已收款 - 绿色主题
                    st.markdown(f"💰 工单总额：<span style='color:green;font-weight:bold;'>✅ ${order['total_amount']:.2f}</span>", unsafe_allow_html=True)
                    if order['payment_method'] == 'transfer':
                        st.markdown(f"💳 付款方式：<span style='color:green'>✅ 转账(含GST)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"💳 付款方式：<span style='color:green'>✅ 现金</span>", unsafe_allow_html=True)
                else:
                    # 未收款 - 红色主题
                    st.markdown(f"💰 工单总额：<span style='color:red;font-weight:bold;'>⭕ ${order['total_amount']:.2f}</span>", unsafe_allow_html=True)
                    if order['payment_method'] == 'transfer':
                        st.markdown(f"💳 付款方式：<span style='color:red'>⭕ 转账(含GST)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"💳 付款方式：<span style='color:red'>⭕ 现金</span>", unsafe_allow_html=True)
                st.write(f"👤 登记人员： {order['created_by']}")
            with col3:
                st.write(f"💵收款状态：{'✅' if order['payment_received'] else '❌'}")
                # 根据paperwork值显示对应状态 (1=receipt, 0=invoice)
                if order['paperwork'] == 0:  # 使用字符串比较
                    st.write(f"📧发票状态：{'✅' if order['invoice_sent'] else '❌'}")
                else:  # paperwork == '1'
                    st.write(f"🧾收据状态：{'✅' if order['receipt_sent'] else '❌'}")

            # 服务内容展示
            services = []
            if order['basic_service']:
                services.extend(order['basic_service'].split('|'))
            if order['rooms']:
                services.extend(order['rooms'].split('|'))
            if order['electricals']:
                services.extend(order['electricals'].split('|'))
            if order['other_services']:
                services.extend(order['other_services'].split('|'))
            if order['custom_item']:
                services.extend(order['custom_item'].split('|'))

            if services:
                service_text = "🛠️ 服务内容：" + ", ".join(services)
                st.write(service_text)

            # 检查是否是已完成工单
            # 检查是否是已完成工单
            is_completed = order['payment_received'] and (
                    (order['paperwork'] == '0' and order['invoice_sent']) or
                    (order['paperwork'] == '1' and order['receipt_sent'])
            )

            # 仅当不是已完成工单时显示按钮
            if not is_completed:
                col1, col2, col3 = st.columns([1, 1, 1])

                with col1:
                    # 派单按钮状态
                    is_assigned = order['assigned_cleaner'] != '暂未派单'
                    if st.button(
                            "立即派单",
                            key=f"{tab_name}_confirm_worker_{order['id']}",
                            use_container_width=True,
                            disabled=is_assigned,
                            help="此工单已完成派单" if is_assigned else "点击进行派单",
                            type="primary"
                    ):
                        show_assign_order_dialog(order)
                with col2:
                    # 确认收款按钮状态
                    is_paid = order['payment_received']
                    if st.button(
                            "确认收款",
                            key=f"{tab_name}_confirm_payment_{order['id']}",
                            use_container_width=True,
                            disabled=is_paid,
                            help="此工单已确认收款" if is_paid else "点击确认收款",
                            type="primary"
                    ):
                        confirm_payment_dialog(
                            order['id'],
                            order['work_address'],
                            order['total_amount'],
                            order['payment_method']
                        )
                with col3:
                    # 只有已收款的工单且已派单才能签发发票或收据
                    if order['payment_received'] and is_assigned:
                        if order['paperwork'] == 1:  # 收据类型
                            is_receipt_sent = order['receipt_sent']
                            if st.button(
                                    "签发收据",
                                    key=f"{tab_name}_confirm_receipt_{order['id']}",
                                    use_container_width=True,
                                    disabled=is_receipt_sent,
                                    help="此工单已签发收据" if is_receipt_sent else "点击签发收据",
                                    type="primary"
                            ):
                                issue_receipt_dialog(order)
                        elif order['paperwork'] == 0:  # 发票类型
                            is_invoice_sent = order['invoice_sent']
                            if st.button(
                                    "签发发票",
                                    key=f"{tab_name}_confirm_invoice_{order['id']}",
                                    use_container_width=True,
                                    disabled=is_invoice_sent,
                                    help="此工单已签发发票" if is_invoice_sent else "点击签发发票",
                                    type="primary"
                            ):
                                issue_invoice_dialog(order)
                    else:
                        # 未派单或未收款的工单显示禁用的按钮，并给出提示信息
                        help_text = "请先派单且收款后再签发" if not is_assigned else "请先确认收款后再签发"

                        if order['paperwork'] == 1:  # 收据类型
                            st.button(
                                "签发收据",
                                key=f"{tab_name}_confirm_receipt_{order['id']}",
                                use_container_width=True,
                                disabled=True,
                                help=help_text
                            )
                        elif order['paperwork'] == 0:  # 发票类型
                            st.button(
                                "签发发票",
                                key=f"{tab_name}_confirm_invoice_{order['id']}",
                                use_container_width=True,
                                disabled=True,
                                help=help_text
                            )
            st.divider()


def work_orders():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    login_state, role = check_login_state()

    if login_state:
        navigation()

        st.title("📝 工单管理")
        st.divider()

        # 创建新工单按钮
        col1, col2, col3 = st.columns([1, 1, 1])

        with col1:
            if st.button("新建工单", use_container_width=True, type="primary"):
                st.switch_page("pages/new_work_order.py")
        with col2:
            if st.button("工单统计", use_container_width=True, type="primary"):
                st.switch_page("pages/orders_show.py")
        with col3:
            if st.button("修改工单", use_container_width=True, type="primary", disabled=True):
                st.switch_page("pages/new_work_order.py")

        # 获取当前主题色
        theme_color = get_theme_color()

        # 动态设置 tab 样式
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

        # 时间范围过滤器
        col1, col2, col3 = st.columns(3)

        with col1:
            time_range = st.selectbox(
                "选择时间范围",
                options=[
                    ("今日", "day"),
                    ("本周", "week"),
                    ("本月", "month"),
                    ("本季度", "quarter"),
                    ("本年", "year"),
                    ("自定义", "custom")
                ],
                format_func=lambda x: x[0],
                index=4,
                key="time_range"
            )

        # 根据选择的时间范围计算起止日期
        today = date.today()
        if time_range[1] == "day":
            start_date = today
            end_date = today
        elif time_range[1] == "week":
            start_date = today - timedelta(days=today.weekday())
            end_date = start_date + timedelta(days=6)
        elif time_range[1] == "month":
            start_date = today.replace(day=1)
            next_month = today.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)
        elif time_range[1] == "quarter":
            current_quarter = (today.month - 1) // 3
            start_date = today.replace(month=current_quarter * 3 + 1, day=1)
            if current_quarter == 3:
                end_date = today.replace(month=12, day=31)
            else:
                end_date = today.replace(month=current_quarter * 3 + 3, day=1) + timedelta(days=32)
                end_date = end_date.replace(day=1) - timedelta(days=1)
        elif time_range[1] == "year":
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
        else:  # custom
            start_date = today
            end_date = today

        with col2:
            selected_start_date = st.date_input(
                "起始日期",
                value=start_date,
                disabled=time_range[1] != "custom"
            )

        with col3:
            try:
                selected_end_date = st.date_input(
                    "结束日期",
                    value=max(end_date, selected_start_date),  # 确保结束日期不早于开始日期
                    min_value=selected_start_date,
                    disabled=time_range[1] != "custom"
                )
            except Exception:
                selected_end_date = selected_start_date  # 如果出现错误，设置为与开始日期相同
                st.warning("结束日期不能早于开始日期，已自动调整", icon="⚠️")

        # 使用实际的日期范围获取工单
        if time_range[1] == "custom":
            if selected_end_date < selected_start_date:
                selected_end_date = selected_start_date
                st.warning("结束日期不能早于开始日期，已自动调整", icon="⚠️")

            # 在自定义模式下显示查询按钮
            if st.button("查询自定义日期范围的工单", use_container_width=True):
                orders, error = get_work_orders_by_date_range(selected_start_date, selected_end_date)
            else:
                return
        else:
            orders, error = get_work_orders(time_range[1])

        # 显示工单列表
        if orders is not None and not orders.empty:
            # 处理数据类型
            # 确保 paperwork 列的比较使用字符串
            orders['paperwork'] = orders['paperwork'].astype(int)

            # 确保布尔值列的类型正确
            boolean_columns = ['payment_received', 'invoice_sent', 'receipt_sent']
            for col in boolean_columns:
                if orders[col].dtype == 'object':
                    orders[col] = orders[col].map({'True': True, 'False': False})
                orders[col] = orders[col].astype(bool)

            # 待派单：所有未派单的工单
            pending_assign = orders[orders['assigned_cleaner'] == '暂未派单']

            # 待收款：所有未收款的工单
            pending_payment = orders[orders['payment_received'] == False]

            # 待开票：已收款但未开发票且paperwork='0'的工单
            pending_invoice = orders[
                (orders['payment_received'] == True) &  # 已收款
                (orders['invoice_sent'] == False) &  # 未开发票
                (orders['paperwork'] == 0) &  # 类型为发票
                (orders['assigned_cleaner'] != '暂未派单')  # 已派单
                ]

            # 待开收据：已收款但未开收据且paperwork='1'的工单
            pending_receipt = orders[
                (orders['payment_received'] == True) &  # 已收款
                (orders['receipt_sent'] == False) &  # 未开收据
                (orders['paperwork'] == 1) &  # 类型为收据
                (orders['assigned_cleaner'] != '暂未派单')  # 已派单
                ]

            # 已完成：根据paperwork类型判断完成状态
            completed = orders[
                (orders['assigned_cleaner'] != '暂未派单') &  # 已派单
                (orders['payment_received'] == True) &  # 已收款
                (  # 根据paperwork类型判断完成状态
                        ((orders['paperwork'] == 0) & (orders['invoice_sent'] == True)) |  # 发票类型且已开发票
                        ((orders['paperwork'] == 1) & (orders['receipt_sent'] == True))  # 收据类型且已开收据
                )
                ]

            # 显示工单详情部分
            st.divider()

            # 获取每个分类的工单总数
            total_pending_assign = len(pending_assign)
            total_pending_payment = len(pending_payment)
            total_pending_invoice = len(pending_invoice)
            total_pending_receipt = len(pending_receipt)
            total_completed = len(completed)

            # 创建标签页
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                f"待派单({total_pending_assign})",
                f"待收款({total_pending_payment})",
                f"待开发票({total_pending_invoice})",
                f"待开收据({total_pending_receipt})",
                f"已完成({total_completed})"
            ])

            with tab1:
                if not pending_assign.empty:
                    display_orders(pending_assign, "pending_assign")
                else:
                    st.info("暂无待派单工单")

            with tab2:
                if not pending_payment.empty:
                    display_orders(pending_payment, "pending_payment")
                else:
                    st.info("暂无待收款工单")

            with tab3:
                if not pending_invoice.empty:
                    display_orders(pending_invoice, "pending_invoice")
                else:
                    st.info("暂无待开票工单")

            with tab4:
                if not pending_receipt.empty:
                    display_orders(pending_receipt, "pending_receipt")
                else:
                    st.info("暂无待开收据工单")

            with tab5:
                if not completed.empty:
                    display_orders(completed, "completed")
                else:
                    st.info("暂无已完成工单")

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
    work_orders()
