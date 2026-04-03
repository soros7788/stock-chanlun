<template>
  <div class="card signal-card">
    <div class="card-header">
      <span class="card-title">缠论信号</span>
    </div>

    <div v-if="signals.length === 0" class="empty-signals">
      <span>暂无买卖点</span>
    </div>

    <div v-else class="signal-list">
      <div
        v-for="(sig, idx) in visibleSignals"
        :key="`${sig.datetime}-${sig.type}-${idx}`"
        class="signal-item"
        :class="sigClass(sig.type)"
      >
        <div class="signal-header">
          <span class="signal-type">{{ sig.type }}</span>
          <span class="signal-level mono">{{ sig.level }}</span>
        </div>
        <div class="signal-detail">
          <span class="signal-price mono">{{ sig.price.toFixed(2) }}</span>
          <span class="signal-date">{{ formatDate(sig.datetime) }}</span>
        </div>
        <div class="signal-meta">
          <div class="confidence-row">
            <span class="conf-label">置信</span>
            <div class="confidence-bar">
              <div
                class="confidence-fill"
                :style="{
                  width: (sig.confidence * 100) + '%',
                  background: confColor(sig.confidence)
                }"
              />
            </div>
            <span class="conf-value mono">{{ (sig.confidence * 100).toFixed(0) }}%</span>
          </div>
          <div class="signal-desc">{{ sig.description }}</div>
        </div>
      </div>

      <button
        v-if="signals.length > visibleCount"
        class="show-more"
        @click="visibleCount = signals.length"
      >
        查看全部 ({{ signals.length }})
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import type { Signal } from '../../api/stock'

const props = defineProps<{ signals: Signal[] }>()

const visibleCount = ref(5)

/** 按日期降序，最新在前 */
const sortedByDateDesc = computed(() =>
  [...props.signals].sort((a, b) => {
    const ta = new Date(a.datetime).getTime()
    const tb = new Date(b.datetime).getTime()
    return tb - ta
  })
)

const visibleSignals = computed(() =>
  sortedByDateDesc.value.slice(0, visibleCount.value)
)

function sigClass(type: string) {
  if (type.includes('买')) return 'sig-buy'
  if (type.includes('卖')) return 'sig-sell'
  return ''
}

function confColor(c: number) {
  if (c >= 0.75) return 'var(--accent-green)'
  if (c >= 0.5) return 'var(--accent-amber)'
  return 'var(--accent-red)'
}

function formatDate(d: string) {
  return d.slice(0, 10)
}
</script>

<style scoped>
.signal-card { padding: 14px; }

.empty-signals {
  text-align: center;
  padding: 20px;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.signal-list { display: flex; flex-direction: column; gap: 8px; }

.signal-item {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  transition: all 0.15s;
}
.sig-buy { border-left: 3px solid var(--accent-green); }
.sig-sell { border-left: 3px solid var(--accent-red); }

.signal-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.signal-type { font-size: 0.85rem; font-weight: 600; }
.sig-buy .signal-type { color: var(--accent-green); }
.sig-sell .signal-type { color: var(--accent-red); }
.signal-level { font-size: 0.7rem; color: var(--text-muted); }

.signal-detail { display: flex; justify-content: space-between; margin-bottom: 6px; }
.signal-price { font-size: 1rem; font-weight: 700; }
.signal-date { font-size: 0.75rem; color: var(--text-muted); }

.signal-meta {}
.confidence-row { display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }
.conf-label { font-size: 0.7rem; color: var(--text-muted); }
.conf-value { font-size: 0.7rem; width: 28px; text-align: right; }
.signal-desc { font-size: 0.7rem; color: var(--text-secondary); line-height: 1.4; }

.show-more {
  background: none;
  border: none;
  color: var(--accent-blue);
  font-size: 0.8rem;
  cursor: pointer;
  text-align: center;
  padding: 6px;
  width: 100%;
  border-radius: 6px;
  transition: background 0.15s;
}
.show-more:hover { background: var(--bg-hover); }
</style>