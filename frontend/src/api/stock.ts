import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 15000,
})

// ─── Types ───────────────────────────────────────────────────────────────────

export interface KLine {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

export interface Bi {
  id: string
  start: string
  end: string
  direction: 'up' | 'down'
  high: number
  low: number
}

export interface XiangSegment {
  id: string
  start: string
  end: string
  direction: 'up' | 'down'
  high: number
  low: number
}

export interface Zhongshu {
  id: string
  start: string
  end: string
  range_high: number
  range_low: number
}

export interface Signal {
  type: string
  level: string
  price: number
  datetime: string
  confidence: number
  stop_loss?: number
  take_profit?: number
  description: string
}

export interface SupportResistance {
  type: 'support' | 'resistance'
  price: number
  source: string
  relatedId: string
  datetime: string
  strength: number
}

export interface HotStock {
  rank: number
  code: string
  name: string
  change_pct?: number
  volume?: number
}

export interface Quote {
  code: string
  name: string
  price: number
  change_pct: number
  volume: number
  high: number
  low: number
  open: number
  prev_close: number
  amount: number
}

export interface ChanlunResult {
  stock_code: string
  level: string
  trend: string
  summary: string
  bis: Bi[]
  xiangs: XiangSegment[]
  zhongshus: Zhongshu[]
  signals: Signal[]
  supportResistance: SupportResistance[]
}

export interface AISignal {
  stock_code: string
  level: string
  direction: string
  confidence: number
  risk_level: string
  entry_price?: number
  stop_loss?: number
  take_profit?: number
  holding_period: string
  description: string
  trend: string
  divergence?: { type: string; probability: number; description: string } | null
  resonance?: { 共振: boolean; direction?: string; levels?: string[]; description: string }
  llm?: {
    model: string
    used: boolean
    error?: string
  }
}

// ─── API Methods ────────────────────────────────────────────────────────────

export const stockApi = {
  search(q: string) {
    return api.get<{ stocks: { code: string; name: string }[]; total: number }>(
      `/stocks/search?q=${q}`
    )
  },

  hotStocks(limit = 15) {
    return api.get<{ stocks: HotStock[]; total: number; error?: string | null }>('/stocks/hot', {
      params: { limit },
      timeout: 60000,
    })
  },

  info(code: string) {
    return api.get(`/stocks/${code}/info`)
  },

  quote(code: string) {
    return api.get<Quote>(`/stocks/${code}/quote`)
  },

  kline(code: string, level: string, limit = 500) {
    return api.get<{ klines: KLine[]; total: number }>(
      `/stocks/${code}/kline?level=${level}&limit=${limit}`
    )
  },

  chanlun(code: string, level: string) {
    return api.get<ChanlunResult>(
      `/chanlun/${code}?level=${level}`
    )
  },

  aiSignal(code: string, level: string, model = 'deepseek') {
    return api.get<AISignal>(
      `/chanlun/${code}/ai?level=${level}&model=${model}`,
      { timeout: 120000 }
    )
  },

  watchlist() {
    return api.get<{ stocks: Quote[]; total: number }>('/watchlist')
  },

  addWatch(code: string) {
    return api.post(`/watchlist/${code}`)
  },

  removeWatch(code: string) {
    return api.delete(`/watchlist/${code}`)
  },

  getSettings() {
    return api.get<{ ai_model: string }>('/settings')
  },

  setAiModel(model: string) {
    return api.put<{ ai_model: string; ok: boolean }>('/settings', null, {
      params: { model },
    })
  },
}

export default api