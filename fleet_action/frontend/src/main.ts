import { createApp } from 'vue'
import { nextTick } from 'vue'
import App from './App.vue'
import router from './router'
import { initSDK, updateToken } from './api'

// eslint-disable-next-line @typescript-eslint/no-explicit-any
declare const HelmSDK: any

function loadScript(src: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const el = document.createElement('script')
    el.src = src
    el.onload = () => resolve()
    el.onerror = () => reject(new Error(`Failed to load ${src}`))
    document.head.appendChild(el)
  })
}

loadScript('/plugin-sdk/helm-sdk.js').then(() => {
  HelmSDK.init((ctx: { token: string; apiBase: string }) => {
    initSDK(ctx.token, ctx.apiBase)

    window.addEventListener('message', (e: MessageEvent) => {
      if (e.data?.type === 'helm:token:refreshed') {
        updateToken(e.data.token as string)
      }
    })

    // Guard against double-mount (e.g. token refresh re-fires callback)
    if (document.getElementById('app')?.childNodes.length === 0) {
      nextTick(() => createApp(App).use(router).mount('#app'))
    }
  })
})