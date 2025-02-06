import asyncio
from typing import List, Dict, Optional
from dataclasses import dataclass
import aiohttp
import hashlib
from datetime import datetime, timedelta
import re
import streamlit as st


@dataclass
class AddressMatch:
    raw_input: str
    formatted_address: str
    confidence_score: float
    components: Dict[str, str]
    unit_number: str = None
    validation_source: str = "llm"  # 'llm' or 'fallback'


class LLMAddressValidator:
    def __init__(self, deepseek_api_key: str):
        self.deepseek_api_key = deepseek_api_key
        self.cache = {}
        self.cache_expiry = {}
        self.CACHE_DURATION = timedelta(hours=24)
        self.session = None
        self.validation_patterns = self._compile_address_patterns()

    def _compile_address_patterns(self) -> Dict[str, re.Pattern]:
        """编译澳大利亚地址的正则表达式模式"""
        return {
            'unit': re.compile(r'^(\d+/)?'),  # 单元号
            'street_number': re.compile(r'\b\d+(-\d+)?\b'),  # 街道号
            'street': re.compile(
                r'[A-Za-z\s]+\s(Street|St|Road|Rd|Avenue|Ave|Lane|Ln|Place|Pl|Drive|Dr|Parade|Pde|Circuit|Cct|Way|Court|Ct)',
                re.I
            ),
            'suburb': re.compile(r'\b[A-Za-z\s]+\b'),  # 区域
            'postcode': re.compile(r'\b\d{4}\b'),  # 邮编
            'state': re.compile(r'\b(VIC|NSW|QLD|WA|SA|TAS|ACT|NT)\b', re.I)  # 州
        }

    def _create_validation_prompt(self, address: str) -> str:
        """创建地址验证提示词"""
        return f"""作为澳大利亚地址验证专家，你需要执行以下步骤：

    1. 分析输入地址: {address}
    2. 想象你可以用Google搜索这个地址，并特别关注 realestate.com.au 和 property.com.au 网站上的结果
    3. 基于搜索结果和你的知识，标准化并验证这个地址

    请按照以下标准格式返回结果：
    地址: <标准化后的完整地址，使用与 realestate.com.au 或 property.com.au 网站相同的格式>
    单元号: <如果有单元号>
    街道号: <门牌号>
    街道: <街道名称>
    区域: <区域/市郊>
    州: <州缩写>
    邮编: <邮政编码>
    置信度: <0.0-1.0之间的数字，表示地址正确的置信度>

    验证要求：
    1. 地址格式必须符合澳大利亚标准，包含街道号、街道名、区域、州和邮编
    2. 州名必须使用标准缩写(VIC, NSW, QLD, WA, SA, TAS, ACT, NT)
    3. 对于无法识别的字段，使用 "N/A"
    4. 置信度评分标准：
       - 1.0: 在realestate.com.au上能找到完全匹配的地址
       - 0.8-0.9: 地址完整且可信，但可能有细微差异
       - 0.6-0.7: 地址基本可识别，但缺少部分细节
       - 0.5以下: 地址信息不完整或无法验证

    如果是公寓或单元：
    - 正确格式示例："12/34 Smith Street, Melbourne VIC 3000"
    - 单元号在前，用斜杠分隔
    - 确保包含所有必要的方向标示(如North, South等)"""

    async def _call_deepseek_api(self, prompt: str) -> Optional[Dict]:
        """调用 Deepseek API 进行地址验证"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                    "https://api.deepseek.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.deepseek_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "你是一个专门处理澳大利亚地址验证的助手。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.1
                    }
            ) as response:
                if response.status == 200:
                    return await response.json()
                return None

        except aiohttp.ClientError as e:
            st.error(f"API请求错误: {str(e)}")
            return None
        except Exception as e:
            st.error(f"未预期的错误: {str(e)}")
            return None

    def _parse_llm_response(self, response: Dict, raw_input: str) -> Optional[AddressMatch]:
        """解析 LLM 响应并创建 AddressMatch 对象"""
        try:
            content = response['choices'][0]['message']['content']

            address_match = re.search(r'地址:\s*(.+)', content)
            unit_match = re.search(r'单元号:\s*(.+)', content)
            confidence_match = re.search(r'置信度:\s*([\d.]+)', content)

            if not all([address_match, confidence_match]):
                return None

            formatted_address = address_match.group(1).strip()
            if formatted_address.lower() == 'n/a':
                return None

            unit_number = None
            if unit_match and unit_match.group(1).strip().lower() != 'n/a':
                unit_number = unit_match.group(1).strip()

            components = {}
            for field in ['街道号', '街道', '区域', '州', '邮编']:
                match = re.search(f'{field}:\s*(.+)', content)
                if match and match.group(1).strip().lower() != 'n/a':
                    components[field] = match.group(1).strip()

            return AddressMatch(
                raw_input=raw_input,
                formatted_address=formatted_address,
                confidence_score=float(confidence_match.group(1)),
                components=components,
                unit_number=unit_number,
                validation_source='llm'
            )

        except Exception as e:
            st.error(f"解析验证结果时出错: {str(e)}")
            return None

    def _fallback_validation(self, address: str) -> Optional[AddressMatch]:
        """本地地址验证回退机制"""
        try:
            # 基本格式验证
            parts = address.strip().split(',')
            if not parts:
                return None

            # 提取并验证各个部分
            street_part = parts[0].strip()
            unit_match = self.validation_patterns['unit'].search(street_part)
            unit_number = unit_match.group(1) if unit_match else None

            # 验证必要元素
            has_street_number = bool(self.validation_patterns['street_number'].search(street_part))
            has_street = bool(self.validation_patterns['street'].search(street_part))

            # 验证州和邮编
            state_found = False
            postcode_found = False
            for part in parts[1:]:
                if self.validation_patterns['state'].search(part):
                    state_found = True
                if self.validation_patterns['postcode'].search(part):
                    postcode_found = True

            # 计算置信度
            confidence = 0.5  # 基础置信度
            if has_street_number and has_street:
                confidence += 0.1
            if state_found:
                confidence += 0.1
            if postcode_found:
                confidence += 0.1
            if unit_number:
                confidence += 0.1

            if confidence > 0.5:  # 只有当基本验证通过时才返回结果
                return AddressMatch(
                    raw_input=address,
                    formatted_address=address,
                    confidence_score=confidence,
                    components={},
                    unit_number=unit_number,
                    validation_source='fallback'
                )
            return None

        except Exception:
            return None

    async def validate_address(self, input_address: str) -> List[AddressMatch]:
        """主验证函数"""
        if not input_address:
            return []

        # 检查缓存
        cache_key = hashlib.md5(input_address.lower().encode()).hexdigest()
        if cache_key in self.cache and datetime.now() < self.cache_expiry[cache_key]:
            return self.cache[cache_key]

        matches = []

        try:
            # 1. 尝试使用 Deepseek API
            prompt = self._create_validation_prompt(input_address)
            llm_response = await self._call_deepseek_api(prompt)

            if llm_response:
                match = self._parse_llm_response(llm_response, input_address)
                if match:
                    matches.append(match)

            # 2. 如果 LLM 验证失败，使用本地验证
            if not matches:
                fallback_match = self._fallback_validation(input_address)
                if fallback_match:
                    matches.append(fallback_match)
                else:
                    # 3. 最后的回退：接受用户输入
                    matches.append(AddressMatch(
                        raw_input=input_address,
                        formatted_address=input_address,
                        confidence_score=0.5,
                        components={},
                        validation_source='user_input'
                    ))
                    st.warning("无法验证地址格式。请确保地址准确。", icon="⚠️")

        except Exception as e:
            st.error(f"地址验证过程出现错误: {str(e)}")
            # 出错时接受用户输入
            matches.append(AddressMatch(
                raw_input=input_address,
                formatted_address=input_address,
                confidence_score=0.5,
                components={},
                validation_source='user_input'
            ))

        finally:
            # 更新缓存
            if matches:
                self.cache[cache_key] = matches
                self.cache_expiry[cache_key] = datetime.now() + self.CACHE_DURATION

            return matches

    async def close_session(self):
        """关闭 aiohttp 会话"""
        if self.session:
            await self.session.close()
            self.session = None


@st.cache_resource
def get_validator(deepseek_api_key: str) -> LLMAddressValidator:
    """获取验证器实例"""
    return LLMAddressValidator(deepseek_api_key)
