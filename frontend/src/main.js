import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import App from './App.vue'
import router from './router'
import { useThemeStore } from './store/theme'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)

// 初始化主题store
const themeStore = useThemeStore()
themeStore.init()

// 获取当前语言配置
const getLocale = () => {
  return themeStore.language === 'en-US' ? en : zhCn
}

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)
}

app.use(router)

// 配置 Element Plus 的国际化
const currentLocale = getLocale()
app.use(ElementPlus, { locale: currentLocale })

// 监听语言变化，重新配置Element Plus
window.addEventListener('language-changed', (event) => {
  const newLocale = event.detail === 'en-US' ? en : zhCn
  // 更新全局配置
  app.config.globalProperties.$ELEMENT = { locale: newLocale }
  console.log('语言已切换为:', event.detail)
})

// 添加全局错误处理
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err)
  console.error('Error Info:', info)
  console.error('Error Stack:', err.stack)
}

// 添加未捕获的错误处理
window.addEventListener('error', (event) => {
  console.error('Unhandled Error:', event.error)
  console.error('Error Message:', event.message)
  console.error('Error Filename:', event.filename)
  console.error('Error Line:', event.lineno)
})

// 添加未处理的 Promise 拒绝处理
window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled Promise Rejection:', event.reason)
})

try {
  const appElement = document.getElementById('app')
  if (!appElement) {
    console.error('App element #app not found in DOM!')
    throw new Error('App element not found')
  }
  app.mount('#app')
  console.log('App mounted successfully')
  
  // 添加调试工具：检查阻止点击的元素
  if (import.meta.env.DEV) {
    window.debugClick = () => {
      const allElements = document.querySelectorAll('*')
      const blockingElements = []
      allElements.forEach(el => {
        const style = window.getComputedStyle(el)
        if (style.pointerEvents === 'none' || style.zIndex > 1000) {
          blockingElements.push({
            element: el,
            tagName: el.tagName,
            className: el.className,
            id: el.id,
            pointerEvents: style.pointerEvents,
            zIndex: style.zIndex,
            position: style.position
          })
        }
      })
      console.log('可能阻止点击的元素:', blockingElements)
      return blockingElements
    }
    console.log('💡 提示：在控制台运行 debugClick() 可以检查阻止点击的元素')
  }
} catch (error) {
  console.error('Failed to mount app:', error)
  document.body.innerHTML = `
    <div style="padding: 20px; font-family: Arial, sans-serif;">
      <h1>应用加载失败</h1>
      <p>错误信息: ${error.message}</p>
      <p>请检查浏览器控制台获取详细信息。</p>
    </div>
  `
}



