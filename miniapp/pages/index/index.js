const { request, aqiLevel, aqiAdvice, weatherIconClass } = require('../../utils/util')

Page({
  data: {
    latestData: [],
    cityNames: [],
    cityIndex: 0,
    currentCity: {},
    levelInfo: { text: '--', color: '#94a3b8', bg: 'linear-gradient(135deg, #f0f4f8, #e2e8f0)' },
    advice: '',
    weatherIcon: { cls: 'cloudy', label: '云' },
    pollutants: [],
    ranking: [],
    history: []
  },

  onLoad() {
    this.loadData()
  },

  onPullDownRefresh() {
    this.loadData().then(() => wx.stopPullDownRefresh())
  },

  async loadData() {
    wx.showLoading({ title: '加载中' })
    try {
      const [latest, ranking] = await Promise.all([
        request('/air-quality/latest'),
        request('/air-quality/ranking?order=desc&limit=15')
      ])
      const names = latest.map(d => d.cityName)
      // 给排名加颜色
      ranking.forEach(r => r.color = aqiLevel(r.aqi).color)

      this.setData({ latestData: latest, cityNames: names, ranking })
      this.selectCity(this.data.cityIndex)
    } catch (e) {
      console.error(e)
    } finally {
      wx.hideLoading()
    }
  },

  selectCity(index) {
    const city = this.data.latestData[index] || {}
    const level = aqiLevel(city.aqi || 0)
    const pollutants = city.aqi ? [
      { name: 'PM2.5', value: city.pm25, unit: 'μg/m³' },
      { name: 'PM10', value: city.pm10, unit: 'μg/m³' },
      { name: 'SO₂', value: city.so2, unit: 'μg/m³' },
      { name: 'NO₂', value: city.no2, unit: 'μg/m³' },
      { name: 'CO', value: city.co, unit: 'mg/m³' },
      { name: 'O₃', value: city.o3, unit: 'μg/m³' }
    ] : []

    this.setData({
      currentCity: city,
      cityIndex: index,
      levelInfo: level,
      advice: aqiAdvice(city.aqi || 0),
      weatherIcon: weatherIconClass(city.weatherCondition),
      pollutants
    })

    if (city.cityId) this.loadHistory(city.cityId)
  },

  async loadHistory(cityId) {
    const history = await request('/air-quality/history?city_id=' + cityId + '&days=7')
    this.setData({ history })
    this.drawChart()
  },

  onCityChange(e) {
    this.selectCity(Number(e.detail.value))
  },

  onRankTap(e) {
    const item = e.currentTarget.dataset.item
    wx.navigateTo({ url: '/pages/detail/detail?cityId=' + item.cityId + '&cityName=' + item.cityName })
  },

  goDetail() {
    const c = this.data.currentCity
    if (c.cityId) {
      wx.navigateTo({ url: '/pages/detail/detail?cityId=' + c.cityId + '&cityName=' + c.cityName })
    }
  },

  drawChart() {
    const data = this.data.history
    if (!data.length) return

    // 延迟确保 canvas 已渲染
    setTimeout(() => {
      const query = wx.createSelectorQuery()
      query.select('.trend-canvas').boundingClientRect(rect => {
        if (!rect || !rect.width) return
        const ctx = wx.createCanvasContext('trendChart', this)
      const W = rect.width, H = rect.height
      const pad = { top: 20, right: 15, bottom: 25, left: 35 }
      const cW = W - pad.left - pad.right
      const cH = H - pad.top - pad.bottom
      const vals = data.map(d => d.aqi)
      const mx = Math.max(...vals, 100), mn = Math.min(...vals, 0)
      const rng = mx - mn || 1

      ctx.setFillStyle('#f8fafc')
      ctx.fillRect(0, 0, W, H)

      // 网格
      ctx.setStrokeStyle('#e2e8f0')
      ctx.setLineWidth(0.5)
      for (let i = 0; i <= 4; i++) {
        const y = pad.top + (cH / 4) * i
        ctx.beginPath(); ctx.moveTo(pad.left, y); ctx.lineTo(W - pad.right, y); ctx.stroke()
        ctx.setFillStyle('#999'); ctx.setFontSize(9)
        ctx.fillText(Math.round(mx - (rng / 4) * i), 2, y + 3)
      }

      // 折线
      ctx.beginPath(); ctx.setStrokeStyle('#0d9488'); ctx.setLineWidth(2)
      data.forEach((d, i) => {
        const x = pad.left + (cW / Math.max(data.length - 1, 1)) * i
        const y = pad.top + cH - ((d.aqi - mn) / rng) * cH
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y)
      })
      ctx.stroke()

      // 点 + 标签
      data.forEach((d, i) => {
        const x = pad.left + (cW / Math.max(data.length - 1, 1)) * i
        const y = pad.top + cH - ((d.aqi - mn) / rng) * cH
        ctx.beginPath(); ctx.arc(x, y, 3, 0, 2 * Math.PI)
        ctx.setFillStyle('#0d9488'); ctx.fill()
        ctx.setFillStyle('#1e293b'); ctx.setFontSize(9); ctx.fillText(d.aqi, x - 6, y - 6)
        ctx.setFillStyle('#94a3b8'); ctx.setFontSize(8); ctx.fillText(d.date.slice(5), x - 10, H - 4)
      })

      ctx.draw()
    }).exec()
    }, 300)
  }
})
