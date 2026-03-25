<template>
  <div class="health-advice" :class="level.className">
    <div class="advice-icon">
      <Icon :icon="level.icon" width="28" />
    </div>
    <div class="advice-body">
      <div class="advice-title">{{ level.title }}</div>
      <div class="advice-text">{{ level.advice }}</div>
    </div>
    <div class="advice-groups">
      <span v-for="g in level.groups" :key="g" class="group-tag">{{ g }}</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { Icon } from '@iconify/vue'

const props = defineProps({
  aqi: { type: Number, default: 0 },
  qualityLevel: { type: String, default: '' },
})

const LEVELS = [
  {
    max: 50, className: 'level-good',
    icon: 'mdi:emoticon-excited-outline',
    title: '优',
    advice: '空气质量令人满意，适宜户外活动。',
    groups: ['适合运动', '可开窗通风'],
  },
  {
    max: 100, className: 'level-moderate',
    icon: 'mdi:emoticon-neutral-outline',
    title: '良',
    advice: '空气质量可接受，部分敏感人群需注意。',
    groups: ['敏感人群减少户外活动'],
  },
  {
    max: 150, className: 'level-unhealthy1',
    icon: 'mdi:emoticon-sad-outline',
    title: '轻度污染',
    advice: '老人、儿童应减少户外活动。',
    groups: ['佩戴口罩', '关闭门窗', '避免剧烈运动'],
  },
  {
    max: 200, className: 'level-unhealthy2',
    icon: 'mdi:alert-circle-outline',
    title: '中度污染',
    advice: '建议减少外出，外出需做好防护。',
    groups: ['佩戴N95口罩', '开启净化器', '心肺疾病患者注意'],
  },
  {
    max: 300, className: 'level-very-unhealthy',
    icon: 'mdi:alert-octagon-outline',
    title: '重度污染',
    advice: '所有人群应尽量留在室内。',
    groups: ['避免外出', '佩戴防护口罩', '开启净化器', '不适请及时就医'],
  },
  {
    max: 999, className: 'level-hazardous',
    icon: 'mdi:skull-outline',
    title: '严重污染',
    advice: '空气质量极差，必须采取防护措施。',
    groups: ['禁止外出', '紧闭门窗', '建议转移', '不适立即就医'],
  },
]

const level = computed(() => {
  const aqi = props.aqi || 0
  return LEVELS.find((l) => aqi <= l.max) || LEVELS[LEVELS.length - 1]
})
</script>

<style scoped>
.health-advice {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  border-radius: 14px;
  margin: 8px 0;
  border-left: 4px solid;
  backdrop-filter: blur(8px);
  transition: transform 0.3s var(--bounce, cubic-bezier(0.34, 1.56, 0.64, 1));
}
.health-advice:hover {
  transform: translateX(4px);
}
.advice-icon { flex-shrink: 0; display: flex; align-items: center; }
.advice-body { flex: 1; }
.advice-title { font-size: 14px; font-weight: 700; margin-bottom: 4px; }
.advice-text { font-size: 12px; line-height: 1.6; color: #5a5a5a; }
.advice-groups { display: flex; flex-wrap: wrap; gap: 6px; flex-shrink: 0; }
.group-tag {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 8px;
  background: rgba(255,255,255,0.7);
  white-space: nowrap;
}

.level-good { background: #e8f5e9; border-color: #2d6a4f; }
.level-good .advice-title { color: #2d6a4f; }
.level-good .advice-icon { color: #2d6a4f; }
.level-moderate { background: #fef3e2; border-color: #d4a373; }
.level-moderate .advice-title { color: #b08350; }
.level-moderate .advice-icon { color: #d4a373; }
.level-unhealthy1 { background: #fde8e0; border-color: #e07a5f; }
.level-unhealthy1 .advice-title { color: #c0603f; }
.level-unhealthy1 .advice-icon { color: #e07a5f; }
.level-unhealthy2 { background: #fce4e4; border-color: #c1121f; }
.level-unhealthy2 .advice-title { color: #c1121f; }
.level-unhealthy2 .advice-icon { color: #c1121f; }
.level-very-unhealthy { background: #f0dde0; border-color: #780116; }
.level-very-unhealthy .advice-title { color: #780116; }
.level-very-unhealthy .advice-icon { color: #780116; }
.level-hazardous { background: #e8d5d8; border-color: #4a0010; }
.level-hazardous .advice-title { color: #4a0010; }
.level-hazardous .advice-icon { color: #4a0010; }
</style>
