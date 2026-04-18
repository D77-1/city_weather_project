export function buildTrendLineOption({
  trendData = {},
  title = 'AQI 趋势与预测',
  metric = 'AQI',
  algorithmLabel = '预测值',
  referenceLabel = '参考线',
} = {}) {
  const d = trendData
  if (!d.dates || d.dates.length === 0) {
    return {
      title: {
        text: '暂无数据',
        left: 'center',
        top: 'center',
        textStyle: { color: '#7a878b', fontFamily: 'IBM Plex Mono, Consolas, monospace', fontSize: 13 },
      },
    }
  }

  const referenceSeries = d.reference || d.ma || []
  const labelInterval = d.dates.length > 60 ? 6 : d.dates.length > 30 ? 3 : 1
  const hasBand = d.upper?.some((x) => x != null) && d.lower?.some((x) => x != null)
  const series = [
    {
      name: `${metric} 实际值`,
      type: 'line',
      data: d.actual,
      smooth: true,
      symbol: d.dates.length > 60 ? 'none' : 'circle',
      symbolSize: 4,
      lineStyle: { width: 2.5, color: '#27d3c3' },
      itemStyle: { color: '#27d3c3' },
      areaStyle: { color: 'rgba(39, 211, 195, 0.08)' },
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
      lineStyle: { width: 2, type: 'dashed', color: '#5a7a8a' },
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
      symbolSize: 8,
      lineStyle: { width: 3, type: 'solid', color: '#a8743f' },
      itemStyle: { color: '#a8743f', borderColor: '#fff7ee', borderWidth: 2 },
      z: 4,
    })
  }

  if (hasBand) {
    series.push({
      name: '预测波动范围',
      type: 'line',
      data: d.upper,
      symbol: 'none',
      lineStyle: { width: 1.5, type: 'dashed', color: 'rgba(168,116,63,0.46)' },
      z: 1,
    })
    series.push({
      name: '_lower',
      type: 'line',
      data: d.lower,
      symbol: 'none',
      lineStyle: { width: 1.5, type: 'dashed', color: 'rgba(168,116,63,0.46)' },
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
      areaStyle: { color: 'rgba(168,116,63,0.10)' },
      z: 0,
    })
  }

  const legendData = [`${metric} 实际值`]
  if (referenceSeries.some((x) => x != null)) legendData.push(referenceLabel)
  if (d.predicted?.some((x) => x != null)) legendData.push(algorithmLabel)
  if (hasBand) legendData.push('预测波动范围')

  return {
    backgroundColor: 'transparent',
    title: {
      text: title,
      left: 18,
      top: 10,
      textStyle: {
        fontSize: 15,
        fontWeight: 700,
        color: '#edf6ff',
      },
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(10, 21, 37, 0.95)',
      borderColor: 'rgba(124, 154, 188, 0.22)',
      borderWidth: 1,
      textStyle: { color: '#edf6ff' },
      extraCssText: 'box-shadow: 0 14px 34px rgba(0,0,0,0.3); border-radius: 14px;',
      formatter: (params) => {
        const date = params[0]?.axisValue || ''
        let html = `<div style="font-weight:700;margin-bottom:6px;color:#edf6ff">${date}</div>`
        for (const p of params) {
          if (p.seriesName.startsWith('_')) continue
          if (p.value != null) html += `<div style="margin:2px 0">${p.marker} ${p.seriesName}: ${p.value}</div>`
        }
        const upperP = params.find(p => p.seriesName === '预测波动范围')
        const lowerP = params.find(p => p.seriesName === '_lower')
        if (upperP?.value != null && lowerP?.value != null) {
          html += `<div style="margin-top:6px;color:#7c91ab">预测在 ${lowerP.value} ~ ${upperP.value} 之间波动</div>`
        }
        return html
      },
    },
    legend: {
      data: legendData,
      top: 14,
      right: 12,
      textStyle: { fontSize: 11, color: '#9bb0c8' },
      itemWidth: 18,
      itemHeight: 10,
    },
    grid: { left: 58, right: 24, top: 64, bottom: 62 },
    xAxis: {
      type: 'category',
      data: d.dates,
      boundaryGap: false,
      axisLine: { lineStyle: { color: 'rgba(124, 154, 188, 0.18)' } },
      axisTick: { show: false },
      axisLabel: {
        rotate: 40,
        fontSize: 10,
        interval: labelInterval,
        color: '#7c91ab',
        formatter: (val) => val.slice(5),
      },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'value',
      name: metric,
      nameTextStyle: { color: '#7a878b', padding: [0, 0, 8, 0] },
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#7a878b' },
      splitLine: { lineStyle: { color: 'rgba(124, 154, 188, 0.08)' } },
    },
    dataZoom: [{ type: 'inside', start: 0, end: 100 }],
    series,
  }
}
