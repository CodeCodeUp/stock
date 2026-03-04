<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`${stockName} (${stockCode}) 所有历史数据`"
    width="80%"
    destroy-on-close
    append-to-body
    :modal="true"
  >
    <div v-loading="loading">
      <div class="history-chart-container">
        <div ref="chartRef" class="history-chart"></div>
      </div>

      <div
        class="history-marks-detail"
        v-if="stockDetail && stockDetail.marks && stockDetail.marks.length > 0"
      >
        <h4>历史增减持记录</h4>
        <el-table :data="stockDetail.marks" stripe size="small" style="width: 100%">
          <el-table-column prop="tradeDate" label="交易日期" width="120" />
          <el-table-column prop="changeType" label="变动类型" width="100">
            <template #default="scope">
              <span :class="scope.row.changeType === '增持' ? 'increase' : 'decrease'">
                {{ scope.row.changeType }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="交易金额" width="150">
            <template #default="scope">
              <span :class="scope.row.changeType === '增持' ? 'increase' : 'decrease'">
                {{ formatNumber(scope.row.totalPrice) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="price" label="成交价" width="120" />
          <el-table-column prop="changerName" label="变动人" />
          <el-table-column prop="changerPosition" label="职位" />
        </el-table>
      </div>
    </div>
  </el-dialog>
</template>

<script lang="ts">
import { defineComponent, nextTick, onMounted, onUnmounted, ref, watch } from 'vue'
import * as echarts from 'echarts'
import { fetchStockHistoryDetail } from '@/services/stockApi'
import { prepareChartData, createChartOption, initChart } from '@/utils/chart'
import { formatNumber } from '@/utils/formatters'
import type { StockDetailData } from '@/types/stock'

export default defineComponent({
  name: 'StockHistoryDetail',
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
    let chartInstance: echarts.ECharts | null = null

    const cleanupChart = () => {
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
    }

    const initHistoryChart = () => {
      if (!stockDetail.value || !stockDetail.value.priceData || !chartRef.value) {
        return
      }

      cleanupChart()

      const { dates, prices, markData } = prepareChartData(stockDetail.value)
      const title = `${props.stockName} (${props.stockCode}) 价格走势`
      const option = createChartOption(title, dates, prices, markData)

      chartInstance = initChart(chartRef.value, option)
    }

    const fetchHistoryData = async () => {
      if (!props.stockCode) return

      loading.value = true
      try {
        stockDetail.value = await fetchStockHistoryDetail(props.stockCode, props.changerNames)
        nextTick(() => {
          initHistoryChart()
        })
      } catch {
        stockDetail.value = null
      } finally {
        loading.value = false
      }
    }

    const handleResize = () => {
      if (chartInstance) {
        chartInstance.resize()
      }
    }

    watch(
      () => props.visible,
      (newValue) => {
        dialogVisible.value = newValue
        if (newValue) {
          fetchHistoryData()
        }
      },
      { immediate: true },
    )

    watch(
      () => dialogVisible.value,
      (newValue) => {
        if (!newValue) {
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
      dialogVisible,
      loading,
      stockDetail,
      chartRef,
      formatNumber,
    }
  },
})
</script>

<style scoped>
.history-chart-container {
  width: 100%;
  height: 400px;
  margin-bottom: 20px;
}

.history-chart {
  width: 100%;
  height: 100%;
}

.history-marks-detail {
  margin-top: 20px;
}

.history-marks-detail h4 {
  margin-bottom: 16px;
  font-weight: 500;
  color: #303133;
  font-size: 15px;
}

.increase {
  color: #f56c6c;
  font-weight: 600;
}

.decrease {
  color: #67c23a;
  font-weight: 600;
}
</style>
