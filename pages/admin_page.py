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

import streamlit as st
from utils.utils import check_login_state, log_out
import os


def admin_page():
    login_state, role = check_login_state()
    # login_state = True
    st.sidebar.title("🏠ATM Cleaning Service")
    st.sidebar.divider()
    if st.sidebar.button("➕创建收据", key="open_receipt_button", use_container_width=True, type="primary"):
        st.switch_page("pages/receipt_page.py")
    # 工单管理
    if st.sidebar.button("🔍工单管理", key="order_management", use_container_width=True, type="primary"):
        st.sidebar.warning("该功能正在开发中，敬请期待！", icon="⚠️")
    # 保洁阿姨管理
    if st.sidebar.button("👩‍👩‍👧‍👦阿姨管理", key="staff_management_button", use_container_width=True, type="primary"):
        st.sidebar.warning("该功能正在开发中，敬请期待！", icon="⚠️")
    # 自动化报价
    if st.sidebar.button("💰生成报价", key="auto_quote_button", use_container_width=True, type="primary"):
        # st.switch_page("pages/auto_quote_page.py")
        st.sidebar.warning("该功能正在开发中，敬请期待！", icon="⚠️")
    # 自动化报价
    if st.sidebar.button("🤖智能助理", key="ai_assistant", use_container_width=True, type="primary"):
        # st.switch_page("pages/auto_quote_page.py")
        st.sidebar.warning("该功能正在开发中，敬请期待！", icon="⚠️")

    # 用户管理模块
    if st.sidebar.button("👥账户管理", key="user_management_button", use_container_width=True, type="primary"):
        st.switch_page("pages/staff_acc.py")
        # st.warning("该功能正在开发中，敬请期待！", icon="⚠️")
    st.sidebar.divider()

    # 退出登录模块
    if st.sidebar.button("🛏️退出登录", key="logout_button", use_container_width=True):
        log_out()

    st.sidebar.write("Copyright 2025 © ATM Cleaning Inc.")
    st.sidebar.write("Version：V2024.12.27.00.01")

    st.title("📊管理控制台")
    st.divider()
    if login_state == True and role == "admin":
        # username = cookies.get("name")
        username = st.session_state['name']
        # 销售额计算模块
        total_sale = "29,814"
        col1, col2 = st.columns([0.5, 0.5])
        with col1:
            st.write(f"本月总成交额: ", )
            if total_sale == None:
                total_sale_value = 0
            else:
                total_sale_value = total_sale
            st.subheader(f"$ {total_sale_value}")
        with col2:
            st.write(f"悉尼时间: ", )
            st.subheader(f"{datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))).strftime('%H:%M:%S')}")

        st.divider()
        st.info("空闲阿姨情况概览", icon="ℹ️")
        # 实现空闲阿姨显示
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            st.subheader(f"{datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))).strftime('%Y-%m-%d')}")
            st.write("小鱼组 | 🔵 空闲")
            st.write("海叔组 | 🔵 空闲")
            st.write("李姨组 | 🔵 空闲")
        with col2:
            st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=1)).strftime('%Y-%m-%d')}")
            st.write("小鱼组 | 🔵 空闲")
            st.write("李姨组 | 🔵 空闲")

        with col3:
            st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=2)).strftime('%Y-%m-%d')}")
            st.write("小鱼组 | 🔵 空闲")
            st.write("海叔组 | 🔵 空闲")
            st.write("李姨组 | 🔵 空闲")
            st.write("Kitty组 | 🔵 空闲")
        col4, col5, col6 = st.columns([1, 1, 1])
        with col4:
            st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=3)).strftime('%Y-%m-%d')}")
            st.write("海叔组 | 🔵 空闲")
            st.write("李姨组 | 🔵 空闲")
        with col5:
            st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=4)).strftime('%Y-%m-%d')}")
            st.write("李姨组 | 🔵 空闲")
        with col6:
            st.subheader(f"{(datetime.datetime.now().astimezone(datetime.timezone(datetime.timedelta(hours=11))) + datetime.timedelta(days=5)).strftime('%Y-%m-%d')}")
            st.write("小鱼组 | 🔵 空闲")
            st.write("海叔组 | 🔵 空闲")



    elif login_state and role != "admin":
        error = st.error("您的权限不足！请联系系统管理员！3秒后跳转...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您的权限不足！请联系系统管理员！2秒后跳转...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您的权限不足！请联系系统管理员！1秒后跳转...", icon="⚠️")
        time.sleep(1)
        # cookies['is_logged_in'] = "0"
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
