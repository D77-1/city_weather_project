import assert from 'node:assert/strict'
import { buildTrendLineOption } from './trendLineOption.js'

const option = buildTrendLineOption({
  trendData: {
    dates: ['2026-03-28', '2026-03-29', '2026-03-30'],
    actual: [100, 110, null],
    reference: [98, 108, null],
    predicted: [null, null, 120],
    upper: [null, null, 130],
    lower: [null, null, 110],
  },
  title: '测试趋势图',
  metric: 'AQI',
  algorithmLabel: 'ARIMA预测',
  referenceLabel: '参考基线',
})

assert.equal(option.legend.data.includes('参考基线'), true, '应展示参考线图例')
assert.equal(option.series.some((item) => item.name === '参考基线'), true, '应生成参考线序列')
assert.deepEqual(option.series.find((item) => item.name === '参考基线')?.data, [98, 108, null], '应使用 reference 数据')
assert.equal(option.series.some((item) => item.name === 'ARIMA预测'), true, '应生成预测序列')

console.log('trendLineOption test passed')
