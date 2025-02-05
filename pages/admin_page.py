"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：admin_page.py.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午10:08
@Contact  ：king.songtao@gmail.com
"""
import datetime
import time
from datetime import date
import streamlit as st
from utils.utils import check_login_state, confirm_logout, navigation
import os
from utils.styles import apply_global_styles


def admin_page():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()

    login_state, role = check_login_state()
    # login_state = True

    navigation()

    st.title("📊管理控制台")
    st.divider()
    if login_state == True and role == "admin":
        # username = cookies.get("name")
        username = st.session_state['name']
        # 销售额计算模块
        total_sale = "29,814"
        col1, col2 = st.columns([0.5, 0.5])
        # with col1:
        #     st.write(f"本月总成交额: ", )
        #     if total_sale == None:
        #         total_sale_value = 0
        #     else:
        #         total_sale_value = total_sale
        #     st.subheader(f"$ {total_sale_value}")
        # with col2:
        #     st.write(f"悉尼时间: ", )
        #     st.subheader(f"{datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))).strftime('%H:%M:%S')}")

        a, b, c = st.columns(3)
        a.metric("本月总成交额", total_sale, "$395")
        b.metric("本月阿姨总支出", "10,269", "-$102")
        c.metric("本月毛利", "19,545", "$1,502")

        st.divider()
        # st.subheader("已派工单概览")
        st.info("已派工单概览", icon="ℹ️")
        # # 实现空闲阿姨显示
        # col1, col2, col3 = st.columns([1, 1, 1])
        # with col1:
        #     st.subheader(f"{datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))).strftime('%Y-%m-%d')}")
        #     st.write("小鱼组 | 🔵 空闲")
        #     st.write("海叔组 | 🔵 空闲")
        #     st.write("李姨组 | 🔵 空闲")
        # with col2:
        #     st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=1)).strftime('%Y-%m-%d')}")
        #     st.write("小鱼组 | 🔵 空闲")
        #     st.write("李姨组 | 🔵 空闲")
        #
        # with col3:
        #     st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=2)).strftime('%Y-%m-%d')}")
        #     st.write("小鱼组 | 🔵 空闲")
        #     st.write("海叔组 | 🔵 空闲")
        #     st.write("李姨组 | 🔵 空闲")
        #     st.write("Kitty组 | 🔵 空闲")
        # col4, col5, col6 = st.columns([1, 1, 1])
        # with col4:
        #     st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=3)).strftime('%Y-%m-%d')}")
        #     st.write("海叔组 | 🔵 空闲")
        #     st.write("李姨组 | 🔵 空闲")
        # with col5:
        #     st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=4)).strftime('%Y-%m-%d')}")
        #     st.write("李姨组 | 🔵 空闲")
        # with col6:
        #     st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=5)).strftime('%Y-%m-%d')}")
        #     st.write("小鱼组 | 🔵 空闲")
        #     st.write("海叔组 | 🔵 空闲")

        # today = datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))).strftime('%Y-%m-%d')
        # tomorrow = (datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
        # day_3 = (datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=2)).strftime('%Y-%m-%d')
        # day_4 = (datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=3)).strftime('%Y-%m-%d')
        # day_5 = (datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=4)).strftime('%Y-%m-%d')
        # day_6 = (datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=5)).strftime('%Y-%m-%d')
        #
        # tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([today, tomorrow, day_3, day_4, day_5, day_6])
        # with tab1:
        #     st.write("小鱼组 | 🔵 今日空闲 | 可派单")
        #     st.write("海叔组 | 🔵 今日空闲 | 可派单")
        # with tab2:
        #     st.write("小鱼组 | 🔵 今日空闲 | 可派单")
        #     st.write("海叔组 | 🔵 今日空闲 | 可派单")
        #     st.write("Kitty组 | 🔵 今日空闲 | 可派单")
        #     st.write("李姨组 | 🔵 今日空闲 | 可派单")
        # with tab3:
        #     st.write("🔴 今日当前无阿姨空闲")
        # with tab4:
        #     st.write("海叔组 | 🔵 今日空闲 | 可派单")
        #     st.write("Kitty组 | 🔵 今日空闲 | 可派单")
        #     st.write("李姨组 | 🔵 今日空闲 | 可派单")
        # with tab5:
        #     st.write("Kitty组 | 🔵 今日空闲 | 可派单")
        # with tab6:
        #     st.write("🔴 今日当前无阿姨空闲")

        tab1, tab2, tab3, tab4 = st.tabs(["海叔组", "小鱼组", "李姨组", "Kitty组"])
        with tab1:
            st.write("2024-12-31 | 5007/462 Elizabeth Street, Mel 3000 | 🔴 上午")
            st.write("2024-01-02 | 2007/105 Clarendon St, Southbank VIC 3006 | 🔴 其他")
            st.write("2024-01-05 | Unit 8308， 228 La Trobe St | 🔴 下午")
        with tab2:
            st.write("2024-12-31 | 850 Whitehorse Road，Box Hill，3128 | 🔴 上午")
            st.write("2024-01-02 | 329/11 Wellington StCollingwood VIC 3066 | 🔴 下午")
            st.write("2024-01-05 | 1807/18 Hoff Bvd southbank | 🔴 其他")
            st.write("2024-01-07 | 1611/105 Batman st West Melbourne | 🔴 下午")

        with tab3:
            st.write("2024-12-31 | 1001/421 Docklands Dr | 🔴 上午")
            st.write("2024-01-02 | 33 rose lane vic melbourbe 3000 | 🔴 下午")

        with tab4:
            st.write("2024-12-31 | 28 miranda road. Reservoir | 🔴 其他")
            st.write("2024-01-02 | 3311/500 Elizabeth St | 🔴 下午")
            st.write("2024-01-05 | 3 Kembla St Hawthorn | 🔴 下午")

        check_available = st.button("查询空闲阿姨", key="dispatch_button", use_container_width=True, type="primary")

        @st.dialog("查询空闲阿姨")
        def check_free():
            st.write("请输入要查询的日期及时间段")
            date = st.date_input("日期", value=None)
            time = st.selectbox("时间段", ["上午", "下午", "全天", "其他"])
            if st.button("查询", use_container_width=True, type="primary"):
                st.success(f"{date} | {time} | 空闲阿姨:", icon="✅")
                # st.success("海叔组 | 小鱼组", icon="✅")
                st.subheader("海叔组 | 小鱼组")

        if check_available:
            check_free()

        # # 工单概览
        # st.divider()
        # st.info("工单概览", icon="ℹ️")
        # tab1, tab2, tab3, tab4 = st.tabs(["海叔组", "小鱼组", "李姨组", "Kitty组"])
        # with tab1:
        #     sample_data = {
        #         "服务时间": ["2024-12-29", "2025-01-02", "2025-01-05"],
        #         "收款状态": ["已收款", "未收款", "已收款"],
        #         "收款金额": ["$275", "-", "$641"],
        #         "基础套餐": ["1B1B - 洗地毯", "1B2B - 蒸汽洗地毯", "1B2B - 蒸汽洗地毯"],
        #         "附加服务": ["冰箱，洗衣机，微波炉", "-", "烤箱，阳台"],
        #         "地址": ["1202/157 A'Beckett St, Melbourne VIC 3000", "Unit 102/488 Swanston Street，Carlton VIC3053", "1302N/889 Collins Street, Docklands VIC 3008"]
        #
        #     }
        #     st.dataframe(sample_data)
        # with tab2:
        #     sample_data = {
        #         "服务时间": ["2024-12-29", "2025-01-02", ],
        #         "收款状态": ["已收款", "已收款"],
        #         "收款金额": ["$275", "$641"],
        #         "基础套餐": ["1B1B - 洗地毯", "1B2B - 蒸汽洗地毯"],
        #         "附加服务": ["冰箱，洗衣机，微波炉", "烤箱，阳台"],
        #         "地址": ["Unit 102/488 Swanston Street，Carlton VIC3053", "1302N/889 Collins Street, Docklands VIC 3008"]
        #
        #     }
        #     st.dataframe(sample_data)
        # with tab3:
        #     st.warning("暂无工单", icon="⚠️")
        # with tab4:
        #     st.warning("暂无工单", icon="⚠️")

    elif login_state and role != "admin":
        error = st.error("您的权限不足！请联系系统管理员！3秒后跳转...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您的权限不足！请联系系统管理员！2秒后跳转...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您的权限不足！请联系系统管理员！1秒后跳转...", icon="⚠️")
        time.sleep(1)
        st.session_state["login_state"] = False
        st.switch_page("pages/login_page.py")
    else:
        error = st.error("您还没有登录！请先登录！3秒后跳转...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您还没有登录！请先登录！2秒后跳转...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您还没有登录！请先登录！1秒后跳转...", icon="⚠️")
        time.sleep(1)
        st.switch_page("pages/login_page.py")


if __name__ == '__main__':
    admin_page()
