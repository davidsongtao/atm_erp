"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：add_acc.py.py
@Author   ：King Songtao
@Time     ：2025/1/6 上午11:39
@Contact  ：king.songtao@gmail.com
"""
import time
import streamlit as st
from utils.utils import navigation, check_login_state


def add_acc():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    login_state, role = check_login_state()

    # 检查登录状态
    if login_state is True and role == "admin":
        navigation()
        st.title("➕创建新的账户")
        st.divider()

        # 创建新的账户逻辑代码


    else:
        error = st.error("您还没有登录！3秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您还没有登录！2秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您还没有登录！1秒后跳转至登录页...", icon="⚠️")
        time.sleep(1)

        st.session_state["login_state"] = False
        st.switch_page("pages/login_page.py")


if __name__ == '__main__':
    add_acc()
