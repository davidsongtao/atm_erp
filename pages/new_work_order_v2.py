"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：new_work_order_v2.py.py
@Author   ：King Songtao
@Time     ：2025/2/15 上午11:51
@Contact  ：king.songtao@gmail.com
"""
import asyncio
import time
import streamlit as st
from datetime import datetime, date

from utils.amount_calculator import calculate_total_amount
from utils.utils import navigation, check_login_state
from utils.db_operations_v2 import create_work_order, connect_db
from utils.styles import apply_global_styles
from utils.validator import get_validator


async def create_work_order_page():
    """创建新工单页面"""
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()

    # 初始化地址验证器
    if 'validator' not in st.session_state:
        api_key = st.secrets["api_keys"]["openai_api_key"]
        st.session_state.validator = get_validator(api_key)

    login_state, role = check_login_state()

    if login_state:
        navigation()
        st.title("➕创建新工单")
        st.divider()

        # 基础信息
        col1, col2, col3 = st.columns(3)
        with col1:
            order_date = st.date_input(
                "登记日期",
                value=date.today(),
                help="创建工单的日期",
                disabled=True  # 默认使用当天日期
            )

        with col2:
            work_date = st.date_input(
                "保洁日期",
                value=None,
                help="实际上门服务的日期（可选）"
            )

        with col3:
            # 生成时间选项
            time_options = []
            for hour in range(6, 22):
                for minute in range(0, 60, 15):
                    period = "上午" if hour < 12 else "下午"
                    time_str = f"{period} {hour:02d}:{minute:02d}"
                    time_options.append(time_str)

            work_time = st.selectbox(
                "保洁时间",
                options=[""] + time_options,
                index=0,
                help="选择保洁时间（可选）"
            )

        # 分配信息
        col1, col2, col3 = st.columns(3)
        with col1:
            # 获取所有用户列表
            conn = connect_db()
            users = conn.query("SELECT name FROM users ORDER BY name", ttl=0)['name'].tolist()
            current_user = st.session_state.get("name")
            # 设置当前用户为默认选项
            default_index = users.index(current_user) if current_user in users else 0
            created_by = st.selectbox(
                "工单创建人",
                options=users,
                index=default_index
            )

        with col2:
            source = st.text_input(
                "工单来源",
                placeholder="请输入客户来源"
            )

        with col3:
            # 获取所有活跃的保洁组
            cleaner_options = [""] + conn.query("""
                SELECT team_name
                FROM clean_teams
                WHERE team_name != '暂未派单' AND is_active = 1
                ORDER BY team_name
            """, ttl=0)['team_name'].tolist()

            assigned_cleaner = st.selectbox(
                "保洁小组",
                options=cleaner_options,
                index=0,
                help="选择保洁小组（可选）"
            )

        # 地址信息处理
        work_address = st.text_input(
            "工作地址",
            value=st.session_state.get("current_address", ""),
            key="address_input",
            placeholder="客户地址。例如：1202/157 A'Beckett St, Melbourne VIC 3000"
        )

        # 检查地址是否为空
        is_address_empty = not bool(work_address.strip())

        # 验证地址按钮
        validate_btn = st.button(
            "自动化验证地址",
            use_container_width=True,
            key="validate-address-btn",
            type="primary",
            disabled=is_address_empty,
            help="请输入地址以开始验证"
        )

        # Google搜索链接
        search_query = work_address.replace(' ', '+')
        search_url = f"https://www.google.com/search?q={search_query}+Australia"
        st.link_button(
            "🔍 在Google中搜索此地址",
            search_url,
            use_container_width=True,
            disabled=is_address_empty
        )

        # 地址验证处理
        address_valid = True
        if validate_btn and not is_address_empty:
            try:
                with st.spinner("验证地址中，耗时较长，请耐心等待，过程中请不要刷新页面..."):
                    matches = await st.session_state.validator.validate_address(work_address)

                    if matches:
                        # 根据验证来源显示不同的提示
                        if matches[0].validation_source == 'llm':
                            st.success("✅ 找到以下地址匹配：")
                        elif matches[0].validation_source == 'fallback':
                            st.warning("ℹ️ DeepSeek API暂时不可用，当前使用本地验证模式，请仔细核对地址：")
                        else:
                            st.warning("⚠️ 无法完全验证地址，请确保地址准确：")

                        # 显示匹配结果
                        for i, match in enumerate(matches):
                            cols = st.columns([6, 2, 1])
                            cols[0].write(f"🏠 {match.formatted_address}")
                            cols[1].write(f"匹配度: {match.confidence_score:.2f}")

                            # 使用回调函数处理选择
                            def select_address():
                                st.session_state.current_address = match.formatted_address

                            cols[2].button(
                                "选择",
                                key=f"select_{i}",
                                on_click=select_address,
                                use_container_width=True
                            )

                        # 如果是LLM验证失败或本地验证，显示Google搜索选项
                        if matches[0].validation_source != 'llm':
                            st.info("如果不确定地址是否正确，建议在Google中搜索确认：", icon="ℹ️")
                            st.link_button(
                                "🔍 在Google中搜索此地址",
                                search_url,
                                use_container_width=True
                            )
                    else:
                        st.warning("⚠️ 无法验证此地址，请检查输入是否正确。")
                        st.info("您可以：\n1. 检查地址拼写\n2. 确保包含门牌号和街道名\n3. 添加州名和邮编")
                        address_valid = False

            except Exception as e:
                st.error(f"地址验证服务暂时不可用: {str(e)}")
                st.info("您可以继续填写其他信息，稍后再尝试验证地址。")
                address_valid = True
            finally:
                await st.session_state.validator.close_session()

        # 收入信息
        col1, col2, col3 = st.columns(3)
        with col1:
            income1 = st.number_input(
                "收入1（现金）",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                help="现金收入金额"
            )

        with col2:
            income2 = st.number_input(
                "收入2（转账）",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                help="转账收入金额（不含GST）"
            )

        with col3:
            subsidy = st.number_input(
                "补贴金额",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                help="工单补贴金额（可选）"
            )

        invoice_status_options = ['未开票', '已开票', '不开票']
        invoice_status = st.selectbox(
            "发票状态",
            options=invoice_status_options,
            index=None,
            help="选择发票状态（可选）",
            placeholder="请选择..."
        )

        # 在显示总金额之前，使用计算函数
        order_amount, total_amount = calculate_total_amount(
            income1,
            income2,
            assigned_cleaner if assigned_cleaner else "暂未派单",
            conn
        )

        # 显示金额
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"订单金额：${order_amount:.2f}", icon="💰")
        with col2:
            st.info(f"总金额：${total_amount:.2f}", icon="💰")

        # 备注信息
        remarks = st.text_area(
            "备注信息",
            placeholder="请输入备注信息（可选）"
        )

        # 确认创建
        confirm_create = st.checkbox("我确认所有工单信息录入无误，立即创建工单！")
        create_btn = st.button("创建工单", use_container_width=True, type="primary")

        if create_btn:
            if not confirm_create:
                st.warning("请确认工单信息无误，并勾选确认按钮！", icon="⚠️")
            elif not work_address.strip():
                st.error("工作地址不能为空！", icon="⚠️")
            else:
                success, error = create_work_order(
                    order_date=order_date,
                    work_date=work_date if work_date else None,
                    work_time=work_time if work_time.strip() else None,
                    created_by=created_by,
                    source=source,
                    work_address=work_address,
                    assigned_cleaner=assigned_cleaner if assigned_cleaner else "暂未派单",
                    income1=income1,
                    income2=income2,
                    subsidy=subsidy if subsidy > 0 else None,
                    remarks=remarks,
                    invoice_status=invoice_status
                )

                if success:
                    st.success("工单创建成功！3秒后返回工单列表...", icon="✅")
                    time.sleep(3)
                    st.switch_page("pages/orders_statistics.py")
                else:
                    st.error(f"工单创建失败：{error}", icon="⚠️")

        if st.button("取消", use_container_width=True, type="secondary"):
            st.switch_page("pages/orders_statistics.py")

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


if __name__ == '__main__':
    asyncio.run(create_work_order_page())
