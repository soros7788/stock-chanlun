<template>
  <div ref="chartRef" class="sub-chart macd-chart" />
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import type { KLine } from '../../api/stock'

const props = defineProps<{ klines: KLine[] }>()

const chartRef = ref<HTMLDivElement | null>(null)
let chart: echarts.ECharts | null = null

function calcEMA(data: number[], period: number) {
  const k = 2 / (period + 1)
  const ema = [data[0]]
  for (let i = 1; i < data.length; i++) {
    ema.push(data[i] * k + ema[i - 1] * (1 - k))
  }
  return ema
}

function calcMACD(closes: number[]) {
  const ema12 = calcEMA(closes, 12)
  const ema26 = calcEMA(closes, 26)
  const dif = ema12.map((v, i) => v - ema26[i])
  const dea = calcEMA(dif, 9)
  const bar = dif.map((v, i) => (v - dea[i]) * 2)
  return { dif, dea, bar }
}

function buildOption() {
  if (props.klines.length < 30) return {}
  const closes = props.klines.map(k => k.close)
  const { dif, dea, bar } = calcMACD(closes)
  const dates = props.klines.map(k => k.date.slice(0, 10))

  return {
    animation: false,
    grid: { left: 10, right: 10, top: 10, bottom: 30 },
    xAxis: [{
      type: 'category', data: dates,
      axisLine: { lineStyle: { color: '#30363d' } },
      axisTick: { show: false }, axisLabel: { show: false }, splitLine: { show: false }
    }],
    yAxis: [{
      scale: true, gridIndex: 0,
      axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: '#21262d', type: 'dashed' } },
      axisLabel: { color: '#7d8590', fontSize: 9 }
    }],
    series: [
      { name: 'DIF', type: 'line', data: dif, lineStyle: { color: '#58a6ff', width: 1 } },
      { name: 'DEA', type: 'line', data: dea, lineStyle: { color: '#d29922', width: 1 } },
      {
        name: 'MACD', type: 'bar', data: bar.map(v => v >= 0 ? v : 0),
        itemStyle: { color: '#f85149' }, barMaxWidth: 4
      },
      {
        name: 'MACDneg', type: 'bar', data: bar.map(v => v < 0 ? Math.abs(v) : 0),
        itemStyle: { color: '#3fb950' }, barMaxWidth: 4
      }
    ],
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1c2128', borderColor: '#30363d',
      textStyle: { color: '#e6edf3', fontSize: 11 }
    }
  }
}

onMounted(() => {
  if (!chartRef.value) return
  chart = echarts.init(chartRef.value)
  chart.setOption(buildOption())
  window.addEventListener('resize', () => chart?.resize())
})
onUnmounted(() => { chart?.dispose() })

watch(() => props.klines, () => {
  if (!chart) return
  chart.setOption(buildOption(), { notMerge: true })
}, { deep: true })
</script>

<style scoped>
.macd-chart {
  width: 100%;
  height: 120px;
  background: var(--bg-card);
  border-radius: 12px;
  border: 1px solid var(--border);
}
</style>
