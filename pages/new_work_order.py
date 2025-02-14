"""
Description: 新版工单创建实现

-*- Encoding: UTF-8 -*-
@Author   ：Claude
@Time     ：2025/2/14
"""
import time
import streamlit as st
from datetime import datetime, date
from utils.utils import navigation, check_login_state
from utils.db_operations import create_work_order, connect_db
from utils.styles import apply_global_styles


def generate_time_options():
    """生成时间选项列表，每15分钟一个间隔"""
    time_options = []
    # 上午时间选项 (8:00 - 11:45)
    for hour in range(8, 12):
        for minute in range(0, 60, 15):
            time_str = f"上午 {hour:02d}:{minute:02d}"
            time_options.append(time_str)
    # 下午时间选项 (12:00 - 21:45)
    for hour in range(12, 22):
        for minute in range(0, 60, 15):
            time_str = f"下午 {hour:02d}:{minute:02d}"
            time_options.append(time_str)
    return time_options


def handle_custom_items():
    """处理自定义项目的添加和删除"""
    # 添加自定义 CSS 来隐藏特定文本输入框的标签
    st.markdown("""
        <style>
            .custom-item-input label {
                display: none !important;
                height: 0px !important;
                margin: 0px !important;
                padding: 0px !important;
            }
            .custom-item-input .st-emotion-cache-1umgz6j {
                margin-top: 0px !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # 初始化或更新 session state
    if 'custom_items' not in st.session_state:
        st.session_state.custom_items = [""]

    # 添加新项目的按钮
    if st.button("新增一个自定义项", use_container_width=True):
        st.session_state.custom_items.append("")
        st.rerun()

    # 创建输入字段
    updated_items = []
    for idx, item in enumerate(st.session_state.custom_items):
        col1, col2 = st.columns([5, 1])

        with col1:
            new_value = st.text_input(
                " ",
                value=item,
                key=f"custom_item_{idx}",
                placeholder=f"请输入第{idx + 1}个自定义项目内容...",
                label_visibility="collapsed",
            )
            updated_items.append(new_value)

        with col2:
            if st.button("删除", key=f"delete_custom_{idx}", use_container_width=True):
                st.session_state.custom_items.pop(idx)
                st.rerun()

    st.session_state.custom_items = updated_items
    return [item for item in updated_items if item.strip()]


def get_users():
    """获取所有用户名"""
    conn = connect_db()
    if conn:
        try:
            result = conn.query("SELECT name FROM users ORDER BY name", ttl=0)
            return result['name'].tolist()
        except Exception as e:
            st.error(f"获取用户列表失败：{e}")
            return []
    return []


def create_work_order_page():
    """创建新工单页面"""
    st.set_page_config(page_title='ATM-Cleaning', page_icon='images/favicon.png')
    apply_global_styles()
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
                disabled=True
            )

        with col2:
            # 可选的工作日期
            work_date = st.date_input(
                "保洁日期",
                value=None,
                help="实际上门服务的日期（可选）",
                min_value=date.today()
            )

        with col3:
            # 可选的工作时间
            work_time = st.selectbox(
                "保洁时间",
                options=[""] + generate_time_options(),
                index=0,
                help="选择保洁时间（可选）"
            )

        # 分配信息
        col1, col2 = st.columns(2)
        with col1:
            # 获取所有用户列表
            users = get_users()
            current_user = st.session_state.get("name")
            # 设置当前用户为默认选项
            default_index = users.index(current_user) if current_user in users else 0
            created_by = st.selectbox(
                "工单所有人",
                options=users,
                index=default_index
            )

        with col2:
            source = st.text_input("工单来源", placeholder="请输入客户来源")

        # 地址信息
        work_address = st.text_input(
            "工作地址",
            value=st.session_state.get("current_address", ""),
            key="address_input",
            placeholder="客户地址。例如：1202/157 A'Beckett St, Melbourne VIC 3000"
        )

        # 房型和保洁组信息
        col1, col2 = st.columns(2)
        with col1:
            room_type = st.selectbox(
                "清洁房间户型",
                options=["1b1b", "2b1b", "2b2b", "3b2b"],
                index=None,
                placeholder="请选择房间户型",
            )

        with col2:
            # 获取所有活跃的保洁组
            conn = connect_db()
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

        # 服务项目
        service_options = {
            "basic_service": ["Steam clean of the carpet", "Steam clean of the mattress",
                              "Steam clean of the sofa", "Vacuum clean of carpet",
                              "Floor boards/Floor tiles mopping"],
            "rooms": ["Bedroom", "Bathroom", "Kitchen"],
            "electricals": ["Microwave", "Oven", "Dishwasher", "Refrigerator",
                            "Washing machine", "Dryer", "Air conditioner"],
            "other_services": ["Skirting board/Window frame/Wardrobe", "Blinds", "Window glasses",
                               "Balcony with sliding door windows", "Wall marks removal",
                               "Furniture wipe off", "Pet hair removal", "Rubbish removal",
                               "Mould removal"]
        }

        col1, col2 = st.columns(2)
        with col1:
            basic_services = st.multiselect(
                "基础服务",
                options=service_options["basic_service"],
                placeholder="选择基础服务项目..."
            )
            electrical_services = st.multiselect(
                "电器服务",
                options=service_options["electricals"],
                placeholder="选择电器服务项目..."
            )
        with col2:
            room_services = st.multiselect(
                "房间服务",
                options=service_options["rooms"],
                placeholder="选择房间服务项目..."
            )
            other_services = st.multiselect(
                "其他服务",
                options=service_options["other_services"],
                placeholder="选择其他服务项目..."
            )

        # 自定义服务项目
        custom_service = st.checkbox("添加自定义服务项目")
        if custom_service:
            custom_item = handle_custom_items()
        else:
            custom_item = []

        st.divider()

        # 收款信息
        col1, col2, col3 = st.columns(3)
        with col1:
            income1 = st.number_input(
                "收入1（现金）",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                help="现金收入金额（可选）"
            )

        with col2:
            income2 = st.number_input(
                "收入2（转账）",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                help="转账收入金额（可选）"
            )

        with col3:
            subsidy = st.number_input(
                "补贴金额",
                min_value=0.0,
                value=0.0,
                format="%.2f",
                help="工单补贴金额（可选）"
            )

        # 开票信息
        col1, col2, col3 = st.columns(3)
        with col1:
            paperwork = st.selectbox(
                "开票方式",
                options=[0, 1],
                format_func=lambda x: "开发票" if x == 0 else "开收据",
                index=None,
                placeholder="请选择...",
                help="选择开具发票或收据（可选）",
                key="paperwork_type"
            )

        with col2:
            invoice_sent = st.selectbox(
                "发票状态",
                options=[False, True],
                format_func=lambda x: "未开发票" if not x else "已开发票",
                disabled=paperwork != 0,
                help="选择发票开具状态",
                key="invoice_status"
            )

        with col3:
            receipt_sent = st.selectbox(
                "收据状态",
                options=[False, True],
                format_func=lambda x: "未开收据" if not x else "已开收据",
                disabled=paperwork != 1,
                help="选择收据开具状态",
                key="receipt_status"
            )
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
                # 设置支付方式和订单金额
                payment_method = None
                order_amount = 0.0
                total_amount = 0.0

                if income1 > 0:
                    payment_method = 'cash'
                    order_amount = income1
                    total_amount = income1
                elif income2 > 0:
                    payment_method = 'transfer'
                    order_amount = income2 / 1.1  # 去除GST
                    total_amount = income2

                success, error = create_work_order(
                    order_date=order_date,
                    work_date=work_date if work_date else None,
                    work_time=work_time if work_time.strip() else None,
                    created_by=created_by,
                    source=source,
                    work_address=work_address,
                    room_type=room_type,
                    assigned_cleaner=assigned_cleaner if assigned_cleaner else "暂未派单",
                    payment_method=payment_method,
                    order_amount=order_amount,
                    total_amount=total_amount,
                    subsidy=subsidy if subsidy > 0 else None,
                    remarks=remarks,
                    basic_service=basic_services,
                    rooms=room_services,
                    electricals=electrical_services,
                    other_services=other_services,
                    custom_item=custom_item,
                    paperwork=paperwork,
                    invoice_sent=invoice_sent if paperwork == 0 else False,
                    receipt_sent=receipt_sent if paperwork == 1 else False
                )

                if success:
                    st.success("工单创建成功！3秒后返回工单列表...", icon="✅")
                    time.sleep(3)
                    st.switch_page("pages/orders_show.py")
                else:
                    st.error(f"工单创建失败：{error}", icon="⚠️")

        if st.button("取消", use_container_width=True, type="secondary"):
            st.switch_page("pages/orders_show.py")

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


if __name__ == "__main__":
    create_work_order_page()
