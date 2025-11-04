import { defineStore } from 'pinia'

export const useThemeStore = defineStore('theme', {
  state: () => {
    // 从localStorage加载配置
    const savedConfig = localStorage.getItem('systemConfig')
    let theme = 'light'
    let language = 'zh-CN'
    
    if (savedConfig) {
      try {
        const config = JSON.parse(savedConfig)
        theme = config.theme || 'light'
        language = config.language || 'zh-CN'
      } catch (error) {
        console.error('加载系统配置失败', error)
      }
    }
    
    return {
      theme, // 'light' | 'dark' | 'auto'
      language // 'zh-CN' | 'en-US'
    }
  },
  actions: {
    setTheme(theme) {
      this.theme = theme
      this.applyTheme()
      this.saveConfig()
    },
    setLanguage(language) {
      this.language = language
      this.applyLanguage()
      this.saveConfig()
    },
    applyTheme() {
      const html = document.documentElement
      const body = document.body
      
      // 移除所有主题类
      html.classList.remove('dark', 'light')
      body.classList.remove('dark', 'light')
      
      if (this.theme === 'auto') {
        // 跟随系统主题
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
        if (prefersDark) {
          html.classList.add('dark')
          body.classList.add('dark')
        } else {
          html.classList.add('light')
          body.classList.add('light')
        }
      } else {
        html.classList.add(this.theme)
        body.classList.add(this.theme)
      }
    },
    applyLanguage() {
      // 语言切换会通过 Element Plus 的 ConfigProvider 处理
      // 这里可以触发自定义事件，让组件重新加载
      window.dispatchEvent(new CustomEvent('language-changed', { detail: this.language }))
    },
    saveConfig() {
      const config = {
        theme: this.theme,
        language: this.language,
        autoSave: JSON.parse(localStorage.getItem('systemConfig') || '{}').autoSave ?? true
      }
      localStorage.setItem('systemConfig', JSON.stringify(config))
    },
    init() {
      // 初始化时应用主题
      this.applyTheme()
      
      // 监听系统主题变化（仅在auto模式下）
      if (this.theme === 'auto') {
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
          if (this.theme === 'auto') {
            this.applyTheme()
          }
        })
      }
    }
  }
})

