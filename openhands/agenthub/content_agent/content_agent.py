"""
Content automation agent integrated with OpenHands architecture.
"""

from openhands.controller.agent import Agent
from openhands.core.config import AgentConfig
from openhands.events.action import Action, MessageAction
from openhands.llm.llm import LLM


class ContentAgent(Agent):
    """Content automation agent for OpenHands."""

    VERSION = '1.0.0'

    def __init__(self, llm: LLM, config: AgentConfig) -> None:
        """Initialize the content agent."""
        super().__init__(llm, config)
        self.content_types = {
            'blog': self._generate_blog_post,
            'social': self._generate_social_media,
            'email': self._generate_email_content,
            'seo': self._generate_seo_content,
            'product': self._generate_product_description,
        }

    def step(self, state) -> Action:
        """Take a step in content generation."""
        # Get the latest user message
        messages = state.history.get_events_as_list()
        if not messages:
            return MessageAction(content='请告诉我您需要创建什么类型的内容？')

        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            user_input = last_message.content

            # Parse content request
            content_request = self._parse_content_request(user_input)

            # Generate content based on request
            if content_request['type'] in self.content_types:
                content = self.content_types[content_request['type']](content_request)
                return MessageAction(content=content)
            else:
                return MessageAction(
                    content=f'支持的内容类型: {", ".join(self.content_types.keys())}'
                )

        return MessageAction(content='请提供内容创建需求。')

    def _parse_content_request(self, user_input: str) -> dict:
        """Parse user content request."""
        # Use LLM to parse the request
        prompt = f"""
        解析以下内容创建请求，提取关键信息：

        用户请求: {user_input}

        请返回JSON格式，包含：
        - type: 内容类型 (blog, social, email, seo, product)
        - topic: 主题
        - target_audience: 目标受众
        - tone: 语调 (professional, casual, friendly等)
        - length: 长度要求
        - keywords: 关键词列表
        - special_requirements: 特殊要求
        """

        response = self.llm.completion(
            messages=[{'role': 'user', 'content': prompt}], temperature=0.1
        )

        try:
            import json

            return json.loads(response.choices[0].message.content)
        except Exception:
            # Fallback parsing
            return {
                'type': 'blog',
                'topic': user_input,
                'target_audience': '一般读者',
                'tone': 'professional',
                'length': 'medium',
                'keywords': [],
                'special_requirements': '',
            }

    def _generate_blog_post(self, request: dict) -> str:
        """Generate blog post content."""
        prompt = f"""
        创建一篇关于"{request['topic']}"的博客文章。

        要求：
        - 目标受众: {request.get('target_audience', '一般读者')}
        - 语调: {request.get('tone', 'professional')}
        - 长度: {request.get('length', 'medium')}
        - 关键词: {', '.join(request.get('keywords', []))}

        请包含：
        1. 吸引人的标题
        2. 引人入胜的开头
        3. 结构清晰的正文（使用小标题）
        4. 实用的建议或见解
        5. 强有力的结尾
        6. SEO优化的元描述

        {request.get('special_requirements', '')}
        """

        response = self.llm.completion(
            messages=[{'role': 'user', 'content': prompt}], temperature=0.7
        )

        return response.choices[0].message.content

    def _generate_social_media(self, request: dict) -> str:
        """Generate social media content."""
        prompt = f"""
        为"{request['topic']}"创建社交媒体内容。

        要求：
        - 平台: {request.get('platform', '通用')}
        - 目标受众: {request.get('target_audience', '一般用户')}
        - 语调: {request.get('tone', 'engaging')}
        - 包含话题标签

        请创建：
        1. 主要帖子内容（简洁有力）
        2. 相关话题标签
        3. 可选的行动号召
        4. 适合的表情符号

        {request.get('special_requirements', '')}
        """

        response = self.llm.completion(
            messages=[{'role': 'user', 'content': prompt}], temperature=0.8
        )

        return response.choices[0].message.content

    def _generate_email_content(self, request: dict) -> str:
        """Generate email content."""
        prompt = f"""
        创建关于"{request['topic']}"的邮件内容。

        要求：
        - 邮件类型: {request.get('email_type', '营销邮件')}
        - 目标受众: {request.get('target_audience', '客户')}
        - 语调: {request.get('tone', 'professional')}

        请包含：
        1. 吸引人的主题行
        2. 个性化的问候语
        3. 清晰的正文内容
        4. 明确的行动号召
        5. 专业的签名

        {request.get('special_requirements', '')}
        """

        response = self.llm.completion(
            messages=[{'role': 'user', 'content': prompt}], temperature=0.6
        )

        return response.choices[0].message.content

    def _generate_seo_content(self, request: dict) -> str:
        """Generate SEO-optimized content."""
        prompt = f"""
        创建SEO优化的内容，主题："{request['topic']}"

        SEO要求：
        - 主关键词: {request.get('primary_keyword', request['topic'])}
        - 次要关键词: {', '.join(request.get('keywords', []))}
        - 目标字数: {request.get('word_count', '800-1200')}

        请优化：
        1. 标题标签（H1）
        2. 子标题（H2, H3）
        3. 关键词密度（1-2%）
        4. 内部链接建议
        5. 元描述
        6. 图片alt标签建议

        {request.get('special_requirements', '')}
        """

        response = self.llm.completion(
            messages=[{'role': 'user', 'content': prompt}], temperature=0.5
        )

        return response.choices[0].message.content

    def _generate_product_description(self, request: dict) -> str:
        """Generate product description."""
        prompt = f"""
        为产品"{request['topic']}"创建产品描述。

        要求：
        - 产品类型: {request.get('product_type', '通用产品')}
        - 目标客户: {request.get('target_audience', '潜在买家')}
        - 语调: {request.get('tone', 'persuasive')}

        请包含：
        1. 吸引人的产品标题
        2. 核心卖点（3-5个）
        3. 详细功能描述
        4. 使用场景
        5. 技术规格（如适用）
        6. 购买理由

        {request.get('special_requirements', '')}
        """

        response = self.llm.completion(
            messages=[{'role': 'user', 'content': prompt}], temperature=0.6
        )

        return response.choices[0].message.content
