"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：customer_service_page.py.py
@Author   ：King Songtao
@Time     ：2024/12/27 上午12:29
@Contact  ：king.songtao@gmail.com
"""
import streamlit as st
from utils.styles import apply_global_styles


def customer_service_page():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    st.title("客户服务")


if __name__ == '__main__':
    customer_service_page()
