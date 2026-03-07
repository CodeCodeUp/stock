<template>
  <div class="monitor-page">
    <section class="filter-panel">
      <div class="panel-heading">
        <div>
          <p class="panel-eyebrow">筛选条件</p>
          <h2>快速定位重点股票</h2>
        </div>
        <p class="panel-desc">默认展示本月增持金额超过 10 万的股票。</p>
      </div>

      <div class="filter-grid">
        <div class="filter-item filter-item-wide">
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
            class="field-control"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">变动方向</label>
          <el-select v-model="changeType" placeholder="全部" class="field-control">
            <el-option label="全部" value="" />
            <el-option label="增持" value="增持" />
            <el-option label="减持" value="减持" />
          </el-select>
        </div>

        <div class="filter-item">
          <label class="filter-label">金额门槛</label>
          <el-input
            v-model.number="totalPrice"
            placeholder="例如 100000"
            type="number"
            :min="0"
            :step="1000"
            clearable
            class="field-control"
          >
            <template #prepend>¥</template>
          </el-input>
        </div>

        <div class="filter-action">
          <el-button type="primary" @click="handleSearch" :loading="loading" class="search-button">
            立即查询
          </el-button>
        </div>
      </div>
    </section>

    <section class="table-panel">
      <StockTable
        :display-data="displayData"
        :date-range="dateRange"
        :loading="loading"
        :header-style="headerStyle"
        :current-page="currentPage"
        :page-size="pageSize"
        :total-count="totalCount"
        :empty-description="emptyDescription"
        @sort-change="handleSortChange"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </section>
  </div>
</template>

<script lang="ts">
import { computed, defineComponent } from 'vue'
import StockTable from './StockTable.vue'
import { useStockData } from '@/composables/useStockData'

export default defineComponent({
  name: 'DataMonitor',
  components: {
    StockTable,
  },
  setup() {
    const stockData = useStockData()

    const handleSearch = () => {
      stockData.fetchData(1)
    }

    const emptyDescription = computed(() => {
      if (stockData.loading.value) {
        return '数据加载中'
      }
      return '当前筛选条件下没有找到符合条件的股票'
    })

    return {
      ...stockData,
      emptyDescription,
      handleSearch,
    }
  },
})
</script>

<style scoped>
.monitor-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.filter-panel,
.table-panel {
  position: relative;
  border-radius: 30px;
  border: 1px solid var(--panel-border);
  box-shadow: var(--panel-shadow);
  overflow: hidden;
}

.filter-panel,
.table-panel {
  min-width: 0;
  overflow: visible;
  background: rgba(255, 255, 255, 0.94);
  padding: 26px;
}

.panel-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 22px;
}

.panel-eyebrow {
  margin: 0 0 4px;
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.panel-heading h2 {
  margin: 0;
  color: var(--text-primary);
  font-size: 24px;
}

.panel-desc {
  max-width: 520px;
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
  line-height: 1.7;
}

.filter-grid {
  display: grid;
  grid-template-columns: 1.35fr 0.8fr 0.8fr auto;
  gap: 16px;
  align-items: end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.filter-item-wide {
  min-width: 0;
}

.filter-label {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.field-control {
  width: 100%;
}

.filter-action {
  display: flex;
}

.search-button {
  min-width: 136px;
  height: 42px;
  border-radius: 14px;
}

@media (max-width: 1100px) {
  .filter-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .filter-panel,
  .table-panel {
    padding: 18px;
    border-radius: 24px;
  }

  .panel-heading {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-grid {
    grid-template-columns: 1fr;
  }

  .filter-action,
  .search-button {
    width: 100%;
  }
}
</style>
