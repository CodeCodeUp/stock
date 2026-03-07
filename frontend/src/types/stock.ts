export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export interface PageResult<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

export interface StockDataItem {
  stockCode: string
  stockName: string
  firstTradeDate: string
  latestTradeDate: string
  changeCount: number
  totalIncrease: number
  totalDecrease: number
  totalAmount: number
  changerName: string
  changerPosition: string
  uiKey?: string
  chartLoading?: boolean
  stockDetail?: StockDetailData | null
}

export interface PriceDataItem {
  trackTime: string
  currentPrice: number
}

export interface MarkItem {
  tradeDate: string
  stockCode: string | null
  stockName: string | null
  changeType: string
  totalPrice: number | null
  price: number | null
  changerName: string | null
  changerPosition: string | null
}

export interface StockDetailData {
  priceData: PriceDataItem[]
  marks: MarkItem[]
}

export interface StockChangesParams {
  start: string
  end: string
  changeType?: string
  changeSort?: string
  totalPrice?: number
  page?: number
  pageSize?: number
}

export interface ChartQueryParams {
  start?: string
  end?: string
}

export interface ChartMarkData {
  name: string
  coord: [string, number]
  value: string
  itemStyle: { color: string }
}

export interface DateShortcut {
  text: string
  value: () => [Date, Date]
}

export interface SortColumn {
  prop: string
  order: 'ascending' | 'descending' | null
}

export type ChangeType = '增持' | '减持' | ''
export type SortOrder = 'asc' | 'desc' | ''

export interface TableHeaderStyle {
  background: string
  color: string
  fontWeight: string
  borderBottom: string
}
