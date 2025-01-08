"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：new_work_order.py
@Author   ：King Songtao
@Time     ：2025/1/8 下午5:42
@Contact  ：king.songtao@gmail.com
"""
import time
import asyncio
import streamlit as st
from datetime import datetime, date
from utils.utils import navigation, check_login_state
from utils.validator import get_validator
from utils.db_operations import create_work_order


async def create_work_order_page():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("➕创建新工单")
        st.divider()

        # 初始化验证器相关的session state
        if 'validator' not in st.session_state:
            st.session_state.validator = get_validator(
                st.secrets.get("HERE_API_KEY"),
                st.secrets.get("DEEPSEEK_API_KEY")
            )

        if "should_validate" not in st.session_state:
            st.session_state.should_validate = False

        if "work_address" not in st.session_state:
            st.session_state.work_address = ""

        # 初始化时间选择相关的session state
        if 'am_pm' not in st.session_state:
            st.session_state.am_pm = "AM"
        if 'hour' not in st.session_state:
            st.session_state.hour = "09:00"

        # 基础信息
        st.info("请完善工单基础信息", icon="📝")
        col1, col2 = st.columns(2)
        with col1:
            order_date = st.date_input(
                "登记日期",
                value=date.today(),
                help="创建工单的日期",
                disabled=True
            )
            work_date = st.date_input(
                "工作日期",
                value=date.today(),
                help="实际上门服务的日期",
                min_value=date.today()
            )

        with col2:
            # 分配人（自动获取当前登录用户）
            current_user = st.session_state.get("logged_in_username")
            st.text_input("工单所有人", value=current_user, disabled=True)
            source = st.text_input("工单来源", placeholder="请输入客户来源")

        # 工作时间选择放在新的一行
        time_col1, time_col2 = st.columns(2)
        with time_col1:
            am_pm = st.selectbox(
                "时间段",
                options=["AM", "PM"],
                key="am_pm",
                index=None,
                placeholder="选择时间段...",
            )
        with time_col2:
            if am_pm == "AM":
                hour_options = [f"{i:02d}:00" for i in range(7, 13)]  # AM 7:00-12:00
            else:
                hour_options = [f"{i:02d}:00" for i in range(12, 19)]  # PM 12:00-18:00

            hour = st.selectbox(
                "具体时间",
                options=hour_options,
                key="hour",
                index=None,
                placeholder="请选择具体时间...",
            )

        work_time = f"{am_pm} {hour}"

        # 地址信息部分
        st.info("请输入客户地址，系统会自动验证地址是否正确。", icon="📍")

        def on_address_change():
            st.session_state.should_validate = True

        def select_address(match):
            st.session_state.work_address = match.formatted_address
            st.session_state.should_validate = False

        work_address = st.text_input(
            "工作地址",
            key="work_address",
            on_change=on_address_change,
            placeholder="客户地址。例如：1202/157 A'Beckett St, Melbourne VIC 3000"
        )

        # 处理地址验证
        address_valid = True
        if st.session_state.should_validate and work_address.strip():
            try:
                with st.spinner("验证地址中..."):
                    matches = await st.session_state.validator.validate_address(work_address)
                    st.session_state.should_validate = False

                    if matches:
                        # 使用字典去重，以格式化地址作为键
                        unique_matches = {}
                        for match in matches:
                            if match.formatted_address not in unique_matches or \
                                    match.confidence_score > unique_matches[match.formatted_address].confidence_score:
                                unique_matches[match.formatted_address] = match

                        # 转换回列表并按置信度排序
                        unique_matches = sorted(
                            unique_matches.values(),
                            key=lambda x: x.confidence_score,
                            reverse=True
                        )
                        st.success("找到以下可能的地址匹配,请从列表中选择准确的地址：", icon="✅")

                        for i, match in enumerate(unique_matches):
                            with st.container():
                                col1, col2, col3 = st.columns([6, 2, 1])
                                with col1:
                                    st.write(f"🏠 {match.formatted_address}")
                                with col2:
                                    st.write(f"匹配度: {match.confidence_score:.2f}")
                                with col3:
                                    if st.button("选择", key=f"select_{i}", on_click=select_address, args=(match,)):
                                        st.rerun()
                        st.info("如果您不确定以上哪个是正确地址，请在google中搜索查看！", icon="ℹ️")

                        # 创建Google搜索URL
                        search_query = work_address.replace(' ', '+')
                        search_url = f"https://www.google.com/search?q={search_query}+Australia"

                        st.link_button(
                            "🔍 在Google Search中搜索",
                            search_url,
                            use_container_width=True
                        )

                        st.divider()
                    else:
                        st.warning("未找到匹配的地址，请检查输入后重试。")
                        address_valid = False
            finally:
                await st.session_state.validator.close_session()

        st.divider()

        # 服务选择部分
        st.info("请选择需要服务的项目。", icon="🛠️")

        service_options = {
            "basic_service": ["Steam clean of the carpet", "Steam clean of the mattress",
                              "Steam clean of the sofa", "Vacuum clean of carpet",
                              "Floor boards/Floor tiles mopping"],
            "rooms": ["Bedroom", "Bathroom", "Kitchen"],
            "electricals": ["Microwave", "Oven", "Dishwasher", "Refrigerator",
                            "Washing machine", "Dryer", "Air conditioner"],
            "other_services": ["Skirting board/Window frame/Wardrobe", "Blinds", "Window glasses",
                               "Balcony with sliding door windows", "Wall marks removal",
                               "Furniture wipe off", "Pet hair removal", "Rubbish removal",
                               "Mould removal"]
        }

        col1, col2 = st.columns(2)
        with col1:
            basic_services = st.multiselect(
                "基础服务",
                options=service_options["basic_service"],
                placeholder="选择基础服务项目..."
            )

            electrical_services = st.multiselect(
                "电器服务",
                options=service_options["electricals"],
                placeholder="选择电器服务项目..."
            )

        with col2:
            room_services = st.multiselect(
                "房间服务",
                options=service_options["rooms"],
                placeholder="选择房间服务项目..."
            )

            other_services = st.multiselect(
                "其他服务",
                options=service_options["other_services"],
                placeholder="选择其他服务项目..."
            )

        # 自定义服务项目
        custom_service = st.checkbox("添加自定义服务项目")
        if custom_service:
            custom_item = st.text_area(
                "自定义服务内容",
                placeholder="请输入自定义服务内容，每行一项...",
                help="多个项目请用换行分隔"
            ).split('\n')
            # 过滤掉空行
            custom_item = [item.strip() for item in custom_item if item.strip()]
        else:
            custom_item = []

        # 付款信息部分
        st.info("请完善付款方式和工单金额。", icon="💰")
        col1, col2 = st.columns(2)
        with col1:
            payment_method = st.selectbox(
                "付款方式",
                options=["transfer", "cash"],
                format_func=lambda x: "转账(+10% GST)" if x == "transfer" else "现金"
            )
        with col2:
            order_amount = st.number_input(
                "工单金额",
                min_value=0.0,
                format="%.2f"
            )

        # 自动计算总金额
        total_amount = order_amount * 1.1 if payment_method == "transfer" else order_amount
        st.success(f"工单总金额：${total_amount:.2f} ({'含 GST' if payment_method == 'transfer' else '不含 GST'})")

        confirm_create = st.checkbox("我确认工单总金额无误，立即创建工单！")
        create_btn = st.button("创建工单", use_container_width=True, type="primary")
        # 确认和取消按钮
        if create_btn and confirm_create:
            if not all([source, work_address, order_amount > 0, address_valid]):
                st.error("请填写所有必填项！", icon="⚠️")
            elif not any([basic_services, room_services, electrical_services, other_services, custom_item]):
                st.error("请至少选择一项服务！", icon="⚠️")
            else:
                success, error = create_work_order(
                    order_date=order_date,
                    work_date=work_date,
                    created_by=current_user,
                    source=source,
                    work_time=work_time,
                    work_address=work_address,
                    payment_method=payment_method,
                    order_amount=order_amount,
                    basic_service=basic_services,
                    rooms=room_services,
                    electricals=electrical_services,
                    other_services=other_services,
                    custom_item=custom_item
                )

                if success:
                    st.success("工单创建成功！3秒后返回工单列表...", icon="✅")
                    time.sleep(3)
                    st.switch_page("pages/work_orders.py")
                else:
                    st.error(f"工单创建失败：{error}", icon="⚠️")
        elif create_btn and not confirm_create:
            st.warning("请确认工单总金额无误，并勾选确认按钮！", icon="⚠️")

        if st.button("取消", use_container_width=True, type="secondary"):
            st.switch_page("pages/work_orders.py")

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
    asyncio.run(create_work_order_page())
