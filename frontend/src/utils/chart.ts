import { LineChart } from 'echarts/charts'
import {
  DataZoomComponent,
  GridComponent,
  MarkPointComponent,
  TitleComponent,
  TooltipComponent,
} from 'echarts/components'
import * as echarts from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import type { ECharts, EChartsCoreOption } from 'echarts/core'
import type { ChartMarkData, MarkItem, PriceDataItem } from '@/types/stock'
import { formatCurrency, formatDate, formatDateTime } from './formatters'

echarts.use([
  LineChart,
  GridComponent,
  TooltipComponent,
  DataZoomComponent,
  MarkPointComponent,
  TitleComponent,
  CanvasRenderer,
])

export const CHART_COLORS = {
  increase: '#d14836',
  decrease: '#15825d',
  line: '#2350a8',
  fill: 'rgba(35, 80, 168, 0.12)',
  axis: '#6b7280',
  split: 'rgba(148, 163, 184, 0.18)',
} as const

const buildDatePointMap = (priceData: PriceDataItem[]) => {
  const dateMap = new Map<string, Array<{ index: number; price: number }>>()

  priceData.forEach((item, index) => {
    const key = formatDate(item.trackTime)
    const points = dateMap.get(key) ?? []
    points.push({ index, price: item.currentPrice })
    dateMap.set(key, points)
  })

  return dateMap
}

export const createChartMarkData = (
  marks: MarkItem[],
  priceData: PriceDataItem[],
  dates: string[],
  prices: number[],
): ChartMarkData[] => {
  const dateMap = buildDatePointMap(priceData)

  return marks.reduce<ChartMarkData[]>((result, mark) => {
    const points = dateMap.get(mark.tradeDate)
    if (!points || points.length === 0) {
      return result
    }

    let targetPoint = points[0]
    if (mark.price !== null && mark.price !== undefined) {
      targetPoint = points.reduce((closest, current) => {
        const currentDiff = Math.abs(current.price - mark.price!)
        const closestDiff = Math.abs(closest.price - mark.price!)
        return currentDiff < closestDiff ? current : closest
      }, points[0])
    }

    result.push({
      name: mark.changeType,
      coord: [dates[targetPoint.index], prices[targetPoint.index]],
      value: `${formatCurrency(mark.totalPrice)} / ${formatCurrency(mark.price)}`,
      itemStyle: {
        color: mark.changeType === '增持' ? CHART_COLORS.increase : CHART_COLORS.decrease,
      },
    })

    return result
  }, [])
}

export const prepareChartData = (stockDetail: {
  priceData: PriceDataItem[]
  marks?: MarkItem[]
}) => {
  const dates = stockDetail.priceData.map((item) => formatDateTime(item.trackTime))
  const prices = stockDetail.priceData.map((item) => item.currentPrice)
  const markData = stockDetail.marks
    ? createChartMarkData(stockDetail.marks, stockDetail.priceData, dates, prices)
    : []

  return { dates, prices, markData }
}

export const createTooltipFormatter = (markData: ChartMarkData[]) => {
  return function (params: Array<{ name: string; marker: string; value: number }>) {
    const point = params[0]
    let result = `${point.name}<br/>${point.marker} 价格: ${point.value}`
    const markInfo = markData.find((mark) => mark.coord[0] === point.name)

    if (markInfo) {
      result += `<br/><span style="color:${markInfo.itemStyle.color}">● ${markInfo.name}: ${markInfo.value}</span>`
    }

    return result
  }
}

export const createChartOption = (
  title: string,
  dates: string[],
  prices: number[],
  markData: ChartMarkData[],
): EChartsCoreOption => ({
  title: {
    text: title,
    left: 'center',
    textStyle: {
      fontSize: 14,
      fontWeight: 600,
      color: '#172033',
    },
  },
  grid: {
    top: 56,
    left: 24,
    right: 24,
    bottom: 40,
    containLabel: true,
  },
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(15, 23, 42, 0.92)',
    borderWidth: 0,
    textStyle: {
      color: '#f8fafc',
    },
    formatter: createTooltipFormatter(markData),
  },
  xAxis: {
    type: 'category',
    data: dates,
    boundaryGap: false,
    axisLine: {
      lineStyle: { color: CHART_COLORS.split },
    },
    axisLabel: {
      color: CHART_COLORS.axis,
      interval: Math.max(0, Math.floor(dates.length / 8)),
      formatter: (value: string) => `${value.split(' ')[0]}
${value.split(' ')[1]}`,
    },
  },
  yAxis: {
    type: 'value',
    scale: true,
    axisLabel: {
      color: CHART_COLORS.axis,
    },
    splitLine: {
      lineStyle: {
        color: CHART_COLORS.split,
      },
    },
  },
  dataZoom: [
    {
      type: 'inside',
      start: 0,
      end: 100,
    },
    {
      height: 18,
      bottom: 10,
      start: 0,
      end: 100,
    },
  ],
  series: [
    {
      type: 'line',
      data: prices,
      smooth: true,
      showSymbol: false,
      lineStyle: {
        width: 2.5,
        color: CHART_COLORS.line,
      },
      areaStyle: {
        color: CHART_COLORS.fill,
      },
      markPoint: {
        symbol: 'pin',
        symbolSize: 42,
        data: markData,
      },
    },
  ],
})

export const initChart = (domElement: HTMLElement, option: EChartsCoreOption): ECharts => {
  const chartInstance = echarts.init(domElement)
  chartInstance.setOption(option)
  return chartInstance
}
