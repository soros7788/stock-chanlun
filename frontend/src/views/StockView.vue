<template>
  <div class="layout">
    <!-- Nav -->
    <nav class="nav">
      <div class="nav-inner">
        <router-link to="/" class="nav-brand">ChanStock</router-link>
        <div class="nav-links">
          <router-link to="/" class="nav-link">首页</router-link>
          <router-link to="/watchlist" class="nav-link">自选股</router-link>
        </div>
        <div class="nav-actions">
          <!-- AI 模型切换 -->
          <div class="ai-model-switch">
            <button
              class="model-btn"
              :class="{ active: store.aiModel === 'deepseek' }"
              @click="switchModel('deepseek')"
              title="DeepSeek"
            >DS</button>
            <button
              class="model-btn"
              :class="{ active: store.aiModel === 'gemini' }"
              @click="switchModel('gemini')"
              title="Gemini"
            >GM</button>
          </div>
          <button class="btn btn-ghost" @click="loadData" :disabled="loadingAny">
            {{ loadingAny ? '加载中...' : '刷新' }}
          </button>
          <button class="btn btn-ghost" @click="toggleWatch" :class="{ 'btn-danger': isWatching }">
            {{ isWatching ? '取消自选' : '+自选' }}
          </button>
        </div>
      </div>
    </nav>

    <div v-if="loadingAny" class="loading-state">
      <div class="spinner" />
      <span>分析中...</span>
    </div>

    <div v-else-if="error" class="error-page">
      <p>{{ error }}</p>
      <button class="btn btn-primary" @click="loadData">重试</button>
    </div>

    <div v-else class="main-grid">
      <!-- Left: Stock info -->
      <aside class="sidebar">
        <div class="card stock-info-card">
          <div class="stock-header">
            <div>
              <div class="stock-code-label mono">{{ stockCode }}</div>
              <div class="stock-name-label">{{ quote?.name || stockCode }}</div>
            </div>
            <div class="stock-price-block">
              <div class="price-current mono">
                {{ quote?.price?.toFixed(2) || '—' }}
              </div>
              <div
                class="price-change mono"
                :class="changeClass"
              >
                {{ changeText }}
              </div>
            </div>
          </div>

          <div class="price-stats">
            <div class="stat-row">
              <span class="stat-label">开盘</span>
              <span class="stat-value mono">{{ quote?.open?.toFixed(2) || '—' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">最高</span>
              <span class="stat-value mono price-up">{{ quote?.high?.toFixed(2) || '—' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">最低</span>
              <span class="stat-value mono price-down">{{ quote?.low?.toFixed(2) || '—' }}</span>
            </div>
            <div class="stat-row">
              <span class="stat-label">成交量</span>
              <span class="stat-value mono">{{ formatVolume(quote?.volume) || '—' }}</span>
            </div>
          </div>
        </div>

        <!-- Level selector -->
        <div class="card">
          <div class="card-title">分析级别</div>
          <div class="level-tabs">
            <button
              v-for="lv in levels"
              :key="lv.value"
              class="level-tab"
              :class="{ active: currentLevel === lv.value }"
              @click="changeLevel(lv.value)"
            >{{ lv.label }}</button>
          </div>
        </div>

        <!-- Trend info -->
        <div class="card">
          <div class="card-title">走势判断</div>
          <div class="trend-info">
            <div class="trend-badge" :class="trendClass">
              {{ store.chanlunResult?.trend || '—' }}
            </div>
            <div class="trend-desc">
              {{ store.chanlunResult?.summary || '暂无数据' }}
            </div>
          </div>
        </div>

        <!-- Signals -->
        <SignalCard :signals="store.chanlunResult?.signals || []" />
      </aside>

      <!-- Center: Chart -->
      <div class="chart-area">
        <div class="chart-header">
          <div class="level-tabs chart-level-tabs">
            <button
              v-for="lv in levels"
              :key="lv.value"
              class="level-tab"
              :class="{ active: currentLevel === lv.value }"
              @click="changeLevel(lv.value)"
            >{{ lv.label }}</button>
          </div>
          <div class="chart-actions">
            <IndicatorSelector />
          </div>
        </div>
        <KLineChart
          ref="klineChartRef"
          :klines="store.klines"
          :bis="store.chanlunResult?.bis || []"
          :xiangs="store.chanlunResult?.xiangs || []"
          :zhongshus="store.chanlunResult?.zhongshus || []"
          :signals="store.chanlunResult?.signals || []"
          :ai-signal="store.aiSignal"
          :support-resistance="store.chanlunResult?.supportResistance || []"
          :indicators="store.indicators"
        />
        <VolumeChart v-if="store.indicators.volume" :klines="store.klines" class="sub-chart" />
        <MACDChart v-if="store.indicators.macd" :klines="store.klines" class="sub-chart" />
        <RSIChart v-if="store.indicators.rsi" :klines="store.klines" class="sub-chart" />
        <SKDJChart v-if="store.indicators.skdj" :klines="store.klines" class="sub-chart" />
      </div>

      <!-- Right: AI Strategy -->
      <aside class="sidebar-right">
        <StrategyCard :signal="store.aiSignal" />
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useChanlunStore, type LevelOption } from '../stores/chanlun'
import { stockApi } from '../api/stock'
import KLineChart from '../components/Chart/KLineChart.vue'
import VolumeChart from '../components/Chart/VolumeChart.vue'
import MACDChart from '../components/Chart/MACDChart.vue'
import RSIChart from '../components/Chart/RSIChart.vue'
import SKDJChart from '../components/Chart/SKDJChart.vue'
import SignalCard from '../components/Signal/SignalCard.vue'
import StrategyCard from '../components/Signal/StrategyCard.vue'
import IndicatorSelector from '../components/IndicatorSelector.vue'

const route = useRoute()
const store = useChanlunStore()
const klineChartRef = ref<InstanceType<typeof KLineChart> | null>(null)

const stockCode = computed(() => route.params.code as string)
const currentLevel = computed(() => store.currentLevel)
const loadingAny = computed(() =>
  store.loadingKline || store.loadingChanlun || store.loadingAI
)
const error = computed(() => store.error)
const quote = ref<any>(null)
const isWatching = ref(false)

const levels = [
  { value: '1min' as LevelOption, label: '1分' },
  { value: '5min' as LevelOption, label: '5分' },
  { value: '15min' as LevelOption, label: '15分' },
  { value: '30min' as LevelOption, label: '30分' },
  { value: '60min' as LevelOption, label: '60分' },
  { value: 'daily' as LevelOption, label: '日线' },
  { value: 'weekly' as LevelOption, label: '周线' },
  { value: 'monthly' as LevelOption, label: '月线' },
]

const changeClass = computed(() => {
  if (!quote.value) return ''
  return quote.value.change_pct > 0 ? 'price-up' : quote.value.change_pct < 0 ? 'price-down' : 'price-flat'
})

const changeText = computed(() => {
  if (!quote.value) return ''
  const pct = quote.value.change_pct
  return `${pct > 0 ? '+' : ''}${pct?.toFixed(2) || 0}%`
})

const trendClass = computed(() => {
  const t = store.chanlunResult?.trend
  if (t === '上涨') return 'trend-up'
  if (t === '下跌') return 'trend-down'
  return 'trend-side'
})

async function loadData() {
  const code = stockCode.value
  if (!code) return
  await store.loadAll(code, currentLevel.value)

  // fetch quote
  try {
    const res = await stockApi.quote(code)
    quote.value = res.data
  } catch {}
}

async function changeLevel(level: LevelOption) {
  await store.loadAll(stockCode.value, level)
}

async function toggleWatch() {
  if (isWatching.value) {
    await stockApi.removeWatch(stockCode.value)
    isWatching.value = false
  } else {
    await stockApi.addWatch(stockCode.value)
    isWatching.value = true
  }
}

async function switchModel(model: string) {
  if (model === store.aiModel) return
  await store.setAiModel(model)
  await store.loadAll(stockCode.value, store.currentLevel)
}

function formatVolume(v?: number) {
  if (!v) return '—'
  if (v >= 1e8) return (v / 1e8).toFixed(2) + '亿'
  if (v >= 1e4) return (v / 1e4).toFixed(2) + '万'
  return v.toString()
}

onMounted(loadData)
watch(() => route.params.code, loadData)
</script>

<style scoped>
.layout { min-height: 100vh; }

.nav-actions { display: flex; gap: 8px; margin-left: auto; }

.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  height: 50vh;
  color: var(--text-secondary);
}
.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--border);
  border-top-color: var(--accent-blue);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.error-page {
  text-align: center;
  padding: 80px 24px;
  color: var(--accent-red);
}
.error-page .btn { margin-top: 16px; }

.main-grid {
  display: grid;
  grid-template-columns: 240px 1fr 280px;
  gap: 16px;
  padding: 16px 24px;
  max-width: 1600px;
  margin: 0 auto;
  min-height: calc(100vh - 56px);
}

.sidebar, .sidebar-right { display: flex; flex-direction: column; gap: 12px; }

.stock-info-card { padding: 16px; }
.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 16px;
}
.stock-code-label { font-size: 0.75rem; color: var(--text-muted); }
.stock-name-label { font-size: 1.1rem; font-weight: 700; }
.price-current { font-size: 1.8rem; font-weight: 700; }
.price-change { font-size: 0.9rem; margin-top: 4px; }

.price-stats { display: flex; flex-direction: column; gap: 8px; }
.stat-row { display: flex; justify-content: space-between; }
.stat-label { color: var(--text-muted); font-size: 0.85rem; }
.stat-value { font-size: 0.85rem; }

.trend-info { display: flex; flex-direction: column; gap: 8px; }
.trend-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.85rem;
  font-weight: 600;
  width: fit-content;
}
.trend-up { background: rgba(239, 68, 68, 0.14); color: var(--accent-red); border: 1px solid rgba(239, 68, 68, 0.25); }
.trend-down { background: rgba(34, 197, 94, 0.14); color: var(--accent-green); border: 1px solid rgba(34, 197, 94, 0.25); }
.trend-side { background: rgba(245, 158, 11, 0.12); color: var(--accent-amber); border: 1px solid rgba(245, 158, 11, 0.28); }
.trend-desc { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.5; }

.ai-model-switch {
  display: flex;
  gap: 4px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 4px;
}
.model-btn {
  padding: 5px 12px;
  border-radius: 7px;
  border: none;
  background: transparent;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  cursor: pointer;
  transition: color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease;
}
.model-btn.active {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: #fff;
  box-shadow: 0 2px 10px rgba(14, 165, 233, 0.35);
}
.model-btn:hover:not(.active) { color: var(--text-primary); background: rgba(255, 255, 255, 0.06); }

.chart-area { display: flex; flex-direction: column; gap: 8px; min-width: 0; }
.chart-header { display: flex; align-items: center; gap: 8px; }
.chart-level-tabs { flex-shrink: 0; }
.chart-actions { margin-left: auto; }
.sub-chart { height: 100px; }

@media (max-width: 1200px) {
  .main-grid { grid-template-columns: 200px 1fr; }
  .sidebar-right { display: none; }
}
@media (max-width: 768px) {
  .main-grid { grid-template-columns: 1fr; }
  .sidebar { display: none; }
}
</style>