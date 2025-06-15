"""
数据分析自动化代理 - 基于OpenHands架构
自动化数据清洗、分析、可视化和报告生成
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import numpy as np
import pandas as pd


class AnalysisType(Enum):
    DESCRIPTIVE = 'descriptive'  # 描述性分析
    DIAGNOSTIC = 'diagnostic'  # 诊断性分析
    PREDICTIVE = 'predictive'  # 预测性分析
    PRESCRIPTIVE = 'prescriptive'  # 处方性分析


class DataSource(Enum):
    CSV = 'csv'
    DATABASE = 'database'
    API = 'api'
    EXCEL = 'excel'
    JSON = 'json'


@dataclass
class AnalysisRequest:
    data_source: DataSource
    data_path: str
    analysis_type: AnalysisType
    business_question: str
    target_metrics: list[str]
    time_range: Optional[tuple] = None
    filters: Optional[dict] = None
    output_format: str = 'report'  # report, dashboard, presentation


class DataAnalysisAgent:
    """数据分析自动化代理"""

    def __init__(self, llm_config):
        self.llm_config = llm_config
        self.data_processors = {
            DataSource.CSV: self._load_csv,
            DataSource.DATABASE: self._load_database,
            DataSource.API: self._load_api,
            DataSource.EXCEL: self._load_excel,
            DataSource.JSON: self._load_json,
        }

    async def analyze_data(self, request: AnalysisRequest) -> dict:
        """执行完整的数据分析流程"""

        # 1. 数据加载和预处理
        data = await self._load_and_preprocess_data(request)

        # 2. 数据质量检查
        quality_report = await self._assess_data_quality(data)

        # 3. 探索性数据分析
        eda_results = await self._exploratory_data_analysis(data, request)

        # 4. 执行具体分析
        analysis_results = await self._execute_analysis(data, request)

        # 5. 生成洞察和建议
        insights = await self._generate_insights(analysis_results, request)

        # 6. 创建可视化
        visualizations = await self._create_visualizations(
            data, analysis_results, request
        )

        # 7. 生成报告
        report = await self._generate_report(
            data, analysis_results, insights, visualizations, request
        )

        return {
            'data_summary': self._summarize_data(data),
            'quality_report': quality_report,
            'eda_results': eda_results,
            'analysis_results': analysis_results,
            'insights': insights,
            'visualizations': visualizations,
            'report': report,
            'recommendations': await self._generate_recommendations(insights, request),
        }

    async def _load_and_preprocess_data(self, request: AnalysisRequest) -> pd.DataFrame:
        """加载和预处理数据"""

        # 加载数据
        loader = self.data_processors[request.data_source]
        data = await loader(request.data_path)

        # 应用过滤器
        if request.filters:
            data = self._apply_filters(data, request.filters)

        # 应用时间范围
        if request.time_range:
            data = self._apply_time_filter(data, request.time_range)

        # 数据清洗
        data = await self._clean_data(data)

        return data

    async def _assess_data_quality(self, data: pd.DataFrame) -> dict:
        """评估数据质量"""

        quality_metrics = {
            'completeness': self._calculate_completeness(data),
            'consistency': self._check_consistency(data),
            'accuracy': await self._assess_accuracy(data),
            'timeliness': self._check_timeliness(data),
            'validity': self._check_validity(data),
        }

        # 使用LLM生成质量报告
        prompt = f"""
        基于以下数据质量指标，生成数据质量评估报告：

        数据形状: {data.shape}
        完整性: {quality_metrics['completeness']}
        一致性问题: {quality_metrics['consistency']}
        准确性评估: {quality_metrics['accuracy']}

        请提供：
        1. 总体数据质量评分
        2. 主要质量问题
        3. 数据清洗建议
        4. 分析可信度评估
        """

        quality_report = await self._call_llm(prompt)
        quality_metrics['llm_assessment'] = quality_report

        return quality_metrics

    async def _exploratory_data_analysis(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> dict:
        """探索性数据分析"""

        eda_results = {
            'basic_stats': data.describe(),
            'correlation_matrix': data.corr()
            if data.select_dtypes(include=[np.number]).shape[1] > 1
            else None,
            'missing_values': data.isnull().sum(),
            'data_types': data.dtypes,
            'unique_values': {col: data[col].nunique() for col in data.columns},
        }

        # 使用LLM分析EDA结果
        prompt = f"""
        基于以下探索性数据分析结果，提供数据洞察：

        业务问题: {request.business_question}
        目标指标: {request.target_metrics}

        基础统计: {eda_results['basic_stats'].to_string()}
        缺失值情况: {eda_results['missing_values'].to_string()}

        请提供：
        1. 数据分布特征
        2. 异常值识别
        3. 变量关系分析
        4. 潜在的分析方向
        """

        eda_insights = await self._call_llm(prompt)
        eda_results['insights'] = eda_insights

        return eda_results

    async def _execute_analysis(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> dict:
        """执行具体的分析类型"""

        if request.analysis_type == AnalysisType.DESCRIPTIVE:
            return await self._descriptive_analysis(data, request)
        elif request.analysis_type == AnalysisType.DIAGNOSTIC:
            return await self._diagnostic_analysis(data, request)
        elif request.analysis_type == AnalysisType.PREDICTIVE:
            return await self._predictive_analysis(data, request)
        elif request.analysis_type == AnalysisType.PRESCRIPTIVE:
            return await self._prescriptive_analysis(data, request)

    async def _descriptive_analysis(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> dict:
        """描述性分析"""

        results = {}

        for metric in request.target_metrics:
            if metric in data.columns:
                results[metric] = {
                    'summary_stats': data[metric].describe(),
                    'trend_analysis': self._analyze_trend(data, metric),
                    'distribution': self._analyze_distribution(data[metric]),
                    'outliers': self._detect_outliers(data[metric]),
                }

        # 生成描述性分析报告
        prompt = f"""
        基于以下描述性分析结果，生成业务洞察：

        业务问题: {request.business_question}
        分析结果: {results}

        请提供：
        1. 关键指标表现总结
        2. 趋势和模式识别
        3. 业务影响分析
        4. 关注点和异常情况
        """

        insights = await self._call_llm(prompt)
        results['business_insights'] = insights

        return results

    async def _predictive_analysis(
        self, data: pd.DataFrame, request: AnalysisRequest
    ) -> dict:
        """预测性分析"""

        from sklearn.ensemble import RandomForestRegressor
        from sklearn.metrics import mean_squared_error, r2_score
        from sklearn.model_selection import train_test_split

        results = {}

        # 为每个目标指标构建预测模型
        for metric in request.target_metrics:
            if metric in data.columns:
                # 准备特征和目标变量
                features = data.select_dtypes(include=[np.number]).drop(
                    columns=[metric], errors='ignore'
                )
                target = data[metric]

                # 分割数据
                X_train, X_test, y_train, y_test = train_test_split(
                    features, target, test_size=0.2, random_state=42
                )

                # 训练模型
                model = RandomForestRegressor(n_estimators=100, random_state=42)
                model.fit(X_train, y_train)

                # 预测和评估
                predictions = model.predict(X_test)

                results[metric] = {
                    'model_performance': {
                        'r2_score': r2_score(y_test, predictions),
                        'mse': mean_squared_error(y_test, predictions),
                        'feature_importance': dict(
                            zip(features.columns, model.feature_importances_)
                        ),
                    },
                    'predictions': predictions.tolist()[:10],  # 前10个预测值
                    'actual_vs_predicted': list(
                        zip(y_test.tolist()[:10], predictions.tolist()[:10])
                    ),
                }

        # 生成预测分析报告
        prompt = f"""
        基于以下预测分析结果，生成预测洞察：

        业务问题: {request.business_question}
        模型性能: {results}

        请提供：
        1. 预测模型可靠性评估
        2. 关键影响因素分析
        3. 未来趋势预测
        4. 业务决策建议
        """

        insights = await self._call_llm(prompt)
        results['predictive_insights'] = insights

        return results

    async def _generate_insights(
        self, analysis_results: dict, request: AnalysisRequest
    ) -> list[str]:
        """生成业务洞察"""

        prompt = f"""
        基于以下分析结果，生成关键业务洞察：

        业务问题: {request.business_question}
        分析类型: {request.analysis_type.value}
        分析结果: {analysis_results}

        请生成5-7个关键洞察，每个洞察应该：
        1. 基于数据事实
        2. 与业务问题相关
        3. 可操作性强
        4. 量化影响程度
        """

        insights_text = await self._call_llm(prompt)
        return self._parse_insights(insights_text)

    async def _create_visualizations(
        self, data: pd.DataFrame, analysis_results: dict, request: AnalysisRequest
    ) -> dict:
        """创建数据可视化"""

        visualizations = {}

        # 为每个目标指标创建可视化
        for metric in request.target_metrics:
            if metric in data.columns:
                viz_code = await self._generate_visualization_code(
                    data, metric, request
                )
                visualizations[metric] = {
                    'code': viz_code,
                    'description': f'{metric}的可视化分析',
                }

        return visualizations

    async def _generate_visualization_code(
        self, data: pd.DataFrame, metric: str, request: AnalysisRequest
    ) -> str:
        """生成可视化代码"""

        prompt = f"""
        为以下数据和指标生成Python可视化代码：

        数据列: {list(data.columns)}
        目标指标: {metric}
        数据类型: {data[metric].dtype}
        业务问题: {request.business_question}

        请生成使用matplotlib/seaborn的可视化代码，包括：
        1. 适合的图表类型
        2. 清晰的标题和标签
        3. 专业的样式设置
        4. 必要的统计信息
        """

        viz_code = await self._call_llm(prompt)
        return viz_code

    async def _generate_report(
        self,
        data: pd.DataFrame,
        analysis_results: dict,
        insights: list[str],
        visualizations: dict,
        request: AnalysisRequest,
    ) -> str:
        """生成完整的分析报告"""

        prompt = f"""
        生成完整的数据分析报告：

        业务问题: {request.business_question}
        分析类型: {request.analysis_type.value}
        数据概况: 共{len(data)}行，{len(data.columns)}列

        分析结果: {analysis_results}
        关键洞察: {insights}

        请生成包含以下部分的专业报告：
        1. 执行摘要
        2. 数据概况
        3. 分析方法
        4. 关键发现
        5. 业务洞察
        6. 建议行动
        7. 局限性说明

        报告应该专业、清晰、面向业务决策者。
        """

        report = await self._call_llm(prompt)
        return report

    # 辅助方法
    def _calculate_completeness(self, data: pd.DataFrame) -> dict:
        """计算数据完整性"""
        total_cells = data.shape[0] * data.shape[1]
        missing_cells = data.isnull().sum().sum()
        completeness = (total_cells - missing_cells) / total_cells * 100

        return {
            'overall_completeness': round(completeness, 2),
            'column_completeness': {
                col: round((1 - data[col].isnull().sum() / len(data)) * 100, 2)
                for col in data.columns
            },
        }

    async def _call_llm(self, prompt: str) -> str:
        """调用LLM"""
        # 这里应该调用实际的LLM API
        # 返回模拟响应
        return f'LLM响应: {prompt[:100]}...'


# 使用示例
async def demo_data_analysis():
    """演示数据分析自动化功能"""

    agent = DataAnalysisAgent(llm_config={})

    # 销售数据分析请求
    analysis_request = AnalysisRequest(
        data_source=DataSource.CSV,
        data_path='sales_data.csv',
        analysis_type=AnalysisType.DESCRIPTIVE,
        business_question='过去一年的销售表现如何？哪些因素影响销售？',
        target_metrics=['revenue', 'units_sold', 'customer_count'],
        time_range=('2023-01-01', '2023-12-31'),
        filters={'region': ['North', 'South']},
        output_format='report',
    )

    result = await agent.analyze_data(analysis_request)

    print('数据分析报告:')
    print(result['report'])
    print(f'关键洞察: {result["insights"]}')


if __name__ == '__main__':
    import asyncio

    asyncio.run(demo_data_analysis())
