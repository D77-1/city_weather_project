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

/** AQI 转等级/颜色 — 冷色调配色 */
function aqiLevel(aqi) {
  if (aqi <= 50) return { text: '优', color: '#059669', bg: 'linear-gradient(135deg, #ecfdf5, #d1fae5)' }
  if (aqi <= 100) return { text: '良', color: '#d97706', bg: 'linear-gradient(135deg, #fffbeb, #fef3c7)' }
  if (aqi <= 150) return { text: '轻度污染', color: '#ea580c', bg: 'linear-gradient(135deg, #fff7ed, #fed7aa)' }
  if (aqi <= 200) return { text: '中度污染', color: '#dc2626', bg: 'linear-gradient(135deg, #fef2f2, #fecaca)' }
  if (aqi <= 300) return { text: '重度污染', color: '#9f1239', bg: 'linear-gradient(135deg, #fff1f2, #fda4af)' }
  return { text: '严重污染', color: '#7f1d1d', bg: 'linear-gradient(135deg, #fef2f2, #f87171)' }
}

/** 天气条件 → SVG 图标路径 + 文字标签（AGENTS.md: 禁止 emoji 作功能图标） */
function weatherIconClass(condition) {
  const map = {
    '晴': { icon: '/images/qing.svg', label: '晴' },
    '大部晴': { icon: '/images/qing.svg', label: '晴' },
    '多云': { icon: '/images/duoyun.svg', label: '多云' },
    '阴': { icon: '/images/yun.svg', label: '阴' },
    '雾': { icon: '/images/wuqi.svg', label: '雾' },
    '霜雾': { icon: '/images/wuqi.svg', label: '雾' },
    '小雨': { icon: '/images/xiaoyu.svg', label: '小雨' },
    '小毛毛雨': { icon: '/images/xiaoyu.svg', label: '小雨' },
    '毛毛雨': { icon: '/images/xiaoyu.svg', label: '小雨' },
    '中雨': { icon: '/images/xiaoyu.svg', label: '中雨' },
    '大雨': { icon: '/images/dayu.svg', label: '大雨' },
    '暴雨': { icon: '/images/dayu.svg', label: '暴雨' },
    '阵雨': { icon: '/images/xiaoyu.svg', label: '阵雨' },
    '小雪': { icon: '/images/daxue.svg', label: '小雪' },
    '中雪': { icon: '/images/daxue.svg', label: '中雪' },
    '大雪': { icon: '/images/daxue.svg', label: '大雪' },
    '雨夹雪': { icon: '/images/daxue.svg', label: '雨夹雪' },
    '雷暴': { icon: '/images/dayu.svg', label: '雷暴' },
  }
  return map[condition] || { icon: '/images/duoyun.svg', label: condition || '--' }
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

module.exports = { request, aqiLevel, aqiAdvice, weatherIconClass }
