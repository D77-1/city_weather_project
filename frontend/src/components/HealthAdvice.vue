<template>
  <div class="health-advice" :class="level.className" v-if="!dismissed">
    <div class="advice-icon-shell">
      <div class="advice-icon">
        <Icon :icon="level.icon" width="26" />
      </div>
    </div>

    <div class="advice-body">
      <div class="advice-title-row">
        <div class="advice-title-group">
          <span class="advice-kicker">HEALTH NOTE</span>
          <div class="advice-title">{{ level.title }}</div>
        </div>
        <span v-if="riskLevel" class="risk-pill">风险：{{ riskText }}</span>
      </div>

      <div class="advice-text">{{ level.advice }}</div>
      <div v-if="futureSummary" class="future-summary">未来提示：{{ futureSummary }}</div>

      <div class="advice-groups">
        <span v-for="g in mergedGroups" :key="g" class="group-tag">{{ g }}</span>
      </div>
    </div>

    <button class="advice-close" @click="dismissed = true" title="关闭">
      <Icon icon="mdi:close" width="16" />
    </button>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps({
  aqi: { type: Number, default: 0 },
  qualityLevel: { type: String, default: '' },
  riskLevel: { type: String, default: '' },
  futureSummary: { type: String, default: '' },
  mainPollutants: { type: Array, default: () => [] },
})

const dismissed = ref(false)
watch(() => [props.aqi, props.riskLevel, props.futureSummary], () => { dismissed.value = false })

const LEVELS = [
  { max: 50, className: 'level-good', icon: 'mdi:leaf', title: '优', advice: '空气质量令人满意，适宜户外活动。', groups: ['适合运动', '可开窗通风'] },
  { max: 100, className: 'level-moderate', icon: 'mdi:weather-partly-cloudy', title: '良', advice: '空气质量可接受，部分敏感人群需注意。', groups: ['敏感人群减少户外活动'] },
  { max: 150, className: 'level-unhealthy1', icon: 'mdi:alert-outline', title: '轻度污染', advice: '老人、儿童应减少户外活动。', groups: ['佩戴口罩', '关闭门窗', '避免剧烈运动'] },
  { max: 200, className: 'level-unhealthy2', icon: 'mdi:alert-circle-outline', title: '中度污染', advice: '建议减少外出，外出需做好防护。', groups: ['佩戴N95口罩', '开启净化器', '心肺疾病患者注意'] },
  { max: 300, className: 'level-very-unhealthy', icon: 'mdi:shield-alert-outline', title: '重度污染', advice: '所有人群应尽量留在室内。', groups: ['避免外出', '佩戴防护口罩', '开启净化器', '不适请及时就医'] },
  { max: 999, className: 'level-hazardous', icon: 'mdi:biohazard', title: '严重污染', advice: '空气质量极差，必须采取防护措施。', groups: ['禁止外出', '紧闭门窗', '建议转移', '不适立即就医'] },
]

const level = computed(() => {
  const aqi = props.aqi || 0
  return LEVELS.find((l) => aqi <= l.max) || LEVELS[LEVELS.length - 1]
})

const riskText = computed(() => ({ low: '低', medium: '中', high: '高', severe: '极高' }[props.riskLevel] || props.riskLevel || '未评估'))
const mergedGroups = computed(() => {
  const pollutantTags = props.mainPollutants.map((p) => `${String(p).toUpperCase()}需关注`)
  return [...new Set([...(level.value.groups || []), ...pollutantTags].slice(0, 6))]
})
</script>

<style scoped>
.health-advice {
  position: relative;
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 20px;
  margin: 8px 0;
  border: 1px solid rgba(26, 37, 41, 0.08);
  box-shadow: var(--aq-shadow-soft);
}

.advice-icon-shell {
  display: flex;
  align-items: flex-start;
}

.advice-icon {
  width: 48px;
  height: 48px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.58);
}

.advice-body {
  display: grid;
  gap: 10px;
}

.advice-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.advice-kicker {
  font-family: var(--aq-mono);
  font-size: 10px;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(26, 37, 41, 0.56);
}

.advice-title {
  margin-top: 6px;
  font-family: var(--aq-display);
  font-size: 28px;
  font-weight: 700;
  line-height: 1.08;
}

.advice-text,
.future-summary {
  font-size: 13px;
  line-height: 1.75;
  color: var(--aq-ink-soft);
}

.risk-pill {
  font-size: 11px;
  background: rgba(255,255,255,0.72);
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(26, 37, 41, 0.08);
  white-space: nowrap;
}

.advice-groups {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.group-tag {
  font-size: 11px;
  padding: 5px 10px;
  border-radius: 999px;
  background: rgba(255,255,255,0.68);
  border: 1px solid rgba(26, 37, 41, 0.06);
  white-space: nowrap;
  color: var(--aq-ink);
}

.advice-close {
  position: absolute;
  top: 10px;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
  color: inherit;
  opacity: 0.5;
  padding: 4px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.advice-close:hover {
  opacity: 1;
  background: rgba(0,0,0,0.05);
}

.level-good {
  background: linear-gradient(180deg, rgba(226, 244, 233, 0.92), rgba(241, 249, 244, 0.82));
}
.level-good .advice-title, .level-good .advice-icon { color: #2d6a4f; }

.level-moderate {
  background: linear-gradient(180deg, rgba(249, 239, 220, 0.92), rgba(252, 246, 234, 0.82));
}
.level-moderate .advice-title, .level-moderate .advice-icon { color: #a8743f; }

.level-unhealthy1 {
  background: linear-gradient(180deg, rgba(251, 233, 225, 0.92), rgba(252, 242, 237, 0.82));
}
.level-unhealthy1 .advice-title, .level-unhealthy1 .advice-icon { color: #c86b4b; }

.level-unhealthy2 {
  background: linear-gradient(180deg, rgba(247, 226, 224, 0.92), rgba(251, 238, 236, 0.82));
}
.level-unhealthy2 .advice-title, .level-unhealthy2 .advice-icon { color: #b42318; }

.level-very-unhealthy {
  background: linear-gradient(180deg, rgba(241, 223, 228, 0.92), rgba(246, 237, 239, 0.82));
}
.level-very-unhealthy .advice-title, .level-very-unhealthy .advice-icon { color: #780116; }

.level-hazardous {
  background: linear-gradient(180deg, rgba(233, 216, 220, 0.94), rgba(240, 231, 234, 0.84));
}
.level-hazardous .advice-title, .level-hazardous .advice-icon { color: #4a0010; }

@media (max-width: 900px) {
  .health-advice {
    grid-template-columns: 1fr;
  }

  .advice-title-row {
    flex-direction: column;
  }
}
</style>
