<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`${stockName} (${stockCode}) 历史走势`"
    width="min(1180px, 96vw)"
    top="4vh"
    destroy-on-close
    append-to-body
  >
    <div class="history-detail" v-loading="loading">
      <div class="history-summary">
        <div>
          <p class="summary-eyebrow">完整回溯</p>
          <h3>历史价格与事件</h3>
        </div>
        <p class="summary-text">变动人：{{ changerNames || '未提供' }}</p>
      </div>

      <div class="history-chart-card">
        <div ref="chartRef" class="history-chart"></div>
      </div>

      <ChangeMarkTable
        v-if="stockDetail?.marks?.length"
        :marks="stockDetail.marks"
        title="完整历史增减持记录"
      />

      <el-empty v-else-if="!loading" description="未获取到历史增减持记录" />
    </div>
  </el-dialog>
</template>

<script lang="ts">
import { defineComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import type { ECharts } from 'echarts/core'
import ChangeMarkTable from './DataMonitor/ChangeMarkTable.vue'
import { fetchStockHistoryDetail } from '@/services/stockApi'
import type { StockDetailData } from '@/types/stock'

export default defineComponent({
  name: 'StockHistoryDetail',
  components: {
    ChangeMarkTable,
  },
  props: {
    visible: {
      type: Boolean,
      required: true,
    },
    stockCode: {
      type: String,
      required: true,
    },
    stockName: {
      type: String,
      required: true,
    },
    changerNames: {
      type: String,
      default: '',
    },
  },
  emits: ['update:visible'],
  setup(props, { emit }) {
    const dialogVisible = ref(false)
    const loading = ref(false)
    const stockDetail = ref<StockDetailData | null>(null)
    const chartRef = ref<HTMLElement | null>(null)
    let chartInstance: ECharts | null = null

    const cleanupChart = () => {
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
    }

    const initHistoryChart = async () => {
      if (!stockDetail.value?.priceData?.length || !chartRef.value) {
        return
      }

      cleanupChart()
      const { createChartOption, initChart, prepareChartData } = await import('@/utils/chart')
      const { dates, prices, markData } = prepareChartData(stockDetail.value)
      chartInstance = initChart(
        chartRef.value,
        createChartOption(`${props.stockName} (${props.stockCode}) 历史价格走势`, dates, prices, markData),
      )
    }

    const fetchHistoryData = async () => {
      if (!props.stockCode || !props.changerNames) {
        stockDetail.value = null
        ElMessage.warning('缺少变动人信息，无法查询完整历史')
        return
      }

      loading.value = true
      try {
        stockDetail.value = await fetchStockHistoryDetail(props.stockCode, props.changerNames)
        nextTick(async () => {
          await initHistoryChart()
        })
      } catch (error) {
        stockDetail.value = null
        ElMessage.error(error instanceof Error ? error.message : '获取历史详情失败')
      } finally {
        loading.value = false
      }
    }

    const handleResize = () => {
      chartInstance?.resize()
    }

    watch(
      () => props.visible,
      (value) => {
        dialogVisible.value = value
        if (value) {
          fetchHistoryData()
        }
      },
      { immediate: true },
    )

    watch(
      () => dialogVisible.value,
      (value) => {
        if (!value) {
          emit('update:visible', false)
          cleanupChart()
        }
      },
    )

    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      cleanupChart()
    })

    return {
      chartRef,
      dialogVisible,
      loading,
      stockDetail,
    }
  },
})
</script>

<style scoped>
.history-detail {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.history-summary {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
}

.summary-eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.history-summary h3 {
  margin: 0;
  font-size: 22px;
  color: var(--text-primary);
}

.summary-text {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.history-chart-card {
  border-radius: 24px;
  border: 1px solid var(--panel-border);
  background: rgba(255, 255, 255, 0.98);
  padding: 18px;
}

.history-chart {
  width: 100%;
  height: 420px;
}

@media (max-width: 768px) {
  .history-summary {
    flex-direction: column;
    align-items: flex-start;
  }

  .history-chart {
    height: 300px;
  }
}
</style>
