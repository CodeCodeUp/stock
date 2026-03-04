<template>
  <div class="table-container">
    <el-table
      :data="displayData"
      stripe
      style="width: 100%"
      :header-cell-style="headerStyle"
      v-loading="loading"
      @expand-change="handleExpandChange"
      @sort-change="handleSortChange"
      :row-key="rowKey"
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
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="totalCount"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <div class="empty-data" v-if="totalCount === 0 && !loading">
      <el-empty description="暂无数据，请选择日期范围查询" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import { formatNumber } from '@/utils/formatters'
import type { SortColumn, StockDataItem, TableHeaderStyle } from '@/types/stock'
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
  },
  emits: ['expand-change', 'sort-change', 'size-change', 'current-change'],
  setup(_, { emit }) {
    const rowKey = (row: StockDataItem) => `${row.stockCode}-${row.tradeDate}`

    const handleExpandChange = (row: StockDataItem, expandedRows: StockDataItem[]) => {
      emit('expand-change', row, expandedRows)
    }

    const handleSortChange = (column: SortColumn) => {
      emit('sort-change', column)
    }

    const handleSizeChange = (size: number) => {
      emit('size-change', size)
    }

    const handleCurrentChange = (page: number) => {
      emit('current-change', page)
    }

    return {
      formatNumber,
      rowKey,
      handleExpandChange,
      handleSortChange,
      handleSizeChange,
      handleCurrentChange,
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
