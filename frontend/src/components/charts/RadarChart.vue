<template>
  <EChartWrapper :option="radarOption" :height="height" />
</template>

<script setup>
import { computed } from 'vue'
import EChartWrapper from './EChartWrapper.vue'

const props = defineProps({
  // { pm25, pm10, so2, no2, co, o3 }
  pollutantData: { type: Object, default: () => ({}) },
  cityName: { type: String, default: '' },
  height: { type: String, default: '320px' },
})

// 各指标的参考上限（用于雷达图的 max 值）
const INDICATORS = [
  { name: 'PM2.5', key: 'pm25', max: 250, unit: 'μg/m³' },
  { name: 'PM10', key: 'pm10', max: 420, unit: 'μg/m³' },
  { name: 'SO₂', key: 'so2', max: 100, unit: 'μg/m³' },
  { name: 'NO₂', key: 'no2', max: 150, unit: 'μg/m³' },
  { name: 'CO', key: 'co', max: 10, unit: 'mg/m³' },
  { name: 'O₃', key: 'o3', max: 300, unit: 'μg/m³' },
]

const radarOption = computed(() => {
  const d = props.pollutantData
  const values = INDICATORS.map((i) => d[i.key] ?? 0)
  const hasData = values.some((v) => v > 0)

  if (!hasData) {
    return { title: { text: '暂无污染物数据', left: 'center', top: 'center', textStyle: { color: '#999' } } }
  }

  return {
    title: {
      text: `${props.cityName} 污染物成分`,
      left: 'center',
      textStyle: { fontSize: 14 },
    },
    tooltip: {
      trigger: 'item',
      formatter: (params) => {
        const v = params.value
        return INDICATORS.map((ind, i) => `${ind.name}: ${v[i]} ${ind.unit}`).join('<br/>')
      },
    },
    radar: {
      indicator: INDICATORS.map((i) => ({ name: i.name, max: i.max })),
      shape: 'polygon',
      splitArea: { areaStyle: { color: ['rgba(64,158,255,0.05)', 'rgba(64,158,255,0.1)'] } },
      axisLine: { lineStyle: { color: '#c0c4cc' } },
      splitLine: { lineStyle: { color: '#dcdfe6' } },
    },
    series: [
      {
        type: 'radar',
        data: [
          {
            value: values,
            name: props.cityName,
            areaStyle: { color: 'rgba(64,158,255,0.25)' },
            lineStyle: { color: '#409EFF', width: 2 },
            itemStyle: { color: '#409EFF' },
          },
        ],
      },
    ],
  }
})
</script>
