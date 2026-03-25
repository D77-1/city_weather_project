<template>
  <div ref="chartRef" :style="{ width: '100%', height: height }" />
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick, inject } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  option: { type: Object, required: true },
  height: { type: String, default: '400px' },
})

const emit = defineEmits(['bindChart'])

const chartRef = ref(null)
const isDark = inject('isDark', ref(false))
let chart = null
let resizeObserver = null
let resizeTimer = null

function initChart() {
  if (!chartRef.value) return
  if (chart) chart.dispose()
  chart = echarts.init(chartRef.value, isDark.value ? 'dark' : null, {
    renderer: 'canvas',
    useDirtyRect: true,
  })
  const opt = { ...props.option }
  if (isDark.value && !opt.backgroundColor) {
    opt.backgroundColor = 'transparent'
  }
  chart.setOption(opt, { lazyUpdate: true })
  emit('bindChart', chart)
}

watch(
  () => props.option,
  (newOpt) => {
    if (chart) {
      const opt = { ...newOpt }
      if (isDark.value && !opt.backgroundColor) {
        opt.backgroundColor = 'transparent'
      }
      chart.setOption(opt, { notMerge: true })
    }
  },
  { deep: true }
)

// 主题切换时重建图表
watch(isDark, () => {
  nextTick(initChart)
})

onMounted(() => {
  nextTick(() => {
    initChart()
    resizeObserver = new ResizeObserver(() => {
      clearTimeout(resizeTimer)
      resizeTimer = setTimeout(() => chart?.resize(), 150)
    })
    if (chartRef.value) resizeObserver.observe(chartRef.value)
  })
})

onBeforeUnmount(() => {
  clearTimeout(resizeTimer)
  resizeObserver?.disconnect()
  chart?.dispose()
  chart = null
})
</script>
