/**
 * Stock Data Composable
 * Composable for managing stock data state and operations
 */

import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchStockChanges } from '@/services/stockApi'
import {
  getCurrentMonthRange,
  getDateRangeFromDaysAgo,
  getDateRangeFromMonthsAgo,
} from '@/utils/formatters'
import type { StockDataItem, DateShortcut, SortColumn, ChangeType, SortOrder } from '@/types/stock'

export const useStockData = () => {
  const stockData = ref<StockDataItem[]>([])
  const loading = ref(false)
  const dateRange = ref<string[]>([])
  const changeType = ref<ChangeType>('增持')
  const changeSort = ref<SortOrder>('')
  const totalPrice = ref<number>(100000)

  const currentPage = ref(1)
  const pageSize = ref(10)
  const totalCount = ref(0)

  const displayData = computed(() => {
    const startIndex = (currentPage.value - 1) * pageSize.value
    const endIndex = startIndex + pageSize.value
    return stockData.value.slice(startIndex, endIndex)
  })

  const shortcuts: DateShortcut[] = [
    {
      text: '最近一周',
      value: () => {
        const [start, end] = getDateRangeFromDaysAgo(7)
        return [new Date(start), new Date(end)]
      },
    },
    {
      text: '最近一个月',
      value: () => {
        const [start, end] = getDateRangeFromMonthsAgo(1)
        return [new Date(start), new Date(end)]
      },
    },
    {
      text: '最近三个月',
      value: () => {
        const [start, end] = getDateRangeFromMonthsAgo(3)
        return [new Date(start), new Date(end)]
      },
    },
  ]

  const headerStyle = {
    background: '#f5f7fa',
    color: '#303133',
    fontWeight: '600',
  }

  /**
   * Fetch stock data with current parameters
   */
  const fetchData = async () => {
    if (!dateRange.value || dateRange.value.length !== 2) {
      ElMessage.warning('请选择日期范围')
      return
    }

    loading.value = true
    try {
      const [startDate, endDate] = dateRange.value
      const hasTotalPriceFilter =
        totalPrice.value !== null &&
        totalPrice.value !== undefined &&
        !Number.isNaN(totalPrice.value)

      const params = {
        start: startDate,
        end: endDate,
        ...(changeType.value && { changeType: changeType.value }),
        ...(changeSort.value && { changeSort: changeSort.value }),
        ...(hasTotalPriceFilter && { totalPrice: totalPrice.value }),
      }

      const data = await fetchStockChanges(params)
      stockData.value = data.map((item) => ({
        ...item,
        chartLoading: false,
        stockDetail: null,
      }))
      totalCount.value = stockData.value.length
      currentPage.value = 1 // Reset to first page
    } catch {
      stockData.value = []
      totalCount.value = 0
    } finally {
      loading.value = false
    }
  }

  /**
   * Handle sort change
   */
  const handleSortChange = (column: SortColumn) => {
    if (column.prop === 'changeAmount') {
      if (column.order === 'ascending') {
        changeSort.value = 'asc'
      } else if (column.order === 'descending') {
        changeSort.value = 'desc'
      } else {
        changeSort.value = ''
      }
      fetchData()
    }
  }

  /**
   * Handle page size change
   */
  const handleSizeChange = (size: number) => {
    pageSize.value = size
    // Adjust page number to ensure data is displayed correctly
    if (currentPage.value > Math.ceil(totalCount.value / pageSize.value)) {
      currentPage.value = 1
    }
  }

  /**
   * Handle page change
   */
  const handleCurrentChange = (page: number) => {
    currentPage.value = page
  }

  /**
   * Initialize with default date range and fetch data
   */
  const initialize = () => {
    // Set default date range to current month
    const [start, end] = getCurrentMonthRange()
    dateRange.value = [start, end]
    fetchData()
  }

  // Initialize on mount
  onMounted(() => {
    initialize()
  })

  return {
    stockData,
    displayData,
    loading,
    dateRange,
    changeType,
    changeSort,
    totalPrice,
    currentPage,
    pageSize,
    totalCount,
    shortcuts,
    headerStyle,
    fetchData,
    handleSortChange,
    handleSizeChange,
    handleCurrentChange,
    initialize,
  }
}
