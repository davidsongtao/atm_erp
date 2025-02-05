"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：user_management_page.py
@Author   ：King Songtao
@Time     ：2024/12/27 上午12:59
@Contact  ：king.songtao@gmail.com
"""
import streamlit as st
from utils.styles import apply_global_styles


def user_management_page():
    """
    用户管理界面
    :return:
    """
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    st.title("员工账户管理")


if __name__ == '__main__':
    user_management_page()
