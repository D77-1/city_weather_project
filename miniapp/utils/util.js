/**
 * 封装 wx.request
 * 自动拼接 baseUrl，自动解包 { code, data }
 */
const app = getApp()

function request(url, options = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: app.globalData.baseUrl + '/api' + url,
      method: options.method || 'GET',
      data: options.data || {},
      header: { 'Content-Type': 'application/json' },
      success(res) {
        if (res.statusCode === 200 && res.data.code === 200) {
          resolve(res.data.data)
        } else {
          wx.showToast({ title: res.data?.message || '请求失败', icon: 'none' })
          reject(new Error(res.data?.message || '请求失败'))
        }
      },
      fail(err) {
        wx.showToast({ title: '网络异常', icon: 'none' })
        reject(err)
      }
    })
  })
}

/** AQI 转等级/颜色 */
function aqiLevel(aqi) {
  if (aqi <= 50) return { text: '优', color: '#00e400', bg: '#f0f9eb' }
  if (aqi <= 100) return { text: '良', color: '#e6a23c', bg: '#fdf6ec' }
  if (aqi <= 150) return { text: '轻度污染', color: '#ff7e00', bg: '#fef0e0' }
  if (aqi <= 200) return { text: '中度污染', color: '#f56c6c', bg: '#fef0f0' }
  if (aqi <= 300) return { text: '重度污染', color: '#99004c', bg: '#f5e0f0' }
  return { text: '严重污染', color: '#7e0023', bg: '#f0e0e5' }
}

/** AQI 转健康建议 */
function aqiAdvice(aqi) {
  if (aqi <= 50) return '空气优质，适宜户外活动。'
  if (aqi <= 100) return '空气良好，敏感人群适当减少户外运动。'
  if (aqi <= 150) return '轻度污染，老人儿童减少外出，建议佩戴口罩。'
  if (aqi <= 200) return '中度污染，避免户外运动，必须佩戴口罩，开启空气净化器。'
  if (aqi <= 300) return '重度污染！所有人群避免外出，紧闭门窗。'
  return '严重污染！禁止户外活动，有条件请暂离该区域。'
}

module.exports = { request, aqiLevel, aqiAdvice }
