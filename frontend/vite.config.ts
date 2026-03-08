import { fileURLToPath, URL } from 'node:url'

import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import vueDevTools from 'vite-plugin-vue-devtools'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'

export default defineConfig(({ mode }) => {
  const workspaceRoot = fileURLToPath(new URL('..', import.meta.url))
  const env = {
    ...loadEnv(mode, workspaceRoot, ''),
    ...loadEnv(mode, process.cwd(), ''),
  }
  const backendPort = env.BACKEND_PORT || '8080'
  const devProxyTarget = env.VITE_DEV_PROXY_TARGET || `http://localhost:${backendPort}`

  return {
    plugins: [
      vue(),
      AutoImport({
        imports: ['vue'],
        resolvers: [ElementPlusResolver()],
        dts: './auto-imports.d.ts',
      }),
      Components({
        resolvers: [ElementPlusResolver({ importStyle: 'css' })],
        dts: './components.d.ts',
      }),
      ...(mode === 'development' ? [vueDevTools()] : []),
    ],
    server: {
      proxy: {
        '/api': {
          target: devProxyTarget,
          changeOrigin: true,
        },
        '/data/api': {
          target: devProxyTarget,
          changeOrigin: true,
        },
      },
    },
    build: {
      rollupOptions: {
        output: {
          manualChunks(id) {
            if (id.includes('node_modules/')) {
              // element-plus and its vue dependencies go together to avoid circular refs
              if (id.includes('/element-plus/') || id.includes('/@element-plus/')) {
                return 'ui-vendor'
              }

              // Only match vue core package, not @vue/* sub-packages that element-plus also uses
              if (
                id.includes('/node_modules/vue/') ||
                id.includes('/@vue/runtime-dom/') ||
                id.includes('/@vue/runtime-core/') ||
                id.includes('/@vue/reactivity/') ||
                id.includes('/@vue/shared/')
              ) {
                return 'vue-vendor'
              }

              if (id.includes('/zrender/') || id.includes('/echarts/')) {
                return 'chart-vendor'
              }
            }
          },
        },
      },
    },
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
  }
})
