<template>
  <EChartWrapper :option="radarOption" :height="height" />
</template>

<script setup>
import { computed } from 'vue'
import EChartWrapper from './EChartWrapper.vue'

const props = defineProps({
  pollutantData: { type: Object, default: () => ({}) },
  cityName: { type: String, default: '' },
  height: { type: String, default: '320px' },
})

// 指标定义 + 国标日均限值 (HJ 633-2012, 二级标准)
const INDICATORS = [
  { name: 'PM2.5', key: 'pm25', max: 250, limit: 75, unit: 'μg/m³' },
  { name: 'PM10', key: 'pm10', max: 420, limit: 150, unit: 'μg/m³' },
  { name: 'SO₂', key: 'so2', max: 150, limit: 60, unit: 'μg/m³' },
  { name: 'NO₂', key: 'no2', max: 200, limit: 80, unit: 'μg/m³' },
  { name: 'CO', key: 'co', max: 10, limit: 4, unit: 'mg/m³' },
  { name: 'O₃', key: 'o3', max: 300, limit: 160, unit: 'μg/m³' },
]

const radarOption = computed(() => {
  const d = props.pollutantData
  const values = INDICATORS.map((i) => d[i.key] ?? 0)
  const hasData = values.some((v) => v > 0)

  if (!hasData) {
    return { title: { text: '暂无污染物数据', left: 'center', top: 'center', textStyle: { color: '#94a3b8' } } }
  }

  // 国标限值（归一化到雷达图坐标）
  const limitValues = INDICATORS.map(i => i.limit)

  return {
    title: {
      text: `${props.cityName} 污染物成分分析`,
      left: 'center',
      top: 5,
      textStyle: { fontSize: 14, fontWeight: 700 },
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const v = params.value
        if (!v) return ''
        return INDICATORS.map((ind, i) => {
          const val = v[i]
          const overLimit = val > ind.limit
          const marker = overLimit ? '<span style="color:#dc2626;font-weight:700">超标</span>' : '<span style="color:#059669">达标</span>'
          return `${ind.name}: ${val} ${ind.unit} (限值 ${ind.limit}) ${marker}`
        }).join('<br/>')
      },
    },
    legend: {
      bottom: 0,
      data: [props.cityName, '国标限值(二级)'],
      textStyle: { fontSize: 11 },
    },
    radar: {
      center: ['50%', '52%'],
      radius: '62%',
      indicator: INDICATORS.map((i) => ({
        name: `${i.name}\n${values[INDICATORS.indexOf(i)]} ${i.unit}`,
        max: i.max,
      })),
      shape: 'polygon',
      splitNumber: 4,
      splitArea: {
        areaStyle: { color: ['rgba(13,148,136,0.02)', 'rgba(13,148,136,0.05)', 'rgba(13,148,136,0.02)', 'rgba(13,148,136,0.05)'] },
      },
      axisLine: { lineStyle: { color: '#cbd5e1' } },
      splitLine: { lineStyle: { color: '#e2e8f0', type: 'dashed' } },
      axisName: { fontSize: 10, color: '#475569', lineHeight: 14 },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: values,
            name: props.cityName,
            symbol: 'circle',
            symbolSize: 6,
            areaStyle: { color: 'rgba(13,148,136,0.2)' },
            lineStyle: { color: '#0d9488', width: 2 },
            itemStyle: { color: '#0d9488', borderWidth: 2, borderColor: '#fff' },
            label: {
              show: true,
              formatter: (p) => {
                const idx = p.dimensionIndex
                const val = p.value
                const limit = INDICATORS[idx].limit
                return val > limit ? `{over|${val}}` : `${val}`
              },
              rich: {
                over: { color: '#dc2626', fontWeight: 700 },
              },
              fontSize: 10,
              color: '#475569',
            },
          },
          {
            value: limitValues,
            name: '国标限值(二级)',
            symbol: 'none',
            areaStyle: { opacity: 0 },
            lineStyle: { color: '#dc2626', width: 1.5, type: 'dashed' },
            itemStyle: { color: '#dc2626' },
          },
        ],
      },
    ],
  }
})
</script>
