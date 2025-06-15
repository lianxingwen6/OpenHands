# OpenHands 自动化代理集成指南

## 🎯 集成状态

### ✅ 已完成的集成

1. **核心代理架构**
   - `openhands/agenthub/content_agent/` - 内容创作自动化代理
   - `openhands/agenthub/data_agent/` - 数据分析自动化代理
   - 基于OpenHands现有的Agent基类构建

2. **API路由集成**
   - `openhands/server/routes/automation.py` - 自动化API端点
   - `openhands/server/routes/billing.py` - 订阅和计费API
   - 已集成到主应用 `app.py` 中

3. **数据模型**
   - `openhands/storage/data_models/subscription.py` - 订阅管理
   - 支持多层级订阅和使用量追踪

4. **中间件**
   - `openhands/server/middleware.py` - 使用量追踪中间件
   - 集成到现有中间件系统

## 🚀 使用方法

### 1. 内容创作自动化

```python
# API调用示例
import requests

# 生成博客文章
response = requests.post('http://localhost:3000/api/automation/content/generate', json={
    "content_type": "blog",
    "topic": "人工智能在教育中的应用",
    "target_audience": "教育工作者",
    "tone": "professional",
    "length": "medium",
    "keywords": ["AI", "教育", "个性化学习"]
})

print(response.json())
```

### 2. 数据分析自动化

```python
# 数据分析API调用
response = requests.post('http://localhost:3000/api/automation/data/analyze', json={
    "data_path": "/path/to/sales_data.csv",
    "analysis_type": "descriptive",
    "business_question": "过去一年的销售趋势如何？",
    "target_metrics": ["revenue", "units_sold"]
})

print(response.json())
```

### 3. 订阅管理

```python
# 创建订阅
response = requests.post('http://localhost:3000/api/billing/create-checkout-session', json={
    "tier": "pro",
    "success_url": "https://yourapp.com/success",
    "cancel_url": "https://yourapp.com/cancel"
})

# 检查使用量
response = requests.get('http://localhost:3000/api/billing/usage')
print(response.json())
```

## 🔧 进一步集成步骤

### 1. 前端集成

需要在 `frontend/` 目录中添加：

```typescript
// frontend/src/api/automation.ts
export const automationAPI = {
  generateContent: async (request: ContentRequest) => {
    return await fetch('/api/automation/content/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
  },

  analyzeData: async (request: DataAnalysisRequest) => {
    return await fetch('/api/automation/data/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(request)
    });
  }
};
```

### 2. 数据库集成

需要添加数据库表：

```sql
-- 订阅表
CREATE TABLE subscriptions (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    tier VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    current_period_start TIMESTAMP,
    current_period_end TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 使用量表
CREATE TABLE usage_metrics (
    id VARCHAR(255) PRIMARY KEY,
    subscription_id VARCHAR(255) REFERENCES subscriptions(id),
    ai_conversations INT DEFAULT 0,
    code_generations INT DEFAULT 0,
    runtime_hours DECIMAL(10,2) DEFAULT 0,
    api_calls INT DEFAULT 0,
    period_start TIMESTAMP,
    period_end TIMESTAMP
);
```

### 3. 环境变量配置

在 `.env` 文件中添加：

```bash
# Stripe配置
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/openhands

# LLM配置
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 4. 完整的代理注册

在 `openhands/agenthub/__init__.py` 中注册新代理：

```python
from openhands.agenthub.content_agent import ContentAgent
from openhands.agenthub.data_agent import DataAgent

# 注册代理
AGENT_CLS_TO_FAKE_USER_RESPONSE_FN['ContentAgent'] = content_agent_fake_user_response
AGENT_CLS_TO_FAKE_USER_RESPONSE_FN['DataAgent'] = data_agent_fake_user_response
```

## 📊 API端点总览

### 自动化API (`/api/automation`)

- `POST /content/generate` - 生成内容
- `POST /data/analyze` - 数据分析
- `GET /content/types` - 获取支持的内容类型
- `GET /data/analysis-types` - 获取支持的分析类型
- `GET /tasks/{task_id}` - 获取任务状态

### 计费API (`/api/billing`)

- `POST /create-checkout-session` - 创建Stripe结账会话
- `POST /webhook` - Stripe webhook处理
- `GET /subscription` - 获取订阅信息
- `GET /usage` - 获取使用量统计
- `POST /cancel-subscription` - 取消订阅

## 🎨 前端界面建议

### 1. 自动化工作台

```jsx
// AutomationWorkspace.tsx
import React from 'react';

const AutomationWorkspace = () => {
  return (
    <div className="automation-workspace">
      <div className="agent-selector">
        <button>内容创作</button>
        <button>数据分析</button>
        <button>客服自动化</button>
        <button>流程自动化</button>
        <button>设计自动化</button>
      </div>

      <div className="agent-interface">
        {/* 动态加载对应的代理界面 */}
      </div>

      <div className="usage-monitor">
        {/* 显示当前使用量和限制 */}
      </div>
    </div>
  );
};
```

### 2. 订阅管理界面

```jsx
// SubscriptionManager.tsx
const SubscriptionManager = () => {
  return (
    <div className="subscription-manager">
      <div className="current-plan">
        <h3>当前订阅: Pro版</h3>
        <div className="usage-bars">
          <UsageBar label="AI对话" current={150} limit={1000} />
          <UsageBar label="代码生成" current={50} limit={500} />
          <UsageBar label="运行时间" current={10.5} limit={50} unit="小时" />
        </div>
      </div>

      <div className="upgrade-options">
        <PricingCard tier="team" />
        <PricingCard tier="enterprise" />
      </div>
    </div>
  );
};
```

## 🔐 安全考虑

1. **API认证**: 所有自动化API都需要用户认证
2. **使用量限制**: 中间件自动追踪和限制使用量
3. **数据隔离**: 每个用户的数据完全隔离
4. **审计日志**: 记录所有自动化操作

## 📈 监控和分析

1. **使用量监控**: 实时追踪API调用和资源使用
2. **性能监控**: 监控代理响应时间和成功率
3. **业务指标**: 追踪转化率、留存率等关键指标
4. **错误追踪**: 自动收集和分析错误日志

## 🚀 部署建议

1. **容器化部署**: 使用Docker容器化所有服务
2. **负载均衡**: 使用Nginx或云负载均衡器
3. **数据库**: 使用PostgreSQL或MySQL
4. **缓存**: 使用Redis缓存频繁访问的数据
5. **监控**: 使用Prometheus + Grafana监控系统

## 📝 下一步开发计划

1. **完善前端界面** - 创建用户友好的自动化工作台
2. **数据库集成** - 实现持久化存储
3. **更多代理** - 添加客服、流程、设计自动化代理
4. **高级功能** - 添加模板、工作流、协作功能
5. **企业功能** - 添加团队管理、权限控制、审计功能

这个集成为OpenHands提供了强大的SaaS自动化能力，可以支持多种商业化场景。
