"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：work_orders_v2.py
@Author   ：King Songtao
@Time     ：2025/2/15 上午11:43
@Contact  ：king.songtao@gmail.com
"""
import time
import streamlit as st
from datetime import datetime, date, timedelta
from utils.utils import navigation, check_login_state
from utils.db_operations_v2 import (
    get_work_orders, get_work_orders_by_date_range,
    update_work_order, connect_db, delete_work_order
)
from utils.styles import apply_global_styles


def display_orders(orders):
    """显示工单列表"""
    for _, order in orders.iterrows():
        with st.container():
            # 工单地址和基本信息
            st.write(f"📍 工单地址：{order['work_address']}")

            col1, col2 = st.columns(2)
            with col1:
                if order['assigned_cleaner'] == '暂未派单':
                    st.write("👷 保洁小组：🔴 暂未派单")
                    st.write("📆 保洁日期：🔴 暂未确认")
                    st.write("🕒 保洁时间：🔴 暂未确认")
                else:
                    st.write(f"👷 保洁小组：{order['assigned_cleaner']}")
                    if order['work_date']:
                        st.write(f"📆 保洁日期：{order['work_date'].strftime('%Y-%m-%d')}")
                    else:
                        st.write("📆 保洁日期：暂未确认")
                    st.write(f"🕒 保洁时间：{order['work_time'] or '暂未确认'}")

            with col2:
                # 显示收入信息
                income1 = float(order['income1'] or 0)
                income2 = float(order['income2'] or 0)

                if income1 > 0:
                    st.write(f"💵 现金收入：${income1:.2f}")
                if income2 > 0:
                    st.write(f"💳 转账收入：${income2:.2f} (含GST)")
                st.write(f"💰 订单总额：${order['total_amount']:.2f}")

                # 显示补贴(如果有)
                subsidy = float(order['subsidy'] or 0)
                if subsidy > 0:
                    st.write(f"🎁 补贴金额：${subsidy:.2f}")

            # 显示其他信息
            col3, col4 = st.columns(2)
            with col3:
                st.write(f"👤 登记人员：{order['created_by']}")
                if order['source']:
                    st.write(f"📋 工单来源：{order['source']}")

            with col4:
                # 显示备注信息(如果有)
                if order['remarks']:
                    st.write(f"📝 备注信息：{order['remarks']}")

            # 操作按钮
            col1, col2 = st.columns(2)
            with col1:
                if st.button("修改工单", key=f"edit_{order['id']}", type="primary"):
                    # 将工单数据存入session state
                    st.session_state['edit_order_data'] = order.to_dict()
                    st.switch_page("pages/edit_orders.py")

            with col2:
                if st.button("删除工单", key=f"delete_{order['id']}", type="primary"):
                    st.session_state['delete_order_id'] = order['id']
                    st.session_state['delete_order_address'] = order['work_address']
                    st.rerun()

            st.divider()


@st.dialog("删除工单")
def delete_order_dialog(order_id, address):
    """删除工单确认对话框"""
    st.write(f"📍 工单地址：{address}")
    st.warning("确定要删除此工单吗？此操作不可恢复！", icon="⚠️")

    # 确认复选框
    confirm_checkbox = st.checkbox(
        "我已了解删除操作不可恢复，并确认删除此工单！",
        key=f"confirm_delete_checkbox_{order_id}"
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button(
                "确认删除",
                use_container_width=True,
                type="primary",
                disabled=not confirm_checkbox
        ):
            success, error = delete_work_order(order_id)
            if success:
                st.success("工单已删除！", icon="✅")
                # 删除session state中的数据
                if 'delete_order_id' in st.session_state:
                    del st.session_state['delete_order_id']
                if 'delete_order_address' in st.session_state:
                    del st.session_state['delete_order_address']
                time.sleep(2)
                st.rerun()
            else:
                st.error(f"删除失败：{error}", icon="⚠️")

    with col2:
        if st.button("取消", use_container_width=True):
            # 删除session state中的数据
            if 'delete_order_id' in st.session_state:
                del st.session_state['delete_order_id']
            if 'delete_order_address' in st.session_state:
                del st.session_state['delete_order_address']
            st.rerun()


def work_orders():
    """工单管理主页面"""
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
                st.switch_page("pages/new_work_order_v2.py")
        with col2:
            if st.button("工单统计", use_container_width=True, type="primary"):
                st.switch_page("pages/orders_statistics.py")
        with col3:
            if st.button("月度结算", use_container_width=True, type="primary"):
                st.switch_page("pages/monthly_review.py")

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
                    value=max(end_date, selected_start_date),
                    min_value=selected_start_date,
                    disabled=time_range[1] != "custom"
                )
            except Exception:
                selected_end_date = selected_start_date
                st.warning("结束日期不能早于开始日期，已自动调整", icon="⚠️")

        # 使用实际的日期范围获取工单
        if time_range[1] == "custom":
            if selected_end_date < selected_start_date:
                selected_end_date = selected_start_date
                st.warning("结束日期不能早于开始日期，已自动调整", icon="⚠️")

            # 在自定义模式下显示查询按钮
            if st.button("查询", use_container_width=True):
                orders, error = get_work_orders_by_date_range(selected_start_date, selected_end_date)
            else:
                return
        else:
            orders, error = get_work_orders(time_range[1])

        # 检查是否有删除请求
        if 'delete_order_id' in st.session_state and 'delete_order_address' in st.session_state:
            delete_order_dialog(
                st.session_state['delete_order_id'],
                st.session_state['delete_order_address']
            )

        # 显示工单数据
        if orders is not None and not orders.empty:
            display_orders(orders)
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
