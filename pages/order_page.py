"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：order_page.py
@Author   ：King Songtao
@Time     ：2024/12/30 下午1:42
@Contact  ：king.songtao@gmail.com
"""
import datetime
import time

import streamlit as st
from utils.utils import navigation


def order_page():
    navigation()

    st.title("🤖工单管理")
    st.divider()

    col1, col2, col3 = st.columns(3)
    col1.metric("今日工单数：", "12", "3")
    col2.metric("今日工单总额：", "$1,532", "$395")
    col3.metric("未派遣工单数：", "6")

    st.divider()

    # 模拟工单数据
    order_data_muckup = {
        "工单编号": ["241230001", "241230002", "241230003", "241230004", "241230005", "241230006", "241230007", "241230008", "241230009", "241230010"],
        "服务日期": ["2024-12-31", "2024-12-31", "2025-01-02", "2025-01-03", "2025-01-03", "2025-01-05", "2025-01-08", "2025-01-07", "2025-01-04", "2025-01-04"],
        "服务地址": ["5506/500 Elizabeth St", "U5007/160 Victoria street Carlton", "609/594 Saint Kilda Road", "304/462 Elizabeth St", "2704/8 Exploration lane, Melbourne", "850 Whitehorse Road，Box Hill，3128", "3009/462 Elizabeth Street",
                     "12 docile Avenue clyde", "314/7 Dudley street caulfield East", "229 Toorak Road, South Yarra"],
        "已派单": ["✅", "❌", "✅", "❌", "✅", "❌", "✅", "❌", "❌", "✅"],
        "保洁阿姨": ["海叔组", "-", "海叔组", "-", "李姨组", "-", "小鱼组", "-", "-", "Kitty组"],
        "工单总额": ["$480", "$535", "$1180", "$325", "$294", "$480", "$415", "$216", "$385", "$190"],
        "已收款": ["✅", "✅", "❌", "✅", "✅", "❌", "❌", "✅", "❌", "✅"],
        "分配人": ["Alex", "Jessica", "Connie", "Connie", "Connie", "Alex", "Ares", "Ares", "Jessica", "Jessica"]
    }

    st.dataframe(order_data_muckup, use_container_width=True)

    if st.button("➕创建工单", use_container_width=True, type="primary"):

        basic_service = ["Steam clean of the carpet", "Steam clean of the mattress", "Steam clean of the sofa", "Vacuum clean of carpet", "Floor boards/Floor tiles mopping"]
        rooms = ["Bedroom", "Bathroom", "Kitchen"]
        electrical = ["Microwave", "Oven", "Dishwasher", "Refrigerator", "Washing machine", "Dryer", "Air conditioner"]
        others = ["Skirting board/Window frame/Wardrobe", "Blinds", "Window glasses", "Balcony with sliding door windows", "Wall marks removal", "Pet hair removal", "Rubbish removal", "Mould removal"]

        @st.dialog("创建新的工单")
        def new_order():
            st.write("分配人:", "Alex")
            address = st.text_input("服务地址", placeholder="请输入服务地址")
            col1, col2 = st.columns([1, 1])
            with col1:
                st.date_input("服务日期", value=None)
                st.multiselect("基础服务", options=basic_service, key="service_list")
                st.multiselect("电器", options=electrical, key="rooms_list")
                st.selectbox("已派单", options=["✅", "❌"], key="dispatch_order", index=None)
            with col2:
                st.number_input("工单总额", value=0, step=1)
                st.multiselect("房间", options=rooms, key="electrical_list")
                st.multiselect("其他服务", options=others, key="others_list")
                st.selectbox("已收款", options=["✅", "❌"], key="receipt", index=None)
            if st.button("确认提交", use_container_width=True, type="primary"):
                try:
                    succ = st.success("工单创建成功！3秒后刷新...", icon="✅")
                    time.sleep(1)
                    succ.empty()
                    succ = st.success("工单创建成功！2秒后刷新...", icon="✅")
                    time.sleep(1)
                    succ.empty()
                    st.success("工单创建成功！1秒后刷新...", icon="✅")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"创建失败！错误信息：{e}", icon="⚠️")

        new_order()

    if st.button("📝修改工单", use_container_width=True, type="primary"):
        st.warning("修改工单功能暂未开放！", icon="⚠️")

    if st.button("❌删除工单", use_container_width=True, type="secondary"):

        @st.dialog("删除工单")
        def delete_order():
            order_id = st.text_input("请输入要删除的工单编号：", placeholder="请输入工单编号")
            if st.button("查询", use_container_width=True, type="primary"):
                st.write("工单编号：", order_id, " | 地址：5506/500 Elizabeth St", )
            if st.button("确认删除", use_container_width=True):
                st.rerun()

        delete_order()


if __name__ == '__main__':
    order_page()
