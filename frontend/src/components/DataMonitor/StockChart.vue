<template>
  <div class="stock-detail-panel" v-loading="loading">
    <div class="detail-overview">
      <div class="overview-card">
        <span class="overview-label">股票</span>
        <strong>{{ row.stockName }} ({{ row.stockCode }})</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">最近变动</span>
        <strong>{{ row.latestTradeDate }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">变动次数</span>
        <strong>{{ row.changeCount }}</strong>
      </div>
      <div class="overview-card">
        <span class="overview-label">累计金额</span>
        <strong>{{ formatCurrency(row.totalAmount) }}</strong>
      </div>
    </div>

    <div class="chart-card">
      <div class="chart-toolbar">
        <div>
          <p class="chart-eyebrow">价格追踪</p>
          <h4>区间价格与增减持标记</h4>
        </div>
      </div>

      <div v-if="hasPriceData" :id="chartDomId" class="stock-chart"></div>
      <el-empty v-else-if="!loading" description="当前库中暂无价格跟踪数据" />

      <div class="chart-actions" v-if="!loading">
        <el-button type="primary" plain @click="showHistoryDetail">查看更多历史数据</el-button>
      </div>
    </div>

    <ChangeMarkTable v-if="stockDetail?.marks?.length" :marks="stockDetail.marks" title="区间增减持记录" />

    <AsyncStockHistoryDetail
      v-model:visible="historyDetailVisible"
      :stock-code="row.stockCode"
      :stock-name="row.stockName"
      :changer-names="selectedChangerNames"
    />
  </div>
</template>

<script lang="ts">
import { computed, defineAsyncComponent, defineComponent, nextTick, onMounted, onUnmounted, type PropType, ref } from 'vue'
import { ElMessage } from 'element-plus'
import type { ECharts } from 'echarts/core'
import ChangeMarkTable from './ChangeMarkTable.vue'
import { fetchStockChart } from '@/services/stockApi'
import { formatCurrency } from '@/utils/formatters'
import type { MarkItem, StockDataItem, StockDetailData } from '@/types/stock'

const AsyncStockHistoryDetail = defineAsyncComponent(() => import('../StockHistoryDetail.vue'))

const waitForChartDom = async (chartDomId: string, retries = 8): Promise<HTMLElement | null> => {
  for (let attempt = 0; attempt < retries; attempt += 1) {
    const chartDom = document.getElementById(chartDomId)
    if (chartDom) {
      return chartDom
    }

    await nextTick()
    await new Promise((resolve) => window.setTimeout(resolve, 16))
  }

  return null
}

export default defineComponent({
  name: 'StockChart',
  components: {
    AsyncStockHistoryDetail,
    ChangeMarkTable,
  },
  props: {
    row: {
      type: Object as PropType<StockDataItem>,
      required: true,
    },
    dateRange: {
      type: Array as PropType<string[]>,
      default: () => [],
    },
  },
  setup(props) {
    const historyDetailVisible = ref(false)
    const loading = ref(false)
    const chartInstance = ref<ECharts | null>(null)
    const stockDetail = ref<StockDetailData | null>(null)

    const chartDomId = computed(() => `chart-${props.row.uiKey ?? props.row.stockCode}`)
    const hasPriceData = computed(() => Boolean(stockDetail.value?.priceData?.length))

    const selectedChangerNames = computed(() => {
      if (props.row.changerName) {
        return props.row.changerName
      }

      const marks = stockDetail.value?.marks ?? []
      const changers = [
        ...new Set(
          marks.filter((mark: MarkItem) => mark.changerName).map((mark: MarkItem) => mark.changerName),
        ),
      ]

      return changers.join(',')
    })

    const disposeChart = () => {
      chartInstance.value?.dispose()
      chartInstance.value = null
    }

    const renderChart = async () => {
      if (!stockDetail.value?.priceData?.length) {
        disposeChart()
        return
      }

      const chartDom = await waitForChartDom(chartDomId.value)
      if (!chartDom) {
        ElMessage.warning('图表容器尚未准备完成，请重新展开后重试')
        return
      }

      disposeChart()
      const { createChartOption, initChart, prepareChartData } = await import('@/utils/chart')
      const { dates, prices, markData } = prepareChartData(stockDetail.value)
      const option = createChartOption(`${props.row.stockName} (${props.row.stockCode}) 价格走势`, dates, prices, markData)
      chartInstance.value = initChart(chartDom, option)
    }

    const loadDetail = async () => {
      loading.value = true
      try {
        stockDetail.value = await fetchStockChart(props.row.stockCode, {
          start: props.dateRange?.[0],
          end: props.dateRange?.[1],
        })

        await nextTick()
        await renderChart()
      } catch (error) {
        stockDetail.value = null
        ElMessage.error(error instanceof Error ? error.message : '获取股票走势图失败')
      } finally {
        loading.value = false
      }
    }

    const showHistoryDetail = () => {
      if (!selectedChangerNames.value) {
        ElMessage.warning('缺少变动人信息，无法拉取完整历史')
        return
      }
      historyDetailVisible.value = true
    }

    const handleResize = () => {
      chartInstance.value?.resize()
    }

    onMounted(async () => {
      window.addEventListener('resize', handleResize)
      await loadDetail()
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      disposeChart()
    })

    return {
      chartDomId,
      formatCurrency,
      hasPriceData,
      historyDetailVisible,
      loading,
      selectedChangerNames,
      stockDetail,
      showHistoryDetail,
    }
  },
})
</script>

<style scoped>
.stock-detail-panel {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 24px;
  margin-top: 12px;
  border-radius: 24px;
  background: linear-gradient(180deg, rgba(246, 249, 252, 0.95), rgba(255, 255, 255, 0.96));
  border: 1px solid var(--panel-border);
}

.detail-overview {
  min-width: 0;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.overview-card {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(148, 163, 184, 0.18);
}

.overview-label {
  display: block;
  font-size: 12px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.overview-card strong {
  color: var(--text-primary);
  font-size: 16px;
}

.chart-card {
  min-width: 0;
  padding: 20px;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid var(--panel-border);
}

.chart-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 18px;
}

.chart-toolbar > div {
  min-width: 0;
}

.chart-eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.chart-toolbar h4 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.chart-toolbar :deep(.el-button),
:deep(.el-empty__bottom .el-button) {
  max-width: 100%;
  white-space: normal;
}

.chart-actions {
  display: flex;
  justify-content: flex-start;
  margin-top: 16px;
}

.chart-actions :deep(.el-button) {
  max-width: 100%;
  white-space: normal;
}

.stock-chart {
  width: 100%;
  height: 340px;
}

@media (max-width: 960px) {
  .detail-overview {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .stock-detail-panel {
    padding: 16px;
  }

  .chart-toolbar {
    width: 100%;
  }

  .stock-chart {
    height: 280px;
  }
}

@media (max-width: 560px) {
  .detail-overview {
    grid-template-columns: 1fr;
  }
}
</style>
