"""
通义千问 (Qwen) AI 服务层
通过 DashScope SDK 调用大模型，生成空气质量分析报告
"""
import time
import json
import dashscope
from dashscope import Generation
from flask import current_app

# 系统 Prompt - 定义 AI 人设与输出格式
SYSTEM_PROMPT = """你是"空气质量智能助手"，一位专业的环境健康顾问。你的任务是根据用户提供的空气质量数据，生成通俗易懂的分析报告和健康建议。

## 你的能力:
1. 解读 AQI（空气质量指数）和六项污染物（PM2.5、PM10、SO2、NO2、CO、O3）的含义
2. 分析空气质量变化趋势和异常波动的可能原因
3. 提供针对性的健康防护建议（户外活动、口罩佩戴、室内通风等）
4. 解读预测数据，帮助用户提前做好防护准备

## 输出要求:
- 使用中文回答，语言亲切易懂，避免过多专业术语
- 回答结构清晰，适当使用 emoji 增加可读性
- 如果数据显示异常，要明确指出并给出应对建议
- 回答控制在 300 字以内，简洁有力"""


def build_context_message(context_data):
    """将结构化数据转为自然语言上下文，注入到用户消息前"""
    if not context_data:
        return ''

    parts = []

    if 'cityName' in context_data:
        parts.append(f"当前查看城市: {context_data['cityName']}")

    if 'current' in context_data:
        c = context_data['current']
        parts.append(
            f"最新数据: AQI={c.get('aqi','N/A')}, "
            f"PM2.5={c.get('pm25','N/A')}μg/m³, PM10={c.get('pm10','N/A')}μg/m³, "
            f"SO2={c.get('so2','N/A')}μg/m³, NO2={c.get('no2','N/A')}μg/m³, "
            f"CO={c.get('co','N/A')}mg/m³, O3={c.get('o3','N/A')}μg/m³, "
            f"空气等级={c.get('qualityLevel','N/A')}"
        )

    if 'prediction' in context_data:
        p = context_data['prediction']
        parts.append(
            f"未来趋势预测(移动平均法): 未来{len(p)}天AQI预测值为 "
            + ', '.join([f"{item.get('date','')}: {item.get('predicted','')}" for item in p[:5]])
        )

    if 'anomalies' in context_data and context_data['anomalies']:
        a_list = context_data['anomalies']
        parts.append(
            f"近期异常事件: 检测到{len(a_list)}个异常, "
            + '; '.join([f"{a.get('date','')}{a.get('metric','')}={a.get('value','')}"
                         f"({a.get('severity','')},{a.get('type','')})" for a in a_list[:3]])
        )

    return '\n'.join(parts)


def chat_with_qwen(user_message, context_data=None, model='qwen-turbo'):
    """
    调用通义千问生成回复

    参数:
        user_message: 用户输入的文本
        context_data: 结构化上下文 (可选的 dict, 包含当前AQI/预测/异常等)
        model: 模型名称 (qwen-turbo / qwen-plus / qwen-max)

    返回:
        { 'content': str, 'tokens': int, 'elapsed_ms': int }
    """
    api_key = current_app.config.get('DASHSCOPE_API_KEY', '')
    if not api_key:
        return {
            'content': '抱歉，AI 服务暂未配置 API Key，请联系管理员。',
            'tokens': 0,
            'elapsed_ms': 0,
        }

    dashscope.api_key = api_key

    # 构建消息列表
    context_text = build_context_message(context_data)
    full_user_msg = f"[数据背景]\n{context_text}\n\n[我的问题]\n{user_message}" if context_text else user_message

    messages = [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': full_user_msg},
    ]

    start = time.time()
    try:
        response = Generation.call(
            model=model,
            messages=messages,
            result_format='message',
        )

        elapsed_ms = int((time.time() - start) * 1000)

        if response.status_code == 200:
            content = response.output.choices[0].message.content
            tokens = response.usage.get('total_tokens', 0) if response.usage else 0
            return {'content': content, 'tokens': tokens, 'elapsed_ms': elapsed_ms}
        else:
            return {
                'content': f'AI 服务返回错误: {response.code} - {response.message}',
                'tokens': 0,
                'elapsed_ms': elapsed_ms,
            }

    except Exception as e:
        elapsed_ms = int((time.time() - start) * 1000)
        return {
            'content': f'AI 服务调用异常: {str(e)}',
            'tokens': 0,
            'elapsed_ms': elapsed_ms,
        }
