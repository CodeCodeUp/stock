<template>
  <div class="table-shell">
    <div class="table-meta">
      <p class="table-title">股票列表</p>
      <p class="table-desc">按股票聚合展示区间内的增减持情况。</p>
    </div>

    <div class="table-container">
        <el-table
          :data="displayData"
          stripe
          style="width: 100%"
          :header-cell-style="headerStyle"
          scrollbar-always-on
          v-loading="loading"
          @sort-change="handleSortChange"
          :row-key="rowKey"
        >
        <el-table-column type="expand">
          <template #default="props">
            <StockChart :row="props.row" :date-range="dateRange" />
          </template>
        </el-table-column>

        <el-table-column label="股票" min-width="170" show-overflow-tooltip>
          <template #default="scope">
            <div class="stock-cell">
              <strong>{{ scope.row.stockName }}</strong>
              <span>{{ scope.row.stockCode }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="latestTradeDate" label="最近变动" width="110" />
        <el-table-column label="覆盖区间" min-width="170" show-overflow-tooltip>
          <template #default="scope">
            {{ scope.row.firstTradeDate }} - {{ scope.row.latestTradeDate }}
          </template>
        </el-table-column>
        <el-table-column prop="changeCount" label="次数" width="76" />

        <el-table-column label="增持金额" width="120">
          <template #default="scope">
            <span class="increase-text">{{ formatCurrency(scope.row.totalIncrease) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="减持金额" width="120">
          <template #default="scope">
            <span class="decrease-text">{{ formatCurrency(scope.row.totalDecrease) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="totalAmount" label="累计金额" width="128" sortable="custom">
          <template #default="scope">
            <span class="total-amount">{{ formatCurrency(scope.row.totalAmount) }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="changerName" label="变动人" min-width="140" show-overflow-tooltip />
        <el-table-column prop="changerPosition" label="职位" min-width="140" show-overflow-tooltip />
      </el-table>
    </div>

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
      <el-empty :description="emptyDescription" />
    </div>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import StockChart from './StockChart.vue'
import { formatCurrency } from '@/utils/formatters'
import type { SortColumn, StockDataItem, TableHeaderStyle } from '@/types/stock'

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
    dateRange: {
      type: Array as PropType<string[]>,
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
    emptyDescription: {
      type: String,
      default: '暂无符合条件的数据',
    },
  },
  emits: ['sort-change', 'size-change', 'current-change'],
  setup(_, { emit }) {
    const rowKey = (row: StockDataItem) => row.uiKey ?? row.stockCode

    return {
      formatCurrency,
      rowKey,
      handleSortChange: (column: SortColumn) => emit('sort-change', column),
      handleSizeChange: (size: number) => emit('size-change', size),
      handleCurrentChange: (page: number) => emit('current-change', page),
    }
  },
})
</script>

<style scoped>
.table-shell {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.table-meta {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
}

.table-title {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
  color: var(--text-primary);
}

.table-desc {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.table-container {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  overflow-x: auto;
  overflow-y: hidden;
  border-radius: 28px;
  border: 1px solid var(--panel-border);
  background: rgba(255, 255, 255, 0.94);
}

.table-container :deep(.el-table) {
  width: 100% !important;
}

.table-container :deep(.el-table__expanded-cell) {
  padding: 12px !important;
  background: transparent;
}

.stock-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stock-cell strong {
  color: var(--text-primary);
}

.stock-cell span {
  color: var(--text-muted);
  font-size: 12px;
  letter-spacing: 0.08em;
}

.increase-text {
  color: var(--increase-color);
  font-weight: 600;
}

.decrease-text {
  color: var(--decrease-color);
  font-weight: 600;
}

.total-amount {
  color: var(--text-primary);
  font-weight: 700;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  overflow-x: auto;
}

.pagination-container :deep(.el-pagination) {
  flex-wrap: wrap;
  justify-content: flex-end;
  row-gap: 8px;
}

.empty-data {
  padding: 48px 0 8px;
}

@media (max-width: 768px) {
  .table-meta {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
