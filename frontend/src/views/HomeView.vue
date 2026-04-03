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
        <!-- Search -->
        <div class="search-box">
          <input
            v-model="keyword"
            @keydown.enter="search"
            placeholder="输入股票代码或名称..."
            class="search-input"
          />
          <button class="btn btn-primary" @click="search">搜索</button>
        </div>
      </div>
    </nav>

    <!-- Main -->
    <div class="container">
      <div v-if="results.length > 0" class="results">
        <div
          v-for="stock in results"
          :key="stock.code"
          class="stock-card card"
          @click="goToStock(stock.code)"
        >
          <div class="stock-info">
            <span class="stock-code mono">{{ stock.code }}</span>
            <span class="stock-name">{{ stock.name }}</span>
          </div>
          <div class="stock-arrow">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M9 18l6-6-6-6"/>
            </svg>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="!searching && keyword.length === 0" class="empty-state">
        <div class="empty-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
          </svg>
        </div>
        <h2>搜索股票</h2>
        <p>输入股票代码或名称开始分析</p>

        <!-- 当日人气榜：代码 + 名称 -->
        <div class="popular-stocks">
          <h3>热门股票</h3>
          <p class="popular-hint">今日人气（新浪财经）</p>

          <!-- 骨架占位（加载中） -->
          <div v-if="hotLoading" class="popular-list">
            <div v-for="i in 6" :key="i" class="popular-skeleton">
              <span class="skeleton-rank" />
              <span class="skeleton-main">
                <span class="skeleton-code" />
                <span class="skeleton-name" />
              </span>
            </div>
          </div>

          <!-- 真实数据 -->
          <div v-else-if="hotStocks.length > 0" class="popular-list">
            <button
              v-for="s in hotStocks"
              :key="s.code"
              type="button"
              class="popular-card"
              @click="goToStock(s.code)"
            >
              <span class="popular-rank">{{ s.rank }}</span>
              <span class="popular-main">
                <span class="popular-code mono">{{ s.code }}</span>
                <span class="popular-name">{{ s.name || '—' }}</span>
              </span>
              <span
                v-if="s.change_pct != null"
                class="popular-pct mono"
                :class="s.change_pct >= 0 ? 'price-up' : 'price-down'"
              >{{ s.change_pct >= 0 ? '+' : '' }}{{ s.change_pct.toFixed(2) }}%</span>
            </button>
          </div>

          <!-- 加载失败展示错误，不给假数据 -->
          <div v-else class="popular-fallback">
            <p v-if="hotError" class="hot-error">{{ hotError }}</p>
            <p v-else class="fallback-hint">暂无数据</p>
          </div>
        </div>
      </div>

      <div v-if="searchError" class="error-msg">{{ searchError }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { stockApi, type HotStock } from '../api/stock'

const router = useRouter()
const keyword = ref('')
const results = ref<{ code: string; name: string }[]>([])
const searching = ref(false)
const searchError = ref('')

const hotStocks = ref<HotStock[]>([])
const hotLoading = ref(true)
const hotError = ref('')

onMounted(async () => {
  try {
    const res = await stockApi.hotStocks(15)
    if (res.data.error) {
      hotError.value = res.data.error
      hotStocks.value = []
    } else {
      hotStocks.value = res.data.stocks || []
    }
  } catch {
    hotError.value = '获取失败，请稍后重试'
    hotStocks.value = []
  } finally {
    hotLoading.value = false
  }
})

async function search() {
  if (!keyword.value.trim()) return
  searching.value = true
  searchError.value = ''
  try {
    const res = await stockApi.search(keyword.value)
    results.value = res.data.stocks || []
  } catch (e: any) {
    searchError.value = e.message
  } finally {
    searching.value = false
  }
}

function goToStock(code: string) {
  router.push(`/stock/${code}`)
}
</script>

<style scoped>
.layout { min-height: 100vh; }

.search-box {
  display: flex;
  gap: 8px;
  margin-left: auto;
  max-width: 400px;
  flex: 1;
}

.search-input {
  flex: 1;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 8px 14px;
  color: var(--text-primary);
  font-size: 0.875rem;
  outline: none;
  transition: border-color 0.15s;
}
.search-input:focus { border-color: var(--accent-blue); }

.container {
  max-width: 800px;
  margin: 48px auto;
  padding: 0 24px;
}

.results { display: flex; flex-direction: column; gap: 8px; }

.stock-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
  transition: all 0.15s;
}
.stock-card:hover { background: var(--bg-hover); border-color: var(--accent-blue); }

.stock-info { display: flex; flex-direction: column; gap: 4px; }
.stock-code { font-size: 0.9rem; color: var(--accent-blue); }
.stock-name { font-size: 1.1rem; font-weight: 600; }
.stock-arrow { color: var(--text-muted); }

.empty-state {
  text-align: center;
  padding: 64px 0;
}
.empty-icon { color: var(--text-muted); margin-bottom: 24px; }
.empty-state h2 { font-size: 1.5rem; margin-bottom: 8px; }
.empty-state p { color: var(--text-secondary); margin-bottom: 40px; }

.popular-stocks { margin-top: 40px; max-width: 520px; margin-left: auto; margin-right: auto; }
.popular-stocks h3 { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; color: var(--text-muted); margin-bottom: 6px; }
.popular-hint { font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 16px; }
.popular-loading { color: var(--text-muted); font-size: 0.875rem; }
.popular-list { display: flex; flex-direction: column; gap: 8px; text-align: left; }
.popular-card {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 10px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  cursor: pointer;
  color: inherit;
  font: inherit;
  text-align: left;
  transition: border-color 0.15s, background 0.15s;
}
.popular-card:hover { border-color: var(--accent-blue); background: var(--bg-hover); }
.popular-rank {
  flex-shrink: 0;
  width: 1.5rem;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-muted);
}
.popular-main { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.popular-code { font-size: 0.85rem; color: var(--accent-blue); }
.popular-name { font-size: 0.95rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.popular-pct { flex-shrink: 0; font-size: 0.8rem; }
.popular-skeleton { display: flex; align-items: center; gap: 12px; padding: 10px 14px; background: var(--bg-card); border-radius: 12px; }
.skeleton-rank, .skeleton-code, .skeleton-name {
  display: block; height: 12px; border-radius: 6px;
  background: linear-gradient(90deg, var(--bg-secondary) 25%, var(--border) 50%, var(--bg-secondary) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}
.skeleton-rank { width: 16px; }
.skeleton-main { flex: 1; display: flex; flex-direction: column; gap: 6px; }
.skeleton-code { width: 60px; }
.skeleton-name { width: 100px; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.popular-fallback { }
.fallback-hint { font-size: 0.75rem; color: var(--text-muted); }
.hot-error { font-size: 0.8rem; color: var(--accent-red); text-align: center; padding: 8px 0; }

.error-msg { color: var(--accent-red); text-align: center; margin-top: 16px; }
</style>