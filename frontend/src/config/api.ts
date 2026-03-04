/**
 * API Configuration
 * Centralized API endpoints and configuration
 */

// Base API URL - empty in production (nginx proxies), configurable for dev
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

// API Endpoints
export const API_ENDPOINTS = {
  // Stock data endpoints
  STOCK_CHANGES: '/api/stocks/changes',
  STOCK_CHART: '/api/stocks/{stockCode}/chart',
  STOCK_HISTORY_DETAIL: '/data/api/detail/chart',
} as const

// API Configuration
export const API_CONFIG = {
  timeout: 10000, // 10 seconds
  retries: 3,
  retryDelay: 1000, // 1 second
} as const

// Helper function to build full URL
export const buildApiUrl = (endpoint: string, params?: Record<string, string>): string => {
  let url = `${API_BASE_URL}${endpoint}`

  // Replace path parameters
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url = url.replace(`{${key}}`, value)
    })
  }

  return url
}

// Helper function to build query string
export const buildQueryString = (params: any): string => {
  const searchParams = new URLSearchParams()

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      searchParams.append(key, String(value))
    }
  })

  return searchParams.toString()
}
