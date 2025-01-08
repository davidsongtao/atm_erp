import time
import streamlit as st
from datetime import datetime, date, timedelta
from utils.utils import navigation, check_login_state
from utils.db_operations import get_work_orders, get_work_orders_by_date_range


def work_orders():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("🔍工单管理")
        st.divider()

        # 创建新工单按钮
        if st.button("➕创建新工单", use_container_width=True, type="primary"):
            st.switch_page("pages/new_work_order.py")

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
                index=2,
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
            # 显示日期范围
            st.info(f"查询时间范围：{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}（按保洁时间计算）", icon="📅")
            st.divider()
            for _, order in orders.iterrows():
                with st.container():
                    st.write(f"📍 工单地址： {order['work_address']}")
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        # st.write(f"📅 登记日期： {order['order_date'].strftime('%Y-%m-%d')}")
                        st.write(f"📆 保洁日期： {order['work_date'].strftime('%Y-%m-%d')}")
                        st.write(f"🕒 保洁时间： {order['work_time']}")
                        st.write(f"👷 保洁小组：{order['assigned_cleaner']}")
                    with col2:
                        st.write(f"💰 工单总额： ${order['total_amount']:.2f}")
                        st.write(f"💳 付款方式：{'转账(含GST)' if order['payment_method'] == 'transfer' else '现金'}")
                        st.write(f"👤 登记人员： {order['created_by']}")
                        # st.write(f"📝 来源：{order['source']}")
                    with col3:
                        # st.write("💡 工单状态：")
                        st.write(f"💵收款状态：{'✅' if order['payment_received'] else '❌'}")
                        st.write(f"📧发票状态：{'✅' if order['invoice_sent'] else '❌'}")
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
                        # if len(service_text) > 80:  # 如果文本太长
                        #     service_text = service_text[:90] + "..."
                        st.write(service_text)

                    col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
                    with col2:
                        if st.button("确认收款", key=f"confirm_payment_{order['id']}", use_container_width=True):
                            st.session_state.selected_order = order['id']
                            # st.switch_page("pages/order_detail.py")
                            st.warning("该功能正在开发中，敬请期待！")
                    with col3:
                        if st.button("签发发票", key=f"confirm_invoice_{order['id']}",use_container_width=True):
                            st.session_state.selected_order = order['id']
                            st.session_state.edit_mode = True
                            # st.switch_page("pages/new_work_order.py")
                            st.warning("该功能正在开发中，敬请期待！")
                    with col4:
                        if st.button("签发收据", key=f"confirm_receipt_{order['id']}",use_container_width=True):
                            st.session_state.selected_order = order['id']
                            st.session_state.edit_mode = False
                            # st.switch_page("pages/new_work_order.py")
                            st.warning("该功能正在开发中，敬请期待！")
                    with col1:
                        if st.button("阿姨派单", key=f"confirm_worker_{order['id']}",use_container_width=True):
                            st.warning("该功能正在开发中，敬请期待！")
                st.divider()
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
    work_orders()
