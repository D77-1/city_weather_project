"""
通义千问 (Qwen) AI 服务层
通过 DashScope SDK 调用大模型，生成空气质量分析报告
"""
import time
import dashscope
from dashscope import Generation
from flask import current_app

SYSTEM_PROMPT = """你是"空气质量智能助手"，一位专业的环境健康顾问。你的任务是根据用户提供的空气质量数据，生成通俗易懂的分析报告和健康建议。

## 你的能力:
1. 解读 AQI（空气质量指数）和六项污染物（PM2.5、PM10、SO2、NO2、CO、O3）的含义
2. 分析空气质量变化趋势、模型预测结果和异常波动的可能原因
3. 结合综合风险评分与未来5天预测，提供针对性的健康防护建议
4. 区分普通人群、儿童老人和敏感人群给出建议

## 输出要求:
- 使用中文回答，语言亲切易懂，避免过多专业术语
- 回答结构清晰，适当使用 emoji 增加可读性
- 如果未来几天存在高风险日期，要明确指出
- 回答控制在 350 字以内，简洁有力"""


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

    if 'prediction' in context_data and context_data['prediction']:
        p = context_data['prediction']
        algorithm = context_data.get('selectedAlgorithm', 'moving_average')
        parts.append(
            f"未来趋势预测(算法={algorithm}): 未来{len(p)}天主要预测为 "
            + ', '.join([f"{item.get('date','')}: {item.get('predicted','')}" for item in p[:5]])
        )

    if 'multiMetricPrediction' in context_data and context_data['multiMetricPrediction']:
        m = context_data['multiMetricPrediction']
        metric_parts = []
        for metric, items in m.items():
            preview = ', '.join([f"{x.get('date','')}: {x.get('predicted','')}" for x in items[:3]])
            metric_parts.append(f"{metric} -> {preview}")
        parts.append("多指标未来预测: " + '；'.join(metric_parts))

    if 'comparison' in context_data and context_data['comparison']:
        c_list = context_data['comparison']
        parts.append(
            "模型评估对比: " + '；'.join([
                f"{item.get('algorithm')}: MAE={item.get('mae')}, RMSE={item.get('rmse')}, MAPE={item.get('mape')}, R2={item.get('r2')}"
                for item in c_list[:3]
            ])
        )

    if 'risk' in context_data and context_data['risk']:
        r = context_data['risk']
        parts.append(f"综合风险评分: {r.get('score','N/A')}，风险等级={r.get('level','N/A')}，摘要={r.get('summary','')}")
        drivers = r.get('drivers') or []
        if drivers:
            parts.append("主要风险因子: " + '；'.join([
                f"{d.get('factor')}={d.get('value')} (贡献{d.get('contribution')})" for d in drivers[:4]
            ]))
        future_risk = r.get('futureRisk') or []
        if future_risk:
            parts.append("未来风险趋势: " + '；'.join([
                f"{d.get('date')}: {d.get('level')}({d.get('score')})" for d in future_risk[:5]
            ]))

    if 'anomalies' in context_data and context_data['anomalies']:
        a_list = context_data['anomalies']
        parts.append(
            f"近期异常事件: 检测到{len(a_list)}个异常, "
            + '; '.join([f"{a.get('date','')}{a.get('metric','')}={a.get('value','')}({a.get('severity','')},{a.get('type','')})" for a in a_list[:3]])
        )

    return '\n'.join(parts)


def chat_with_qwen(user_message, context_data=None, model='qwen-turbo'):
    api_key = current_app.config.get('DASHSCOPE_API_KEY', '')
    if not api_key:
        return {
            'content': '抱歉，AI 服务暂未配置 API Key，请联系管理员。',
            'tokens': 0,
            'elapsed_ms': 0,
        }

    dashscope.api_key = api_key
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
