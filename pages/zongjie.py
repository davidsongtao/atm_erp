"""
Description: 课程总结页面

-*- Encoding: UTF-8 -*-
@File     ：zongjie.py
@Time     ：2025/2/9
"""
import time
import streamlit as st
from utils.utils import navigation, check_login_state
from utils.styles import apply_global_styles


@st.dialog("确认处理")
def confirm_process_dialog(uploaded_files):
    """确认处理文档的对话框"""
    st.write("即将处理以下文档:")
    # 每行显示一个文件名
    for file in uploaded_files:
        st.text(file.name)  # 使用 st.text 代替 st.write 来避免列表样式

    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认处理", type="primary", use_container_width=True):
            # 存储文件信息到session state
            st.session_state['files_to_process'] = uploaded_files
            # 跳转到处理页面
            st.switch_page("pages/class_result.py")

    with col2:
        if st.button("取消", use_container_width=True):
            confirm_cancel_dialog()


@st.dialog("确认取消")
def confirm_cancel_dialog():
    """确认取消处理的对话框"""
    st.warning("确定要取消处理吗？", icon="⚠️")
    st.info("返回后上传的文件将被清除，需要重新上传。", icon="ℹ️")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("确认取消", type="primary", use_container_width=True):
            # 清除session state中的文件
            if 'files_to_process' in st.session_state:
                del st.session_state['files_to_process']
            st.rerun()

    with col2:
        if st.button("继续处理", use_container_width=True):
            st.rerun()


def course_summary():
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
    login_state, role = check_login_state()

    if not login_state:
        error = st.error("您还没有登录！3秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        error.empty()
        error = st.error("您还没有登录！2秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        error.empty()
        st.error("您还没有登录！1秒后跳转至登录页面...", icon="⚠️")
        time.sleep(1)
        st.switch_page("pages/login_page.py")
    else:
        # 检查是否是特定用户
        current_user = st.session_state.get("logged_in_username")
        if current_user != "connie":
            error = st.error("您没有权限访问此页面！3秒后跳转至登录页面...", icon="⚠️")
            time.sleep(1)
            error.empty()
            error = st.error("您没有权限访问此页面！2秒后跳转至登录页面...", icon="⚠️")
            time.sleep(1)
            error.empty()
            st.error("您没有权限访问此页面！1秒后跳转至登录页面...", icon="⚠️")
            time.sleep(1)
            st.switch_page("pages/login_page.py")
        else:
            navigation()
            st.title("📚课程总结")
            st.divider()

            # 添加说明信息
            st.info("请上传您需要处理的记录文件，该文件应从通义听悟中直接导出，不要对导出文件进行任何修改。", icon="ℹ️")

            # 文件上传部分
            uploaded_files = st.file_uploader(
                "选择要处理的Word文档",
                type=['docx'],
                accept_multiple_files=True,
                key='file_uploader'
            )

            # 检查文件名是否重复并获取有效文件
            valid_files = []
            if uploaded_files:
                current_files = set()
                for file in uploaded_files:
                    if file.name not in current_files:
                        current_files.add(file.name)
                        valid_files.append(file)

            # 始终显示处理按钮，但根据是否有有效文件来决定是否禁用
            if st.button("开始处理",
                        type="primary",
                        use_container_width=True,
                        disabled=len(valid_files) == 0,  # 没有有效文件时禁用按钮
                        help="请先上传文件" if len(valid_files) == 0 else "点击开始处理"  # 根据状态显示不同的提示
                        ):
                confirm_process_dialog(valid_files)


if __name__ == '__main__':
    course_summary()