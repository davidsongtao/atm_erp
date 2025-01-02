"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：quote_page.py
@Author   ：King Songtao
@Time     ：2024/12/30 下午3:15
@Contact  ：king.songtao@gmail.com
"""
from utils.utils import navigation, stream_res, get_response
import streamlit as st
from configs.settings import BaseConfig
from langchain.memory import ConversationBufferMemory


def get_price_mapping():
    """获取服务项目与价格的映射关系"""
    standard_prices = BaseConfig().STANDARD_PRICE
    return {
        # 基础服务映射
        "Steam clean of the sofa": ("沙发-蒸汽清洁", standard_prices.get("1B1B(steam)", 275)),
        "Vacuum clean of carpet": ("地毯-吸尘清洁", standard_prices.get("1B1B(None-steam)", 220)),

        # 电器映射
        "Microwave": ("微波炉", standard_prices.get("Microwave", 50)),
        "Oven": ("烤箱", standard_prices.get("Oven", 50)),
        "Dishwasher": ("洗碗机", standard_prices.get("Dishwasher", 25)),
        "Refrigerator": ("冰箱", standard_prices.get("Refrigerator", 50)),
        "Washing machine": ("洗衣机", standard_prices.get("Washing machine", 25)),
        "Dryer": ("烘干机", standard_prices.get("Dryer", 25)),
        "Air conditioner": ("空调", standard_prices.get("Air conditioner", 25)),

        # 其他服务映射
        "Window glasses": ("窗户玻璃", standard_prices.get("Window glasses", 8)),
        "Blinds": ("百叶窗", standard_prices.get("Blinds", 80)),
        "1B1B(steam)": ("1B1B房型-蒸汽清洁", standard_prices.get("1B1B(steam)", 275)),
        "1B1B(None-steam)": ("1B1B房型- 无蒸汽清洁", standard_prices.get("1B1B(None-steam)", 220)),
        "2B1B(steam)": ("2B1B房型-蒸汽清洁", standard_prices.get("2B1B(steam)", 320))
    }


def calculate_total_price(selected_services):
    """计算所选服务的总价"""
    price_mapping = get_price_mapping()
    total = 0
    service_details = []

    for category, items in selected_services.items():
        for item in items:
            if item in price_mapping:
                chinese_name, price = price_mapping[item]
                total += price
                service_details.append((chinese_name, price))

    return total, service_details


def format_initial_prompt():
    """格式化初始报价的提示词"""
    pricing_details = st.session_state.get("pricing_details", {})
    total_price, service_details = calculate_total_price(pricing_details)

    # 构建详细的服务列表字符串
    services_list = ""
    for service, price in service_details:
        services_list += f"- {service} | {price} 元\n"

    return (
        "请根据以下标准价格生成一份正式的清洁服务报价单：\n\n"
        "1. 服务项目明细和单价：\n"
        f"{services_list}\n"
        f"2. 总价格：{total_price} 元\n\n"
        "请使用以下格式生成报价单：\n"
        "• 使用专业的语气\n"
        "• 价格必须严格按照提供的标准价格\n"
        "• 如果客户选择的服务项目价格表中没有，请告知需要单独询价\n"
        "• 落款是ATM Cleaning Service"

    )


def preprocess_response(response):
    """预处理AI返回的响应，确保格式正确"""
    response = response.replace('\n', '  \n')
    response = response.replace('\\n', '  \n')
    response = response.replace('|', ' | ')
    response = response.replace('# ', '\n# ')
    response = response.replace('## ', '\n## ')
    return response


def quote_page():
    navigation()
    st.title("⌨️自动化智能报价")
    st.divider()

    # 初始化会话状态
    if "memory" not in st.session_state:
        st.session_state["memory"] = ConversationBufferMemory(return_messages=True)
        st.session_state["messages"] = []
        st.session_state["current_quote"] = None  # 存储当前的报价单内容

    # 如果是新的报价请求，生成初始报价
    if st.session_state.get("new_quote_needed", False):
        initial_prompt = format_initial_prompt()

        try:
            with st.spinner("正在生成初始报价单..."):
                response = get_response(initial_prompt, st.session_state["memory"])

                if response:
                    formatted_response = preprocess_response(response)
                    st.session_state["messages"] = [{
                        "role": "ai",
                        "content": formatted_response
                    }]
                    st.session_state["current_quote"] = formatted_response  # 保存初始报价单
                else:
                    st.error("生成初始报价单时出错")
        except Exception as e:
            st.error(f"生成报价时发生错误: {str(e)}")

        st.session_state["new_quote_needed"] = False

    # 显示所有历史消息
    for message in st.session_state["messages"]:
        content = message["content"]
        if message["role"] == "ai":
            content = preprocess_response(content)
        st.chat_message(message["role"]).markdown(content)

    # 处理用户的调整请求
    if prompt_input := st.chat_input("请告诉我需要调整的地方..."):
        st.chat_message("human").write(prompt_input)
        st.session_state["messages"].append({
            "role": "human",
            "content": prompt_input
        })

        try:
            with st.spinner("正在调整报价单..."):
                # 包含当前报价单内容的调整提示
                adjustment_prompt = (
                    "这是当前的报价单内容：\n\n"
                    f"{st.session_state['current_quote']}\n\n"
                    "请根据用户的需求调整上述报价单，注意：\n"
                    "1. 严格遵守标准价格\n"
                    "2. 保持原有格式\n"
                    "3. 标注调整的部分\n"
                    f"\n用户需求：{prompt_input}"
                )
                response = get_response(adjustment_prompt, st.session_state["memory"])

                if response:
                    formatted_response = preprocess_response(response)
                    st.session_state["messages"].append({
                        "role": "ai",
                        "content": formatted_response
                    })
                    st.session_state["current_quote"] = formatted_response  # 更新当前报价单
                    st.chat_message("ai").markdown(formatted_response)
                else:
                    st.error("生成调整后的报价单时出错")

        except Exception as e:
            st.error(f"调整报价时发生错误: {str(e)}")


if __name__ == '__main__':
    quote_page()
