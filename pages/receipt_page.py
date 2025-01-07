"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：receipt_page.py.py
@Author   ：King Songtao
@Time     ：2024/12/27 上午12:55
@Contact  ：king.songtao@gmail.com
"""
import time
import asyncio
from datetime import date
import streamlit as st
from docx import Document
from utils.utils import check_login_state, validate_address, generate_receipt, formate_date, navigation, clear_form_state
from utils.validator import AddressValidator, get_validator


def initialize_receipt_data():
    """初始化收据数据"""
    if 'previous_form_data' in st.session_state:
        # 如果存在之前的表单数据，恢复自定义项目的session state
        if 'included_items' not in st.session_state and 'custom_notes' in st.session_state['previous_form_data']:
            st.session_state['included_items'] = st.session_state['previous_form_data']['custom_notes']

        if 'excluded_items' not in st.session_state and 'custom_excluded_items' in st.session_state['previous_form_data']:
            st.session_state['excluded_items'] = st.session_state['previous_form_data']['custom_excluded_items']

        return st.session_state['previous_form_data']

    return {
        "selected_template": "手动版（手动选择excluded中的内容）",
        "address": "",
        "selected_date": date.today(),
        "amount": 0.0,
        "basic_service": [],
        "electrical": [],
        "rooms": [],
        "other": [],
        "custom_notes": [],
        "custom_notes_enabled": False,
        "excluded_enabled": False,
        "custom_excluded_enabled": False,  # 新增字段
        "manual_excluded_selection": [],
        "custom_excluded_items": [],
        "output_doc": None,
        "receipt_file_name": "",
        "ready_doc": None
    }


def save_form_state(form_data):
    """保存表单状态到session"""
    st.session_state['previous_form_data'] = form_data


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


async def render_input_form(service_options, receipt_data):
    """渲染输入表单"""
    # 初始化验证器相关的session state
    if 'validator' not in st.session_state:
        st.session_state.validator = get_validator(
            st.secrets.get("HERE_API_KEY"),
            st.secrets.get("DEEPSEEK_API_KEY")
        )

    if "should_validate" not in st.session_state:
        st.session_state.should_validate = False

    if "address" not in st.session_state:
        st.session_state.address = receipt_data["address"]

    def on_address_change():
        st.session_state.should_validate = True

    def select_address(match):
        st.session_state.address = match.formatted_address
        st.session_state.should_validate = False

    address = st.text_input('客户地址',
                            key="address",
                            on_change=on_address_change,
                            placeholder="客户地址。例如：1202/157 A'Beckett St, Melbourne VIC 3000")

    # 处理地址验证
    address_valid = True
    if st.session_state.should_validate and address.strip():
        try:
            with st.spinner("验证地址中..."):
                matches = await st.session_state.validator.validate_address(address)
                st.session_state.should_validate = False

                if matches:
                    # 使用字典去重，以格式化地址作为键
                    unique_matches = {}
                    for match in matches:
                        # 如果遇到相同地址，保留置信度更高的那个
                        if match.formatted_address not in unique_matches or \
                                match.confidence_score > unique_matches[match.formatted_address].confidence_score:
                            unique_matches[match.formatted_address] = match

                    # 转换回列表并按置信度排序
                    unique_matches = sorted(
                        unique_matches.values(),
                        key=lambda x: x.confidence_score,
                        reverse=True
                    )
                    st.success("找到以下可能的地址匹配：", icon="✅")

                    for i, match in enumerate(unique_matches):
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])

                            with col1:
                                st.write(f"🏠 {match.formatted_address}")
                            with col2:
                                st.write(f"匹配度: {match.confidence_score:.2f}")
                            with col3:
                                if st.button("选择", key=f"select_{i}", on_click=select_address, args=(match,)):
                                    st.rerun()
                    st.info("如果您不确定以上哪个是正确地址，请在google中搜索查看！", icon="ℹ️")
                    # 创建Google搜索URL
                    search_query = address.replace(' ', '+')
                    search_url = f"https://www.google.com/search?q={search_query}+Australia"

                    # 使用st.link_button替代JavaScript方式
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

    # 创建两列布局
    col1, col2 = st.columns(2)

    with col1:
        selected_date = st.date_input('收据日期',
                                      value=receipt_data["selected_date"])
        basic_service_selection = st.multiselect('基础服务（多选）',
                                                 service_options["basic_service"],
                                                 default=receipt_data["basic_service"],
                                                 placeholder="请选择基础服务...")
        electrical_selections = st.multiselect('电器服务（多选）',
                                               service_options["electrical"],
                                               default=receipt_data["electrical"],
                                               placeholder="请选择电器服务...")

    with col2:
        amount = st.number_input('收据金额',
                                 value=float(receipt_data["amount"]),
                                 min_value=0.0,
                                 step=1.0,
                                 format='%f')
        rooms_selection = st.multiselect('房间（多选）',
                                         service_options["rooms"],
                                         default=receipt_data["rooms"],
                                         placeholder="请选择房间...")
        other_selection = st.multiselect('其他服务（多选）',
                                         service_options["others"],
                                         default=receipt_data["other"],
                                         placeholder="请输入其他服务...")

    return (address_valid, address, selected_date, amount,
            basic_service_selection, electrical_selections,
            rooms_selection, other_selection)


def handle_custom_items(item_type, receipt_data):
    """处理自定义项目的添加和删除"""
    items_key = "custom_notes" if item_type == "included" else "custom_excluded_items"
    session_key = f'{item_type}_items'

    # 添加自定义 CSS 来隐藏特定文本输入框的标签
    st.markdown("""
        <style>
            /* 隐藏所有自定义项目的label */
            div[data-testid="stTextInput"] > label {
                display: none !important;
                height: 0px !important;
                margin: 0px !important;
                padding: 0px !important;
            }
            /* 移除label占用的空间 */
            div[data-testid="stTextInput"] > .st-emotion-cache-1umgz6j {
                margin-top: 0px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 初始化或更新 session state
    if session_key not in st.session_state:
        saved_items = receipt_data[items_key]
        st.session_state[session_key] = saved_items if saved_items else [""]

    # 添加新项目的按钮
    if st.button(f"新增一个自定义项", key=f"add_{item_type}", use_container_width=True):
        st.session_state[session_key].append("")
        st.rerun()

    # 创建输入字段
    updated_items = []
    for idx, item in enumerate(st.session_state[session_key]):
        col1, col2 = st.columns([5, 1])

        with col1:
            new_value = st.text_input(
                " ",  # 使用空格作为label而不是空字符串
                value=item,
                key=f"{item_type}_item_{idx}",
                placeholder=f"请输入第{idx + 1}个自定义项目内容..."
            )
            updated_items.append(new_value)

        with col2:
            if st.button("删除", key=f"delete_{item_type}_{idx}", use_container_width=True):
                st.session_state[session_key].pop(idx)
                st.rerun()

    st.session_state[session_key] = updated_items
    return updated_items


def handle_excluded_content(all_services, selected_services, receipt_data):
    """处理excluded内容"""
    manual_excluded = [service for service in all_services if service not in selected_services]
    excluded_enabled = st.checkbox("添加Excluded模块",
                                   value=receipt_data["excluded_enabled"])

    manual_excluded_selection = []
    custom_excluded_items = []

    if excluded_enabled:
        manual_excluded_selection = st.multiselect(
            "请选择您要添加的内容：",
            manual_excluded,
            default=receipt_data["manual_excluded_selection"],
            placeholder="请选择要添加的服务..."
        )

        # Add checkbox for custom excluded items
        custom_excluded_enabled = st.checkbox(
            "为Excluded模块添加自定义项目",
            value=receipt_data.get("custom_excluded_enabled", False)
        )

        return manual_excluded_selection, custom_excluded_items, excluded_enabled, custom_excluded_enabled

    return manual_excluded_selection, custom_excluded_items, excluded_enabled, False


def generate_included_content(selections, order_map, custom_items=None):
    """生成included内容"""
    all_selections = []
    for service_list in selections:
        for item in service_list:
            all_selections.append((order_map[item], f"{item}"))

    all_selections.sort(key=lambda x: x[0])

    # 生成基本内容
    content = "\n".join(f"{i}.{service}" for i, (_, service) in enumerate(all_selections, 1))

    # 添加多个自定义内容
    if custom_items:
        last_number = len(all_selections)
        for idx, item in enumerate(custom_items, 1):
            if item.strip():  # 只添加非空的项目
                content += f"\n{last_number + idx}.{item}"

    return content


def generate_excluded_content(manual_excluded_selection, all_services, custom_items=None):
    """生成excluded内容"""
    if not manual_excluded_selection and not (custom_items and any(item.strip() for item in custom_items)):
        return ""

    excluded_content = "It has excluded\n\n"
    order_list = {item: index for index, item in enumerate(all_services)}
    excluded_content_list = sorted(manual_excluded_selection,
                                   key=lambda x: order_list.get(x, len(all_services)))

    # 生成基本excluded内容
    content = "\n".join(f"{i}.{service}"
                        for i, service in enumerate(excluded_content_list, 1))

    # 添加多个自定义excluded内容
    if custom_items:
        last_number = len(excluded_content_list)
        for idx, item in enumerate(custom_items, 1):
            if item.strip():  # 只添加非空的项目
                if content:
                    content += "\n"
                content += f"{last_number + idx}.{item}"

    return excluded_content + content


async def receipt_page():
    """收据生成页面主函数"""
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')

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
    receipt_data = initialize_receipt_data()

    # 获取服务选项
    service_options = get_service_options()

    # 渲染输入表单
    form_data = await render_input_form(service_options, receipt_data)
    (address_valid, address, selected_date, amount,
     basic_service_selection, electrical_selections,
     rooms_selection, other_selection) = form_data

    # 处理自定义included项目
    custom_notes = st.checkbox("为Included添加自定义项目",
                               value=receipt_data["custom_notes_enabled"])
    custom_notes_items = []
    if custom_notes:
        custom_notes_items = handle_custom_items("included", receipt_data)

    # 处理excluded内容
    all_services = (service_options["basic_service"] + service_options["rooms"] +
                    service_options["electrical"] + service_options["others"])
    selected_services = (basic_service_selection + electrical_selections +
                         rooms_selection + other_selection)
    manual_excluded_selection, custom_excluded_items, excluded_enabled, custom_excluded_enabled = handle_excluded_content(
        all_services,
        selected_services,
        receipt_data
    )

    # Only show custom excluded items input if both checkboxes are enabled
    if excluded_enabled and custom_excluded_enabled:
        custom_excluded_items = handle_custom_items("excluded", receipt_data)

    # st.divider()
    st.info("确保收据信息录入正确后，点击生成收据按钮即可预览或下载您的收据！", icon="ℹ️")

    # 提交按钮
    submit = st.button("生成收据", use_container_width=True, type="primary")

    if submit:
        if not (address_valid and address and selected_date and
                amount and basic_service_selection):
            st.error("发票信息有缺失！请填写完整信息！", icon="⚠️")
            return

        # 保存表单状态
        current_form_data = {
            "selected_template": "手动版（手动选择excluded中的内容）",
            "address": address,
            "selected_date": selected_date,
            "amount": amount,
            "basic_service": basic_service_selection,
            "electrical": electrical_selections,
            "rooms": rooms_selection,
            "other": other_selection,
            "custom_notes": custom_notes_items,
            "custom_notes_enabled": custom_notes,
            "excluded_enabled": excluded_enabled,
            "custom_excluded_enabled": custom_excluded_enabled,
            "manual_excluded_selection": manual_excluded_selection,
            "custom_excluded_content": custom_excluded_items,
            "output_doc": Document("templates/Recipte单项.docx"),
            "receipt_file_name": f"Receipt.{address}.docx",
        }

        save_form_state(current_form_data)
        st.session_state['receipt_data'] = current_form_data

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
            custom_notes_items if custom_notes and custom_notes_items else None
        )

        # 生成excluded内容
        excluded_content = generate_excluded_content(
            manual_excluded_selection,
            all_services,
            custom_excluded_items if custom_excluded_items else None
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
        if current_form_data['output_doc']:
            current_form_data['ready_doc'] = generate_receipt(current_form_data['output_doc'],
                                                              replace_dic)
            st.switch_page("pages/receipt_preview.py")
        else:
            st.error("模板文档未正确加载，请重试！")


if __name__ == '__main__':
    asyncio.run(receipt_page())
