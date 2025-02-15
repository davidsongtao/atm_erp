"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：edit_orders_v2.py
@Author   ：King Songtao
@Time     ：2025/2/15 上午11:44
@Contact  ：king.songtao@gmail.com
"""
import time
import streamlit as st
from datetime import datetime, date
from utils.utils import navigation, check_login_state
from utils.db_operations_v2 import update_work_order, connect_db
from utils.styles import apply_global_styles


def edit_order():
    """编辑工单页面"""
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("✏️ 修改工单")
        st.divider()

        # 检查是否有工单数据
        if 'edit_order_data' not in st.session_state:
            st.error("未找到要编辑的工单！", icon="⚠️")
            time.sleep(2)
            st.switch_page("pages/orders_statistics.py")
            return

        order_data = st.session_state['edit_order_data']

        # 基础信息
        col1, col2, col3 = st.columns(3)
        with col1:
            work_date = st.date_input(
                "保洁日期",
                value=order_data['work_date'] if order_data['work_date'] else None,
                min_value=date(2020, 1, 1),
                help="实际上门服务的日期（可选）"
            )

        with col2:
            # 生成时间选项列表
            time_options = []
            for hour in range(6, 22):
                for minute in range(0, 60, 15):
                    period = "上午" if hour < 12 else "下午"
                    time_str = f"{period} {hour:02d}:{minute:02d}"
                    time_options.append(time_str)

            current_time = order_data['work_time'] if order_data['work_time'] else ""
            work_time = st.selectbox(
                "保洁时间",
                options=[""] + time_options,
                index=time_options.index(current_time) + 1 if current_time in time_options else 0,
                help="选择保洁时间（可选）"
            )

        with col3:
            # 获取所有活跃的保洁组
            conn = connect_db()
            cleaner_options = ["暂未派单"] + conn.query("""
                SELECT team_name
                FROM clean_teams
                WHERE team_name != '暂未派单' AND is_active = 1
                ORDER BY team_name
            """, ttl=0)['team_name'].tolist()

            current_cleaner = order_data['assigned_cleaner']
            cleaner_index = cleaner_options.index(current_cleaner) if current_cleaner in cleaner_options else 0

            assigned_cleaner = st.selectbox(
                "保洁小组",
                options=cleaner_options,
                index=cleaner_index,
                help="选择保洁小组（可选）"
            )

        # 地址和来源信息
        col1, col2 = st.columns(2)
        with col1:
            work_address = st.text_input(
                "工作地址",
                value=order_data['work_address'],
                help="客户地址"
            )

        with col2:
            source = st.text_input(
                "工单来源",
                value=order_data['source'] if order_data['source'] else "",
                help="客户来源信息（可选）"
            )

        # 收入信息
        col1, col2, col3 = st.columns(3)
        with col1:
            income1 = st.number_input(
                "收入1（现金）",
                min_value=0.0,
                value=float(order_data['income1'] or 0),
                format="%.2f",
                help="现金收入金额"
            )

        with col2:
            income2 = st.number_input(
                "收入2（转账）",
                min_value=0.0,
                value=float(order_data['income2'] or 0),
                format="%.2f",
                help="转账收入金额（不含GST）"
            )

        with col3:
            subsidy = st.number_input(
                "补贴金额",
                min_value=0.0,
                value=float(order_data['subsidy'] or 0),
                format="%.2f",
                help="工单补贴金额（可选）"
            )

        # 显示自动计算的总金额
        col1, col2 = st.columns(2)
        with col1:
            order_amount = income1 + income2
            st.info(f"订单金额：${order_amount:.2f}", icon="💰")
        with col2:
            total_amount = income1 + (income2 * 1.1)  # 转账收入加10% GST
            st.info(f"总金额(含GST)：${total_amount:.2f}", icon="💰")

        # 备注信息
        remarks = st.text_area(
            "备注信息",
            value=order_data['remarks'] if order_data['remarks'] else "",
            placeholder="请输入备注信息（可选）"
        )

        # 确认和取消按钮
        col1, col2 = st.columns(2)
        with col1:
            confirm = st.checkbox("我已确认所有信息无误，确认修改！")

            if st.button(
                    "确认修改",
                    use_container_width=True,
                    type="primary",
                    disabled=not confirm
            ):
                # 收集更新数据
                update_data = {
                    'id': order_data['id'],
                    'work_date': work_date if work_date else None,
                    'work_time': work_time if work_time else None,
                    'assigned_cleaner': assigned_cleaner,
                    'work_address': work_address,
                    'source': source if source.strip() else None,
                    'income1': income1,
                    'income2': income2,
                    'subsidy': subsidy if subsidy > 0 else None,
                    'remarks': remarks if remarks.strip() else None
                }

                # 更新工单
                success, error = update_work_order(update_data)
                if success:
                    st.success("工单修改成功！", icon="✅")
                    # 清除session state中的编辑数据
                    if 'edit_order_data' in st.session_state:
                        del st.session_state['edit_order_data']
                    time.sleep(2)
                    st.switch_page("pages/orders_statistics.py")
                else:
                    st.error(f"修改失败：{error}", icon="⚠️")

        with col2:
            if st.button("取消", use_container_width=True):
                # 清除session state中的编辑数据
                if 'edit_order_data' in st.session_state:
                    del st.session_state['edit_order_data']
                st.switch_page("pages/orders_statistics.py")

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
    edit_order()
