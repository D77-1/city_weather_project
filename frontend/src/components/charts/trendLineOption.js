export function buildTrendLineOption({
  trendData = {},
  title = 'AQI 趋势与预测',
  metric = 'AQI',
  algorithmLabel = '预测值',
  referenceLabel = '参考线',
} = {}) {
  const d = trendData
  if (!d.dates || d.dates.length === 0) {
    return { title: { text: '暂无数据', left: 'center', top: 'center', textStyle: { color: '#999' } } }
  }

  const referenceSeries = d.reference || d.ma || []
  const labelInterval = d.dates.length > 60 ? 6 : d.dates.length > 30 ? 3 : 1
  const series = [
    {
      name: `${metric} 实际值`,
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

  if (referenceSeries.some((x) => x != null)) {
    series.push({
      name: referenceLabel,
      type: 'line',
      data: referenceSeries,
      smooth: true,
      symbol: 'none',
      lineStyle: { width: 2, type: 'dashed', color: '#67C23A' },
      z: 2,
    })
  }

  if (d.predicted?.some((x) => x != null)) {
    series.push({
      name: algorithmLabel,
      type: 'line',
      data: d.predicted,
      smooth: true,
      connectNulls: false,
      symbol: 'diamond',
      symbolSize: 7,
      lineStyle: { width: 3, type: 'solid', color: '#E6A23C' },
      itemStyle: { color: '#E6A23C' },
      z: 4,
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

  const legendData = [`${metric} 实际值`]
  if (referenceSeries.some((x) => x != null)) legendData.push(referenceLabel)
  if (d.predicted?.some((x) => x != null)) legendData.push(algorithmLabel)
  if (d.upper?.some((x) => x != null) && d.lower?.some((x) => x != null)) legendData.push('预测波动范围')

  return {
    title: { text: title, left: 'center', top: 5, textStyle: { fontSize: 14 } },
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
    yAxis: { type: 'value', name: metric },
    dataZoom: [{ type: 'inside', start: d.dates.length > 60 ? 40 : 0, end: 100 }],
    series,
  }
}
