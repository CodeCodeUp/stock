/**
 * Formatting Utilities
 * Common formatting functions for numbers, dates, etc.
 */

/**
 * Format number with Chinese locale
 * @param num - Number to format
 * @returns Formatted number string
 */
export const formatNumber = (num: number | bigint): string => {
  return new Intl.NumberFormat('zh-CN').format(num)
}

/**
 * Format date to local date string
 * @param date - Date to format
 * @returns Formatted date string
 */
export const formatDate = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return dateObj.toLocaleDateString()
}

/**
 * Format time to local time string
 * @param date - Date to format
 * @returns Formatted time string
 */
export const formatTime = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  return dateObj.toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * Format date and time together
 * @param date - Date to format
 * @returns Formatted date and time string
 */
export const formatDateTime = (date: Date | string): string => {
  const dateObj = typeof date === 'string' ? new Date(date) : date
  const dateStr = formatDate(dateObj)
  const timeStr = formatTime(dateObj)
  return `${dateStr} ${timeStr}`
}

/**
 * Format ISO date string to YYYY-MM-DD
 * @param date - Date to format
 * @returns Formatted date string
 */
export const formatISODate = (date: Date): string => {
  return date.toISOString().split('T')[0]
}

/**
 * Get current month date range
 * @returns Array with start and end date strings
 */
export const getCurrentMonthRange = (): [string, string] => {
  const end = new Date()
  const start = new Date()
  start.setDate(1) // First day of current month
  
  return [formatISODate(start), formatISODate(end)]
}

/**
 * Get date range for specified number of days ago
 * @param days - Number of days ago
 * @returns Array with start and end date strings
 */
export const getDateRangeFromDaysAgo = (days: number): [string, string] => {
  const end = new Date()
  const start = new Date()
  start.setTime(start.getTime() - 3600 * 1000 * 24 * days)
  
  return [formatISODate(start), formatISODate(end)]
}

/**
 * Get date range for specified number of months ago
 * @param months - Number of months ago
 * @returns Array with start and end date strings
 */
export const getDateRangeFromMonthsAgo = (months: number): [string, string] => {
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - months)
  
  return [formatISODate(start), formatISODate(end)]
}
