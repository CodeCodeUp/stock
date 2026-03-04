/**
 * Chart Utilities
 * Common chart configuration and helper functions
 */

import * as echarts from 'echarts'
import type { ChartMarkData, MarkItem, PriceDataItem } from '@/types/stock'
import { formatNumber, formatDateTime } from './formatters'

/**
 * Default chart colors
 */
export const CHART_COLORS = {
  INCREASE: '#f56c6c', // Red for increase
  DECREASE: '#67c23a', // Green for decrease
  LINE: '#409EFF', // Blue for line
} as const

/**
 * Create chart mark data from stock marks
 * @param marks - Array of mark items
 * @param priceData - Array of price data
 * @param dates - Array of formatted dates
 * @param prices - Array of prices
 * @returns Array of chart mark data
 */
export const createChartMarkData = (
  marks: MarkItem[],
  priceData: PriceDataItem[],
  dates: string[],
  prices: number[],
): ChartMarkData[] => {
  const markData: ChartMarkData[] = []

  marks.forEach((mark) => {
    // Find all price data points for the same date
    const sameDayPrices = priceData.filter(
      (price) => new Date(price.trackTime).toISOString().split('T')[0] === mark.tradeDate,
    )

    if (sameDayPrices.length > 0) {
      // Find the closest price data point
      let closestPriceData = sameDayPrices[0]
      let closestPriceIndex = priceData.indexOf(closestPriceData)

      // If mark has specific price, find the closest match
      if (mark.price) {
        let minDiff = Math.abs(sameDayPrices[0].currentPrice - mark.price)

        for (const priceDataItem of sameDayPrices) {
          const priceDiff = Math.abs(priceDataItem.currentPrice - mark.price)
          if (priceDiff < minDiff) {
            minDiff = priceDiff
            closestPriceData = priceDataItem
            closestPriceIndex = priceData.indexOf(priceDataItem)
          }
        }
      }

      if (closestPriceIndex >= 0) {
        markData.push({
          name: mark.changeType,
          coord: [dates[closestPriceIndex], prices[closestPriceIndex]],
          value: `${formatNumber(mark.totalPrice)} (¥${mark.price})`,
          itemStyle: {
            color: mark.changeType === '增持' ? CHART_COLORS.INCREASE : CHART_COLORS.DECREASE,
          },
        })
      }
    }
  })

  return markData
}

/**
 * Prepare chart data from stock detail
 * @param stockDetail - Stock detail data
 * @returns Object with dates, prices, and mark data
 */
export const prepareChartData = (stockDetail: {
  priceData: PriceDataItem[]
  marks?: MarkItem[]
}) => {
  const dates: string[] = []
  const prices: number[] = []

  // Process price data
  stockDetail.priceData.forEach((item) => {
    const dateTime = formatDateTime(item.trackTime)
    dates.push(dateTime)
    prices.push(item.currentPrice)
  })

  // Process marks if available
  const markData = stockDetail.marks
    ? createChartMarkData(stockDetail.marks, stockDetail.priceData, dates, prices)
    : []

  return { dates, prices, markData }
}

/**
 * Create chart tooltip formatter
 * @param markData - Array of chart mark data
 * @returns Tooltip formatter function
 */
export const createTooltipFormatter = (markData: ChartMarkData[]) => {
  return function (params: { name: string; marker: string; value: number }[]) {
    let result = params[0].name + '<br/>'
    result += params[0].marker + ' 价格: ' + params[0].value

    // Find if there's a mark point at this position
    const markInfo = markData.find((mark) => mark.coord[0] === params[0].name)
    if (markInfo) {
      result +=
        '<br/><span style="color:' +
        markInfo.itemStyle.color +
        '">● ' +
        markInfo.name +
        ': ' +
        markInfo.value +
        '</span>'
    }

    return result
  }
}

/**
 * Create default chart option
 * @param title - Chart title
 * @param dates - Array of dates
 * @param prices - Array of prices
 * @param markData - Array of mark data
 * @returns ECharts option object
 */
export const createChartOption = (
  title: string,
  dates: string[],
  prices: number[],
  markData: ChartMarkData[],
) => {
  return {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 14,
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    tooltip: {
      trigger: 'axis',
      formatter: createTooltipFormatter(markData),
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLabel: {
        interval: Math.floor(dates.length / 8),
        formatter: function (value: string) {
          return value.split(' ')[0] + '\n' + value.split(' ')[1]
        },
      },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLabel: {
        formatter: '{value}',
      },
    },
    dataZoom: [
      {
        type: 'inside',
        start: 0,
        end: 100,
      },
      {
        start: 0,
        end: 100,
      },
    ],
    series: [
      {
        type: 'line',
        data: prices,
        smooth: true,
        lineStyle: {
          width: 2,
          color: CHART_COLORS.LINE,
        },
        markPoint: {
          symbol: 'pin',
          symbolSize: 40,
          data: markData,
        },
      },
    ],
  }
}

/**
 * Initialize chart instance
 * @param domElement - DOM element to render chart
 * @param option - Chart option
 * @returns ECharts instance
 */
export const initChart = (domElement: HTMLElement, option: any): echarts.ECharts => {
  const chartInstance = echarts.init(domElement)
  chartInstance.setOption(option)
  return chartInstance
}
