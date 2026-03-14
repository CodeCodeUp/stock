<template>
  <div class="backtest-page">
    <section class="hero-panel">
      <div class="hero-copy">
        <p class="hero-eyebrow">Backtest Lab</p>
        <h2>增持事件回测分析</h2>
        <p class="hero-desc">
          基于本地落库的历史日线、事件聚合和评分结果，筛出更有概率在增持后走强的股票。
        </p>
      </div>

      <div class="hero-actions">
        <el-button type="primary" :loading="rebuildLoading" @click="handleRebuild('incremental')">
          增量刷新
        </el-button>
        <el-button plain :loading="rebuildLoading" @click="handleRebuild('full')">
          全量校准
        </el-button>
      </div>
    </section>

    <section class="filter-panel">
      <div class="panel-heading">
        <div>
          <p class="panel-eyebrow">筛选条件</p>
          <h3>查找高质量增持信号</h3>
        </div>
        <p class="panel-tip">第一版按交易日定义信号日，属于事件研究口径，不等同于严格可交易回测。</p>
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
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            class="field-control"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">关键词</label>
          <el-input v-model="keyword" placeholder="股票代码 / 股票名称" clearable class="field-control" />
        </div>

        <div class="filter-item">
          <label class="filter-label">最小增持金额</label>
          <el-input
            v-model.number="minIncreaseAmount"
            placeholder="例如 300000"
            type="number"
            :min="0"
            clearable
            class="field-control"
          />
        </div>

        <div class="filter-item">
          <label class="filter-label">最小信号评分</label>
          <el-input-number v-model="minSignalScore" :min="0" :max="100" class="field-control" />
        </div>

        <div class="filter-item">
          <label class="filter-label">最小回测评分</label>
          <el-input-number v-model="minBacktestScore" :min="0" :max="100" class="field-control" />
        </div>

        <div class="filter-item">
          <label class="filter-label">同日减持</label>
          <el-select v-model="hasSameDayDecreaseValue" class="field-control">
            <el-option label="全部" value="" />
            <el-option label="仅无同日减持" value="false" />
            <el-option label="仅有同日减持" value="true" />
          </el-select>
        </div>

        <div class="filter-actions">
          <el-button type="primary" :loading="loading" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>
      </div>
    </section>

    <section class="overview-grid">
      <article v-for="card in overviewCards" :key="card.label" class="overview-card">
        <span>{{ card.label }}</span>
        <strong :class="card.className">{{ card.value }}</strong>
        <p>{{ card.caption }}</p>
      </article>
    </section>

    <section class="table-panel">
      <div class="table-heading">
        <div>
          <p class="panel-eyebrow">事件列表</p>
          <h3>高分事件与历史表现</h3>
        </div>
      </div>

      <div class="table-shell">
        <el-table
          :data="events"
          stripe
          style="width: 100%"
          :header-cell-style="headerStyle"
          v-loading="loading"
          @sort-change="handleSortChange"
        >
          <el-table-column label="股票" min-width="170" show-overflow-tooltip>
            <template #default="scope">
              <button class="stock-trigger" @click="openDetail(scope.row)">
                <strong>{{ scope.row.stockName }}</strong>
                <span>{{ scope.row.stockCode }}</span>
              </button>
            </template>
          </el-table-column>
          <el-table-column prop="signalDate" label="信号日" width="110" sortable="custom" />
          <el-table-column prop="increaseAmount" label="增持金额" width="140" sortable="custom">
            <template #default="scope">{{ formatCurrency(scope.row.increaseAmount) }}</template>
          </el-table-column>
          <el-table-column label="增持比例" width="120">
            <template #default="scope">{{ formatPercentage(scope.row.increaseRatioMax) }}</template>
          </el-table-column>
          <el-table-column prop="changerCount" label="人数" width="80" />
          <el-table-column prop="consecutiveIncreaseDays" label="连续天数" width="100" />
          <el-table-column prop="signalScore" label="信号分" width="96" sortable="custom" />
          <el-table-column prop="backtestScore" label="回测分" width="96" sortable="custom" />
          <el-table-column prop="return20d" label="20日收益" width="120" sortable="custom">
            <template #default="scope">
              <span :class="getReturnClass(scope.row.return20d)">
                {{ formatPercentage(scope.row.return20d) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column prop="return60d" label="60日收益" width="120" sortable="custom">
            <template #default="scope">
              <span :class="getReturnClass(scope.row.return60d)">
                {{ formatPercentage(scope.row.return60d) }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="同日减持" width="96">
            <template #default="scope">{{ scope.row.hasSameDayDecrease ? '有' : '无' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="scope">
              <el-button link type="primary" @click="openDetail(scope.row)">详情</el-button>
            </template>
          </el-table-column>
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

      <div class="empty-state" v-if="!loading && totalCount === 0">
        <el-empty description="当前条件下没有回测事件" />
      </div>
    </section>

    <AsyncBacktestEventDetail v-model:visible="detailVisible" :event-id="selectedEventId" />
  </div>
</template>

<script lang="ts">
import { computed, defineAsyncComponent, defineComponent, onMounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  fetchBacktestEvents,
  fetchBacktestOverview,
  triggerBacktestRebuild,
} from '@/services/stockApi'
import { formatCurrency, formatPercentage, getCurrentMonthRange } from '@/utils/formatters'
import type {
  BacktestEventItem,
  BacktestOverview,
  BacktestQueryParams,
  BacktestSortBy,
  SortColumn,
  SortOrder,
  TableHeaderStyle,
} from '@/types/stock'

const AsyncBacktestEventDetail = defineAsyncComponent(() => import('./BacktestEventDetail.vue'))

const createDefaultOverview = (): BacktestOverview => ({
  totalEvents: 0,
  totalStocks: 0,
  avgSignalScore: 0,
  avgBacktestScore: 0,
  winRate20d: 0,
  avgReturn20d: 0,
  hit10PctRate60d: 0,
  latestSignalDate: null,
})

export default defineComponent({
  name: 'BacktestDashboard',
  components: {
    AsyncBacktestEventDetail,
  },
  setup() {
    const [defaultStart, defaultEnd] = getCurrentMonthRange()
    const loading = ref(false)
    const rebuildLoading = ref(false)
    const overview = ref<BacktestOverview>(createDefaultOverview())
    const events = ref<BacktestEventItem[]>([])
    const dateRange = ref<string[]>([defaultStart, defaultEnd])
    const keyword = ref('')
    const minIncreaseAmount = ref<number | undefined>(300000)
    const minSignalScore = ref<number | undefined>(20)
    const minBacktestScore = ref<number | undefined>(10)
    const hasSameDayDecreaseValue = ref('')
    const currentPage = ref(1)
    const pageSize = ref(20)
    const totalCount = ref(0)
    const sortBy = ref<BacktestSortBy | undefined>('signalDate')
    const sortOrder = ref<SortOrder>('desc')
    const detailVisible = ref(false)
    const selectedEventId = ref(0)

    const headerStyle: TableHeaderStyle = {
      background: 'rgba(241, 245, 249, 0.95)',
      color: '#1e293b',
      fontWeight: '600',
      borderBottom: '1px solid rgba(148, 163, 184, 0.18)',
    }

    const buildQueryParams = (page = currentPage.value): BacktestQueryParams => ({
      start: dateRange.value?.[0],
      end: dateRange.value?.[1],
      keyword: keyword.value || undefined,
      minIncreaseAmount: minIncreaseAmount.value,
      minSignalScore: minSignalScore.value,
      minBacktestScore: minBacktestScore.value,
      hasSameDayDecrease:
        hasSameDayDecreaseValue.value === ''
          ? undefined
          : hasSameDayDecreaseValue.value === 'true',
      sortBy: sortBy.value,
      sortOrder: sortOrder.value || undefined,
      page,
      pageSize: pageSize.value,
    })

    const loadData = async (page = currentPage.value) => {
      loading.value = true
      try {
        const params = buildQueryParams(page)
        const [overviewResult, eventResult] = await Promise.all([
          fetchBacktestOverview(params),
          fetchBacktestEvents(params),
        ])
        overview.value = overviewResult
        events.value = eventResult.items
        totalCount.value = eventResult.total
        currentPage.value = eventResult.page
        pageSize.value = eventResult.pageSize
      } catch (error) {
        overview.value = createDefaultOverview()
        events.value = []
        totalCount.value = 0
        ElMessage.error(error instanceof Error ? error.message : '获取回测分析失败')
      } finally {
        loading.value = false
      }
    }

    const overviewCards = computed(() => [
      {
        label: '事件样本',
        value: `${overview.value.totalEvents}`,
        caption: `覆盖 ${overview.value.totalStocks} 只股票`,
        className: '',
      },
      {
        label: '20日胜率',
        value: formatPercentage(overview.value.winRate20d),
        caption: '未来 20 个交易日收盘收益为正',
        className: overview.value.winRate20d >= 0.5 ? 'positive-text' : '',
      },
      {
        label: '20日平均收益',
        value: formatPercentage(overview.value.avgReturn20d),
        caption: '全样本 20 日窗口平均回报',
        className: overview.value.avgReturn20d >= 0 ? 'positive-text' : 'negative-text',
      },
      {
        label: '60日命中 10%',
        value: formatPercentage(overview.value.hit10PctRate60d),
        caption: `平均信号分 ${Math.round(overview.value.avgSignalScore || 0)} / 平均回测分 ${Math.round(overview.value.avgBacktestScore || 0)}`,
        className: overview.value.hit10PctRate60d >= 0.2 ? 'positive-text' : '',
      },
    ])

    const getReturnClass = (value: number | null | undefined) => {
      if (value === null || value === undefined || Number.isNaN(value)) {
        return ''
      }
      if (value > 0) {
        return 'positive-text'
      }
      if (value < 0) {
        return 'negative-text'
      }
      return ''
    }

    const handleSearch = async () => {
      await loadData(1)
    }

    const handleReset = async () => {
      const [start, end] = getCurrentMonthRange()
      dateRange.value = [start, end]
      keyword.value = ''
      minIncreaseAmount.value = 300000
      minSignalScore.value = 20
      minBacktestScore.value = 10
      hasSameDayDecreaseValue.value = ''
      sortBy.value = 'signalDate'
      sortOrder.value = 'desc'
      await loadData(1)
    }

    const handleSortChange = async (column: SortColumn) => {
      const supportedSorts = new Set<BacktestSortBy>([
        'signalDate',
        'increaseAmount',
        'signalScore',
        'backtestScore',
        'return20d',
        'return60d',
      ])
      if (!supportedSorts.has(column.prop as BacktestSortBy)) {
        return
      }

      sortBy.value = column.prop as BacktestSortBy
      if (column.order === 'ascending') {
        sortOrder.value = 'asc'
      } else if (column.order === 'descending') {
        sortOrder.value = 'desc'
      } else {
        sortOrder.value = ''
      }
      await loadData(1)
    }

    const handleSizeChange = async (size: number) => {
      pageSize.value = size
      await loadData(1)
    }

    const handleCurrentChange = async (page: number) => {
      currentPage.value = page
      await loadData(page)
    }

    const openDetail = (item: BacktestEventItem) => {
      selectedEventId.value = item.eventId
      detailVisible.value = true
    }

    const handleRebuild = async (mode: 'incremental' | 'full') => {
      const confirmMessage =
        mode === 'full'
          ? '全量校准会在后台重新同步全部股票历史日线并重建回测结果，是否继续？'
          : '将触发一次后台增量回测刷新，是否继续？'

      try {
        await ElMessageBox.confirm(confirmMessage, '触发回测任务', {
          confirmButtonText: '继续',
          cancelButtonText: '取消',
          type: 'warning',
        })
      } catch {
        return
      }

      rebuildLoading.value = true
      try {
        const response = await triggerBacktestRebuild(mode)
        ElMessage.success(response.message || '回测任务已提交')
      } catch (error) {
        ElMessage.error(error instanceof Error ? error.message : '触发回测任务失败')
      } finally {
        rebuildLoading.value = false
      }
    }

    onMounted(async () => {
      await loadData(1)
    })

    return {
      currentPage,
      dateRange,
      detailVisible,
      events,
      formatCurrency,
      formatPercentage,
      getReturnClass,
      handleCurrentChange,
      handleRebuild,
      handleReset,
      handleSearch,
      handleSizeChange,
      handleSortChange,
      hasSameDayDecreaseValue,
      headerStyle,
      keyword,
      loading,
      minBacktestScore,
      minIncreaseAmount,
      minSignalScore,
      openDetail,
      overviewCards,
      pageSize,
      rebuildLoading,
      selectedEventId,
      totalCount,
    }
  },
})
</script>

<style scoped>
.backtest-page {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.hero-panel,
.filter-panel,
.table-panel {
  border-radius: 30px;
  border: 1px solid var(--panel-border);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: var(--panel-shadow);
}

.hero-panel {
  padding: 28px;
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-end;
  background:
    radial-gradient(circle at top right, rgba(35, 80, 168, 0.18), transparent 25%),
    radial-gradient(circle at left bottom, rgba(209, 72, 54, 0.1), transparent 28%),
    rgba(255, 255, 255, 0.96);
}

.hero-eyebrow,
.panel-eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.hero-copy h2,
.panel-heading h3,
.table-heading h3 {
  margin: 0;
  font-size: 24px;
  color: var(--text-primary);
}

.hero-desc,
.panel-tip {
  margin: 12px 0 0;
  max-width: 760px;
  color: var(--text-secondary);
  line-height: 1.7;
}

.hero-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-panel,
.table-panel {
  padding: 24px;
}

.panel-heading,
.table-heading {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
  margin-bottom: 18px;
}

.filter-grid {
  display: grid;
  grid-template-columns: 1.25fr repeat(5, minmax(0, 1fr));
  gap: 14px;
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

.filter-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
}

.overview-card {
  padding: 20px;
  border-radius: 24px;
  border: 1px solid var(--panel-border);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: var(--panel-shadow);
}

.overview-card span {
  display: block;
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.overview-card strong {
  display: block;
  font-size: 28px;
  color: var(--text-primary);
}

.overview-card p {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.table-shell {
  overflow-x: auto;
  border-radius: 24px;
  border: 1px solid var(--panel-border);
  background: rgba(255, 255, 255, 0.96);
}

.stock-trigger {
  border: 0;
  background: transparent;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
  cursor: pointer;
  color: inherit;
}

.stock-trigger strong {
  color: var(--text-primary);
}

.stock-trigger span {
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.08em;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.empty-state {
  padding: 36px 0 0;
}

.positive-text {
  color: var(--increase-color);
}

.negative-text {
  color: var(--decrease-color);
}

@media (max-width: 1180px) {
  .filter-grid {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .overview-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 768px) {
  .hero-panel,
  .panel-heading,
  .table-heading {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-grid,
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .filter-actions {
    width: 100%;
  }
}
</style>
