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
from utils.utils import check_login_state, confirm_back, validate_address, generate_receipt, formate_date, navigation


def initialize_receipt_data():
    """初始化收据数据"""
    return {
        "selected_template": "手动版（手动选择excluded中的内容）",
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


def get_service_options():
    """获取所有服务选项"""
    return {
        "basic_service": ["Steam clean of the carpet", "Steam clean of the mattress",
                          "Steam clean of the sofa", "Vacuum clean of carpet",
                          "Floor boards/Floor tiles mopping"],
        "rooms": ["Bedroom", "Bathroom", "Kitchen"],
        "electrical": ["Microwave", "Oven", "Dishwasher", "Refrigerator",
                       "Washing machine", "Dryer", "Air conditioner"],
        "others": ["Skirting board/Window frame/Wardrobe", "Blinds", "Window glasses",
                   "Balcony with sliding door windows", "Wall marks removal",
                   "Furniture wipe off", "Pet hair removal", "Rubbish removal",
                   "Mould removal"]
    }


def render_input_form(service_options):
    """渲染输入表单"""
    # 地址输入和验证
    address = st.text_input('客户地址', placeholder="例如：1202/157 A'Beckett St, Melbourne VIC 3000")
    address_valid = True
    if address:
        is_valid, error_message = validate_address(address)
        if not is_valid:
            st.error(error_message)
            address_valid = False

    # 创建两列布局
    col1, col2 = st.columns(2)

    with col1:
        selected_date = st.date_input('收据日期', date.today())
        basic_service_selection = st.multiselect('基础服务（多选）',
                                                 service_options["basic_service"],
                                                 placeholder="请选择基础服务...")
        electrical_selections = st.multiselect('电器服务（多选）',
                                               service_options["electrical"],
                                               placeholder="请选择电器服务...")

    with col2:
        amount = st.number_input('收据金额', min_value=0.0, step=1.0, format='%f')
        rooms_selection = st.multiselect('房间（多选）',
                                         service_options["rooms"],
                                         placeholder="请选择房间...")
        other_selection = st.multiselect('其他服务（多选）',
                                         service_options["others"],
                                         placeholder="请输入其他服务...")

    return (address_valid, address, selected_date, amount,
            basic_service_selection, electrical_selections,
            rooms_selection, other_selection)


def handle_excluded_content(all_services, selected_services):
    """处理excluded内容"""
    manual_excluded = [service for service in all_services if service not in selected_services]
    add_excluded_manually = st.checkbox("添加Excluded模块", value=False)

    manual_excluded_selection = []
    custom_excluded_content = ""

    if add_excluded_manually:
        manual_excluded_selection = st.multiselect("请选择您要添加的内容：",
                                                   manual_excluded,
                                                   placeholder="请输入其他服务...")
        # 只有在勾选了添加Excluded模块时，才显示自定义excluded项选项
        add_custom_excluded = st.checkbox("为Excluded添加自定义项", value=False,
                                          disabled=not add_excluded_manually)

        if add_custom_excluded:
            custom_excluded_content = st.text_input("请输入要添加到Excluded模块的自定义项目",
                                                    placeholder="请填写自定义项目内容...")

    return manual_excluded_selection, custom_excluded_content


def generate_included_content(selections, order_map, custom_notes_content=None):
    """生成included内容"""
    all_selections = []
    for service_list in selections:
        for item in service_list:
            all_selections.append((order_map[item], f"{item}"))

    all_selections.sort(key=lambda x: x[0])

    # 生成基本内容
    content = "\n".join(f"{i}.{service}" for i, (_, service) in enumerate(all_selections, 1))

    # 如果有自定义内容，添加到末尾
    if custom_notes_content:
        # 获取当前最后一个编号
        last_number = len(all_selections)
        # 添加自定义内容（序号续接）
        content += f"\n{last_number + 1}.{custom_notes_content}"

    return content


def generate_excluded_content(manual_excluded_selection, all_services, custom_excluded_content=None):
    """生成excluded内容"""
    if not manual_excluded_selection and not custom_excluded_content:
        return ""

    excluded_content = "It has excluded\n\n"
    order_list = {item: index for index, item in enumerate(all_services)}
    excluded_content_list = sorted(manual_excluded_selection,
                                   key=lambda x: order_list.get(x, len(all_services)))

    # 生成基本excluded内容
    content = "\n".join(f"{i}.{service}"
                        for i, service in enumerate(excluded_content_list, 1))

    # 如果有自定义excluded内容，添加到末尾
    if custom_excluded_content:
        # 如果已经有其他excluded内容，需要添加换行
        if content:
            content += "\n"
        # 获取当前最后一个编号
        last_number = len(excluded_content_list)
        # 添加自定义内容（序号续接）
        content += f"{last_number + 1}.{custom_excluded_content}"

    return excluded_content + content


def receipt_page():
    """收据生成页面主函数"""
    login_state, role = check_login_state()

    if not login_state:
        st.title("ATM员工管理控制台")
        st.divider()
        for i in range(3, 0, -1):
            error = st.error(f"对不起！您未登录，请先登录!{i}秒后跳转至登录页...", icon="❌")
            time.sleep(1)
            if i > 1:
                error.empty()
        st.switch_page("pages/login_page.py")

    navigation()
    st.title("🧾收据自动化生成")
    st.divider()

    if role != "admin":
        if st.button("⬅️返回控制台", use_container_width=True):
            st.switch_page("pages/customer_service_page.py")
        return

    # 初始化收据数据
    st.session_state['receipt_data'] = initialize_receipt_data()

    # 获取服务选项
    service_options = get_service_options()

    # 渲染输入表单
    form_data = render_input_form(service_options)
    (address_valid, address, selected_date, amount,
     basic_service_selection, electrical_selections,
     rooms_selection, other_selection) = form_data

    # 处理自定义注释
    custom_notes = st.checkbox("为Included添加自定义项目", value=False)
    custom_notes_content = ""
    if custom_notes:
        custom_notes_content = st.text_input("请输入您要添加的自定义项目",
                                             placeholder="请填写自定义项目内容...")

    # 处理excluded内容
    all_services = (service_options["basic_service"] + service_options["rooms"] +
                    service_options["electrical"] + service_options["others"])
    selected_services = (basic_service_selection + electrical_selections +
                         rooms_selection + other_selection)
    manual_excluded_selection, custom_excluded_content = handle_excluded_content(
        all_services,
        selected_services
    )

    # 提交按钮
    submit = st.button("生成收据", use_container_width=True, type="primary")

    if submit:
        if not (address_valid and address and selected_date and
                amount and basic_service_selection):
            st.error("发票信息有缺失！请填写完整信息！", icon="⚠️")
            return

        # 更新收据数据
        receipt_data = st.session_state['receipt_data']
        receipt_data.update({
            "address": address,
            "selected_date": selected_date,
            "amount": amount,
            "basic_service": basic_service_selection,
            "electrical": electrical_selections,
            "rooms": rooms_selection,
            "other": other_selection,
            "custom_notes": custom_notes_content,
            "receipt_file_name": f"Receipt.{address}.docx",
            "output_doc": Document("templates/Recipte单项.docx")
        })

        # 创建order_map用于排序
        order_map = {}
        for i, service_list in enumerate(service_options.values()):
            for item in service_list:
                order_map[item] = len(order_map)

        # 生成included内容
        included_content = generate_included_content(
            [basic_service_selection, rooms_selection,
             electrical_selections, other_selection],
            order_map,
            custom_notes_content if custom_notes and custom_notes_content else None
        )

        # 生成excluded内容
        excluded_content = generate_excluded_content(
            manual_excluded_selection,
            all_services,
            custom_excluded_content if custom_excluded_content else None
        )

        # 准备替换字典
        replace_dic = {
            "$receipt_date$": formate_date(selected_date),
            "$receipt_address$": address,
            "$total_amount$": f"{amount:.2f}",
            "$included_content$": included_content,
            "$exculded_content$": excluded_content
        }

        # 生成收据
        if receipt_data['output_doc']:
            receipt_data['ready_doc'] = generate_receipt(receipt_data['output_doc'],
                                                         replace_dic)
            st.switch_page("pages/receipt_preview.py")
        else:
            st.error("模板文档未正确加载，请重试！")

    if st.button("返回", key="back_button", use_container_width=True):
        confirm_back()


if __name__ == '__main__':
    receipt_page()
