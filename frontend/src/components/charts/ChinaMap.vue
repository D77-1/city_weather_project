<template>
  <div v-if="!mapReady" :style="{ height }" class="map-loading">
    <el-icon class="is-loading" :size="32"><Loading /></el-icon>
    <span>地图加载中...</span>
  </div>
  <EChartWrapper v-else :option="mapOption" :height="height" @bind-chart="onChartReady" />
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import * as echarts from 'echarts'
import EChartWrapper from './EChartWrapper.vue'

const props = defineProps({
  data: { type: Array, default: () => [] },
  height: { type: String, default: '500px' },
})

const emit = defineEmits(['cityClick'])
const mapReady = ref(false)

const AQI_PIECES = [
  { min: 0, max: 50, label: '优', color: '#00e400' },
  { min: 51, max: 100, label: '良', color: '#ffff00' },
  { min: 101, max: 150, label: '轻度', color: '#ff7e00' },
  { min: 151, max: 200, label: '中度', color: '#ff0000' },
  { min: 201, max: 300, label: '重度', color: '#99004c' },
  { min: 301, max: 500, label: '严重', color: '#7e0023' },
]

const mapOption = computed(() => ({
  backgroundColor: 'transparent',
  title: {
    text: '全国空气质量分布',
    left: 'center',
    top: 10,
    textStyle: { color: '#e0e6ed', fontSize: 16 },
  },
  tooltip: {
    trigger: 'item',
    formatter: (params) => {
      if (!params.value) return params.name
      return `<b>${params.name}</b><br/>AQI: ${params.value[2]}`
    },
  },
  visualMap: {
    type: 'piecewise',
    pieces: AQI_PIECES,
    left: 20,
    bottom: 20,
    textStyle: { color: '#ccc' },
    seriesIndex: 0,
  },
  geo: {
    map: 'china',
    roam: true,
    zoom: 1.2,
    itemStyle: { areaColor: '#1b2838', borderColor: '#3a4a5c' },
    emphasis: {
      itemStyle: { areaColor: '#2a475e' },
      label: { show: true, color: '#fff' },
    },
    label: { show: false },
  },
  series: [
    {
      name: 'AQI',
      type: 'scatter',
      coordinateSystem: 'geo',
      data: props.data,
      symbolSize: (val) => Math.max(8, Math.min(30, val[2] / 8)),
      encode: { value: 2 },
      itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.3)' },
      label: {
        show: true,
        position: 'right',
        formatter: '{b}',
        fontSize: 10,
        color: '#ccd',
      },
    },
  ],
}))

function onChartReady(chart) {
  chart.on('click', 'series', (params) => {
    if (params.data) {
      emit('cityClick', {
        cityId: params.data.cityId,
        name: params.data.name,
        aqi: params.data.value[2],
      })
    }
  })
}

onMounted(async () => {
  // 必须先注册地图，再让 EChartWrapper 渲染
  try {
    const chinaJson = await import('@/assets/china.json')
    echarts.registerMap('china', chinaJson.default || chinaJson)
  } catch {
    console.warn('china.json not found in src/assets/')
  }
  mapReady.value = true
})
</script>

<style scoped>
.map-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: #909399;
  background: #0d1b2a;
  border-radius: 8px;
}
</style>
