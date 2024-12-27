"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：receipt_page.py.py
@Author   ：King Songtao
@Time     ：2024/12/27 上午12:55
@Contact  ：king.songtao@gmail.com
"""
import time
from datetime import date
import streamlit as st
from docx import Document
from utils.utils import check_login_state, log_out, validate_address


def receipt_page():
    """
    客户服务界面
    :return:
    """
    login_state, role = check_login_state()

    if login_state:
        st.title("🧾收据自动化生成")
        st.divider()
        if role == "admin":
            # 收据自动生成逻辑代码
            st.session_state['receipt_data'] = {
                "selected_template": "",
                "address": "",
                "selected_date": "",
                "amount": "",
                "basic_service": [],
                "electrical": [],
                "rooms": [],
                "other": [],
                "custom_notes": "",
                "output_doc": None,
                "receipt_file_name": ""
            }

            selected_template = st.selectbox('选择收据模板', ["完整版（带exclude模块）", "精简版（不带exclude模块）"], placeholder="请选择收据模板", index=None)
            # 构建选项
            basic_service = ["Steam clean of the carpet", "Steam clean of the mattress", "Steam clean of the sofa", "Vacuum clean of carpet", "Floor boards/Floor tiles mopping"]
            rooms = ["Bedroom", "Bathroom", "Kitchen"]
            electrical = ["Microwave", "Oven", "Dishwasher", "Refrigerator", "Washing machine", "Dryer", "Air conditioner"]
            others = ["Skirting board/Window frame/Wardrobe", "Blinds", "Window glasses", "Balcony with sliding door windows", "Wall marks removal", "Pet hair removal", "Rubbish removal", "Mould removal"]
            # 输入区域
            address = st.text_input('客户地址', placeholder="例如：1202/157 A'Beckett St, Melbourne VIC 3000")  # 输入地址
            address_valid = True  # 地址验证标志
            if address:
                is_valid, error_message = validate_address(address)
                if not is_valid:
                    st.error(error_message)
                    address_valid = False
                else:
                    address_valid = True

            col1, col2 = st.columns(2)
            with col1:
                selected_date = st.date_input('收据日期', date.today())
                basic_service_selection = st.multiselect('基础服务（多选）', basic_service, placeholder="请选择基础服务...")
                electrical_selections = st.multiselect('电器服务（多选）', electrical, placeholder="请选择电器服务...")
            with col2:
                amount = st.number_input('收据金额', min_value=0.0, step=1.0, format='%f')
                rooms_selection = st.multiselect('房间（多选）', rooms, placeholder="请选择房间...")
                other_selection = st.multiselect('其他服务（多选）', others, placeholder="请输入其他服务...")
            custom_notes = st.checkbox("我希望添加自定义项目", value=False)
            if custom_notes:
                custom_notes_content = st.text_input("自定义项目", placeholder="请填写自定义项目内容...")
            else:
                custom_notes_content = ""
            st.info("请仔细核对以上信息，确认无误后点击生成收据即可查看发票预览。", icon="ℹ️")
            submit = st.button("✅生成收据", use_container_width=True, type="primary")

            if submit:
                if selected_template and address_valid and address and selected_date and amount and basic_service_selection:
                    st.session_state['receipt_data'] = {
                        "selected_template": selected_template,
                        "address": address,
                        "selected_date": selected_date,
                        "amount": amount,
                        "basic_service": basic_service_selection,
                        "electrical": electrical_selections,
                        "rooms": rooms_selection,
                        "other": other_selection,
                        "custom_notes": custom_notes_content,
                        "receipt_file_name": f"Receipt.{address}.docx"

                    }
                    if st.session_state['receipt_data']['selected_template'] == "完整版（带exclude模块）":
                        st.session_state['receipt_data']['output_doc'] = Document("templates/Recipte单项.docx")
                    elif st.session_state['receipt_data']['selected_template'] == "精简版（不带exclude模块）":
                        st.session_state['receipt_data']['output_doc'] = Document("templates/Recipte单项2.docx")
                    st.switch_page("pages/receipt_preview.py")
                else:
                    st.error("发票信息有缺失！请填写完整信息！", icon="⚠️")
            if st.button("⬅️返回控制台", use_container_width=True):
                st.switch_page("pages/admin_page.py")
        elif role == "customer_service":
            if st.button("⬅️返回控制台", use_container_width=True):
                st.switch_page("pages/customer_service_page.py")

        # 退出登录模块
        st.session_state["logout_button_disabled"] = False
        logout_check = st.checkbox("我希望退出登录！")
        if logout_check:
            if st.button("🛏️退出登录", key="logout_button", use_container_width=True, disabled=st.session_state["logout_button_disabled"]):
                log_out()
        else:
            st.session_state["logout_button_disabled"] = True
            st.button("🛏️退出登录", key="logout_button", use_container_width=True, disabled=st.session_state["logout_button_disabled"])

    else:
        st.title("ATM员工管理控制台")
        st.divider()
        error = st.error("对不起！您未登录，请先登录!3秒后跳转至登录页...", icon="❌")
        time.sleep(1)
        error.empty()
        error = st.error("对不起！您未登录，请先登录!2秒后跳转至登录页...", icon="❌")
        time.sleep(1)
        error.empty()
        st.error("对不起！您未登录，请先登录!1秒后跳转至登录页...", icon="❌")
        time.sleep(1)
        st.switch_page("pages/login_page.py")


if __name__ == '__main__':
    receipt_page()
