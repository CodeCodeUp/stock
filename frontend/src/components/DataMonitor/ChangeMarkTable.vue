<template>
  <div class="marks-table-card">
    <div class="section-heading">
      <div>
        <p class="section-eyebrow">交易明细</p>
        <h4>{{ title }}</h4>
      </div>
      <span class="section-count">{{ marks.length }} 条记录</span>
    </div>

    <el-table :data="marks" stripe size="small" style="width: 100%">
      <el-table-column prop="tradeDate" label="交易日期" width="120" />
      <el-table-column prop="changeType" label="变动类型" width="110">
        <template #default="scope">
          <span :class="['change-tag', scope.row.changeType === '增持' ? 'is-increase' : 'is-decrease']">
            {{ scope.row.changeType }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="交易金额" width="150">
        <template #default="scope">
          <span :class="scope.row.changeType === '增持' ? 'is-increase-text' : 'is-decrease-text'">
            {{ formatCurrency(scope.row.totalPrice) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="成交价" width="120">
        <template #default="scope">
          {{ formatCurrency(scope.row.price) }}
        </template>
      </el-table-column>
      <el-table-column prop="changerName" label="变动人" min-width="120" />
      <el-table-column prop="changerPosition" label="职位" min-width="140" />
    </el-table>
  </div>
</template>

<script lang="ts">
import { defineComponent, type PropType } from 'vue'
import { formatCurrency } from '@/utils/formatters'
import type { MarkItem } from '@/types/stock'

export default defineComponent({
  name: 'ChangeMarkTable',
  props: {
    marks: {
      type: Array as PropType<MarkItem[]>,
      required: true,
    },
    title: {
      type: String,
      default: '增减持记录',
    },
  },
  setup() {
    return {
      formatCurrency,
    }
  },
})
</script>

<style scoped>
.marks-table-card {
  border: 1px solid var(--panel-border);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.94);
  padding: 20px;
}

.section-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.section-eyebrow {
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.section-heading h4 {
  margin: 0;
  font-size: 18px;
  color: var(--text-primary);
}

.section-count {
  color: var(--text-muted);
  font-size: 13px;
}

.change-tag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 600;
}

.is-increase {
  color: var(--increase-color);
  background: rgba(209, 72, 54, 0.12);
}

.is-decrease {
  color: var(--decrease-color);
  background: rgba(21, 130, 93, 0.12);
}

.is-increase-text {
  color: var(--increase-color);
  font-weight: 600;
}

.is-decrease-text {
  color: var(--decrease-color);
  font-weight: 600;
}

@media (max-width: 768px) {
  .marks-table-card {
    padding: 16px;
  }

  .section-heading {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
