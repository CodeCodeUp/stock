<template>
  <div class="stock-detail-row" v-loading="row.chartLoading">
    <div class="chart-container">
      <div :id="`chart-${row.stockCode}-${row.tradeDate}`" class="stock-chart"></div>
    </div>

    <div class="history-button-container">
      <el-button type="primary" size="small" @click="showHistoryDetail">
        查看所有历史数据
      </el-button>
    </div>

    <div
      class="marks-detail"
      v-if="row.stockDetail && row.stockDetail.marks && row.stockDetail.marks.length > 0"
    >
      <h4>增减持记录</h4>
      <el-table :data="row.stockDetail.marks" stripe size="small" style="width: 100%">
        <el-table-column prop="tradeDate" label="交易日期" width="120" />
        <el-table-column prop="changeType" label="变动类型" width="100">
          <template #default="scope">
            <span :class="scope.row.changeType === '增持' ? 'increase' : 'decrease'">
              {{ scope.row.changeType }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="交易金额" width="150">
          <template #default="scope">
            <span :class="scope.row.changeType === '增持' ? 'increase' : 'decrease'">
              {{ formatNumber(scope.row.totalPrice) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="price" label="成交价" width="120" />
        <el-table-column prop="changerName" label="变动人" />
        <el-table-column prop="changerPosition" label="职位" />
      </el-table>
    </div>

    <StockHistoryDetail
      v-model:visible="historyDetailVisible"
      :stock-code="selectedStockCode"
      :stock-name="selectedStockName"
      :changer-names="selectedChangerNames"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent, ref, type PropType } from 'vue'
import { formatNumber } from '@/utils/formatters'
import type { StockDataItem, MarkItem } from '@/types/stock'
import StockHistoryDetail from '../StockHistoryDetail.vue'

export default defineComponent({
  name: 'StockChart',
  components: {
    StockHistoryDetail,
  },
  props: {
    row: {
      type: Object as PropType<StockDataItem>,
      required: true,
    },
  },
  setup(props) {
    // History detail state
    const historyDetailVisible = ref(false)
    const selectedStockCode = ref('')
    const selectedStockName = ref('')
    const selectedChangerNames = ref('')

    /**
     * Show history detail dialog
     */
    const showHistoryDetail = () => {
      selectedStockCode.value = props.row.stockCode
      selectedStockName.value = props.row.stockName

      // Extract changer names
      if (props.row.changerName) {
        selectedChangerNames.value = props.row.changerName
      } else if (
        props.row.stockDetail &&
        props.row.stockDetail.marks &&
        props.row.stockDetail.marks.length > 0
      ) {
        // Extract all unique changer names from marks
        const uniqueChangers = [
          ...new Set(
            props.row.stockDetail.marks
              .filter((mark: MarkItem) => mark.changerName)
              .map((mark: MarkItem) => mark.changerName),
          ),
        ]
        selectedChangerNames.value = uniqueChangers.join(',')
      } else {
        selectedChangerNames.value = ''
      }

      historyDetailVisible.value = true
    }

    return {
      formatNumber,
      historyDetailVisible,
      selectedStockCode,
      selectedStockName,
      selectedChangerNames,
      showHistoryDetail,
    }
  },
})
</script>

<style scoped>
.stock-detail-row {
  padding: 20px;
  margin-left: 50px;
  background-color: #fafafa;
  border-radius: 4px;
}

.chart-container {
  width: 100%;
  height: 300px;
  margin-bottom: 20px;
}

.stock-chart {
  width: 100%;
  height: 100%;
}

.history-button-container {
  margin-bottom: 20px;
}

.marks-detail {
  margin-top: 20px;
}

.marks-detail h4 {
  margin-bottom: 16px;
  font-weight: 500;
  color: #303133;
  font-size: 15px;
}

.increase {
  color: #f56c6c;
  font-weight: 600;
}

.decrease {
  color: #67c23a;
  font-weight: 600;
}

@media (max-width: 768px) {
  .chart-container {
    height: 250px;
  }
}
</style>
