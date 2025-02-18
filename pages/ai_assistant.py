"""
Description: AI智能问答助手页面

-*- Encoding: UTF-8 -*-
@File     ：ai_assistant.py
@Author   ：King Songtao
@Time     ：2024/12/26 下午8:36
"""
import streamlit as st
from langchain.memory import ConversationBufferMemory
from utils.utils import get_response, stream_res, navigation, check_login_state
from utils.styles import apply_global_styles

# 页面配置必须是第一个Streamlit命令
st.set_page_config(
    page_title="AI Assistant",
    page_icon="🤖",
    layout="wide"
)


def get_user_chat_key(username):
    """获取用户特定的聊天记录键"""
    return f"chat_messages_{username}"


def get_user_memory_key(username):
    """获取用户特定的记忆键"""
    return f"chat_memory_{username}"


def clear_chat_history():
    """清空聊天记录"""
    username = st.session_state.get("logged_in_username")
    chat_key = get_user_chat_key(username)
    memory_key = get_user_memory_key(username)

    # 清空聊天记录和记忆
    st.session_state[chat_key] = []
    st.session_state[memory_key] = ConversationBufferMemory()

    # 强制重新加载页面
    st.rerun()


def init_session_state():
    """初始化会话状态"""
    # 检查登录状态
    login_state, _ = check_login_state()
    if not login_state:
        st.error("请先登录！")
        st.switch_page("app.py")
        return False

    # 获取当前登录用户
    username = st.session_state.get("logged_in_username")
    if not username:
        st.error("无法获取用户信息！")
        st.switch_page("app.py")
        return False

    # 初始化用户特定的聊天记录和记忆
    chat_key = get_user_chat_key(username)
    memory_key = get_user_memory_key(username)

    if chat_key not in st.session_state:
        st.session_state[chat_key] = []
    if memory_key not in st.session_state:
        st.session_state[memory_key] = ConversationBufferMemory()

    # 初始化清除标志
    if "should_clear_chat" not in st.session_state:
        st.session_state.should_clear_chat = False

    return True


def main():
    # 应用全局样式
    apply_global_styles()

    # 初始化会话状态并检查登录
    if not init_session_state():
        return

    # 获取当前用户的聊天记录和记忆
    username = st.session_state.get("logged_in_username")
    chat_key = get_user_chat_key(username)
    memory_key = get_user_memory_key(username)

    # 侧边栏导航
    navigation()

    # 主页面
    st.title(f"🤖 {username} 的 AI 助手")
    st.divider()

    # 清理聊天记录按钮 - 移到聊天记录显示之前
    if len(st.session_state[chat_key]) > 0:
        col1, col2 = st.columns([6, 1])
        with col2:
            if st.button("清空记录", type="secondary", use_container_width=True):
                clear_chat_history()

    # 显示聊天历史
    for message in st.session_state[chat_key]:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # 用户输入
    if prompt := st.chat_input("请输入您的问题..."):
        # 添加用户消息到历史
        st.session_state[chat_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # 获取AI响应
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            full_response = get_response(prompt, st.session_state[memory_key])

            # 流式输出
            displayed_response = ""
            for char in stream_res(full_response):
                displayed_response += char
                response_placeholder.markdown(displayed_response + "▌")
            response_placeholder.markdown(displayed_response)

            # 添加AI响应到历史
            st.session_state[chat_key].append({"role": "assistant", "content": full_response})


if __name__ == "__main__":
    main()
