import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { airQualityApi, predictionApi, anomalyApi } from '@/api/modules'

export const useAirQualityStore = defineStore('airQuality', () => {
  // ========== State ==========
  const latestData = ref([])               // 各城市最新 AQI 列表
  const historyRecords = ref([])           // 历史趋势数据
  const predictionResult = ref(null)       // 预测结果 { history, predictions, mape }
  const anomalyResult = ref(null)          // 异常检测结果
  const anomalyList = ref([])              // 异常事件列表
  const rankingList = ref([])              // 排名
  const mapData = ref([])                  // 地图散点数据
  const loading = ref(false)

  // ========== Getters ==========
  const chartData = computed(() => ({
    dates: historyRecords.value.map((r) => r.date),
    aqi: historyRecords.value.map((r) => r.aqi),
    pm25: historyRecords.value.map((r) => r.pm25),
    pm10: historyRecords.value.map((r) => r.pm10),
    so2: historyRecords.value.map((r) => r.so2),
    no2: historyRecords.value.map((r) => r.no2),
    co: historyRecords.value.map((r) => r.co),
    o3: historyRecords.value.map((r) => r.o3),
  }))

  // 历史 + 预测合并数据（用于趋势折线图）
  const trendWithPrediction = computed(() => {
    if (!predictionResult.value) return { dates: [], actual: [], predicted: [], upper: [], lower: [] }
    const h = predictionResult.value.history || []
    const p = predictionResult.value.predictions || []
    return {
      dates: [...h.map((i) => i.date), ...p.map((i) => i.date)],
      actual: [...h.map((i) => i.value), ...p.map(() => null)],
      ma: [...h.map((i) => i.ma), ...p.map(() => null)],
      predicted: [...h.map(() => null), ...p.map((i) => i.predicted)],
      upper: [...h.map(() => null), ...p.map((i) => i.upper)],
      lower: [...h.map(() => null), ...p.map((i) => i.lower)],
    }
  })

  // ========== Actions ==========
  async function fetchLatest() {
    latestData.value = await airQualityApi.getLatest()
  }

  async function fetchHistory(cityId, days = 30) {
    loading.value = true
    try {
      historyRecords.value = await airQualityApi.getHistory({ city_id: cityId, days })
    } finally {
      loading.value = false
    }
  }

  async function fetchPrediction(cityId, metric = 'aqi', window = 7, forecastDays = 7) {
    predictionResult.value = await predictionApi.run({ cityId, metric, window, forecastDays })
  }

  async function fetchAnomalyDetect(cityId, metric = 'aqi', days = 90) {
    anomalyResult.value = await anomalyApi.detect({ cityId, metric, days })
  }

  async function fetchAnomalyList(params = {}) {
    anomalyList.value = await anomalyApi.getList(params)
  }

  async function fetchRanking(order = 'desc', limit = 10) {
    rankingList.value = await airQualityApi.getRanking({ order, limit })
  }

  async function fetchMapData() {
    mapData.value = await airQualityApi.getMapData()
  }

  return {
    latestData, historyRecords, predictionResult, anomalyResult,
    anomalyList, rankingList, mapData, loading,
    chartData, trendWithPrediction,
    fetchLatest, fetchHistory, fetchPrediction, fetchAnomalyDetect,
    fetchAnomalyList, fetchRanking, fetchMapData,
  }
})
