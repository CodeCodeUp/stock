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
            if (id.includes('node_modules/vue')) {
              return 'vue-vendor'
            }

            if (id.includes('node_modules/element-plus')) {
              return 'ui-vendor'
            }

            if (id.includes('node_modules/zrender')) {
              return 'chart-runtime'
            }

            if (id.includes('node_modules/echarts')) {
              if (/(?:\\|\/)echarts(?:\\|\/)(?:charts|components|renderers)(?:\\|\/)/.test(id)) {
                return 'chart-modules'
              }
              return 'chart-core'
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
