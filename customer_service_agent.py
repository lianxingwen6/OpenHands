"""
智能客服自动化代理 - 基于OpenHands架构
提供多渠道智能客服、知识库管理、工单自动化
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class ChannelType(Enum):
    WEBCHAT = 'webchat'
    EMAIL = 'email'
    PHONE = 'phone'
    WHATSAPP = 'whatsapp'
    WECHAT = 'wechat'
    SLACK = 'slack'
    TELEGRAM = 'telegram'


class TicketPriority(Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    URGENT = 'urgent'


class TicketStatus(Enum):
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    WAITING_CUSTOMER = 'waiting_customer'
    RESOLVED = 'resolved'
    CLOSED = 'closed'


@dataclass
class CustomerQuery:
    query_id: str
    customer_id: str
    channel: ChannelType
    message: str
    context: dict  # 历史对话、客户信息等
    timestamp: datetime
    language: str = 'zh'
    attachments: list[str] = None


@dataclass
class Ticket:
    ticket_id: str
    customer_id: str
    subject: str
    description: str
    priority: TicketPriority
    status: TicketStatus
    category: str
    assigned_agent: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    resolution: Optional[str] = None


class CustomerServiceAgent:
    """智能客服自动化代理"""

    def __init__(self, llm_config, knowledge_base):
        self.llm_config = llm_config
        self.knowledge_base = knowledge_base
        self.intent_classifier = IntentClassifier()
        self.sentiment_analyzer = SentimentAnalyzer()
        self.escalation_rules = EscalationRules()
        self.response_templates = self._load_response_templates()

    async def handle_customer_query(self, query: CustomerQuery) -> dict:
        """处理客户查询的主要方法"""

        # 1. 意图识别和分类
        intent = await self._classify_intent(query)

        # 2. 情感分析
        sentiment = await self._analyze_sentiment(query)

        # 3. 知识库搜索
        relevant_info = await self._search_knowledge_base(query, intent)

        # 4. 生成回复
        response = await self._generate_response(
            query, intent, sentiment, relevant_info
        )

        # 5. 判断是否需要人工介入
        escalation_needed = await self._check_escalation(query, intent, sentiment)

        # 6. 创建或更新工单
        ticket = None
        if escalation_needed or intent.requires_ticket:
            ticket = await self._create_or_update_ticket(query, intent, sentiment)

        # 7. 记录对话历史
        await self._log_conversation(query, response, intent, sentiment)

        return {
            'response': response,
            'intent': intent,
            'sentiment': sentiment,
            'escalation_needed': escalation_needed,
            'ticket': ticket,
            'confidence_score': response.get('confidence', 0),
            'suggested_actions': await self._suggest_follow_up_actions(query, intent),
        }

    async def _classify_intent(self, query: CustomerQuery) -> dict:
        """意图识别和分类"""

        prompt = f"""
        分析以下客户查询的意图：

        客户消息: {query.message}
        渠道: {query.channel.value}
        客户历史: {query.context.get('history', [])}

        请识别：
        1. 主要意图类别 (咨询、投诉、退款、技术支持、销售等)
        2. 具体子类别
        3. 紧急程度 (1-5分)
        4. 是否需要创建工单
        5. 预估解决复杂度

        返回JSON格式结果。
        """

        intent_result = await self._call_llm(prompt)
        return self._parse_intent_result(intent_result)

    async def _analyze_sentiment(self, query: CustomerQuery) -> dict:
        """情感分析"""

        prompt = f"""
        分析以下客户消息的情感：

        消息内容: {query.message}

        请分析：
        1. 整体情感倾向 (积极/中性/消极)
        2. 情感强度 (1-10分)
        3. 具体情感类型 (满意、不满、愤怒、困惑、急迫等)
        4. 客户满意度预估
        5. 风险等级评估

        返回JSON格式结果。
        """

        sentiment_result = await self._call_llm(prompt)
        return self._parse_sentiment_result(sentiment_result)

    async def _search_knowledge_base(
        self, query: CustomerQuery, intent: dict
    ) -> list[dict]:
        """搜索知识库"""

        # 基于意图和查询内容搜索相关信息
        search_terms = [query.message] + intent.get('keywords', [])

        relevant_docs = []
        for term in search_terms:
            docs = await self.knowledge_base.search(
                query=term, category=intent.get('category'), limit=5
            )
            relevant_docs.extend(docs)

        # 去重和排序
        unique_docs = self._deduplicate_and_rank(relevant_docs, query)

        return unique_docs[:3]  # 返回最相关的3个文档

    async def _generate_response(
        self,
        query: CustomerQuery,
        intent: dict,
        sentiment: dict,
        relevant_info: list[dict],
    ) -> dict:
        """生成客服回复"""

        # 选择合适的回复模板
        template = self._select_response_template(intent, sentiment)

        prompt = f"""
        基于以下信息生成专业的客服回复：

        客户查询: {query.message}
        意图分析: {intent}
        情感分析: {sentiment}
        相关知识: {relevant_info}
        回复模板: {template}

        回复要求：
        1. 语调友好专业
        2. 针对性强，解决客户问题
        3. 包含具体的解决方案或下一步行动
        4. 适当表达同理心
        5. 符合公司品牌调性

        如果无法完全解决问题，请说明原因并提供替代方案。
        """

        response_text = await self._call_llm(prompt)

        return {
            'text': response_text,
            'template_used': template['name'],
            'confidence': self._calculate_response_confidence(relevant_info, intent),
            'suggested_actions': self._extract_suggested_actions(response_text),
            'escalation_triggers': self._identify_escalation_triggers(response_text),
        }

    async def _check_escalation(
        self, query: CustomerQuery, intent: dict, sentiment: dict
    ) -> bool:
        """检查是否需要人工介入"""

        escalation_factors = {
            'high_priority_intent': intent.get('priority', 0) >= 4,
            'negative_sentiment': sentiment.get('score', 0) <= -0.5,
            'complex_query': intent.get('complexity', 0) >= 4,
            'vip_customer': query.context.get('customer_tier') == 'VIP',
            'repeated_contact': len(query.context.get('history', [])) >= 3,
            'legal_compliance': intent.get('category')
            in ['legal', 'compliance', 'privacy'],
            'refund_request': intent.get('category') == 'refund'
            and intent.get('amount', 0) > 1000,
        }

        # 应用升级规则
        return self.escalation_rules.should_escalate(escalation_factors)

    async def _create_or_update_ticket(
        self, query: CustomerQuery, intent: dict, sentiment: dict
    ) -> Ticket:
        """创建或更新工单"""

        # 检查是否已有相关工单
        existing_ticket = await self._find_existing_ticket(query.customer_id, intent)

        if existing_ticket:
            # 更新现有工单
            existing_ticket.description += (
                f'\n\n新消息 ({query.timestamp}): {query.message}'
            )
            existing_ticket.updated_at = datetime.now()
            await self._update_ticket(existing_ticket)
            return existing_ticket
        else:
            # 创建新工单
            ticket = Ticket(
                ticket_id=self._generate_ticket_id(),
                customer_id=query.customer_id,
                subject=await self._generate_ticket_subject(query, intent),
                description=query.message,
                priority=self._determine_priority(intent, sentiment),
                status=TicketStatus.OPEN,
                category=intent.get('category', 'general'),
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )

            await self._save_ticket(ticket)
            return ticket

    async def _suggest_follow_up_actions(
        self, query: CustomerQuery, intent: dict
    ) -> list[str]:
        """建议后续行动"""

        prompt = f"""
        基于客户查询和意图分析，建议后续行动：

        客户查询: {query.message}
        意图类别: {intent.get('category')}

        请建议3-5个具体的后续行动，例如：
        - 发送相关文档链接
        - 安排技术支持回电
        - 提供产品演示
        - 发送满意度调查
        - 关注客户反馈
        """

        suggestions = await self._call_llm(prompt)
        return self._parse_action_suggestions(suggestions)


class IntentClassifier:
    """意图分类器"""

    def __init__(self):
        self.intent_categories = {
            'product_inquiry': ['产品咨询', '功能介绍', '价格询问'],
            'technical_support': ['技术问题', '故障报告', '使用帮助'],
            'billing': ['账单问题', '付款', '退款'],
            'complaint': ['投诉', '不满', '问题反馈'],
            'sales': ['购买咨询', '升级', '续费'],
            'account': ['账户问题', '密码重置', '权限'],
            'general': ['一般咨询', '其他'],
        }


class SentimentAnalyzer:
    """情感分析器"""

    def analyze(self, text: str) -> dict:
        """分析文本情感"""
        # 实际实现会使用专门的情感分析模型
        return {
            'polarity': 0.0,  # -1到1之间
            'intensity': 0.5,  # 0到1之间
            'emotion': 'neutral',
            'confidence': 0.8,
        }


class EscalationRules:
    """升级规则引擎"""

    def should_escalate(self, factors: dict[str, bool]) -> bool:
        """判断是否应该升级"""

        # 强制升级条件
        if factors.get('legal_compliance') or factors.get('vip_customer'):
            return True

        # 计分升级
        score = sum(
            [
                factors.get('high_priority_intent', False) * 3,
                factors.get('negative_sentiment', False) * 2,
                factors.get('complex_query', False) * 2,
                factors.get('repeated_contact', False) * 2,
                factors.get('refund_request', False) * 1,
            ]
        )

        return score >= 4


# 知识库管理
class KnowledgeBase:
    """知识库管理系统"""

    def __init__(self):
        self.documents = []
        self.categories = {}
        self.search_index = {}

    async def search(
        self, query: str, category: str = None, limit: int = 5
    ) -> list[dict]:
        """搜索知识库"""
        # 实际实现会使用向量搜索或全文搜索
        results = []

        # 模拟搜索结果
        for i in range(min(limit, 3)):
            results.append(
                {
                    'id': f'doc_{i}',
                    'title': f'相关文档 {i + 1}',
                    'content': f'这是关于 {query} 的相关信息...',
                    'category': category or 'general',
                    'relevance_score': 0.9 - i * 0.1,
                }
            )

        return results

    async def add_document(
        self, title: str, content: str, category: str, metadata: dict = None
    ):
        """添加文档到知识库"""
        doc = {
            'id': self._generate_doc_id(),
            'title': title,
            'content': content,
            'category': category,
            'metadata': metadata or {},
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
        }

        self.documents.append(doc)
        await self._update_search_index(doc)


# 使用示例
async def demo_customer_service():
    """演示智能客服功能"""

    knowledge_base = KnowledgeBase()
    agent = CustomerServiceAgent(llm_config={}, knowledge_base=knowledge_base)

    # 客户查询示例
    query = CustomerQuery(
        query_id='q_001',
        customer_id='cust_123',
        channel=ChannelType.WEBCHAT,
        message='我的订单还没有发货，已经等了一周了，什么时候能收到？',
        context={
            'history': ['上次咨询过配送时间'],
            'customer_tier': 'Premium',
            'order_id': 'ORD_789',
        },
        timestamp=datetime.now(),
        language='zh',
    )

    result = await agent.handle_customer_query(query)

    print('客服回复:')
    print(result['response']['text'])
    print(f'意图分析: {result["intent"]}')
    print(f'是否需要升级: {result["escalation_needed"]}')
    if result['ticket']:
        print(f'工单已创建: {result["ticket"].ticket_id}')


if __name__ == '__main__':
    import asyncio

    asyncio.run(demo_customer_service())
