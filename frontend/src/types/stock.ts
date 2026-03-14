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

export interface BacktestOverview {
  totalEvents: number
  totalStocks: number
  avgSignalScore: number
  avgBacktestScore: number
  winRate20d: number
  avgReturn20d: number
  hit10PctRate60d: number
  latestSignalDate: string | null
}

export interface BacktestEventItem {
  eventId: number
  stockCode: string
  stockName: string
  signalDate: string
  eventScope: string
  increaseCount: number
  increaseAmount: number
  increaseRatioSum: number
  increaseRatioMax: number
  changerCount: number
  changerNames: string
  positionTags: string
  hasSameDayDecrease: boolean
  sameDayDecreaseAmount: number
  consecutiveIncreaseDays: number
  signalScore: number
  backtestScore: number
  return5d?: number | null
  return10d?: number | null
  return20d?: number | null
  return60d?: number | null
}

export interface BacktestMetricItem {
  horizonDays: number
  entryDate: string
  entryPrice: number
  entryPriceType: string
  exitDate: string
  exitPrice: number
  returnPct: number
  maxReturnPct: number
  maxDrawdownPct: number
  volatilityPct: number | null
  hit3pctFlag: boolean
  hit5pctFlag: boolean
  hit10pctFlag: boolean
  isPositiveFlag: boolean
  barsCount: number
}

export interface BacktestPriceBar {
  tradeDate: string
  openPrice: number
  closePrice: number
  highPrice: number
  lowPrice: number
}

export interface StockBacktestSummary {
  stockCode: string
  stockName: string
  sampleEventCount: number
  winRate5d: number | null
  winRate10d: number | null
  winRate20d: number | null
  avgReturn5d: number | null
  avgReturn10d: number | null
  avgReturn20d: number | null
  medianReturn20d: number | null
  avgMaxDrawdown20d: number | null
  hit5pctRate20d: number | null
  hit10pctRate60d: number | null
  historicalResponseScore: number
  backtestScore: number
  lastEventDate: string | null
}

export interface BacktestEventDetail {
  event: BacktestEventItem
  stockSummary: StockBacktestSummary
  metrics: BacktestMetricItem[]
  priceBars: BacktestPriceBar[]
  marks: MarkItem[]
}

export interface BacktestRebuildResponse {
  mode: 'incremental' | 'full'
  status: string
  message: string
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

export interface BacktestQueryParams {
  start?: string
  end?: string
  keyword?: string
  minIncreaseAmount?: number
  minSignalScore?: number
  minBacktestScore?: number
  hasSameDayDecrease?: boolean
  sortBy?: BacktestSortBy
  sortOrder?: SortOrder
  page?: number
  pageSize?: number
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
export type BacktestSortBy =
  | 'signalDate'
  | 'increaseAmount'
  | 'signalScore'
  | 'backtestScore'
  | 'return20d'
  | 'return60d'

export interface TableHeaderStyle {
  background: string
  color: string
  fontWeight: string
  borderBottom: string
}
