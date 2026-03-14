const pad = (value: number): string => String(value).padStart(2, '0')

const normalizeDate = (date: Date | string): Date => (date instanceof Date ? date : new Date(date))

const formatFixedNumber = (value: number, digits: number): string => {
  return new Intl.NumberFormat('zh-CN', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  }).format(value)
}

export const formatNumber = (num: number | bigint | null | undefined): string => {
  if (num === null || num === undefined || Number.isNaN(Number(num))) {
    return '--'
  }
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 2 }).format(num)
}

export const formatCurrency = (num: number | null | undefined): string => {
  if (num === null || num === undefined || Number.isNaN(num)) {
    return '--'
  }

  const absValue = Math.abs(num)
  const sign = num < 0 ? '-' : ''

  if (absValue >= 100000000) {
    return `${sign}¥${formatFixedNumber(absValue / 100000000, 3)}亿`
  }

  if (absValue >= 10000) {
    return `${sign}¥${formatFixedNumber(absValue / 10000, 3)}万`
  }

  return `${sign}¥${formatNumber(absValue)}`
}

export const formatPercentage = (
  value: number | null | undefined,
  digits = 2,
  includeSign = true,
): string => {
  if (value === null || value === undefined || Number.isNaN(value)) {
    return '--'
  }

  const percentage = value * 100
  const sign = includeSign && percentage > 0 ? '+' : ''
  return `${sign}${formatFixedNumber(percentage, digits)}%`
}

export const formatDate = (date: Date | string | null | undefined): string => {
  if (!date) {
    return '--'
  }

  if (typeof date === 'string') {
    const trimmed = date.trim()
    if (!trimmed) {
      return '--'
    }
    if (/^\d{4}-\d{2}-\d{2}$/.test(trimmed)) {
      return trimmed
    }
    if (trimmed.length >= 10) {
      return trimmed.slice(0, 10)
    }
  }

  const dateObj = normalizeDate(date)
  return `${dateObj.getFullYear()}-${pad(dateObj.getMonth() + 1)}-${pad(dateObj.getDate())}`
}

export const formatTime = (date: Date | string): string => {
  const dateObj = normalizeDate(date)
  return `${pad(dateObj.getHours())}:${pad(dateObj.getMinutes())}`
}

export const formatDateTime = (date: Date | string): string => {
  if (typeof date === 'string') {
    const trimmed = date.trim()
    if (!trimmed) {
      return '--'
    }
    if (trimmed.includes('T')) {
      return `${trimmed.slice(0, 10)} ${trimmed.slice(11, 16)}`
    }
    if (trimmed.includes(' ')) {
      return `${trimmed.slice(0, 10)} ${trimmed.slice(11, 16)}`
    }
  }

  const dateObj = normalizeDate(date)
  return `${formatDate(dateObj)} ${formatTime(dateObj)}`
}

export const formatISODate = (date: Date): string => {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export const getCurrentMonthRange = (): [string, string] => {
  const end = new Date()
  const start = new Date()
  start.setDate(1)
  return [formatISODate(start), formatISODate(end)]
}

export const getDateRangeFromDaysAgo = (days: number): [string, string] => {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - days)
  return [formatISODate(start), formatISODate(end)]
}

export const getDateRangeFromMonthsAgo = (months: number): [string, string] => {
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - months)
  return [formatISODate(start), formatISODate(end)]
}

export const formatDateRange = (range: string[]): string => {
  if (!range || range.length !== 2) {
    return '未选择'
  }
  return `${formatDate(range[0])} - ${formatDate(range[1])}`
}
