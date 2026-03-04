<template>
  <div class="table-container">
    <el-table
      :data="displayData"
      stripe
      style="width: 100%"
      :header-cell-style="headerStyle"
      v-loading="loading"
      @expand-change="$emit('expand-change', $event)"
      @sort-change="$emit('sort-change', $event)"
      :row-key="(row: any) => row.stockCode + row.tradeDate"
    >
      <el-table-column type="expand">
        <template #default="props">
          <StockChart :row="props.row" />
        </template>
      </el-table-column>

      <el-table-column prop="tradeDate" label="交易日期" width="120" />
      <el-table-column prop="stockCode" label="股票代码" width="120" />
      <el-table-column prop="stockName" label="股票名称" width="120" />
      <el-table-column prop="changeAmount" label="变动数量" width="160" sortable="custom">
        <template #default="scope">
          <span v-if="scope.row.totalIncrease != 0" class="increase">
            {{ formatNumber(scope.row.totalIncrease) }}
          </span>
          <span v-if="scope.row.totalDecrease != 0" class="decrease">
            {{ formatNumber(scope.row.totalDecrease) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="changerName" label="变动人" />
      <el-table-column prop="changerPosition" label="职位" />
    </el-table>

    <!-- Pagination -->
    <div class="pagination-container" v-if="totalCount > 0">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalCount"
        @size-change="$emit('size-change', $event)"
        @current-change="$emit('current-change', $event)"
      />
    </div>

    <div class="empty-data" v-if="stockData.length === 0 && !loading">
      <el-empty description="暂无数据，请选择日期范围查询" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import { formatNumber } from '@/utils/formatters'
import type { StockDataItem, TableHeaderStyle } from '@/types/stock'
import StockChart from './StockChart.vue'

export default defineComponent({
  name: 'StockTable',
  components: {
    StockChart,
  },
  props: {
    displayData: {
      type: Array as PropType<StockDataItem[]>,
      required: true,
    },
    loading: {
      type: Boolean,
      required: true,
    },
    headerStyle: {
      type: Object as PropType<TableHeaderStyle>,
      required: true,
    },
    currentPage: {
      type: Number,
      required: true,
    },
    pageSize: {
      type: Number,
      required: true,
    },
    totalCount: {
      type: Number,
      required: true,
    },
    stockData: {
      type: Array as PropType<StockDataItem[]>,
      required: true,
    },
  },
  emits: ['expand-change', 'sort-change', 'size-change', 'current-change'],
  setup() {
    return {
      formatNumber,
    }
  },
})
</script>

<style scoped>
.table-container {
  width: auto;
  max-width: 100%;
  overflow-x: auto;
  margin-top: 20px;
  border-radius: 4px;
  overflow: hidden;
  /* Ensure dialogs can appear above table content */
  position: relative;
  z-index: 1;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
  padding: 10px 0;
}

.empty-data {
  padding: 40px 0;
}

.increase {
  color: #f56c6c;
  font-weight: 600;
}

.decrease {
  color: #67c23a;
  font-weight: 600;
}

@media (max-width: 600px) {
  .table-container {
    overflow-x: scroll;
  }
}
</style>
