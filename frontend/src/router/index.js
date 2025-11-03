import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import Dashboard from '../views/Dashboard.vue'
import Projects from '../views/Projects.vue'
import APIs from '../views/APIs.vue'
import TestCases from '../views/TestCases.vue'
import TestSuites from '../views/TestSuites.vue'
import Executions from '../views/Executions.vue'
import Scheduler from '../views/Scheduler.vue'
import Environments from '../views/Environments.vue'
import GlobalTokens from '../views/GlobalTokens.vue'
import Settings from '../views/Settings.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'projects',
        name: 'Projects',
        component: Projects
      },
      {
        path: 'apis',
        name: 'APIs',
        component: APIs
      },
      {
        path: 'testcases',
        name: 'TestCases',
        component: TestCases
      },
      {
        path: 'testsuites',
        name: 'TestSuites',
        component: TestSuites
      },
      {
        path: 'executions',
        name: 'Executions',
        component: Executions
      },
      {
        path: 'scheduler',
        name: 'Scheduler',
        component: Scheduler
      },
      {
        path: 'environments',
        name: 'Environments',
        component: Environments
      },
      {
        path: 'global-tokens',
        name: 'GlobalTokens',
        component: GlobalTokens
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  try {
    // 安全访问 localStorage
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null
    if (to.path === '/login') {
      next()
    } else if (!token && to.path !== '/login') {
      next('/login')
    } else {
      next()
    }
  } catch (error) {
    console.error('Router guard error:', error)
    next('/login')
  }
})

export default router



