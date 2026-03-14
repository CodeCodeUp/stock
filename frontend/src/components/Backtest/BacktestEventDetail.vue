<template>
  <el-drawer
    v-model="drawerVisible"
    :title="drawerTitle"
    size="min(980px, 94vw)"
    append-to-body
    destroy-on-close
  >
    <div class="detail-shell" v-loading="loading">
      <template v-if="detail">
        <section class="detail-grid">
          <article class="detail-card">
            <span class="detail-label">信号日期</span>
            <strong>{{ formatDate(detail.event.signalDate) }}</strong>
          </article>
          <article class="detail-card">
            <span class="detail-label">增持金额</span>
            <strong>{{ formatCurrency(detail.event.increaseAmount) }}</strong>
          </article>
          <article class="detail-card">
            <span class="detail-label">信号评分</span>
            <strong>{{ detail.event.signalScore }}</strong>
          </article>
          <article class="detail-card">
            <span class="detail-label">历史回测评分</span>
            <strong>{{ detail.event.backtestScore }}</strong>
          </article>
        </section>

        <section class="chart-card">
          <div class="section-heading">
            <div>
              <p class="section-eyebrow">事件图谱</p>
              <h3>事件前后价格走势与增减持标记</h3>
            </div>
            <p class="section-note">入场价口径：信号次一交易日开盘价</p>
          </div>
          <div ref="chartRef" class="detail-chart"></div>
        </section>

        <section class="summary-card">
          <div class="section-heading">
            <div>
              <p class="section-eyebrow">股票画像</p>
              <h3>历史增持响应表现</h3>
            </div>
          </div>
          <div class="summary-grid">
            <div class="summary-item">
              <span>样本事件数</span>
              <strong>{{ detail.stockSummary.sampleEventCount }}</strong>
            </div>
            <div class="summary-item">
              <span>20日胜率</span>
              <strong>{{ formatPercentage(detail.stockSummary.winRate20d) }}</strong>
            </div>
            <div class="summary-item">
              <span>20日平均收益</span>
              <strong :class="getReturnClass(detail.stockSummary.avgReturn20d)">
                {{ formatPercentage(detail.stockSummary.avgReturn20d) }}
              </strong>
            </div>
            <div class="summary-item">
              <span>20日平均回撤</span>
              <strong :class="getReturnClass(detail.stockSummary.avgMaxDrawdown20d)">
                {{ formatPercentage(detail.stockSummary.avgMaxDrawdown20d) }}
              </strong>
            </div>
          </div>
        </section>

        <section class="metric-card">
          <div class="section-heading">
            <div>
              <p class="section-eyebrow">回测窗口</p>
              <h3>不同持有周期表现</h3>
            </div>
          </div>
          <el-table :data="detail.metrics" stripe size="small" style="width: 100%">
            <el-table-column prop="horizonDays" label="窗口" width="90">
              <template #default="scope">{{ scope.row.horizonDays }} 日</template>
            </el-table-column>
            <el-table-column prop="entryDate" label="入场日" width="110" />
            <el-table-column prop="exitDate" label="退出日" width="110" />
            <el-table-column label="区间收益" width="120">
              <template #default="scope">
                <span :class="getReturnClass(scope.row.returnPct)">
                  {{ formatPercentage(scope.row.returnPct) }}
                </span>
              </template>
            </el-table-column>
            <el-table-column label="最大涨幅" width="120">
              <template #default="scope">
                <span class="positive-text">{{ formatPercentage(scope.row.maxReturnPct) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="最大回撤" width="120">
              <template #default="scope">
                <span class="negative-text">{{ formatPercentage(scope.row.maxDrawdownPct) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="命中 5%" width="100">
              <template #default="scope">{{ scope.row.hit5pctFlag ? '是' : '否' }}</template>
            </el-table-column>
            <el-table-column label="命中 10%" width="100">
              <template #default="scope">{{ scope.row.hit10pctFlag ? '是' : '否' }}</template>
            </el-table-column>
          </el-table>
        </section>

        <section class="mark-card" v-if="detail.marks.length">
          <div class="section-heading">
            <div>
              <p class="section-eyebrow">事件明细</p>
              <h3>区间增减持记录</h3>
            </div>
          </div>
          <el-table :data="detail.marks" stripe size="small" style="width: 100%">
            <el-table-column prop="tradeDate" label="日期" width="110" />
            <el-table-column prop="changeType" label="方向" width="90" />
            <el-table-column label="金额" width="140">
              <template #default="scope">{{ formatCurrency(scope.row.totalPrice) }}</template>
            </el-table-column>
            <el-table-column prop="changerName" label="变动人" min-width="140" show-overflow-tooltip />
            <el-table-column prop="changerPosition" label="职位" min-width="140" show-overflow-tooltip />
          </el-table>
        </section>
      </template>

      <el-empty v-else-if="!loading" description="未获取到事件详情" />
    </div>
  </el-drawer>
</template>

<script lang="ts">
import { computed, defineComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { ECharts, EChartsCoreOption } from 'echarts/core'
import { CHART_COLORS, initChart } from '@/utils/chart'
import { fetchBacktestEventDetail } from '@/services/stockApi'
import { formatCurrency, formatDate, formatPercentage } from '@/utils/formatters'
import type { BacktestEventDetail, BacktestPriceBar, MarkItem } from '@/types/stock'

const buildChartOption = (
  title: string,
  priceBars: BacktestPriceBar[],
  marks: MarkItem[],
): EChartsCoreOption => {
  const dates = priceBars.map((item) => formatDate(item.tradeDate))
  const prices = priceBars.map((item) => item.closePrice)
  const priceMap = new Map(priceBars.map((item) => [formatDate(item.tradeDate), item.closePrice]))
  const markData = marks
    .map((item) => {
      const tradeDate = formatDate(item.tradeDate)
      const price = priceMap.get(tradeDate)
      if (price === undefined) {
        return null
      }
      return {
        name: item.changeType,
        coord: [tradeDate, price],
        value: formatCurrency(item.totalPrice),
        itemStyle: {
          color: item.changeType === '增持' ? CHART_COLORS.increase : CHART_COLORS.decrease,
        },
      }
    })
    .filter((item): item is NonNullable<typeof item> => item !== null)

  return {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
        fontWeight: 600,
        color: '#172033',
      },
    },
    grid: {
      top: 56,
      left: 24,
      right: 24,
      bottom: 40,
      containLabel: true,
    },
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(15, 23, 42, 0.92)',
      borderWidth: 0,
      textStyle: {
        color: '#f8fafc',
      },
    },
    xAxis: {
      type: 'category',
      data: dates,
      boundaryGap: false,
      axisLine: {
        lineStyle: { color: CHART_COLORS.split },
      },
      axisLabel: {
        color: CHART_COLORS.axis,
        interval: Math.max(0, Math.floor(dates.length / 10)),
      },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        color: CHART_COLORS.axis,
      },
      splitLine: {
        lineStyle: {
          color: CHART_COLORS.split,
        },
      },
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        height: 18,
        bottom: 10,
        start: 0,
        end: 100,
      },
    ],
    series: [
      {
        type: 'line',
        data: prices,
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 2.5,
          color: CHART_COLORS.line,
        },
        areaStyle: {
          color: CHART_COLORS.fill,
        },
        markPoint: {
          symbol: 'pin',
          symbolSize: 42,
          data: markData,
        },
      },
    ],
  }
}

export default defineComponent({
  name: 'BacktestEventDetail',
  props: {
    visible: {
      type: Boolean,
      required: true,
    },
    eventId: {
      type: Number,
      default: 0,
    },
  },
  emits: ['update:visible'],
  setup(props, { emit }) {
    const drawerVisible = ref(false)
    const loading = ref(false)
    const detail = ref<BacktestEventDetail | null>(null)
    const chartRef = ref<HTMLElement | null>(null)
    const chartInstance = ref<ECharts | null>(null)

    const drawerTitle = computed(() => {
      const event = detail.value?.event
      if (!event) {
        return '事件详情'
      }
      return `${event.stockName} (${event.stockCode}) 事件画像`
    })

    const disposeChart = () => {
      chartInstance.value?.dispose()
      chartInstance.value = null
    }

    const renderChart = async () => {
      if (!detail.value || !chartRef.value || !detail.value.priceBars.length) {
        disposeChart()
        return
      }

      await nextTick()
      disposeChart()
      chartInstance.value = initChart(
        chartRef.value,
        buildChartOption(drawerTitle.value, detail.value.priceBars, detail.value.marks),
      )
    }

    const loadDetail = async () => {
      if (!props.eventId) {
        detail.value = null
        return
      }

      loading.value = true
      try {
        detail.value = await fetchBacktestEventDetail(props.eventId)
        await renderChart()
      } catch (error) {
        detail.value = null
        ElMessage.error(error instanceof Error ? error.message : '获取事件详情失败')
      } finally {
        loading.value = false
      }
    }

    const handleResize = () => {
      chartInstance.value?.resize()
    }

    watch(
      () => props.visible,
      async (value) => {
        drawerVisible.value = value
        if (value) {
          await loadDetail()
        }
      },
      { immediate: true },
    )

    watch(
      () => props.eventId,
      async (value, oldValue) => {
        if (drawerVisible.value && value && value !== oldValue) {
          await loadDetail()
        }
      },
    )

    watch(
      () => drawerVisible.value,
      (value) => {
        if (!value) {
          emit('update:visible', false)
          disposeChart()
        }
      },
    )

    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      disposeChart()
    })

    const getReturnClass = (value: number | null | undefined) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        return ''
      }
      if (value > 0) {
        return 'positive-text'
      }
      if (value < 0) {
        return 'negative-text'
      }
      return ''
    }

    return {
      chartRef,
      detail,
      drawerTitle,
      drawerVisible,
      formatCurrency,
      formatDate,
      formatPercentage,
      getReturnClass,
      loading,
    }
  },
})
</script>

<style scoped>
.detail-shell {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.detail-grid,
.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.detail-card,
.summary-item,
.chart-card,
.summary-card,
.metric-card,
.mark-card {
  border-radius: 22px;
  border: 1px solid var(--panel-border);
  background: rgba(255, 255, 255, 0.96);
}

.detail-card,
.summary-item {
  padding: 16px 18px;
}

.detail-label,
.summary-item span {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.detail-card strong,
.summary-item strong {
  font-size: 18px;
  color: var(--text-primary);
}

.chart-card,
.summary-card,
.metric-card,
.mark-card {
  padding: 20px;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 18px;
}

.section-eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.section-heading h3 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.section-note {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.detail-chart {
  width: 100%;
  height: 360px;
}

.positive-text {
  color: var(--increase-color);
  font-weight: 700;
}

.negative-text {
  color: var(--decrease-color);
  font-weight: 700;
}

@media (max-width: 960px) {
  .detail-grid,
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .detail-grid,
  .summary-grid {
    grid-template-columns: 1fr;
  }

  .section-heading {
    flex-direction: column;
    align-items: flex-start;
  }

  .detail-chart {
    height: 280px;
  }
}
</style>
