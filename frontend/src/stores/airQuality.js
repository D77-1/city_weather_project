import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { airQualityApi, predictionApi, anomalyApi, riskApi } from '@/api/modules'

export const useAirQualityStore = defineStore('airQuality', () => {
  const latestData = ref([])
  const historyRecords = ref([])
  const predictionResult = ref(null)
  const anomalyResult = ref(null)
  const riskResult = ref(null)
  const anomalyList = ref([])
  const rankingList = ref([])
  const mapData = ref([])
  const loading = ref(false)
  const selectedMetric = ref('aqi')
  const selectedAlgorithm = ref('moving_average')

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

  const trendWithPrediction = computed(() => {
    if (!predictionResult.value) return { dates: [], actual: [], predicted: [], upper: [], lower: [], ma: [] }
    const h = predictionResult.value.history || []
    const p = predictionResult.value.predictions || []
    return {
      dates: [...h.map((i) => i.date), ...p.map((i) => i.date)],
      actual: [...h.map((i) => i.value), ...p.map(() => null)],
      ma: [...h.map((i) => i.ma ?? null), ...p.map(() => null)],
      predicted: [...h.map(() => null), ...p.map((i) => i.predicted)],
      upper: [...h.map(() => null), ...p.map((i) => i.upper)],
      lower: [...h.map(() => null), ...p.map((i) => i.lower)],
    }
  })

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

  async function fetchPrediction(cityId, metric = 'aqi', window = 7, forecastDays = 5, algorithm = 'moving_average', compare = true) {
    selectedMetric.value = metric
    selectedAlgorithm.value = algorithm
    predictionResult.value = await predictionApi.run({ cityId, metric, window, forecastDays, algorithm, compare })
  }

  async function fetchAnomalyDetect(cityId, metric = 'aqi', days = 90) {
    anomalyResult.value = await anomalyApi.detect({ cityId, metric, days })
  }

  async function fetchRiskAssess(cityId, forecastDays = 5) {
    riskResult.value = await riskApi.assess({ cityId, forecastDays })
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
    latestData,
    historyRecords,
    predictionResult,
    anomalyResult,
    riskResult,
    anomalyList,
    rankingList,
    mapData,
    loading,
    selectedMetric,
    selectedAlgorithm,
    chartData,
    trendWithPrediction,
    fetchLatest,
    fetchHistory,
    fetchPrediction,
    fetchAnomalyDetect,
    fetchRiskAssess,
    fetchAnomalyList,
    fetchRanking,
    fetchMapData,
  }
})
