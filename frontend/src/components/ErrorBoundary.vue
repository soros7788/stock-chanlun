<template>
  <slot v-if="!hasError" />
  <div v-else class="error-boundary">
    <div class="eb-icon">
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
    </div>
    <h3 class="eb-title">页面渲染出错</h3>
    <p class="eb-msg">{{ errorMessage }}</p>
    <div class="eb-actions">
      <button class="eb-btn eb-btn-primary" @click="reload">
        刷新页面
      </button>
      <button v-if="showDetails" class="eb-btn" @click="showDetails = false">
        收起详情
      </button>
      <button v-else class="eb-btn" @click="showDetails = true">
        查看详情
      </button>
    </div>
    <pre v-if="showDetails && errorInfo" class="eb-stack">{{ errorInfo }}</pre>
  </div>
</template>

<script setup lang="ts">
import { ref, onErrorCaptured } from 'vue'

const hasError = ref(false)
const errorMessage = ref('')
const errorInfo = ref('')
const showDetails = ref(false)

onErrorCaptured((err: unknown, instance, info: string) => {
  hasError.value = true
  errorMessage.value = err instanceof Error ? err.message : String(err)
  errorInfo.value = `${errorMessage.value}\n\n组件信息: ${info}\n\n堆栈:\n${
    err instanceof Error && err.stack
      ? err.stack.split('\n').slice(0, 6).join('\n')
      : '（无可用堆栈）'
  }`
  return false // 阻止错误继续传播
})

function reload() {
  window.location.reload()
}
</script>

<style scoped>
.error-boundary {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 32px 24px;
  text-align: center;
  background: var(--bg-primary);
  color: var(--text-primary);
  gap: 12px;
}
.eb-icon {
  color: var(--accent-amber);
  margin-bottom: 4px;
}
.eb-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
}
.eb-msg {
  font-size: 0.875rem;
  color: var(--text-secondary);
  max-width: 480px;
  margin: 0;
}
.eb-actions {
  display: flex;
  gap: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
  justify-content: center;
}
.eb-btn {
  padding: 8px 20px;
  border-radius: 8px;
  border: 1px solid var(--border-strong);
  background: var(--bg-card);
  color: var(--text-secondary);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.15s;
}
.eb-btn:hover {
  border-color: var(--accent-blue);
  color: var(--accent-blue);
}
.eb-btn-primary {
  background: linear-gradient(135deg, rgba(56,189,248,0.2), rgba(52,211,153,0.12));
  border-color: rgba(56,189,248,0.4);
  color: var(--accent-cyan);
  font-weight: 600;
}
.eb-btn-primary:hover {
  background: linear-gradient(135deg, rgba(56,189,248,0.3), rgba(52,211,153,0.2));
  border-color: var(--accent-cyan);
  color: var(--accent-cyan);
}
.eb-stack {
  margin-top: 12px;
  padding: 16px;
  background: var(--bg-elevated);
  border: 1px solid var(--border);
  border-radius: 10px;
  text-align: left;
  font-size: 0.72rem;
  color: var(--text-muted);
  max-width: 640px;
  width: 100%;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
