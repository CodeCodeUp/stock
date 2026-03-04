/**
 * Chart Composable
 * Composable for managing chart functionality
 */

import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'
import { fetchStockChart } from '@/services/stockApi'
import { prepareChartData, createChartOption, initChart } from '@/utils/chart'
import type { StockDataItem } from '@/types/stock'

export const useChart = () => {
  // Chart instances storage
  const chartInstances = ref<Record<string, echarts.ECharts>>({})

  /**
   * Fetch stock detail data
   */
  const fetchStockDetail = async (row: StockDataItem): Promise<void> => {
    // Mark as loading
    row.chartLoading = true

    try {
      const stockDetail = await fetchStockChart(row.stockCode)
      row.stockDetail = stockDetail

      // Wait for DOM update then initialize chart
      nextTick(() => {
        initStockChart(row)
      })
    } catch (error) {
      console.error('Failed to fetch stock detail:', error)
      ElMessage.error('获取股票详情失败，请重试')
      row.stockDetail = null
    } finally {
      row.chartLoading = false
    }
  }

  /**
   * Initialize chart for a stock row
   */
  const initStockChart = (row: StockDataItem): void => {
    if (!row.stockDetail || !row.stockDetail.priceData) return

    // Get chart DOM element using composite ID for uniqueness
    const chartDomId = `chart-${row.stockCode}-${row.tradeDate}`
    const chartDom = document.getElementById(chartDomId)
    if (!chartDom) {
      console.error(`Chart container ${chartDomId} does not exist`)
      return
    }

    // Dispose old chart instance if exists
    if (chartInstances.value[chartDomId]) {
      chartInstances.value[chartDomId].dispose()
    }

    // Prepare chart data
    const { dates, prices, markData } = prepareChartData(row.stockDetail)

    // Create chart option
    const title = `${row.stockName} (${row.stockCode}) 价格走势`
    const option = createChartOption(title, dates, prices, markData)

    // Initialize chart
    chartInstances.value[chartDomId] = initChart(chartDom, option)
    console.log(`Chart ${chartDomId} initialized`)
  }

  /**
   * Handle expand change event
   */
  const handleExpandChange = async (
    row: StockDataItem,
    expandedRows: StockDataItem[],
  ): Promise<void> => {
    // Update expand state
    console.log('Expanded rows:', expandedRows, 'Current row:', row)

    // If row is expanded and has no stock detail data, fetch it
    if (!row.stockDetail) {
      await fetchStockDetail(row)
    } else {
      // If data already exists, just reinitialize chart
      nextTick(() => {
        initStockChart(row)
      })
    }
  }

  /**
   * Resize all chart instances
   */
  const handleResize = (): void => {
    Object.values(chartInstances.value).forEach((chart) => {
      chart.resize()
    })
  }

  /**
   * Dispose all chart instances
   */
  const disposeAllCharts = (): void => {
    Object.values(chartInstances.value).forEach((chart) => {
      chart.dispose()
    })
    chartInstances.value = {}
  }

  /**
   * Dispose specific chart instance
   */
  const disposeChart = (chartId: string): void => {
    if (chartInstances.value[chartId]) {
      chartInstances.value[chartId].dispose()
      delete chartInstances.value[chartId]
    }
  }

  // Setup window resize listener
  onMounted(() => {
    window.addEventListener('resize', handleResize)
  })

  // Cleanup on unmount
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    disposeAllCharts()
  })

  return {
    // State
    chartInstances,

    // Methods
    fetchStockDetail,
    initStockChart,
    handleExpandChange,
    handleResize,
    disposeAllCharts,
    disposeChart,
  }
}
