"""
Simplified data analysis automation agent integrated with OpenHands architecture.
"""

import json

from openhands.controller.agent import Agent
from openhands.core.config import AgentConfig
from openhands.events.action import Action, MessageAction
from openhands.llm.llm import LLM


class DataAgent(Agent):
    """Data analysis automation agent for OpenHands."""

    VERSION = '1.0.0'

    def __init__(self, llm: LLM, config: AgentConfig) -> None:
        """Initialize the data agent."""
        super().__init__(llm, config)
        self.analysis_types = {
            'descriptive': self._descriptive_analysis,
            'diagnostic': self._diagnostic_analysis,
            'predictive': self._predictive_analysis,
            'prescriptive': self._prescriptive_analysis,
        }

    def step(self, state) -> Action:
        """Take a step in data analysis."""
        # Get the latest user message
        messages = state.history.get_events_as_list()
        if not messages:
            return MessageAction(
                content='请提供数据文件路径和分析需求。支持CSV、Excel、JSON格式。'
            )

        last_message = messages[-1]
        if hasattr(last_message, 'content'):
            user_input = last_message.content

            # Parse analysis request
            analysis_request = self._parse_analysis_request(user_input)

            # Perform analysis based on type
            analysis_type = analysis_request.get('analysis_type', 'descriptive')
            if analysis_type in self.analysis_types:
                return self.analysis_types[analysis_type](analysis_request)
            else:
                return MessageAction(
                    content=f'支持的分析类型: {", ".join(self.analysis_types.keys())}'
                )

        return MessageAction(content='请提供数据分析需求。')

    def _parse_analysis_request(self, user_input: str) -> dict:
        """Parse user analysis request."""
        prompt = f"""
        解析以下数据分析请求，提取关键信息：

        用户请求: {user_input}

        请返回JSON格式，包含：
        - data_path: 数据文件路径（如果提到）
        - analysis_type: 分析类型 (descriptive, diagnostic, predictive, prescriptive)
        - business_question: 业务问题
        - target_metrics: 目标指标列表
        """

        response = self.llm.completion(
            messages=[{'role': 'user', 'content': prompt}], temperature=0.1
        )

        try:
            return json.loads(response.choices[0].message.content)
        except Exception:
            # Fallback parsing
            return {
                'analysis_type': 'descriptive',
                'business_question': user_input,
                'target_metrics': [],
                'data_path': None,
            }

    def _descriptive_analysis(self, request: dict) -> Action:
        """Perform descriptive analysis."""
        data_path = request.get('data_path', 'your_data.csv')
        business_question = request.get('business_question', '')

        analysis_guide = f"""
=== 描述性数据分析指南 ===

业务问题: {business_question}
数据文件: {data_path}

建议的分析步骤：

1. **数据加载和概览**
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 加载数据
df = pd.read_csv('{data_path}')
print(f"数据形状: {{df.shape[0]}}行 {{df.shape[1]}}列")
print("列名:", list(df.columns))
print("\\n前5行数据:")
print(df.head())
```

2. **基础统计分析**
```python
# 基础统计信息
print("\\n=== 基础统计 ===")
print(df.describe())

# 缺失值检查
print("\\n=== 缺失值检查 ===")
missing_data = df.isnull().sum()
print(missing_data[missing_data > 0])
```

3. **数据可视化**
```python
# 数值列相关性分析
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) > 1:
    plt.figure(figsize=(10, 8))
    correlation_matrix = df[numeric_cols].corr()
    sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title('特征相关性热力图')
    plt.show()
```

请根据您的具体数据文件运行上述代码进行分析。
        """

        return MessageAction(content=analysis_guide)

    def _diagnostic_analysis(self, request: dict) -> Action:
        """Perform diagnostic analysis."""
        business_question = request.get('business_question', '')

        analysis_guide = f"""
=== 诊断性数据分析指南 ===

业务问题: {business_question}

诊断性分析重点关注"为什么会发生"，建议的分析方法：

1. **异常值检测**
```python
# 使用IQR方法检测异常值
for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
    print(f"{{col}}: 发现 {{len(outliers)}} 个异常值")
```

2. **趋势分析**
```python
# 如果有时间列，分析趋势
if 'date' in df.columns or 'time' in df.columns:
    # 时间序列分析
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date').plot(figsize=(12, 6))
    plt.title('时间序列趋势')
    plt.show()
```

3. **分组分析**
```python
# 按分类变量分组分析
categorical_cols = df.select_dtypes(include=['object']).columns
for cat_col in categorical_cols[:2]:
    print(f"\\n=== {{cat_col}} 分组统计 ===")
    grouped = df.groupby(cat_col)[numeric_cols].mean()
    print(grouped)
```

这些分析将帮助您理解数据中的模式和异常。
        """

        return MessageAction(content=analysis_guide)

    def _predictive_analysis(self, request: dict) -> Action:
        """Perform predictive analysis."""
        target_metrics = request.get('target_metrics', [])

        analysis_guide = f"""
=== 预测性数据分析指南 ===

目标指标: {target_metrics}

预测性分析重点关注"将来会发生什么"，建议的方法：

1. **特征工程**
```python
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split

# 处理分类变量
le = LabelEncoder()
for col in categorical_cols:
    if df[col].nunique() < 20:
        df[col + '_encoded'] = le.fit_transform(df[col])

# 特征标准化
scaler = StandardScaler()
numeric_features = df.select_dtypes(include=[np.number]).columns
df[numeric_features] = scaler.fit_transform(df[numeric_features])
```

2. **模型训练**
```python
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score

# 假设目标变量是第一个数值列
target_col = numeric_features[0]
feature_cols = [col for col in numeric_features if col != target_col]

X = df[feature_cols]
y = df[target_col]

# 分割数据
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 训练模型
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 预测和评估
predictions = model.predict(X_test)
print(f"R² 分数: {{r2_score(y_test, predictions):.3f}}")
print(f"均方误差: {{mean_squared_error(y_test, predictions):.3f}}")
```

3. **特征重要性**
```python
# 特征重要性分析
feature_importance = pd.DataFrame({{
    'feature': feature_cols,
    'importance': model.feature_importances_
}}).sort_values('importance', ascending=False)

print("\\n特征重要性排名:")
print(feature_importance)
```

请根据您的具体业务需求调整目标变量和特征。
        """

        return MessageAction(content=analysis_guide)

    def _prescriptive_analysis(self, request: dict) -> Action:
        """Perform prescriptive analysis."""
        business_question = request.get('business_question', '')

        # Generate prescriptive insights using LLM
        prompt = f"""
        基于数据分析结果，为以下业务问题提供处方性建议：

        业务问题: {business_question}

        请提供：
        1. 关键发现总结
        2. 具体行动建议
        3. 优先级排序
        4. 预期影响评估
        5. 实施步骤
        6. 风险评估
        """

        response = self.llm.completion(
            messages=[{'role': 'user', 'content': prompt}], temperature=0.3
        )

        insights = response.choices[0].message.content

        return MessageAction(
            content=f'=== 处方性分析建议 ===\n\n{insights}\n\n'
            f'注意：这些建议基于数据分析结果，请结合实际业务情况进行决策。'
        )
