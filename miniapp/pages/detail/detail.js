const { request, aqiLevel, aqiAdvice, weatherIconClass } = require('../../utils/util')

Page({
  data: {
    cityId: null,
    cityName: '',
    latest: {},
    levelInfo: { text: '--', color: '#909399', bg: '#f5f6fa' },
    advice: '',
    pollutants: [],
    weather: {},
    forecast: [],
    realAqi: null,
    aqiForecast: [],
    history: [],
    predictions: []
  },

  onLoad(options) {
    this.setData({
      cityId: Number(options.cityId),
      cityName: options.cityName || ''
    })
    wx.setNavigationBarTitle({ title: options.cityName || '详情' })
    this.loadData()
  },

  async loadData() {
    wx.showLoading({ title: '加载中' })
    try {
      const [latestAll, history, predResult] = await Promise.all([
        request('/air-quality/latest'),
        request('/air-quality/history?city_id=' + this.data.cityId + '&days=7'),
        request('/prediction/run', {
          method: 'POST',
          data: { cityId: this.data.cityId, metric: 'aqi', window: 7, forecastDays: 7 }
        })
      ])

      const latest = latestAll.find(d => d.cityId === this.data.cityId) || {}
      const level = aqiLevel(latest.aqi || 0)

      const pollutants = latest.aqi ? [
        { name: 'PM2.5', value: latest.pm25, limit: 75 },
        { name: 'PM10', value: latest.pm10, limit: 150 },
        { name: 'SO₂', value: latest.so2, limit: 60 },
        { name: 'NO₂', value: latest.no2, limit: 80 },
        { name: 'CO', value: latest.co, limit: 4 },
        { name: 'O₃', value: latest.o3, limit: 160 }
      ].map(p => ({
        ...p,
        percent: Math.min(100, Math.round((p.value / p.limit) * 100)),
        over: p.value > p.limit
      })) : []

      const predictions = (predResult.predictions || []).map(p => ({
        ...p,
        dateShort: p.date.slice(5),
        color: aqiLevel(p.predicted).color
      }))

      // 天气数据
      const wIcon = weatherIconClass(latest.weatherCondition)
      const weather = latest.temperature != null ? {
        temperature: latest.temperature,
        humidity: latest.humidity,
        windSpeed: latest.windSpeed,
        windDirection: latest.windDirection,
        rainfall: latest.rainfall || 0,
        condition: latest.weatherCondition || '--',
        icon: wIcon.icon,
        label: wIcon.label
      } : {}

      this.setData({
        latest, levelInfo: level,
        advice: aqiAdvice(latest.aqi || 0),
        pollutants, weather, history, predictions
      })

      this.drawChart()

      // 加载真实天气预报(不阻塞)
      request('/weather/forecast?city_id=' + this.data.cityId + '&days=7').then(res => {
        const forecast = (res.forecast || []).map(f => {
          const ic = weatherIconClass(f.weatherText)
          return { ...f, icon: ic.icon, label: ic.label }
        })
        this.setData({ forecast })
      }).catch(() => {})

      // 加载真实 AQI 数据(不阻塞)
      request('/realtime-aqi?city_id=' + this.data.cityId).then(res => {
        this.setData({ realAqi: res })
      }).catch(() => {})

      // 加载真实 AQI 预报
      request('/aqi-forecast?city_id=' + this.data.cityId + '&days=5').then(res => {
        this.setData({ aqiForecast: res.forecast || [] })
      }).catch(() => {})
    } catch (e) {
      console.error(e)
    } finally {
      wx.hideLoading()
    }
  },

  goAi() {
    const app = getApp()
    app.globalData.aiCity = {
      cityId: this.data.cityId,
      cityName: this.data.cityName,
      current: this.data.latest
    }
    wx.switchTab({ url: '/pages/ai/ai' })
  },

  drawChart() {
    const data = this.data.history
    if (!data.length) return

    // 延迟确保 canvas 已渲染（与 index.js 保持一致）
    setTimeout(() => {
    const query = wx.createSelectorQuery()
    query.select('.chart-canvas').boundingClientRect(rect => {
      if (!rect || !rect.width) return
      const ctx = wx.createCanvasContext('detailChart', this)
      const W = rect.width, H = rect.height
      const pad = { top: 20, right: 15, bottom: 25, left: 35 }
      const cW = W - pad.left - pad.right
      const cH = H - pad.top - pad.bottom
      const vals = data.map(d => d.aqi)
      const mx = Math.max(...vals, 100), mn = Math.min(...vals, 0)
      const rng = mx - mn || 1

      ctx.setFillStyle('#fff')
      ctx.fillRect(0, 0, W, H)
      ctx.setStrokeStyle('#eee'); ctx.setLineWidth(0.5)
      for (let i = 0; i <= 4; i++) {
        const y = pad.top + (cH / 4) * i
        ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke()
        ctx.setFillStyle('#999'); ctx.setFontSize(9)
        ctx.fillText(Math.round(mx - (rng / 4) * i), 2, y + 3)
      }
      ctx.beginPath(); ctx.setStrokeStyle('#409EFF'); ctx.setLineWidth(2)
      data.forEach((d, i) => {
        const x = pad.left + (cW / Math.max(data.length - 1, 1)) * i
        const y = pad.top + cH - ((d.aqi - mn) / rng) * cH
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
      })
      ctx.stroke()
      data.forEach((d, i) => {
        const x = pad.left + (cW / Math.max(data.length - 1, 1)) * i
        const y = pad.top + cH - ((d.aqi - mn) / rng) * cH
        ctx.beginPath(); ctx.arc(x, y, 3, 0, 2 * Math.PI)
        ctx.setFillStyle('#409EFF'); ctx.fill()
        ctx.setFillStyle('#303133'); ctx.setFontSize(9); ctx.fillText(d.aqi, x - 6, y - 6)
        ctx.setFillStyle('#999'); ctx.setFontSize(8); ctx.fillText(d.date.slice(5), x - 10, H - 4)
      })
      ctx.draw()
    }).exec()
    }, 300)
  }
})
