"""
Description: 工单管理页面

-*- Encoding: UTF-8 -*-
@File     ：work_orders.py
@Author   ：King Songtao
@Time     ：2025/1/8
@Contact  ：king.songtao@gmail.com
"""

import time
import streamlit as st
from datetime import datetime, date, timedelta
from utils.utils import navigation, check_login_state
from utils.db_operations import get_work_orders, get_work_orders_by_date_range
import pandas as pd
from utils.styles import apply_global_styles


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
                    st.markdown(f"👷 保洁小组：<span style='color:red;background-color:#ffecec;padding:2px 6px;border-radius:3px;font-weight:bold;'>暂未确认</span>", unsafe_allow_html=True)
                    st.markdown(f"📆 保洁日期：<span style='color:red;background-color:#ffecec;padding:2px 6px;border-radius:3px;font-weight:bold;'>暂未确认</span>", unsafe_allow_html=True)
                    st.markdown(f"🕒 保洁时间：<span style='color:red;background-color:#ffecec;padding:2px 6px;border-radius:3px;font-weight:bold;'>暂未派单</span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"👷 保洁小组：<span style='color:green;background-color:#ecffec;padding:2px 6px;border-radius:3px;font-weight:bold;'>{order['assigned_cleaner']}</span>", unsafe_allow_html=True)
                    st.markdown(f"📆 保洁日期：<span style='color:green;background-color:#ecffec;padding:2px 6px;border-radius:3px;font-weight:bold;'>{order['work_date'].strftime('%Y-%m-%d')}</span>", unsafe_allow_html=True)
                    st.markdown(f"🕒 保洁时间：<span style='color:green;background-color:#ecffec;padding:2px 6px;border-radius:3px;font-weight:bold;'>{order['work_time']}</span>", unsafe_allow_html=True)
            with col2:
                # 根据收款状态决定高亮颜色
                if order['payment_received']:
                    # 已收款 - 绿色主题
                    st.markdown(f"💰 工单总额：<span style='color:green;background-color:#ecffec;padding:2px 6px;border-radius:3px;font-weight:bold;'>${order['total_amount']:.2f}</span>", unsafe_allow_html=True)
                    if order['payment_method'] == 'transfer':
                        st.markdown(f"💳 付款方式：<span style='color:green;background-color:#ecffec;padding:2px 6px;border-radius:3px;font-weight:bold;'>转账(含GST)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"💳 付款方式：<span style='color:green;background-color:#ecffec;padding:2px 6px;border-radius:3px;font-weight:bold;'>现金</span>", unsafe_allow_html=True)
                else:
                    # 未收款 - 红色主题
                    st.markdown(f"💰 工单总额：<span style='color:red;background-color:#ffecec;padding:2px 6px;border-radius:3px;font-weight:bold;'>${order['total_amount']:.2f}</span>", unsafe_allow_html=True)
                    if order['payment_method'] == 'transfer':
                        st.markdown(f"💳 付款方式：<span style='color:red;background-color:#ffecec;padding:2px 6px;border-radius:3px;font-weight:bold;'>转账(含GST)</span>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"💳 付款方式：<span style='color:red;background-color:#ffecec;padding:2px 6px;border-radius:3px;font-weight:bold;'>现金</span>", unsafe_allow_html=True)
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
                        st.warning("该功能正在开发中，敬请期待！")
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
                        st.warning("该功能正在开发中，敬请期待！")
                with col3:
                    # 根据paperwork值显示对应按钮 (1=receipt, 0=invoice)
                    if order['paperwork'] == 0:  # 使用字符串比较
                        is_invoice_sent = order['invoice_sent']
                        if st.button(
                                "签发发票",
                                key=f"{tab_name}_confirm_invoice_{order['id']}",
                                use_container_width=True,
                                disabled=is_invoice_sent,
                                help="此工单已签发发票" if is_invoice_sent else "点击签发发票",
                                type="primary"
                        ):
                            st.warning("该功能正在开发中，敬请期待！")
                    else:  # paperwork == '1'
                        is_receipt_sent = order['receipt_sent']
                        if st.button(
                                "签发收据",
                                key=f"{tab_name}_confirm_receipt_{order['id']}",
                                use_container_width=True,
                                disabled=is_receipt_sent,
                                help="此工单已签发收据" if is_receipt_sent else "点击签发收据",
                                type="primary"
                        ):
                            st.warning("该功能正在开发中，敬请期待！")
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

        st.markdown("""
        <style>
        	.stTabs [data-baseweb="tab-list"] {
        		gap: 2px;
            }
        	.stTabs [data-baseweb="tab"] {
        		height: 50px;
        		background-color: #F0F2F6;
        		border-radius: 0px 0px 0px 0px;
        		padding-left: 15px;
        		padding-right: 15px;
            }
        	.stTabs [aria-selected="true"] {
          		background-color: #FF4B4B;
          		color: #FFFFFF
        	}
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
                (orders['paperwork'] == 0)  # 类型为发票
                ]

            # 待开收据：已收款但未开收据且paperwork='1'的工单
            pending_receipt = orders[
                (orders['payment_received'] == True) &  # 已收款
                (orders['receipt_sent'] == False) &  # 未开收据
                (orders['paperwork'] == 1)  # 类型为收据,使用字符串 '1'
                ]

            # 已完成：根据paperwork类型判断完成状态
            completed = orders[
                (orders['payment_received'] == True) &
                (
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
