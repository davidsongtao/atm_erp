"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：quote_page.py
@Author   ：King Songtao
@Time     ：2024/12/30 下午3:15
@Contact  ：king.songtao@gmail.com
"""
from utils.utils import navigation, stream_res
import streamlit as st
from openai import OpenAI


def quote_page():
    navigation()
    st.title("⌨️自动化报价生成")
    st.divider()

    st.chat_message("ai").write(stream_res("基于您的选择，我为您制作了一份报价proposal,具体如下：\n\n{报价内容详情\n\n报价内容详情\n\n报价内容详情\n\n报价内容详情\n\n报价内容详情}\n\n如果您觉得有什么需要调整的，请在下方的输入框告诉我告诉我，我将为您修改~"))

    # 处理用户输入
    if prompt := st.chat_input("请告诉我有什么需要修改的..."):
        with st.chat_message("user"):
            st.markdown(prompt)
        with st.chat_message("ai"):
            st.write(stream_res("好的没问题，我帮您修改了一份新的报价proposal,请查阅~"))


if __name__ == '__main__':
    quote_page()
