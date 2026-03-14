import axios, { AxiosError, type AxiosRequestConfig } from 'axios'
import { API_CONFIG, API_ENDPOINTS, buildApiUrl, buildQueryString } from '@/config/api'
import type {
  ApiResponse,
  BacktestEventDetail,
  BacktestEventItem,
  BacktestOverview,
  BacktestQueryParams,
  BacktestRebuildResponse,
  ChartQueryParams,
  PageResult,
  StockBacktestSummary,
  StockChangesParams,
  StockDataItem,
  StockDetailData,
} from '@/types/stock'

const apiClient = axios.create({
  timeout: API_CONFIG.timeout,
})

const extractMessage = (error: unknown): string => {
  if (error instanceof AxiosError) {
    const responseMessage = error.response?.data?.message
    if (typeof responseMessage === 'string' && responseMessage.trim()) {
      return responseMessage
    }
    if (error.code === 'ECONNABORTED') {
      return '请求超时，请稍后重试'
    }
    if (error.response?.status) {
      return `请求失败 (${error.response.status})`
    }
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  return '网络异常，请稍后重试'
}

const request = async <T>(config: AxiosRequestConfig): Promise<T> => {
  try {
    const response = await apiClient.request<ApiResponse<T>>(config)
    const payload = response.data

    if (!payload || typeof payload.code !== 'number') {
      throw new Error('接口响应格式错误')
    }

    if (payload.code !== 0) {
      throw new Error(payload.message || '请求失败')
    }

    return payload.data
  } catch (error) {
    throw new Error(extractMessage(error))
  }
}

export const fetchStockChanges = async (
  params: StockChangesParams,
): Promise<PageResult<StockDataItem>> => {
  const url = buildApiUrl(API_ENDPOINTS.STOCK_CHANGES)
  const queryString = buildQueryString(params)
  return request<PageResult<StockDataItem>>({
    url: queryString ? `${url}?${queryString}` : url,
    method: 'GET',
  })
}

export const fetchStockChart = async (
  stockCode: string,
  params?: ChartQueryParams,
): Promise<StockDetailData> => {
  const url = buildApiUrl(API_ENDPOINTS.STOCK_CHART, { stockCode })
  const queryString = params ? buildQueryString(params) : ''
  return request<StockDetailData>({
    url: queryString ? `${url}?${queryString}` : url,
    method: 'GET',
  })
}

export const fetchStockHistoryDetail = async (
  stockCode: string,
  changerNames: string,
): Promise<StockDetailData> => {
  const url = buildApiUrl(API_ENDPOINTS.STOCK_HISTORY_DETAIL)
  const queryString = buildQueryString({ code: stockCode, name: changerNames })
  return request<StockDetailData>({
    url: `${url}?${queryString}`,
    method: 'GET',
  })
}

export const fetchBacktestOverview = async (
  params?: BacktestQueryParams,
): Promise<BacktestOverview> => {
  const url = buildApiUrl(API_ENDPOINTS.BACKTEST_OVERVIEW)
  const queryString = params ? buildQueryString(params) : ''
  return request<BacktestOverview>({
    url: queryString ? `${url}?${queryString}` : url,
    method: 'GET',
  })
}

export const fetchBacktestEvents = async (
  params: BacktestQueryParams,
): Promise<PageResult<BacktestEventItem>> => {
  const url = buildApiUrl(API_ENDPOINTS.BACKTEST_EVENTS)
  const queryString = buildQueryString(params)
  return request<PageResult<BacktestEventItem>>({
    url: queryString ? `${url}?${queryString}` : url,
    method: 'GET',
  })
}

export const fetchBacktestEventDetail = async (
  eventId: number,
): Promise<BacktestEventDetail> => {
  const url = buildApiUrl(API_ENDPOINTS.BACKTEST_EVENT_DETAIL, { eventId: String(eventId) })
  return request<BacktestEventDetail>({
    url,
    method: 'GET',
  })
}

export const fetchBacktestStockSummary = async (
  stockCode: string,
): Promise<StockBacktestSummary> => {
  const url = buildApiUrl(API_ENDPOINTS.BACKTEST_STOCK_SUMMARY, { stockCode })
  return request<StockBacktestSummary>({
    url,
    method: 'GET',
  })
}

export const triggerBacktestRebuild = async (
  mode: 'incremental' | 'full',
): Promise<BacktestRebuildResponse> => {
  const url = buildApiUrl(API_ENDPOINTS.BACKTEST_REBUILD)
  const queryString = buildQueryString({ mode })
  return request<BacktestRebuildResponse>({
    url: queryString ? `${url}?${queryString}` : url,
    method: 'POST',
  })
}
