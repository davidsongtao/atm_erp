"""
Description: 工单编辑页面

-*- Encoding: UTF-8 -*-
@File     ：edit_order.py
@Author   ：King Songtao
@Time     ：2025/1/8
@Contact  ：king.songtao@gmail.com
"""
import time
import asyncio
import streamlit as st
from datetime import datetime

from pages.new_work_order import handle_custom_items
from utils.utils import navigation, check_login_state
from utils.validator import get_validator
from utils.db_operations import update_work_order, update_payment_status, update_receipt_status
from utils.db_operations import update_invoice_status, update_cleaning_status
from utils.styles import apply_global_styles


async def edit_work_order_page():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("✏️ 修改工单")
        st.divider()

        # 检查是否有工单数据
        if 'edit_order_data' not in st.session_state:
            st.error("未找到要修改的工单数据！")
            if st.button("返回工单列表", use_container_width=True):
                st.switch_page("pages/work_orders.py")
            return

        order_data = st.session_state['edit_order_data']

        # 重要：在页面初始化时，根据当前工单ID重置custom_items
        current_order_id = order_data['id']
        if 'current_editing_order_id' not in st.session_state or st.session_state.current_editing_order_id != current_order_id:
            # 如果是新的工单，重置custom_items
            if 'custom_items' in st.session_state:
                del st.session_state.custom_items
            st.session_state.current_editing_order_id = current_order_id

        # 初始化验证器相关的session state
        if 'validator' not in st.session_state:
            api_key = st.secrets["api_keys"]["openai_api_key"]
            st.session_state.validator = get_validator(api_key)

        # 基础信息
        col1, col2 = st.columns(2)
        with col1:
            order_date = st.date_input(
                "登记日期",
                value=datetime.strptime(order_data['order_date'], '%Y-%m-%d').date()
                if isinstance(order_data['order_date'], str)
                else order_data['order_date'],
                disabled=True
            )

        with col2:
            current_user = order_data['created_by']
            st.text_input("工单所有人", value=current_user, disabled=True)

        source = st.text_input("工单来源", value=order_data['source'])

        # 修改地址输入部分
        work_address = st.text_input(
            "工作地址",
            value=order_data['work_address'],
            key="address_input",
            placeholder="客户地址。例如：1202/157 A'Beckett St, Melbourne VIC 3000",
            help="请输入地址以开始验证"
        )

        st.divider()

        # 户型选择
        room_types = ["1b1b", "2b1b", "2b2b", "3b2b"]
        current_room_type = room_types.index(order_data['room_type']) if order_data['room_type'] in room_types else None
        room_type = st.selectbox(
            "清洁房间户型",
            options=room_types,
            index=current_room_type,
            placeholder="请选择房间户型",
        )

        # 服务选项
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

        # 修改服务数据的处理逻辑
        current_basic_services = order_data.get('basic_service', [])
        if isinstance(current_basic_services, str):
            current_basic_services = current_basic_services.split('|') if current_basic_services else []

        current_room_services = order_data.get('rooms', [])
        if isinstance(current_room_services, str):
            current_room_services = current_room_services.split('|') if current_room_services else []

        current_electrical_services = order_data.get('electricals', [])
        if isinstance(current_electrical_services, str):
            current_electrical_services = current_electrical_services.split('|') if current_electrical_services else []

        current_other_services = order_data.get('other_services', [])
        if isinstance(current_other_services, str):
            current_other_services = current_other_services.split('|') if current_other_services else []

        # 服务选项的显示部分
        col1, col2 = st.columns(2)
        with col1:
            basic_services = st.multiselect(
                "基础服务",
                options=service_options["basic_service"],
                default=current_basic_services,
                placeholder="选择基础服务项目..."
            )

            electrical_services = st.multiselect(
                "电器服务",
                options=service_options["electricals"],
                default=current_electrical_services,
                placeholder="选择电器服务项目..."
            )

        with col2:
            room_services = st.multiselect(
                "房间服务",
                options=service_options["rooms"],
                default=current_room_services,
                placeholder="选择房间服务项目..."
            )

            other_services = st.multiselect(
                "其他服务",
                options=service_options["other_services"],
                default=current_other_services,
                placeholder="选择其他服务项目..."
            )

        # 自定义服务项目处理
        custom_items = order_data.get('custom_items', [])
        if isinstance(custom_items, str):
            custom_items = custom_items.split('|') if custom_items else []

        custom_service = st.checkbox(
            "添加自定义服务项目",
            value=bool(custom_items)
        )

        if custom_service:
            # 初始化自定义项目的session state
            if 'custom_items' not in st.session_state:
                st.session_state.custom_items = custom_items if custom_items else [""]

            custom_item = handle_custom_items()
        else:
            custom_item = []
            if 'custom_items' in st.session_state:
                del st.session_state.custom_items

        # 付款信息
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            payment_method = st.selectbox(
                "付款方式",
                options=["transfer", "cash"],
                format_func=lambda x: "转账(+10% GST)" if x == "transfer" else "现金",
                index=0 if order_data['payment_method'] == "transfer" else 1,
                placeholder="请选择付款方式..."
            )
        with col2:
            order_amount = st.number_input(
                "工单金额",
                min_value=0.0,
                value=float(order_data['total_amount']),
                format="%.2f"
            )
        with col3:
            paperwork = st.selectbox(
                "开票方式",
                options=[0, 1],
                format_func=lambda x: "开发票" if x == 0 else "开收据",
                help="选择开具发票或收据",
                index=0 if order_data['paperwork'] == 0 else 1
            )

        # 自动计算总金额
        total_amount = order_amount * 1.1 if payment_method == "transfer" else order_amount
        st.success(f"工单总金额：${total_amount:.2f} ({'含 GST' if payment_method == 'transfer' else '不含 GST'})")
        st.divider()

        # 备注信息
        remarks = st.text_area(
            "备注信息",
            value=order_data.get('remarks', ''),
            placeholder="请输入备注信息(选填)"
        )

        # 确认更新
        confirm_update = st.checkbox("我确认所有修改信息无误，立即更新工单！")

        update_btn = st.button("更新工单", use_container_width=True, type="primary")

        if st.button("取消", use_container_width=True):
            # 清除所有相关的session state
            for key in ['edit_order_data', 'custom_items', 'current_editing_order_id']:
                if key in st.session_state:
                    del st.session_state[key]
            st.switch_page("pages/work_orders.py")

        # 更新按钮处理
        if update_btn and confirm_update:
            if not all([
                source,
                work_address,
                order_amount > 0,
                room_type,
                payment_method is not None,
                paperwork is not None
            ]):
                st.error("请填写所有必填项！", icon="⚠️")
            else:
                # 更新工单信息
                updated_data = {
                    'id': order_data['id'],
                    'source': source,
                    'work_address': work_address,
                    'room_type': room_type,
                    'payment_method': payment_method,
                    'total_amount': total_amount,
                    'remarks': remarks,
                    'basic_service': '|'.join(basic_services) if basic_services else None,
                    'rooms': '|'.join(room_services) if room_services else None,
                    'electricals': '|'.join(electrical_services) if electrical_services else None,
                    'other_services': '|'.join(other_services) if other_services else None,
                    'custom_item': '|'.join([item for item in custom_item if item.strip()]) if custom_item else None,
                    'paperwork': paperwork
                }

                success, error = update_work_order(updated_data)

                if success:
                    # 清除所有相关的session state
                    for key in ['edit_order_data', 'custom_items', 'current_editing_order_id']:
                        if key in st.session_state:
                            del st.session_state[key]

                    st.success("工单更新成功！3秒后返回工单列表...", icon="✅")
                    time.sleep(3)
                    st.switch_page("pages/work_orders.py")
                else:
                    st.error(f"工单更新失败：{error}", icon="⚠️")
        elif update_btn and not confirm_update:
            st.warning("请确认修改信息无误，并勾选确认按钮！", icon="⚠️")

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
    asyncio.run(edit_work_order_page())
