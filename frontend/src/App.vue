<template>
  <DataMonitor />
</template>

<script lang="ts">
import { defineComponent } from 'vue'
import DataMonitor from './components/DataMonitor/DataMonitor.vue'

export default defineComponent({
  name: 'App',
  components: {
    DataMonitor,
  },
})
</script>
