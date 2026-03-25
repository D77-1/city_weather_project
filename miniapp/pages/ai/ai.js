const { request } = require('../../utils/util')

Page({
  data: {
    inputText: '',
    messages: [],
    loading: false,
    scrollToId: '',
    sessionId: '',
    cityContext: null,
    quickQuestions: ['今天空气质量如何？', '哪些城市空气最好？', '如何防护空气污染？']
  },

  onLoad() {
    this.setData({ sessionId: this.genId() })
  },

  onShow() {
    // 从详情页跳过来时读取城市上下文
    const app = getApp()
    if (app.globalData.aiCity) {
      const city = app.globalData.aiCity
      this.setData({
        cityContext: city,
        quickQuestions: [
          city.cityName + '今天空气怎么样？',
          city.cityName + '需要戴口罩吗？',
          city.cityName + '未来几天会好转吗？'
        ]
      })
      app.globalData.aiCity = null
    }
  },

  genId() {
    return 'xxxx-xxxx'.replace(/x/g, () => Math.floor(Math.random() * 16).toString(16))
  },

  onInput(e) {
    this.setData({ inputText: e.detail.value })
  },

  sendQuick(e) {
    this.setData({ inputText: e.currentTarget.dataset.text })
    this.sendMessage()
  },

  async sendMessage() {
    const text = this.data.inputText.trim()
    if (!text || this.data.loading) return

    const messages = this.data.messages
    messages.push({ role: 'user', content: text })
    this.setData({ messages, inputText: '', loading: true })
    this.scrollBottom()

    try {
      const context = this.data.cityContext ? {
        cityName: this.data.cityContext.cityName,
        current: this.data.cityContext.current
      } : {}

      const res = await request('/ai/advice', {
        method: 'POST',
        data: {
          message: text,
          sessionId: this.data.sessionId,
          cityId: this.data.cityContext?.cityId,
          context
        }
      })

      messages.push({
        role: 'ai',
        content: res.content,
        tokens: res.tokensUsed,
        elapsed: res.responseTimeMs
      })
    } catch (err) {
      messages.push({ role: 'ai', content: '抱歉，请求失败，请稍后重试。' })
    }

    this.setData({ messages, loading: false })
    this.scrollBottom()
  },

  scrollBottom() {
    setTimeout(() => {
      this.setData({ scrollToId: 'msg-bottom' })
    }, 100)
  }
})
