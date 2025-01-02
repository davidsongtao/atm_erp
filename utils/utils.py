"""
Description: 项目中用到的工具函数
    
-*- Encoding: UTF-8 -*-
@File     ：utils.py.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午8:27
@Contact  ：king.songtao@gmail.com
"""
import streamlit as st
import time
import re
from docx.shared import Pt
from langchain.memory import ConversationBufferMemory

from configs.log_config import *


# # 创建一个加密的Cookie 管理器
# cookies = EncryptedCookieManager(prefix="atm_erp", password="dst881009...")
# if not cookies.ready():
#     st.stop()


# # 权限管理装饰器
# def role_required(allowed_roles):
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             if st.session_state['role'] not in allowed_roles:
#                 st.warning("您没有权限访问此功能!")
#                 return
#             return func(*args, **kwargs)
#
#         return wrapper
#
#     return decorator


def stream_res(res):
    """前端制作流式输出效果"""
    for char in res:
        yield char
        time.sleep(0.02)


def check_login_state():
    """获取或存储登录状态"""
    try:
        if "login_state" not in st.session_state:
            st.session_state["login_state"] = False
            st.session_state["role"] = None
            return False, st.session_state["role"]
        elif st.session_state["login_state"]:
            # 用户已登陆
            st.session_state["login_state"] = True
            return True, st.session_state["role"]
        else:
            st.session_state["login_state"] = False
            st.session_state["role"] = None
            print("用户未登录")
            return False, st.session_state["role"]
            # 用户未登录
    except Exception as e:
        logger.error(f"检测登录状态时发生错误！错误信息：{e}")
        st.error("发生未知错误！即将跳转到首页...")
        st.switch_page("pages/login_page.py")

    # """通过cookies管理登陆状态"""
    # if cookies.get("is_logged_in") == "1":
    #     st.session_state['is_logged_in'] = True
    #     st.session_state['role'] = cookies.get("role", "user")
    #     return True, cookies.get("role")
    # else:
    #     st.session_state['is_logged_in'] = False
    #     return False, cookies.get("role")


def set_login_state(is_logged_in, role, name):
    st.session_state["login_state"] = True if is_logged_in else False
    st.session_state["role"] = role
    st.session_state["name"] = name

    # cookies["is_logged_in"] = "1" if is_logged_in else "0"
    # cookies["role"] = role
    # cookies["name"] = name
    # cookies.save()  # 保存 Cookie


def log_out():
    """注销登录"""
    # 清除与登录状态相关的 Cookie
    # cookies["is_logged_in"] = "0"  # 或直接删除整个 key
    # cookies["role"] = ""
    # cookies.save()  # 必须调用 save() 才能生效

    st.session_state["login_state"] = False
    st.session_state["role"] = None
    st.switch_page("app.py")


def validate_address(address):
    """
    验证地址是否只包含英文字符、数字和常见标点符号
    """
    # 增加 / 到允许的字符中
    pattern = r'^[a-zA-Z0-9\s\.\,\-\#\/]+$'

    if not address:
        return False, "地址不能为空"

    if not re.match(pattern, address):
        return False, "地址只能包含英文字符、数字和符号(.,- #/)。请检查是否含有中文逗号！"

    return True, ""


def extract_date_from_html(html_content):
    """
    提取 HTML 内容中的日期
    假设日期格式为 "16th Dec. 2024"（可以根据需要调整正则表达式）
    """
    # 用正则表达式匹配日期
    date_pattern = r"\d{1,2}[a-zA-Z]{2}\s[A-Za-z]+\.\s\d{4}"
    match = re.search(date_pattern, html_content)

    if match:
        return match.group(0)  # 返回匹配到的日期
    return None


def generate_receipt(doc, data_dict):
    """
        替换文档中的占位符并统一字体
        """
    # 替换段落中的文本
    for paragraph in doc.paragraphs:
        for key, value in data_dict.items():
            if key in paragraph.text:
                paragraph.text = paragraph.text.replace(key, str(value))

        # 统一段落字体和大小
        for run in paragraph.runs:
            run.font.name = 'Arial'
            run.font.size = Pt(10)

    # 替换表格中的文本
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for key, value in data_dict.items():
                    if key in cell.text:
                        cell.text = cell.text.replace(key, str(value))

                # 统一单元格内段落的字体和大小
                for paragraph in cell.paragraphs:
                    for run in paragraph.runs:
                        run.font.name = 'Arial'
                        run.font.size = Pt(10)

    return doc


def formate_date(input_date):
    """
    自定义日期格式化
    将 2024-12-11 格式化为 11th Dec. 2024
    """
    day = input_date.day
    month_abbr = input_date.strftime('%b')
    year = input_date.year

    # 添加日期后缀
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')

    return f"{day}{suffix} {month_abbr}. {year}"


def formate_acc_info(data):
    formatted_orders = []
    for i in range(len(data['账户编号'])):
        formatted_order = f"{data['登录账号'][i]} | {data['用户名'][i]}"
        formatted_orders.append(formatted_order)
    return formatted_orders


@st.dialog("退出登录！")
def confirm_logout():
    st.write("您正在退出登录，确认要继续吗?")
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        if st.button("确认", key="confirm_logout", type="primary", use_container_width=True):
            log_out()
    with col2:
        if st.button("取消", key="cancel_logout", type="secondary", use_container_width=True):
            st.rerun()


def navigation():
    # 导航模块
    # st.sidebar.title("🏠ATM Cleaning Service")
    st.sidebar.image("images/logo.png")
    # st.sidebar.divider()
    if st.sidebar.button("➕创建收据", key="open_receipt_button", use_container_width=True, type="primary"):
        st.switch_page("pages/receipt_page.py")
    # 自动化报价
    if st.sidebar.button("🤖智能报价", key="auto_quote_button", use_container_width=True, type="primary"):
        st.switch_page("pages/pricing_page.py")
        # st.sidebar.warning("该功能正在开发中，敬请期待！", icon="⚠️")
    # 工单管理
    if st.sidebar.button("🔍工单管理", key="order_management", use_container_width=True, type="primary"):
        st.switch_page("pages/order_page.py")  # 保洁阿姨管理
    if st.sidebar.button("👩‍👩‍👧‍👦月度结算", key="staff_management_button", use_container_width=True, type="primary"):
        st.sidebar.warning("该功能正在开发中，敬请期待！", icon="⚠️")

    # 自动化报价
    # if st.sidebar.button("🤖智能助理", key="ai_assistant", use_container_width=True, type="primary"):
    #     # st.switch_page("pages/auto_quote_page.py")
    #     st.sidebar.warning("该功能正在开发中，敬请期待！", icon="⚠️")
    # 用户管理模块
    if st.sidebar.button("👥账户管理", key="user_management_button", use_container_width=True, type="primary"):
        st.switch_page("pages/staff_acc.py")
        # st.warning("该功能正在开发中，敬请期待！", icon="⚠️")

    st.sidebar.divider()

    # 控制台
    if st.sidebar.button("📊回控制台", key="admin_page_button", use_container_width=True):
        st.switch_page("pages/admin_page.py")

    # 个人设置
    if st.sidebar.button("⚙️系统设置", key="system_setting_button", use_container_width=True):
        st.sidebar.warning("该功能正在开发中，敬请期待！", icon="⚠️")
    # 退出登录模块
    if st.sidebar.button("🛏️退出登录", key="logout_button", use_container_width=True):
        confirm_logout()

    st.sidebar.write("Copyright 2025 © ATM Cleaning Inc.")
    st.sidebar.write("Version：V - 2024.12.27.00.01")


@st.dialog("退出确认")
def confirm_back():
    st.write("离开该页面后收据信息将丢失且不可恢复，确认要返回吗?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认", use_container_width=True, type="primary"):
            st.switch_page("pages/admin_page.py")
    with col2:
        if st.button("取消", use_container_width=True, type="secondary"):
            st.rerun()


def get_response(prompt, memory):
    """
    获取AI响应的函数

    Args:
        prompt (str): 用户输入的提示词
        memory (ConversationBufferMemory): 对话记忆对象

    Returns:
        str: AI的响应文本
    """
    from langchain.chat_models import ChatOpenAI
    from langchain.chains import ConversationChain

    # 使用 ChatOpenAI 而不是 OpenAI
    chat_model = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key="sk-cabc0773085a4122b473aeb954300db4",
        openai_api_base="https://api.deepseek.com/v1",
        temperature=0.7
    )

    # 构建对话链
    chain = ConversationChain(
        llm=chat_model,
        memory=memory,
        verbose=True  # 设置为True可以看到更多调试信息
    )

    try:
        # 确保prompt是字符串
        if not isinstance(prompt, str):
            prompt = str(prompt)

        # 调用对话链
        response = chain.run(prompt)
        return response

    except Exception as e:
        print(f"Error in get_response: {str(e)}")
        # 返回一个友好的错误信息
        return f"抱歉，生成回复时出现错误：{str(e)}"
