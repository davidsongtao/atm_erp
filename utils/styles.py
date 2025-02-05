"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：styles.py.py
@Author   ：King Songtao
@Time     ：2025/2/5 下午12:46
@Contact  ：king.songtao@gmail.com
"""


def apply_global_styles():
    """应用全局样式"""
    import streamlit as st

    st.markdown("""
        <style>
            /* 按钮样式 */
            .stButton button {
                border-radius: 0px !important;
            }

            .stLinkButton > a {
                border-radius: 0px !important;
            }

            /* 输入框样式 */
            [data-baseweb="input"] {
                border-radius: 0px !important;
            }

            [data-baseweb="input"] > div {
                border-radius: 0px !important;
            }

            /* 数字输入框相关样式 */
            [data-testid="stNumberInput"] input {
                border-radius: 0px !important;
            }

            .stNumberInput > div {
                border-radius: 0px !important;
            }

            .stNumberInput div[data-baseweb="input"] {
                border-radius: 0px !important;
            }

            .stNumberInput [data-baseweb="input"] > div {
                border-radius: 0px !important;
            }

            /* 数字输入框的增减按钮样式 */
            .stNumberInput div[data-baseweb="spinner"] {
                border-radius: 0px !important;
            }

            .stNumberInput [data-baseweb="spinner"] div {
                border-radius: 0px !important;
            }

            .stNumberInput button {
                border-radius: 0px !important;
            }

            [data-baseweb="spinbutton"] {
                border-radius: 0px !important;
            }

            [data-baseweb="spinbutton"] > div {
                border-radius: 0px !important;
            }

            /* DataFrame 相关样式 */
            .stDataFrame {
                border-radius: 0px !important;
            }

            /* DataFrame 容器 */
            [data-testid="stDataFrame"] > div {
                border-radius: 0px !important;
            }

            /* DataFrame 表格本身 */
            .css-jhkxg0 {
                border-radius: 0px !important;
            }

            /* DataFrame 所有子元素 */
            [data-testid="stDataFrame"] div {
                border-radius: 0px !important;
            }

            /* DataFrame 滚动区域 */
            .element-container > div > div > div {
                border-radius: 0px !important;
            }

            /* 其他输入框样式 */
            [data-baseweb="input-wrapper"] div {
                border-radius: 0px !important;
            }

            [data-baseweb="select"] > div {
                border-radius: 0px !important;
            }

            [data-baseweb="datepicker"] div {
                border-radius: 0px !important;
            }

            input, textarea, select, .stTextInput > div {
                border-radius: 0px !important;
            }

            /* 消息提示框样式 */
            div[data-testid="stCaptionContainer"] > div {
                border-radius: 0px !important;
            }

            div[role="alert"] {
                border-radius: 0px !important;
            }

            .st-emotion-cache-16idsys,
            .st-emotion-cache-1rmzxen,
            .st-emotion-cache-1ghyxq7,
            .st-emotion-cache-k7vsyb,
            .element-container div[data-testid="stMarkdownContainer"] {
                border-radius: 0px !important;
            }

            .stAlert > div {
                border-radius: 0px !important;
            }

            .stAlert > div > div {
                border-radius: 0px !important;
            }
            
            /* 下载按钮特定样式 */
            .stDownloadButton button {
                border-radius: 0px !important;
            }
            
            /* 下载按钮容器样式 */
            .stDownloadButton > div {
                border-radius: 0px !important;
            }
            
            /* 确保下载按钮内部元素也是直角 */
            .stDownloadButton * {
                border-radius: 0px !important;
            }
            
            /* 扩展现有的按钮样式以涵盖所有类型 */
            button, .stButton>button, .stDownloadButton button {
                border-radius: 0px !important;
            }
        </style>
    """, unsafe_allow_html=True)