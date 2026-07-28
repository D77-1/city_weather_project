<template>
  <EChartWrapper :option="lineOption" :height="height" />
</template>

<script setup>
import { computed } from 'vue'
import EChartWrapper from './EChartWrapper.vue'
import { buildTrendLineOption } from './trendLineOption.js'

const props = defineProps({
  trendData: { type: Object, default: () => ({}) },
  title: { type: String, default: 'AQI 趋势与预测' },
  height: { type: String, default: '360px' },
  metric: { type: String, default: 'AQI' },
  algorithmLabel: { type: String, default: '预测值' },
  referenceLabel: { type: String, default: '参考线' },
})

const lineOption = computed(() => buildTrendLineOption({
  trendData: props.trendData,
  title: props.title,
  metric: props.metric,
  algorithmLabel: props.algorithmLabel,
  referenceLabel: props.referenceLabel,
}))
</script>
