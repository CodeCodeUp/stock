/**
 * Stock API Service
 * Centralized API service functions for stock data
 */

import axios from 'axios'
import { ElMessage } from 'element-plus'
import { API_ENDPOINTS, buildApiUrl, buildQueryString, API_CONFIG } from '@/config/api'
import type { StockDataItem, StockDetailData, StockChangesParams } from '@/types/stock'

// Create axios instance with default config
const apiClient = axios.create({
  timeout: API_CONFIG.timeout,
})

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // Show user-friendly error messages
    if (error.response) {
      const status = error.response.status
      switch (status) {
        case 404:
          ElMessage.error('请求的资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        case 503:
          ElMessage.error('服务暂时不可用')
          break
        default:
          ElMessage.error(`请求失败 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请重试')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  },
)

/**
 * Fetch stock changes data
 * @param params - Query parameters
 * @returns Promise with stock data array
 */
export const fetchStockChanges = async (params: StockChangesParams): Promise<StockDataItem[]> => {
  const url = buildApiUrl(API_ENDPOINTS.STOCK_CHANGES)
  const queryString = buildQueryString(params)
  const fullUrl = queryString ? `${url}?${queryString}` : url

  const response = await apiClient.get(fullUrl)
  return response.data
}

/**
 * Fetch stock chart detail
 * @param stockCode - Stock code
 * @returns Promise with stock detail data
 */
export const fetchStockChart = async (stockCode: string): Promise<StockDetailData> => {
  const url = buildApiUrl(API_ENDPOINTS.STOCK_CHART, { stockCode })
  const response = await apiClient.get(url)
  return response.data
}

/**
 * Fetch stock history detail
 * @param stockCode - Stock code
 * @param changerNames - Changer names (optional)
 * @returns Promise with stock detail data
 */
export const fetchStockHistoryDetail = async (
  stockCode: string,
  changerNames?: string,
): Promise<StockDetailData> => {
  const url = buildApiUrl(API_ENDPOINTS.STOCK_HISTORY_DETAIL)
  const params = {
    code: stockCode,
    name: changerNames || '',
  }
  const queryString = buildQueryString(params)
  const fullUrl = `${url}?${queryString}`

  const response = await apiClient.get(fullUrl)
  return response.data
}
