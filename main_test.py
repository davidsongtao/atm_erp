import streamlit as st
import aiohttp
import asyncio
from typing import List, Dict, Tuple
import re
from dataclasses import dataclass
import json
from functools import lru_cache
import hashlib
from datetime import datetime, timedelta


@dataclass
class AddressMatch:
    raw_input: str
    formatted_address: str
    confidence_score: float
    components: Dict[str, str]


class CacheManager:
    def __init__(self):
        self.cache = {}
        self.expiry = {}
        self.CACHE_DURATION = timedelta(hours=24)

    def get(self, key: str) -> any:
        if key in self.cache:
            if datetime.now() < self.expiry[key]:
                return self.cache[key]
            else:
                del self.cache[key]
                del self.expiry[key]
        return None

    def set(self, key: str, value: any):
        self.cache[key] = value
        self.expiry[key] = datetime.now() + self.CACHE_DURATION


class AddressValidator:
    def __init__(self, here_api_key: str, deepseek_api_key: str):
        self.here_api_key = here_api_key
        self.deepseek_api_key = deepseek_api_key
        self.here_base_url = "https://autosuggest.search.hereapi.com/v1/autosuggest"
        self.deepseek_url = "https://api.deepseek.com/v1/chat/completions"
        self.cache = CacheManager()
        self.session = None

    async def ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    def _get_cache_key(self, input_address: str) -> str:
        """生成缓存键"""
        return hashlib.md5(input_address.lower().encode()).hexdigest()

    async def _fetch_here_suggestions(self, input_address: str) -> List[Dict]:
        """异步获取HERE API建议"""
        await self.ensure_session()

        params = {
            "q": input_address,
            "apiKey": self.here_api_key,
            "limit": 5,
            "in": "countryCode:AUS",
            "lang": ["en"],
            "show": "streetInfo,details",
            "at": "-37.8136,144.9631"
        }

        try:
            async with self.session.get(self.here_base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("items", [])
        except Exception as e:
            st.error(f"HERE API Error: {str(e)}")
            return []

    async def _call_deepseek_batch(self, prompts: List[str]) -> List[Dict]:
        """批量调用DeepSeek API"""
        await self.ensure_session()

        async def process_prompt(prompt):
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {"role": "system", "content": "你是一个专门处理澳大利亚地址验证的助手。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1
            }

            try:
                async with self.session.post(self.deepseek_url, headers=headers, json=data) as response:
                    response.raise_for_status()
                    return await response.json()
            except Exception as e:
                st.error(f"DeepSeek API Error: {str(e)}")
                return None

        tasks = [process_prompt(prompt) for prompt in prompts]
        return await asyncio.gather(*tasks)

    def _create_analysis_prompt(self, user_input: str, here_suggestion: Dict) -> str:
        """创建分析提示词"""
        return f"""简要分析以下地址:
用户输入: {user_input}
HERE建议: {self._format_here_address(here_suggestion)}
仅需返回:
地址: <标准化地址>
置信度: <0-1分数>"""

    def _format_here_address(self, suggestion: Dict) -> str:
        """格式化HERE API返回的地址"""
        address = suggestion.get("address", {})
        components = []

        if address.get("unit"):
            components.append(f"{address['unit']}/")
        if address.get("houseNumber"):
            components.append(address["houseNumber"])
        if address.get("street"):
            components.append(address["street"])
        if address.get("district"):
            components.append(address["district"])
        if address.get("state"):
            state_mapping = {
                "Victoria": "VIC", "New South Wales": "NSW",
                "Queensland": "QLD", "Western Australia": "WA",
                "South Australia": "SA", "Tasmania": "TAS",
                "Australian Capital Territory": "ACT", "Northern Territory": "NT"
            }
            state = state_mapping.get(address["state"], address["state"])
            components.append(state)
        if address.get("postalCode"):
            components.append(address["postalCode"])

        return ", ".join(filter(None, components))

    async def validate_address(self, input_address: str) -> List[AddressMatch]:
        """验证并标准化地址"""
        if not input_address:
            return []

        # 检查缓存
        cache_key = self._get_cache_key(input_address)
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result

        # 获取HERE API建议
        suggestions = await self._fetch_here_suggestions(input_address)
        if not suggestions:
            return []

        # 批量创建提示词
        prompts = [
            self._create_analysis_prompt(input_address, suggestion)
            for suggestion in suggestions
            if suggestion.get("address", {}).get("countryCode") == "AUS"
        ]

        # 批量获取LLM分析结果
        llm_results = await self._call_deepseek_batch(prompts)

        # 处理结果
        matches = []
        for suggestion, llm_result in zip(suggestions, llm_results):
            if llm_result and suggestion.get("address", {}).get("countryCode") == "AUS":
                try:
                    content = llm_result['choices'][0]['message']['content']
                    address_match = re.search(r'地址: (.+)', content)
                    confidence_match = re.search(r'置信度: (0\.\d+)', content)

                    if address_match and confidence_match:
                        matches.append(AddressMatch(
                            raw_input=input_address,
                            formatted_address=address_match.group(1),
                            confidence_score=float(confidence_match.group(1)),
                            components=suggestion.get("address", {})
                        ))
                except Exception as e:
                    st.error(f"Error parsing LLM response: {str(e)}")

        # 按置信度排序
        matches.sort(key=lambda x: x.confidence_score, reverse=True)

        # 缓存结果
        self.cache.set(cache_key, matches)

        return matches


@st.cache_resource
def get_validator(here_api_key: str, deepseek_api_key: str) -> AddressValidator:
    return AddressValidator(here_api_key, deepseek_api_key)


async def main():
    st.title("AI-Enhanced Australian Address Validator")

    # 初始化session state，但只在完全不存在时初始化
    if "input_address" not in st.session_state:
        st.session_state.input_address = ""

    if "selected_address" not in st.session_state:
        st.session_state.selected_address = None

    for key in ["here_api_key", "deepseek_api_key"]:
        if key not in st.session_state:
            st.session_state[key] = st.secrets.get(key.upper(), None)

    validator = get_validator(
        st.session_state.here_api_key,
        st.session_state.deepseek_api_key
    )

    def select_address(match):
        st.session_state.input_address = match.formatted_address
        st.session_state.selected_address = match

    # 修改输入框：移除 value 参数，只使用 key
    input_address = st.text_input(
        "Enter Australian address",
        placeholder="Example: 160 Victoria Street, Carlton VIC",
        key="input_address"
    )

    if st.button("Validate") and input_address:
        try:
            with st.spinner("Analyzing address..."):
                matches = await validator.validate_address(input_address)

                if matches:
                    st.success("Found potential matches:")

                    for i, match in enumerate(matches):
                        with st.container():
                            col1, col2, col3 = st.columns([3, 1, 1])

                            with col1:
                                st.write(f"🏠 {match.formatted_address}")
                            with col2:
                                st.write(f"Confidence: {match.confidence_score:.2f}")
                            with col3:
                                if st.button("Select", key=f"select_{i}", on_click=select_address, args=(match,)):
                                    st.rerun()

                else:
                    st.warning("No matches found. Please check the address and try again.")
        finally:
            await validator.close_session()

        if st.button("Clear"):
            st.session_state.input_address = ""
            st.session_state.selected_address = None
            st.rerun()


if __name__ == "__main__":
    asyncio.run(main())
