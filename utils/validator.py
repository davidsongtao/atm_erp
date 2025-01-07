"""
Description: 
    
-*- Encoding: UTF-8 -*-
@File     ：validator.py.py
@Author   ：King Songtao
@Time     ：2025/1/7 上午10:18
@Contact  ：king.songtao@gmail.com
"""
import asyncio
from typing import List, Dict
import aiohttp
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass
import re
import streamlit as st


def extract_unit_number(address):
    """
    从地址中提取单元号
    例如：从 "607/111 Parkview Rd" 提取 "607/"
    """
    if '/' in address:
        parts = address.split('/')
        if len(parts) >= 2 and parts[0].strip().isdigit():
            return f"{parts[0].strip()}/"
    return None


def merge_unit_number(original_address, validated_address):
    """
    将原始地址中的单元号合并到验证后的地址中
    """
    unit_number = extract_unit_number(original_address)
    if unit_number:
        # 检查验证后的地址是否已包含单元号
        if '/' not in validated_address:
            # 找到第一个数字开始的位置
            import re
            match = re.search(r'\d', validated_address)
            if match:
                start_pos = match.start()
                # 插入单元号
                return validated_address[:start_pos] + unit_number + validated_address[start_pos:]
    return validated_address


@dataclass
class AddressMatch:
    raw_input: str
    formatted_address: str
    confidence_score: float
    components: Dict[str, str]
    unit_number: str = None  # 添加单元号字段


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

        # 添加已知的地址修正映射
        self.known_corrections = {
            "abeckett": "A'Beckett",
            "a beckett": "A'Beckett",
            "a'beckett": "A'Beckett",
        }

    async def ensure_session(self):
        """确保aiohttp会话存在"""
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close_session(self):
        """关闭aiohttp会话"""
        if self.session:
            await self.session.close()
            self.session = None

    def _normalize_street_name(self, street: str) -> str:
        """标准化街道名称"""
        if not street:
            return street
        street = street.lower().strip()
        for incorrect, correct in self.known_corrections.items():
            if incorrect in street:
                street = street.replace(incorrect, correct)
        return street

    def _extract_unit_number(self, address: str) -> str:
        """从地址中提取单元号"""
        if address and '/' in address:
            parts = address.split('/')
            if len(parts) >= 2 and parts[0].strip().isdigit():
                return parts[0].strip()
        return None

    def _score_address_match(self, suggestion: Dict, input_address: str, district: str = "Melbourne") -> float:
        """为地址匹配结果评分"""
        address = suggestion.get("address", {})
        base_score = 0.0

        # 如果区域是Melbourne CBD，给予更高的基础分数
        if address.get("district", "").lower() == district.lower():
            base_score += 0.5

        # 邮政编码3000（Melbourne CBD）给予额外分数
        if address.get("postalCode") == "3000":
            base_score += 0.3

        # 根据地址完整性评分
        if address.get("street") and address.get("houseNumber"):
            base_score += 0.2

        return min(1.0, base_score)

    async def _fetch_here_suggestions(self, input_address: str) -> List[Dict]:
        """异步获取HERE API建议"""
        await self.ensure_session()

        # 标准化输入地址中的街道名
        normalized_address = self._normalize_street_name(input_address)

        params = {
            "q": normalized_address,
            "apiKey": self.here_api_key,
            "limit": 5,
            "in": "countryCode:AUS",
            "lang": ["en"],
            "show": "streetInfo,details",
            "at": "-37.8136,144.9631"  # Melbourne CBD coordinates
        }

        try:
            async with self.session.get(self.here_base_url, params=params) as response:
                response.raise_for_status()
                data = await response.json()

                # 对结果进行初步过滤和排序
                items = data.get("items", [])
                for item in items:
                    item['score'] = self._score_address_match(item, input_address)

                # 按自定义评分排序
                items.sort(key=lambda x: x.get('score', 0), reverse=True)
                return items
        except Exception as e:
            st.error(f"HERE API Error: {str(e)}")
            return []

    def _format_here_address(self, suggestion: Dict, input_address: str = None) -> str:
        """格式化HERE API返回的地址"""
        address = suggestion.get("address", {})
        components = []

        # 处理单元号
        unit_number = self._extract_unit_number(input_address) if input_address else None
        if unit_number:
            components.append(f"{unit_number}/")

        if address.get("houseNumber"):
            components.append(address["houseNumber"])

        # 确保使用正确的街道名格式
        if address.get("street"):
            street_name = self._normalize_street_name(address["street"])
            components.append(street_name)

        if address.get("district"):
            # 只在不是Melbourne CBD时添加区域
            if address.get("postalCode") != "3000":
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

    def _get_cache_key(self, input_address: str) -> str:
        """生成缓存键"""
        return hashlib.md5(input_address.lower().encode()).hexdigest()

    def _create_analysis_prompt(self, user_input: str, here_suggestion: Dict) -> str:
        """创建分析提示词"""
        return f"""简要分析以下地址:
用户输入: {user_input}
HERE建议: {self._format_here_address(here_suggestion)}
仅需返回:
地址: <标准化地址>
置信度: <0-1分数>"""

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
                        # 提取单元号
                        unit_number = self._extract_unit_number(input_address)
                        formatted_address = self._normalize_street_name(address_match.group(1))

                        # 如果找到单元号且验证后的地址中没有包含单元号，则添加单元号
                        if unit_number and '/' not in formatted_address:
                            # 在第一个数字之前插入单元号
                            number_match = re.search(r'\d', formatted_address)
                            if number_match:
                                start_pos = number_match.start()
                                formatted_address = (
                                        formatted_address[:start_pos] +
                                        f"{unit_number}/" +
                                        formatted_address[start_pos:]
                                )

                        matches.append(AddressMatch(
                            raw_input=input_address,
                            formatted_address=formatted_address,
                            confidence_score=float(confidence_match.group(1)),
                            components=suggestion.get("address", {}),
                            unit_number=unit_number
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
