/**
 * API Configuration
 * Centralized API endpoints and configuration
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export const API_ENDPOINTS = {
  STOCK_CHANGES: '/api/stocks/changes',
  STOCK_CHART: '/api/stocks/{stockCode}/chart',
  BACKTEST_OVERVIEW: '/api/backtest/overview',
  BACKTEST_EVENTS: '/api/backtest/events',
  BACKTEST_EVENT_DETAIL: '/api/backtest/events/{eventId}',
  BACKTEST_STOCK_SUMMARY: '/api/backtest/stocks/{stockCode}/summary',
  BACKTEST_REBUILD: '/api/backtest/rebuild',
  STOCK_HISTORY_DETAIL: '/data/api/detail/chart',
} as const

export const API_CONFIG = {
  timeout: 10000,
} as const

export const buildApiUrl = (endpoint: string, params?: Record<string, string>): string => {
  let url = `${API_BASE_URL}${endpoint}`

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, value)
    })
  }

  return url
}

export const buildQueryString = (params: object): string => {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value))
    }
  })

  return searchParams.toString()
}
