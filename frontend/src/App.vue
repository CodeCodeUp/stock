<template>
  <div id="app">
    <DataMonitor />
  </div>
</template>

<script lang="ts">
import DataMonitor from './components/DataMonitor/DataMonitor.vue'

export default {
  name: 'App',
  components: {
    DataMonitor,
  },
}
</script>

<style scoped>
#app {
  width: 100%;
  height: 100vh;
}
</style>
