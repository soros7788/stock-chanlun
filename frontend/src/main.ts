import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import App from './App.vue'
import './styles/main.css'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')

// PWA: 新版本就绪时提示用户刷新
import { registerSW } from 'virtual:pwa-register'
registerSW({
  onNeedRefresh() {
    const ok = confirm('ChanStock 有新版本可用，是否刷新更新？')
    if (ok) location.reload()
  },
  onOfflineReady() {
    console.log('ChanStock 已准备好离线使用')
  },
})