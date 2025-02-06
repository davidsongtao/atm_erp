"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：monthly_review.py.py
@Author   ：King Songtao
@Time     ：2025/2/6 下午4:15
@Contact  ：king.songtao@gmail.com
"""
import streamlit as st

from pages.work_orders import get_theme_color
from utils.styles import apply_global_styles
from utils.utils import check_login_state, navigation


def monthly_review():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    # 动态设置 tab 样式
    theme_color = get_theme_color()
    st.markdown(f"""
                <style>
                    .stTabs [data-baseweb="tab-list"] {{
                        gap: 2px;
                    }}
                    .stTabs [data-baseweb="tab"] {{
                        height: 50px;
                        background-color: #F0F2F6;
                        border-radius: 0px 0px 0px 0px;
                        padding-left: 15px;
                        padding-right: 15px;
                    }}
                    .stTabs [aria-selected="true"] {{
                        background-color: {theme_color} !important;
                        color: #FFFFFF !important;
                    }}
                </style>""", unsafe_allow_html=True)

    login_state, role = check_login_state()

    if login_state is True and role == "admin":
        navigation()

        st.title("📊 月度结算")
        st.divider()


if __name__ == '__main__':
    monthly_review()
