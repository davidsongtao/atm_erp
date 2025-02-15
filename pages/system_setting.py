"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：system_setting.py.py
@Author   ：King Songtao
@Time     ：2025/1/8 上午12:08
@Contact  ：king.songtao@gmail.com
"""
import time

import streamlit as st
from utils.utils import navigation, check_login_state
from utils.db_operations_v2 import update_account, login_auth
from utils.styles import apply_global_styles


def system_settings():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("⚙️系统设置")

        tab1, tab2, tab3, tab4 = st.tabs(["👤 个人信息", "🔑 修改密码", "🎨 界面设置", "🔧 系统配置"])

        with tab1:
            personal_info_settings()

        with tab2:
            password_settings()

        with tab3:
            appearance_settings()

        with tab4:
            system_config_settings()

    else:
        error = st.error("您还没有登录！3秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您还没有登录！2秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您还没有登录！1秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        st.switch_page("pages/login_page.py")


def personal_info_settings():
    # 获取当前用户信息
    current_user = st.session_state.get("logged_in_username")
    name = st.session_state.get("name")

    # 头像上传（预留）
    st.info("头像功能开发中...", icon="ℹ️")

    # 基本信息修改
    new_name = st.text_input("用户名", value=name)
    contact_email = st.text_input("联系邮箱", value=current_user)
    phone = st.text_input("联系电话", value="", placeholder="请输入联系电话")

    confirm_edit = st.checkbox("我确定想要进行个人信息修改！我已知晓此操作不可逆！", value=False, key="confirm_password_change")
    confirm_edit_btn = st.button("确认修改", use_container_width=True, type="primary", key="confirm_password_change_YES")
    if confirm_edit_btn and confirm_edit:
        st.warning("个人信息修改模块正在开发中，暂时不可用...", icon="⚠️")

    elif confirm_edit_btn and not confirm_edit:
        st.error("请勾选确认信息后进行提交！", icon="⚠️")

    if st.button("取消", use_container_width=True, type="secondary", key="personal_info_cancel"):
        st.switch_page("pages/orders_statistics.py")


def password_settings():
    current_password = st.text_input("当前密码", type="password")
    col1, col2 = st.columns(2)
    with col1:
        new_password = st.text_input("新密码", type="password")
    with col2:
        confirm_password = st.text_input("确认新密码", type="password")

    st.info("修改密码后，需要重新登录！", icon="ℹ️")

    confirm_password = st.checkbox("我确定想要进行密码修改！我已知晓此操作不可逆！", value=False, key="super_password")
    edit_password = st.button("确认修改", use_container_width=True, type="primary")

    if edit_password and confirm_password:
        if not current_password or not new_password or not confirm_password:
            st.error("请填写所有密码字段！", icon="⚠️")
            return
        if new_password != confirm_password:
            st.error("两次输入的新密码不一致！", icon="⚠️")
            return

        # 验证当前密码
        username = st.session_state.get("logged_in_username")
        login_state, _, error_message, _ = login_auth(username, current_password)
        if not login_state:
            st.error("当前密码错误！", icon="⚠️")
            return

        # 更新密码
        success, error = update_account(username, st.session_state.name, new_password)
        if success:
            st.success("密码修改成功！请重新登录...", icon="✅")
            time.sleep(2)
            st.session_state.clear()
            st.switch_page("pages/login_page.py")
        else:
            st.error(f"密码修改失败：{error}", icon="⚠️")

    elif edit_password and not confirm_password:
        st.error("请勾选确认信息后进行提交！", icon="⚠️")

    if st.button("取消", use_container_width=True, type="secondary", key="confirm_password_change_no"):
        st.switch_page("pages/orders_statistics.py")


def appearance_settings():
    import toml
    import os

    # 加载当前配置
    config_path = ".streamlit/config.toml"
    try:
        if os.path.exists(config_path):
            with open(config_path, "r", encoding='utf-8') as f:
                current_config = toml.load(f)
        else:
            current_config = {"theme": {"primaryColor": "#1E88E5"}}
    except Exception as e:
        st.error(f"加载配置文件失败: {str(e)}")
        current_config = {"theme": {"primaryColor": "#1E88E5"}}

    # 主题色选择
    theme_color = st.color_picker(
        "选择主题色",
        value=current_config.get("theme", {}).get("primaryColor", "#1E88E5")
    )

    # 主题模式选择
    theme_modes = {
        "Light": {
            "backgroundColor": "#FFFFFF",
            "textColor": "#000000",
            "secondaryBackgroundColor": "#F0F2F6"
        },
        "Dark": {
            "backgroundColor": "#0E1117",
            "textColor": "#FFFFFF",
            "secondaryBackgroundColor": "#262730"
        }
    }

    current_mode = "Light"
    if current_config.get("theme", {}).get("backgroundColor") == "#0E1117":
        current_mode = "Dark"

    theme_mode = st.radio(
        "选择主题模式",
        options=["Light", "Dark"],
        index=0 if current_mode == "Light" else 1,
        horizontal=True
    )

    # 预览效果

    confirm_change_theme = st.checkbox("我确定想要进行主题设置！", value=False,
                                       key="confirm_change_theme")

    save_change = st.button("保存设置", use_container_width=True, type="primary")

    if save_change and confirm_change_theme:
        try:
            # 准备新的配置
            if "theme" not in current_config:
                current_config["theme"] = {}

            # 更新主题配置
            current_config["theme"]["primaryColor"] = theme_color
            current_config["theme"].update(theme_modes[theme_mode])

            # 保存到配置文件
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, "w", encoding='utf-8') as f:
                toml.dump(current_config, f)

            st.success("主题设置已保存！请刷新页面查看效果。", icon="✅")

        except Exception as e:
            st.error(f"保存主题设置失败: {str(e)}", icon="⚠️")

    elif save_change and not confirm_change_theme:
        st.error("请勾选确认信息后进行提交！", icon="⚠️")

    if st.button("立即刷新", use_container_width=True, type="secondary",
                 key="change_theme_cancel"):
        st.switch_page("pages/orders_statistics.py")


def system_config_settings():
    st.info("清除缓存功能将会清除掉所有浏览器缓存的数据，清除后需重新登录！", icon="ℹ️")
    clear_cache_confirm = st.checkbox("我确定想要清除缓存！我已知晓此操作不可逆！", value=False, key="clear_cache_confirm")
    clear_cache = st.button("清除缓存", use_container_width=True, type="primary")

    if clear_cache and clear_cache_confirm:
        st.session_state.clear()
        st.success("缓存已清除！需要重新登录...")
        time.sleep(2)
        st.switch_page("app.py")

    elif clear_cache and not clear_cache_confirm:
        st.error("请勾选确认信息后进行提交！", icon="⚠️")

    if st.button("取消", use_container_width=True, type="secondary", key="clear_coach_no"):
        st.switch_page("pages/orders_statistics.py")


if __name__ == '__main__':
    system_settings()
