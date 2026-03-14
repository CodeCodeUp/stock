<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="brand-block">
        <p class="brand-eyebrow">Stock Signal Studio</p>
        <h1>股票增减持监控与回测分析</h1>
      </div>

      <nav class="view-switch">
        <button
          v-for="item in viewOptions"
          :key="item.value"
          :class="['view-button', { 'is-active': currentView === item.value }]"
          @click="currentView = item.value"
        >
          <span>{{ item.label }}</span>
          <small>{{ item.caption }}</small>
        </button>
      </nav>
    </header>

    <main class="content-shell">
      <DataMonitor v-if="currentView === 'monitor'" />
      <AsyncBacktestDashboard v-else />
    </main>
  </div>
</template>

<script lang="ts">
import { defineAsyncComponent, defineComponent, ref } from 'vue'
import DataMonitor from './components/DataMonitor/DataMonitor.vue'

const AsyncBacktestDashboard = defineAsyncComponent(
  () => import('./components/Backtest/BacktestDashboard.vue'),
)

export default defineComponent({
  name: 'App',
  components: {
    AsyncBacktestDashboard,
    DataMonitor,
  },
  setup() {
    const currentView = ref<'monitor' | 'backtest'>('monitor')
    const viewOptions = [
      {
        value: 'monitor',
        label: '监控页',
        caption: '看近期增减持',
      },
      {
        value: 'backtest',
        label: '回测分析',
        caption: '看事件后表现',
      },
    ] as const

    return {
      currentView,
      viewOptions,
    }
  },
})
</script>

<style scoped>
.app-shell {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.topbar {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  padding: 12px 2px 0;
}

.brand-eyebrow {
  margin: 0 0 6px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 0.16em;
  text-transform: uppercase;
}

.brand-block h1 {
  margin: 0;
  font-size: clamp(26px, 3vw, 36px);
  color: var(--text-primary);
  line-height: 1.1;
}

.view-switch {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.view-button {
  min-width: 172px;
  border: 1px solid rgba(35, 80, 168, 0.12);
  border-radius: 20px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.82);
  box-shadow: 0 12px 32px rgba(15, 23, 42, 0.06);
  color: var(--text-primary);
  cursor: pointer;
  transition:
    transform 180ms ease,
    border-color 180ms ease,
    background 180ms ease;
  text-align: left;
}

.view-button:hover {
  transform: translateY(-1px);
  border-color: rgba(35, 80, 168, 0.28);
}

.view-button span,
.view-button small {
  display: block;
}

.view-button span {
  font-size: 16px;
  font-weight: 700;
}

.view-button small {
  margin-top: 4px;
  color: var(--text-muted);
}

.view-button.is-active {
  background: linear-gradient(135deg, rgba(35, 80, 168, 0.96), rgba(31, 114, 132, 0.92));
  color: #fff;
  border-color: transparent;
}

.view-button.is-active small {
  color: rgba(255, 255, 255, 0.82);
}

.content-shell {
  min-width: 0;
}

@media (max-width: 900px) {
  .topbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .view-switch {
    width: 100%;
  }

  .view-button {
    flex: 1 1 220px;
  }
}
</style>
