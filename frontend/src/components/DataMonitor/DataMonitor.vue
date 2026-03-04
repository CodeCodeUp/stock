<template>
  <div class="data-monitor">
    <div class="monitor-header">
      <div class="title">
        <h2>数据监控</h2>
        <div class="subtitle">变动情况</div>
      </div>

      <div class="filter-controls">
        <div class="filter-row">
          <div class="filter-item">
            <label class="filter-label">日期范围</label>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              :shortcuts="shortcuts"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              class="date-picker"
            />
          </div>

          <div class="filter-item">
            <label class="filter-label">变动类型</label>
            <el-select v-model="changeType" placeholder="变动类型" class="change-type-select">
              <el-option label="全部" value=""></el-option>
              <el-option label="增持" value="增持"></el-option>
              <el-option label="减持" value="减持"></el-option>
            </el-select>
          </div>

          <div class="filter-item">
            <label class="filter-label">金额筛选</label>
            <el-input
              v-model.number="totalPrice"
              placeholder="请输入金额"
              type="number"
              :min="0"
              :step="1000"
              clearable
              class="amount-input"
            >
              <template #prepend>￥</template>
            </el-input>
          </div>

          <div class="filter-item">
            <el-button type="primary" @click="fetchData" :loading="loading" class="search-button">
              <el-icon><Search /></el-icon>
              搜索
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <StockTable
      :display-data="displayData"
      :loading="loading"
      :header-style="headerStyle"
      :current-page="currentPage"
      :page-size="pageSize"
      :total-count="totalCount"
      :stock-data="stockData"
      @expand-change="handleExpandChange"
      @sort-change="handleSortChange"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />
  </div>
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { useStockData } from '@/composables/useStockData'
import { useChart } from '@/composables/useChart'
import StockTable from './StockTable.vue'

export default defineComponent({
  name: 'DataMonitor',
  components: {
    StockTable,
    Search,
  },
  setup() {
    // Use composables
    const stockDataComposable = useStockData()
    const chartComposable = useChart()

    return {
      // Stock data composable
      ...stockDataComposable,

      // Chart composable
      ...chartComposable,
    }
  },
})
</script>

<style scoped>
.data-monitor {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  padding: 20px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  border-bottom: 1px solid #eaeaea;
  padding-bottom: 16px;
}

.title h2 {
  margin: 0;
  font-weight: 600;
  color: #303133;
  font-size: 22px;
}

.subtitle {
  color: #909399;
  font-size: 14px;
  margin-top: 5px;
}

.filter-controls {
  width: 100%;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 20px;
  margin-top: 10px;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 0;
}

.filter-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  margin-bottom: 0;
  white-space: nowrap;
}

.date-picker {
  width: 280px;
}

.change-type-select {
  width: 140px;
}

.amount-input {
  width: 180px;
}

.search-button {
  height: 40px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  gap: 6px;
}

/* 手机端适配 */
@media (max-width: 768px) {
  .data-monitor {
    padding: 15px;
    border-radius: 0;
    box-shadow: none;
  }

  .monitor-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .filter-controls {
    width: 100%;
  }

  .filter-row {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }

  .filter-item {
    width: 100%;
  }

  .date-picker,
  .change-type-select,
  .amount-input {
    width: 100%;
  }

  .search-button {
    width: 100%;
    height: 44px;
    justify-content: center;
    font-size: 16px;
  }

  .filter-label {
    font-size: 15px;
    font-weight: 600;
  }
}

/* 小屏手机适配 */
@media (max-width: 480px) {
  .data-monitor {
    padding: 10px;
  }

  .title h2 {
    font-size: 20px;
  }

  .subtitle {
    font-size: 13px;
  }

  .filter-row {
    gap: 12px;
  }

  .search-button {
    height: 48px;
    font-size: 16px;
  }
}
</style>
