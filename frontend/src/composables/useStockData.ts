import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { fetchStockChanges } from '@/services/stockApi'
import {
  getCurrentMonthRange,
  getDateRangeFromDaysAgo,
  getDateRangeFromMonthsAgo,
} from '@/utils/formatters'
import type { ChangeType, DateShortcut, SortColumn, SortOrder, StockDataItem } from '@/types/stock'

const createUiKey = (item: StockDataItem, index: number): string => {
  return `${item.stockCode}-${item.latestTradeDate}-${index}`
}

export const useStockData = () => {
  const stockData = ref<StockDataItem[]>([])
  const loading = ref(false)
  const dateRange = ref<string[]>([])
  const changeType = ref<ChangeType>('增持')
  const changeSort = ref<SortOrder>('')
  const totalPrice = ref<number>(100000)
  const currentPage = ref(1)
  const pageSize = ref(20)
  const totalCount = ref(0)

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
    background: 'rgba(241, 245, 249, 0.95)',
    color: '#1e293b',
    fontWeight: '600',
    borderBottom: '1px solid rgba(148, 163, 184, 0.18)',
  }

  const displayData = computed(() => stockData.value)

  const fetchData = async (page = currentPage.value) => {
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

      const response = await fetchStockChanges({
        start: startDate,
        end: endDate,
        changeType: changeType.value || undefined,
        changeSort: changeSort.value || undefined,
        totalPrice: hasTotalPriceFilter ? totalPrice.value : undefined,
        page,
        pageSize: pageSize.value,
      })

      stockData.value = response.items.map((item, index) => ({
        ...item,
        totalIncrease: Number(item.totalIncrease ?? 0),
        totalDecrease: Number(item.totalDecrease ?? 0),
        totalAmount: Number(item.totalAmount ?? 0),
        changeCount: Number(item.changeCount ?? 0),
        uiKey: createUiKey(item, index),
        chartLoading: false,
        stockDetail: null,
      }))
      totalCount.value = response.total
      currentPage.value = response.page
      pageSize.value = response.pageSize
    } catch (error) {
      stockData.value = []
      totalCount.value = 0
      ElMessage.error(error instanceof Error ? error.message : '获取股票列表失败')
    } finally {
      loading.value = false
    }
  }

  const handleSortChange = async (column: SortColumn) => {
    if (column.prop !== 'totalAmount') {
      return
    }

    if (column.order === 'ascending') {
      changeSort.value = 'asc'
    } else if (column.order === 'descending') {
      changeSort.value = 'desc'
    } else {
      changeSort.value = ''
    }

    await fetchData(1)
  }

  const handleSizeChange = async (size: number) => {
    pageSize.value = size
    await fetchData(1)
  }

  const handleCurrentChange = async (page: number) => {
    currentPage.value = page
    await fetchData(page)
  }

  const initialize = async () => {
    const [start, end] = getCurrentMonthRange()
    dateRange.value = [start, end]
    await fetchData(1)
  }

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
  }
}
