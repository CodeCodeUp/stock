<template>
  <el-dialog
    v-model="dialogVisible"
    :title="`${stockName} (${stockCode}) 所有历史数据`"
    width="80%"
    destroy-on-close
    :z-index="3000"
    append-to-body
    :modal="true"
    class="stock-history-dialog"
  >
    <div v-loading="loading">
      <div class="history-chart-container">
        <div id="history-chart" class="history-chart"></div>
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
import { ref, onMounted, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { fetchStockHistoryDetail } from '@/services/stockApi'
import { prepareChartData, createChartOption, initChart } from '@/utils/chart'
import { formatNumber } from '@/utils/formatters'
import type { StockDetailData } from '@/types/stock'

export default {
  name: 'StockHistoryDetail',
  props: {
    visible: Boolean,
    stockCode: String,
    stockName: String,
    changerNames: String,
  },
  emits: ['update:visible'],
  setup(props, { emit }) {
    const dialogVisible = ref(false)
    const loading = ref(false)
    const stockDetail = ref<StockDetailData | null>(null)
    let chartInstance: echarts.ECharts | null = null

    // Watch visible property changes
    watch(
      () => props.visible,
      (newValue) => {
        dialogVisible.value = newValue
        if (newValue) {
          fetchHistoryData()
        }
      },
    )

    // Watch dialog close
    watch(
      () => dialogVisible.value,
      (newValue) => {
        if (!newValue) {
          emit('update:visible', false)
        }
      },
    )

    const fetchHistoryData = async () => {
      if (!props.stockCode) return

      loading.value = true
      try {
        const data = await fetchStockHistoryDetail(props.stockCode, props.changerNames)
        stockDetail.value = data

        nextTick(() => {
          initHistoryChart()
        })
      } catch (error) {
        console.error('Failed to fetch history data:', error)
        stockDetail.value = null
      } finally {
        loading.value = false
      }
    }

    const initHistoryChart = () => {
      if (!stockDetail.value || !stockDetail.value.priceData) return

      const chartDom = document.getElementById('history-chart')
      if (!chartDom) {
        console.error('Chart container does not exist')
        return
      }

      // Dispose old chart instance
      if (chartInstance) {
        chartInstance.dispose()
      }

      // Prepare chart data
      const { dates, prices, markData } = prepareChartData(stockDetail.value)

      // Create chart option
      const title = `${props.stockName} (${props.stockCode}) 价格走势`
      const option = createChartOption(title, dates, prices, markData)

      // Initialize chart
      chartInstance = initChart(chartDom, option)
    }

    // Handle window resize
    const handleResize = () => {
      if (chartInstance) {
        chartInstance.resize()
      }
    }

    onMounted(() => {
      window.addEventListener('resize', handleResize)
    })

    return {
      dialogVisible,
      loading,
      stockDetail,
      formatNumber,
    }
  },
}
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

<style>
/* Global styles for the dialog to ensure proper z-index layering */
.stock-history-dialog {
  z-index: 3000 !important;
}

.stock-history-dialog .el-dialog {
  z-index: 3000 !important;
}

.stock-history-dialog .el-overlay {
  z-index: 2999 !important;
}

/* Ensure the dialog appears above all other elements */
.el-dialog__wrapper.stock-history-dialog {
  z-index: 3000 !important;
}
</style>
