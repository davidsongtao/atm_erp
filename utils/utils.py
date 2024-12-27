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
from streamlit_cookies_manager import EncryptedCookieManager
import re
from docx.shared import Pt

# 创建一个加密的Cookie 管理器
cookies = EncryptedCookieManager(prefix="atm_erp", password="123456")
if not cookies.ready():
    st.stop()


# 权限管理装饰器
def role_required(allowed_roles):
    def decorator(func):
        def wrapper(*args, **kwargs):
            if st.session_state['role'] not in allowed_roles:
                st.warning("您没有权限访问此功能!")
                return
            return func(*args, **kwargs)

        return wrapper

    return decorator


def stream_res(res):
    """前端制作流式输出效果"""
    for char in res:
        yield char
        time.sleep(0.02)


def check_login_state():
    """获取或存储登录状态"""
    if cookies.get("is_logged_in") == "1":
        st.session_state['is_logged_in'] = True
        st.session_state['role'] = cookies.get("role", "user")
        return True, cookies.get("role")
    else:
        st.session_state['is_logged_in'] = False
        return False, cookies.get("role")


def set_login_state(is_logged_in, role, username, name):
    cookies["is_logged_in"] = "1" if is_logged_in else "0"
    cookies["role"] = role
    cookies["name"] = name
    cookies.save()  # 保存 Cookie


def log_out():
    """注销登录"""
    # 清除与登录状态相关的 Cookie
    cookies["is_logged_in"] = "0"  # 或直接删除整个 key
    cookies["role"] = ""
    cookies.save()  # 必须调用 save() 才能生效
    success = st.success("您已成功退出登录！3秒后跳转...", icon="✅")
    time.sleep(1)
    success.empty()
    success = st.success("您已成功退出登录！2秒后跳转...", icon="✅")
    time.sleep(1)
    success.empty()
    st.success("您已成功退出登录！1秒后跳转...", icon="✅")
    time.sleep(1)
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
