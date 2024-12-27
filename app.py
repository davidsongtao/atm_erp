"""
Description: 程序入口，直接进入登录界面
    
-*- Encoding: UTF-8 -*-
@File     ：app.py.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午8:36
@Contact  ：king.songtao@gmail.com
"""
import streamlit as st
from utils.utils import check_login_state, log_out
from pages.login_page import login_page


def main():
    # 配置页面信息
    # st.set_page_config(page_title='ATM Cleaning Service', page_icon='🤖', layout="wide")
    st.title("ATM员工管理控制中心")
    st.divider()
    message = st.chat_message("assistant")
    message.write("欢迎来到ATM员工管理控制台,我是您的人工智能助手小江!")
    message.write("请告诉我您想干什么~")
    login_state, role = check_login_state()
    if login_state:
        col1, col2 = st.columns([1, 1])
        if role == "admin":
            # 使用按钮更新页面状态
            if col1.button("管理控制台", use_container_width=True, type='primary'):
                st.switch_page("pages/admin_page.py")
        elif role == "customer_service":
            if col1.button("客服控制台", use_container_width=True, type='primary'):
                st.switch_page("pages/customer_service_page.py")

        if col2.button("退出登录", use_container_width=True):
            log_out()
    else:
        if st.button("员工登录", use_container_width=True, type="primary"):
            st.switch_page("pages/login_page.py")


if __name__ == '__main__':
    login_page()
