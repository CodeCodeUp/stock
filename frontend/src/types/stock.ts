/**
 * Stock Data Types
 * TypeScript interfaces and types for stock-related data
 */

// Basic stock data item interface
export interface StockDataItem {
  totalIncrease: number
  totalDecrease: number
  tradeDate: string
  stockCode: string
  stockName: string
  changerName: string
  changerPosition: string
  chartLoading?: boolean
  stockDetail?: StockDetailData | null
  expanded?: boolean
  price?: number
}

// Price data interface
export interface PriceDataItem {
  trackTime: string
  currentPrice: number
}

// Mark item interface for trading records
export interface MarkItem {
  price: number
  tradeDate: string
  stockCode: string | null
  stockName: string | null
  changeType: string
  totalPrice: number
  changerName: string | null
  changerPosition: string | null
}

// Stock detail data interface
export interface StockDetailData {
  priceData: PriceDataItem[]
  marks: MarkItem[]
}

// API request parameters
export interface StockChangesParams {
  start: string
  end: string
  changeType?: string
  changeSort?: string
  totalPrice?: number
}

// Chart mark data interface
export interface ChartMarkData {
  name: string
  coord: [string, number]
  value: string
  itemStyle: { color: string }
}

// Date range shortcut interface
export interface DateShortcut {
  text: string
  value: () => [Date, Date]
}

// Sort column interface
export interface SortColumn {
  prop: string
  order: string | null
}

// History detail props interface
export interface HistoryDetailProps {
  visible: boolean
  stockCode: string
  stockName: string
  changerNames: string
}

// Change types
export type ChangeType = '增持' | '减持' | ''
export type SortOrder = 'asc' | 'desc' | ''

// Table header style interface
export interface TableHeaderStyle {
  background: string
  color: string
  fontWeight: string
}
