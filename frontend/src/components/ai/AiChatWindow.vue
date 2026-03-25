<template>
  <!-- 悬浮触发按钮 -->
  <div class="ai-fab" @click="visible = !visible" title="AI 助手">
    <Icon icon="mdi:chat-processing-outline" width="24" />
  </div>

  <!-- 聊天窗口 -->
  <Teleport to="body">
    <div
      v-show="visible"
      ref="windowRef"
      class="ai-window"
      :style="{ left: pos.x + 'px', top: pos.y + 'px' }"
    >
      <!-- 标题栏（可拖拽） -->
      <div class="ai-header" @mousedown="startDrag">
        <span>AI 助手</span>
        <Icon icon="mdi:close" class="close-btn" @click="visible = false" width="18" />
      </div>

      <!-- 消息区域 -->
      <div ref="msgListRef" class="ai-messages">
        <div v-if="messages.length === 0" class="welcome-msg">
          您好，我是空气质量智能助手。可以为您提供空气质量分析与建议，请尝试以下问题：
          <div class="quick-questions">
            <el-tag
              v-for="q in quickQuestions"
              :key="q"
              class="quick-tag"
              @click="sendQuickQuestion(q)"
            >{{ q }}</el-tag>
          </div>
        </div>
        <div
          v-for="(msg, i) in messages"
          :key="i"
          :class="['msg-bubble', msg.role === 'user' ? 'msg-user' : 'msg-ai']"
        >
          <div class="msg-content" v-html="formatContent(msg.content)"></div>
          <div v-if="msg.tokens" class="msg-meta">{{ msg.tokens }} tokens / {{ msg.elapsed }}ms</div>
        </div>
        <div v-if="loading" class="msg-bubble msg-ai">
          <div class="typing-indicator"><span /><span /><span /></div>
        </div>
      </div>

      <!-- 输入区域 -->
      <div class="ai-input-area">
        <el-input
          v-model="inputText"
          placeholder="请输入您的问题..."
          :disabled="loading"
          @keyup.enter="sendMessage"
        />
        <el-button type="primary" :loading="loading" @click="sendMessage">
          发送
        </el-button>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { Icon } from '@iconify/vue'
import { aiApi } from '@/api/modules'

const props = defineProps({
  cityId: { type: Number, default: null },
  cityName: { type: String, default: '' },
  context: { type: Object, default: () => ({}) },
})

const visible = ref(false)
const inputText = ref('')
const loading = ref(false)
const messages = ref([])
const sessionId = ref(crypto.randomUUID())
const windowRef = ref(null)
const msgListRef = ref(null)

const pos = ref({ x: window.innerWidth - 420, y: 100 })

const quickQuestions = [
  '今天能出门吗？',
  '明天会好点吗？',
  '要不要戴口罩？',
]

// ===== 拖拽逻辑 =====
let dragging = false
let dragOffset = { x: 0, y: 0 }

function startDrag(e) {
  dragging = true
  dragOffset.x = e.clientX - pos.value.x
  dragOffset.y = e.clientY - pos.value.y
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(e) {
  if (!dragging) return
  pos.value.x = e.clientX - dragOffset.x
  pos.value.y = e.clientY - dragOffset.y
}

function stopDrag() {
  dragging = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// ===== 消息发送 =====
async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || loading.value) return

  messages.value.push({ role: 'user', content: text })
  inputText.value = ''
  loading.value = true
  scrollToBottom()

  try {
    const res = await aiApi.getAdvice({
      message: text,
      sessionId: sessionId.value,
      cityId: props.cityId,
      context: props.context,
    })
    messages.value.push({
      role: 'ai',
      content: res.content,
      tokens: res.tokensUsed,
      elapsed: res.responseTimeMs,
    })
  } catch (err) {
    messages.value.push({ role: 'ai', content: `出错了: ${err.message}` })
  } finally {
    loading.value = false
    scrollToBottom()
  }
}

function sendQuickQuestion(q) {
  inputText.value = q
  sendMessage()
}

function scrollToBottom() {
  nextTick(() => {
    if (msgListRef.value) {
      msgListRef.value.scrollTop = msgListRef.value.scrollHeight
    }
  })
}

function formatContent(text) {
  return text.replace(/\n/g, '<br/>')
}
</script>

<style scoped>
/* 悬浮按钮 */
.ai-fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: linear-gradient(135deg, #e07a5f, #0d9488);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 16px rgba(224, 122, 95, 0.35);
  z-index: 2000;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}
.ai-fab:hover { transform: scale(1.12) rotate(-8deg); }

/* 聊天窗口 */
.ai-window {
  position: fixed;
  width: 380px;
  height: 520px;
  background: var(--bg-card, rgba(255,255,255,0.95));
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  z-index: 2001;
  overflow: hidden;
  backdrop-filter: blur(12px);
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(135deg, #0d9488, #14b8a6);
  color: #fff;
  font-weight: 700;
  cursor: move;
  user-select: none;
}
.close-btn { cursor: pointer; }

/* 消息区 */
.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
}
.welcome-msg {
  font-size: 13px;
  color: var(--text-secondary, #5a5a5a);
  line-height: 1.8;
}
.quick-questions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 8px;
}
.quick-tag { cursor: pointer; }

.msg-bubble {
  margin: 8px 0;
  max-width: 85%;
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 13px;
  line-height: 1.6;
  word-break: break-word;
}
.msg-user {
  background: var(--primary, #0d9488);
  color: #fff;
  margin-left: auto;
  border-bottom-right-radius: 2px;
}
.msg-ai {
  background: var(--bg-page, #eae6e1);
  color: var(--text-primary, #2c2c2c);
  border-bottom-left-radius: 2px;
}
.msg-meta {
  font-size: 10px;
  color: var(--text-muted, #8a8a8a);
  margin-top: 4px;
}

/* 打字动画 - 弹性 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0;
}
.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-muted, #8a8a8a);
  animation: bounce 1.4s infinite both;
}
.typing-indicator span:nth-child(2) { animation-delay: 0.15s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.3s; }
@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.6); opacity: 0.3; }
  40% { transform: scale(1.2); opacity: 1; }
}

/* 输入区 */
.ai-input-area {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid var(--border-color, #d5cfc7);
}
</style>
