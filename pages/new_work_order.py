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
from utils.styles import apply_global_styles


def handle_custom_items():
    """处理自定义项目的添加和删除"""
    # 添加自定义 CSS 来隐藏特定文本输入框的标签
    st.markdown("""
        <style>
            /* 隐藏所有自定义项目的label */
            .custom-item-input label {
                display: none !important;
                height: 0px !important;
                margin: 0px !important;
                padding: 0px !important;
            }
            /* 移除label占用的空间 */
            .custom-item-input .st-emotion-cache-1umgz6j {
                margin-top: 0px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 初始化或更新 session state
    if 'custom_items' not in st.session_state:
        st.session_state.custom_items = [""]

    # 添加新项目的按钮
    if st.button("新增一个自定义项", use_container_width=True):
        st.session_state.custom_items.append("")
        st.rerun()

    # 创建输入字段
    updated_items = []
    for idx, item in enumerate(st.session_state.custom_items):
        col1, col2 = st.columns([5, 1])

        with col1:
            new_value = st.text_input(
                " ",  # 使用空格作为label而不是空字符串
                value=item,
                key=f"custom_item_{idx}",
                placeholder=f"请输入第{idx + 1}个自定义项目内容...",
                label_visibility="collapsed",  # 这里添加了 label_visibility="collapsed"
            )
            updated_items.append(new_value)

        with col2:
            if st.button("删除", key=f"delete_custom_{idx}", use_container_width=True):
                st.session_state.custom_items.pop(idx)
                st.rerun()

    st.session_state.custom_items = updated_items
    return updated_items


async def create_work_order_page():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("➕创建新工单")
        st.divider()

        # 初始化验证器相关的session state
        # 修改验证器初始化部分
        if 'validator' not in st.session_state:
            api_key = st.secrets["api_keys"]["openai_api_key"]
            st.session_state.validator = get_validator(api_key)

        # 初始化时间选择相关的session state
        if 'am_pm' not in st.session_state:
            st.session_state.am_pm = "AM"
        if 'hour' not in st.session_state:
            st.session_state.hour = "09:00"

        # 基础信息
        col1, col2 = st.columns(2)
        with col1:
            order_date = st.date_input(
                "登记日期",
                value=date.today(),
                help="创建工单的日期",
                disabled=True
            )
            # work_date = st.date_input(
            #     "工作日期",
            #     value=date.today(),
            #     help="实际上门服务的日期",
            #     min_value=date.today()
            # )

        with col2:
            # 分配人（自动获取当前登录用户的name）
            current_username = st.session_state.get("logged_in_username")
            current_user = st.session_state.get("name")  # 使用session中存储的name
            st.text_input("工单所有人", value=current_user, disabled=True)
        source = st.text_input("工单来源", placeholder="请输入客户来源")

        # 修改地址输入部分
        work_address = st.text_input(
            "工作地址",
            value=st.session_state.get("current_address", ""),
            key="address_input",
            placeholder="客户地址。例如：1202/157 A'Beckett St, Melbourne VIC 3000",
            help="请输入地址以开始验证"
        )

        # 检查地址是否为空
        is_address_empty = not work_address.strip()

        # 验证按钮 - 当地址为空时禁用
        validate_btn = st.button(
            "自动化验证地址",
            use_container_width=True,
            key="validate-address-btn",
            type="primary",
            disabled=is_address_empty,
        )

        # Google搜索按钮 - 当地址为空时禁用
        search_query = work_address.replace(' ', '+')
        search_url = f"https://www.google.com/search?q={search_query}+Australia"
        st.link_button(
            "🔍 在Google中搜索此地址",
            search_url,
            use_container_width=True,
            disabled=is_address_empty
        )

        # 修改地址验证处理部分
        address_valid = True
        if validate_btn and work_address.strip():
            try:
                with st.spinner("验证地址中，请勿进行其他操作。地址验证有可能耗时较长，请耐心等待..."):
                    matches = await st.session_state.validator.validate_address(work_address)

                    if matches:
                        # 根据验证来源显示不同的提示
                        if matches[0].validation_source == 'llm':
                            st.success("✅ 找到以下地址匹配：")
                        elif matches[0].validation_source == 'fallback':
                            st.warning("ℹ️ DeepSeek API暂时不可用，当前使用本地验证模式，请仔细核对地址：")
                        else:
                            st.warning("⚠️ 无法完全验证地址，请确保地址准确：")

                        # 显示匹配结果
                        for i, match in enumerate(matches):
                            col1, col2, col3 = st.columns([6, 2, 1])
                            with col1:
                                st.write(f"🏠 {match.formatted_address}")
                            with col2:
                                st.write(f"匹配度: {match.confidence_score:.2f}")
                            with col3:
                                # 使用回调函数处理选择
                                def select_address():
                                    st.session_state.current_address = match.formatted_address

                                st.button(
                                    "选择",
                                    key=f"select_{i}",
                                    on_click=select_address,
                                    use_container_width=True,
                                    type="primary"
                                )

                        # 如果是LLM验证失败或本地验证，显示Google搜索选项
                        if matches[0].validation_source != 'llm':
                            st.info("如果不确定地址是否正确，建议在Google中搜索确认：", icon="ℹ️")
                            search_query = work_address.replace(' ', '+')
                            search_url = f"https://www.google.com/search?q={search_query}+Australia"
                            st.link_button(
                                "🔍 在Google中搜索此地址",
                                search_url,
                                use_container_width=True,
                                type="primary"
                            )
                    else:
                        st.warning("⚠️ 无法验证此地址，请检查输入是否正确。")
                        st.info("您可以：\n1. 检查地址拼写\n2. 确保包含门牌号和街道名\n3. 添加州名和邮编")
                        address_valid = False

            except Exception:
                st.error("地址验证服务暂时不可用")
                st.info("您可以继续填写其他信息，稍后再尝试验证地址。")
                address_valid = True  # 允许用户继续，但显示警告
            finally:
                await st.session_state.validator.close_session()

        st.divider()

        room_type = st.selectbox(
            "清洁房间户型",
            options=["1b1b", "2b1b", "2b2b", "3b2b"],
            index=None,
            placeholder="请选择房间户型",
        )

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
        # st.markdown("""
        #         <style>
        #             /* 隐藏所有自定义项目的label */
        #             div[data-testid="stTextInput"] > label {
        #                 display: none !important;
        #                 height: 0px !important;
        #                 margin: 0px !important;
        #                 padding: 0px !important;
        #             }
        #             /* 移除label占用的空间 */
        #             div[data-testid="stTextInput"] > .st-emotion-cache-1umgz6j {
        #                 margin-top: 0px !important;
        #             }
        #         </style>
        #     """, unsafe_allow_html=True)
        custom_service = st.checkbox("添加自定义服务项目")
        if custom_service:
            custom_item = handle_custom_items()
        else:
            custom_item = []

        # 在付款信息部分添加开票选择
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            payment_method = st.selectbox(
                "付款方式",
                options=["transfer", "cash"],
                format_func=lambda x: "转账(+10% GST)" if x == "transfer" else "现金",
                index=None,
                placeholder="请选择付款方式..."
            )
        with col2:
            order_amount = st.number_input(
                "工单金额",
                min_value=0.0,
                format="%.2f"
            )
        with col3:
            # 添加开票方式选择
            paperwork = st.selectbox(
                "开票方式",
                options=[0, 1],
                format_func=lambda x: "开发票" if x == 0 else "开收据",
                help="选择开具发票或收据",
                index=None,
                placeholder="请选择开票方式..."
            )

        # 自动计算总金额
        total_amount = order_amount * 1.1 if payment_method == "transfer" else order_amount
        st.success(f"工单总金额：${total_amount:.2f} ({'含 GST' if payment_method == 'transfer' else '不含 GST'})")
        st.divider()

        remarks = st.text_area(
            "备注信息",
            placeholder="请输入备注信息(选填)"
        )

        confirm_create = st.checkbox("我确认所有工单信息录入无误，立即创建工单！")
        create_btn = st.button("创建工单", use_container_width=True, type="primary")

        # 确认和取消按钮
        if create_btn and confirm_create:
            if not all([
                # ... 其他验证条件
            ]):
                st.error("请填写所有必填项！", icon="⚠️")
            else:
                success, error = create_work_order(
                    order_date=order_date,
                    created_by=current_user,
                    source=source,
                    work_address=st.session_state.get("current_address", ""),
                    room_type=room_type,  # 新增房间户型参数
                    payment_method=payment_method,
                    order_amount=order_amount,
                    remarks=remarks,  # 新增备注参数
                    basic_service=basic_services,
                    rooms=room_services,
                    electricals=electrical_services,
                    other_services=other_services,
                    paperwork=paperwork,
                    custom_item=custom_item  # 将自定义项目传递给create_work_order函数
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
