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
from utils.utils import check_login_state, log_out, validate_address, generate_receipt, formate_date


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
                "receipt_file_name": "",
                "ready_doc": None
            }

            selected_template = st.selectbox('选择收据模板', ["完整版（带excluded模块）", "精简版（不带excluded模块）", "手动版（手动选择excluded中的内容）"], placeholder="请选择收据模板", index=None)
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

            # 手动勾选excluded的内容，这个列表要从总部表中去掉上面勾选的
            all_services = basic_service + rooms + electrical + others
            selected = basic_service_selection + electrical_selections + rooms_selection + other_selection
            manual_excluded = [service for service in all_services if service not in selected]
            if selected_template == "手动版（手动选择excluded中的内容）":
                manual_excluded_selection = st.multiselect("手动添加Excluded中包含的内容：", manual_excluded, placeholder="请输入其他服务...")
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
                    elif st.session_state['receipt_data']['selected_template'] == "手动版（手动选择excluded中的内容）":
                        st.session_state['receipt_data']['output_doc'] = Document("templates/Recipte单项.docx")
                    # 准备要替换的数据
                    # 准备included模块的内容(处理排序问题，不管用户怎么选择，最终都要按照规定的顺序排序)
                    order_map = {}
                    current_index = 0
                    for item in basic_service:
                        order_map[item] = current_index
                        current_index += 1

                    for item in rooms:
                        order_map[item] = current_index
                        current_index += 1

                    for item in electrical:
                        order_map[item] = current_index
                        current_index += 1

                    for item in others:
                        order_map[item] = current_index
                        current_index += 1

                    included_content = ""
                    all_selections = []
                    new_list = []
                    for item in basic_service_selection:
                        all_selections.append((order_map[item], f"{item}"))

                    for item in rooms_selection:
                        all_selections.append((order_map[item], f"{item}"))

                    for item in electrical_selections:
                        all_selections.append((order_map[item], f"{item}"))

                    for item in other_selection:
                        all_selections.append((order_map[item], f"{item}"))

                    all_selections.sort(key=lambda x: x[0])

                    if all_selections:
                        for i, (_, service) in enumerate(all_selections, 1):
                            new_list.append(f"{i}.{service}")

                    for item in new_list:
                        included_content += f"{item}\n"

                    if st.session_state['receipt_data']['selected_template'] == "完整版（带exclude模块）":

                        # TODO 准备excluded模块的内容
                        excluded_content = ""
                        all_unselected = []

                        for item in basic_service:
                            if item not in basic_service_selection:
                                all_unselected.append((order_map[item], f"{item}"))

                        for item in rooms:
                            if item not in rooms_selection:
                                all_unselected.append((order_map[item], f"{item}"))

                        for item in electrical:
                            if item not in electrical_selections:
                                all_unselected.append((order_map[item], f"{item}"))

                        for item in others:
                            if item not in other_selection:
                                all_unselected.append((order_map[item], f"{item}"))

                        all_unselected.sort(key=lambda x: x[0])

                        new_unselected_list = []
                        if all_unselected:
                            for i, (_, service) in enumerate(all_unselected, 1):
                                new_unselected_list.append(f"{i}.{service}")

                        for item in new_unselected_list:
                            excluded_content += f"{item}\n"

                    if st.session_state['receipt_data']['selected_template'] == "手动版（手动选择excluded中的内容）":

                        # 将手动选择的excluded中的内容按照总表的顺序排序
                        excluded_content = ""
                        excluded_content_list_new = []
                        order_list = {item: index for index, item in enumerate(all_services)}
                        excluded_content_list = sorted(manual_excluded_selection, key=lambda x: order_list.get(x, len(all_services)))
                        if excluded_content_list:
                            print(excluded_content_list)
                            for i, service in enumerate(excluded_content_list, 1):
                                excluded_content_list_new.append(f"{i}.{service}")
                        for item in excluded_content_list_new:
                            excluded_content += f"{item}\n"

                    else:
                        excluded_content = ""

                    replace_dic = {
                        "$receipt_date$": formate_date(selected_date),
                        "$receipt_address$": address,
                        "$total_amount$": f"{amount:.2f}",
                        "$included_content$": included_content,
                        "$exculded_content$": excluded_content
                    }
                    # 替换模板文件，生成收据
                    template_doc = st.session_state['receipt_data']['output_doc']
                    ready_doc = generate_receipt(template_doc, replace_dic)
                    st.session_state['receipt_data']['ready_doc'] = ready_doc
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
