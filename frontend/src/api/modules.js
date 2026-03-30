import request from '@/api'

// 城市相关
export const cityApi = {
  getList: (params) => request.get('/cities', { params }),
  getDetail: (cityId) => request.get(`/cities/${cityId}`),
  getStations: (cityId) => request.get(`/cities/${cityId}/stations`),
  getProvinces: () => request.get('/provinces'),
}

// 空气质量
export const airQualityApi = {
  getLatest: () => request.get('/air-quality/latest'),
  getHistory: (params) => request.get('/air-quality/history', { params }),
  getRanking: (params) => request.get('/air-quality/ranking', { params }),
  getMapData: () => request.get('/air-quality/map-data'),
  getStationRecords: (stationId, params) => request.get(`/air-quality/station/${stationId}`, { params }),
}

// 预测
export const predictionApi = {
  run: (data) => request.post('/prediction/run', data),
  getHistory: (params) => request.get('/prediction/history', { params }),
}

// 异常检测
export const anomalyApi = {
  detect: (data) => request.post('/anomaly/detect', data),
  getList: (params) => request.get('/anomaly/list', { params }),
  updateStatus: (eventId, data) => request.put(`/anomaly/${eventId}/status`, data),
}

// 综合风险
export const riskApi = {
  assess: (data) => request.post('/risk/assess', data),
}

// AI
export const aiApi = {
  getAdvice: (data) => request.post('/ai/advice', data),
  getHistory: (params) => request.get('/ai/history', { params }),
}

// 天气 (Open-Meteo 真实数据)
export const weatherApi = {
  getRealtime: (cityId) => request.get('/weather/realtime', { params: { city_id: cityId } }),
  getForecast: (cityId, days = 7) => request.get('/weather/forecast', { params: { city_id: cityId, days } }),
  getHistory: (cityId, days = 30) => request.get('/weather/history', { params: { city_id: cityId, days } }),
}

// 真实 AQI 数据 (Open-Meteo CAMS)
export const realAqiApi = {
  getRealtime: (cityId) => request.get('/realtime-aqi', { params: { city_id: cityId } }),
  getRealtimeAll: (cityId) => request.get('/realtime-all', { params: { city_id: cityId } }),
  getForecast: (cityId, days = 5) => request.get('/aqi-forecast', { params: { city_id: cityId, days } }),
  getHistory: (cityId, days = 30) => request.get('/aqi-history-real', { params: { city_id: cityId, days } }),
}

// 城市对比
export const compareApi = {
  getCities: (cityIds) => request.get('/compare', { params: { city_ids: cityIds.join(',') } }),
}
