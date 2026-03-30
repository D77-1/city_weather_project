<template>
  <EChartWrapper :option="lineOption" :height="height" />
</template>

<script setup>
import { computed } from 'vue'
import EChartWrapper from './EChartWrapper.vue'

const props = defineProps({
  trendData: { type: Object, default: () => ({}) },
  title: { type: String, default: 'AQI 趋势与预测' },
  height: { type: String, default: '360px' },
  metric: { type: String, default: 'AQI' },
  algorithmLabel: { type: String, default: '预测值' },
  referenceLabel: { type: String, default: '参考线' },
})

const lineOption = computed(() => {
  const d = props.trendData
  if (!d.dates || d.dates.length === 0) {
    return { title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999' } } }
  }

  const labelInterval = d.dates.length > 60 ? 6 : d.dates.length > 30 ? 3 : 1
  const series = [
    {
      name: `${props.metric} 实际值`,
      type: 'line',
      data: d.actual,
      smooth: true,
      symbol: d.dates.length > 60 ? 'none' : 'circle',
      symbolSize: 3,
      lineStyle: { width: 2 },
      itemStyle: { color: '#409EFF' },
      sampling: 'lttb',
      large: d.dates.length > 200,
      z: 3,
    },
  ]

  if (d.ma?.some((x) => x != null)) {
    series.push({
      name: props.referenceLabel,
      type: 'line',
      data: d.ma,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 1.5, type: 'dashed', color: '#67C23A' },
      z: 2,
    })
  }

  if (d.predicted?.some((x) => x != null)) {
    series.push({
      name: props.algorithmLabel,
      type: 'line',
      data: d.predicted,
      smooth: true,
      symbol: 'diamond',
      symbolSize: 6,
      lineStyle: { width: 2, type: 'dotted' },
      itemStyle: { color: '#E6A23C' },
      z: 3,
    })
  }

  if (d.upper?.some((x) => x != null) && d.lower?.some((x) => x != null)) {
    series.push({
      name: '预测波动范围',
      type: 'line',
      data: d.upper,
      symbol: 'none',
      lineStyle: { width: 1, type: 'dashed', color: 'rgba(230,162,60,0.5)' },
      z: 1,
    })
    series.push({
      name: '_lower',
      type: 'line',
      data: d.lower,
      symbol: 'none',
      lineStyle: { width: 1, type: 'dashed', color: 'rgba(230,162,60,0.5)' },
      z: 1,
    })
    series.push({
      name: '_band_base',
      type: 'line',
      data: d.lower,
      symbol: 'none',
      lineStyle: { width: 0 },
      stack: '_ci',
      areaStyle: { opacity: 0 },
      z: 0,
    })
    series.push({
      name: '_band_fill',
      type: 'line',
      data: d.lower?.map((v, i) => {
        if (v != null && d.upper[i] != null) return Math.max(0, d.upper[i] - v)
        return null
      }),
      symbol: 'none',
      lineStyle: { width: 0 },
      stack: '_ci',
      areaStyle: { color: 'rgba(230,162,60,0.10)' },
      z: 0,
    })
  }

  const legendData = [`${props.metric} 实际值`]
  if (d.ma?.some((x) => x != null)) legendData.push(props.referenceLabel)
  if (d.predicted?.some((x) => x != null)) legendData.push(props.algorithmLabel)
  if (d.upper?.some((x) => x != null) && d.lower?.some((x) => x != null)) legendData.push('预测波动范围')

  return {
    title: { text: props.title, left: 'center', top: 5, textStyle: { fontSize: 14 } },
    tooltip: {
      trigger: 'axis',
      formatter: (params) => {
        const date = params[0]?.axisValue || ''
        let html = `<b>${date}</b>`
        for (const p of params) {
          if (p.seriesName.startsWith('_')) continue
          if (p.value != null) html += `<br/>${p.marker} ${p.seriesName}: ${p.value}`
        }
        const upperP = params.find(p => p.seriesName === '预测波动范围')
        const lowerP = params.find(p => p.seriesName === '_lower')
        if (upperP?.value != null && lowerP?.value != null) {
          html += `<br/><span style="color:#aaa">预测在 ${lowerP.value} ~ ${upperP.value} 之间波动</span>`
        }
        return html
      },
    },
    legend: {
      data: legendData,
      top: 28,
      right: 10,
      textStyle: { fontSize: 11 },
      itemWidth: 16,
      itemHeight: 10,
    },
    grid: { left: 55, right: 20, top: 55, bottom: 60 },
    xAxis: {
      type: 'category',
      data: d.dates,
      axisLabel: {
        rotate: 40,
        fontSize: 10,
        interval: labelInterval,
        formatter: (val) => val.slice(5),
      },
      boundaryGap: false,
    },
    yAxis: { type: 'value', name: props.metric },
    dataZoom: [{ type: 'inside', start: d.dates.length > 60 ? 40 : 0, end: 100 }],
    series,
  }
})
</script>
