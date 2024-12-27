"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：admin_page.py.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午10:08
@Contact  ：king.songtao@gmail.com
"""
import time

import streamlit as st
from utils.utils import check_login_state, log_out
import os


def admin_page():
    login_state, role = check_login_state()
    # login_state = True
    st.title("📊管理控制台")
    st.divider()
    if login_state == True and role == "admin":
        # username = cookies.get("name")
        username = st.session_state['name']
        # 销售额计算模块
        total_sale = 1000
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write(f"本月总成交额: ", )
            if total_sale == None:
                total_sale_value = 0
            else:
                total_sale_value = total_sale
            st.subheader(f"$ {total_sale_value}(示例数据)")
        with col2:
            st.write(f"本月已赚取佣金: ", )
            if total_sale == None:
                total_commission = 0
            else:
                total_commission = round(total_sale * 0.024, 2)
            st.subheader(f"$ {total_commission}(示例数据)")
        st.divider()
        st.success(f"{username} 您好，欢迎来到ATM员工管理控制台！", icon="👋")
        st.info("请选择您要使用的模块", icon="ℹ️")
        # 开收据模块
        if st.button("🧾收据自动化", key="open_receipt_button", use_container_width=True, type="primary"):
            st.switch_page("pages/receipt_page.py")
        # 自动化报价
        if st.button("💰自动化报价", key="auto_quote_button", use_container_width=True, type="primary"):
            # st.switch_page("pages/auto_quote_page.py")
            st.warning("该功能正在开发中，敬请期待！", icon="⚠️")
        # 用户管理模块
        if st.button("👥员工账户管理", key="user_management_button", use_container_width=True, type="primary"):
            st.switch_page("pages/staff_acc.py")
            # st.warning("该功能正在开发中，敬请期待！", icon="⚠️")

        # 退出登录模块
        st.session_state["logout_button_disabled"] = False
        logout_check = st.checkbox("我希望退出登录！")
        if logout_check:
            if st.button("🛏️退出登录", key="logout_button", use_container_width=True, disabled=st.session_state["logout_button_disabled"]):
                log_out()
        else:
            st.session_state["logout_button_disabled"] = True
            st.button("🛏️退出登录", key="logout_button", use_container_width=True, disabled=st.session_state["logout_button_disabled"])

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
