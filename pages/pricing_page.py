"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：pricing_page.py
@Author   ：King Songtao
@Time     ：2024/12/30 下午3:04
@Contact  ：king.songtao@gmail.com
"""
from utils.utils import navigation, stream_res
import streamlit as st
from utils.styles import apply_global_styles


def pricing_page():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    navigation()
    st.title("⌨️自动化报价生成")
    st.divider()
    st.info("请选择服务详情", icon="ℹ️")

    basic_service = ["1B1B(steam)", "1B1B(None-steam)", "2B1B(steam)", "2B1B(None-steam)", "2B2B(steam)", "2B2B(None-steam)", "3B1B(steam)", "3B1B(None-steam)", "3B2B(steam)", "3B2B(None-steam)", "Steam clean of the mattress",
                     "Steam clean of the sofa", "Vacuum clean of carpet", "Floor boards/Floor tiles mopping"]
    rooms = ["Bedroom", "Bathroom", "Kitchen"]
    electrical = ["Microwave", "Oven", "Dishwasher", "Refrigerator", "Washing machine", "Dryer", "Air conditioner"]
    others = ["Skirting board/Window frame/Wardrobe", "Blinds", "Window glasses", "Balcony with sliding door windows", "Wall marks removal", "Pet hair removal", "Rubbish removal", "Mould removal"]

    col1, col2 = st.columns([1, 1])

    with col1:
        service_list_data = st.multiselect("基础服务", options=basic_service, key="service_list")
        rooms_list_data = st.multiselect("电器", options=electrical, key="rooms_list")
    with col2:
        electrical_list_data = st.multiselect("房间", options=rooms, key="electrical_list")
        others_list_data = st.multiselect("其他服务", options=others, key="others_list")

    st.info("点击开始后，进入自动化报价机器人，让AI帮您生成理想的报价单吧~", icon="ℹ️")
    if st.button("开始自动化报价", use_container_width=True, type="primary"):
        # 存储选择的服务详情
        st.session_state["pricing_details"] = {
            "基础服务": service_list_data,
            "房间": electrical_list_data,
            "电器": rooms_list_data,
            "其他服务": others_list_data,
        }
        # 标记为新会话，需要生成初始报价
        st.session_state["new_quote_needed"] = True
        st.switch_page("pages/quote_page.py")


if __name__ == '__main__':
    pricing_page()
