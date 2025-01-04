"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：receipt_preview.py
@Author   ：King Songtao
@Time     ：2024/12/27 上午9:21
@Contact  ：king.songtao@gmail.com
"""
import io
import time
import mammoth
import streamlit as st
from utils.utils import check_login_state, extract_date_from_html, confirm_back, navigation


def receipt_preview():
    """
    收据预览界面
    :return:
    """
    # 验证登录状态
    login_state, role = check_login_state()

    if login_state and role == "admin" or role == "customer_service":

        navigation()

        if "receipt_data" in st.session_state:
            # 收据生成逻辑
            safe_filename = st.session_state['receipt_data']['address'].replace('/', '.')
            st.session_state['receipt_data']['receipt_file_name'] = f"Receipt.{safe_filename}.docx"
            st.title('🧾ATM Receipt')
            st.success(f"收据 >>>{st.session_state['receipt_data']['receipt_file_name']}<<< 创建成功！", icon="✅")
            st.info('点击"下载收据"按钮，即可下载Word收据。', icon="ℹ️")
            st.divider()

            # 发票预览模块
            custom_css = """
                    <style>
                    body {
                        font-family: Arial, sans-serif; /* 全局设置字体为 Arial */
                    }
                    .date-right {
                        text-align: right;
                        margin-bottom: 10px;
                        font-family: Arial, sans-serif; /* 确保日期部分也使用 Arial */
                    }
                    .other-content {
                        text-align: left;
                        font-family: Arial, sans-serif; /* Word 内容字体设置为 Arial */
                    }
                    .image-container {
                        width: 100%;
                        text-align: right;
                        margin: 10px 0;
                    }
                    /* 控制图片大小并右对齐 */
                    .other-content img {
                        max-width: 35%;
                        height: auto;
                        display: inline-block;  /* 改为inline-block以支持右对齐 */
                        margin: 0;  /* 移除自动边距 */
                    }
                    </style>
                    """

            # 使用 mammoth 转换 Word 文档内容为 HTML
            with io.BytesIO() as buffer:
                st.session_state['receipt_data']['ready_doc'].save(buffer)
                buffer.seek(0)
                result = mammoth.convert_to_html(buffer)
                html_content = result.value

            # 提取文档中的日期
            extracted_date = extract_date_from_html(html_content)

            # 如果找到了日期，渲染右对齐的日期
            if extracted_date:
                date_html = f'<div class="date-right">{extracted_date}</div>'
            else:
                date_html = ""  # 如果没有日期则不显示

            # 删除 HTML 中的日期内容（如果有的话）
            html_content = html_content.replace(extracted_date, "") if extracted_date else html_content

            # 将 mammoth 转换的 HTML 包裹在 "other-content" 样式中
            html_content_wrapped = f'<div class="other-content">{html_content}</div>'

            # 渲染自定义 CSS、日期和 Word 文档内容
            st.markdown(custom_css, unsafe_allow_html=True)
            st.markdown(date_html, unsafe_allow_html=True)  # 日期单独渲染，右对齐
            st.markdown(html_content_wrapped, unsafe_allow_html=True)  # 其他内容左对齐

            st.divider()

            # 将文档保存到内存
            output_buffer = io.BytesIO()
            st.session_state['receipt_data']['ready_doc'].save(output_buffer)
            output_buffer.seek(0)

            st.info("该模块仅用于收据快速生成，数据并不会保存至服务器，请及时下载留存，以防数据丢失！", icon="ℹ️")

            print(st.session_state['receipt_data']['ready_doc'])

            st.download_button(
                label="下载Word格式收据",
                data=output_buffer,
                file_name=st.session_state['receipt_data']['receipt_file_name'],
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                type="primary"  # 添加主要按钮样式
            )

            if st.button("返回", key="back_button", use_container_width=True):

                confirm_back()

        else:
            st.error("您还没有生成收据！请先生成收据后再预览！", icon="⚠️")
            st.switch_page("pages/receipt_page.py")
    else:
        st.error("您还没有登录或无权限！请联系系统管理员!5秒后跳转至登录页...", icon="⚠️")
        time.sleep(5)
        st.switch_page("pages/login_page.py")


if __name__ == '__main__':
    receipt_preview()
