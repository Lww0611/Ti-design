import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../layout/index.vue'

const routes = [
    // 登录页独立，不使用 Layout
    // 登录页
    {
        path: '/login',
        name: 'Login',
        component: () => import('../views/auth/Login.vue'),
        meta: { title: '系统登录' }
    },

    // 首页（独立页面，不使用 Layout）
    {
        path: '/dashboard',
        name: 'Dashboard',
        component: () => import('../views/dashboard/index.vue'),
        meta: { title: '工作台首页' }
    },
    // 后台管理页使用 Layout
    {
        path: '/',
        component: Layout,
        redirect: '/login', // 初始重定向到登录页
        children: [
            {
                path: '/cases',
                name: 'cases',
                component: () => import('@/views/case/case.vue'),
                meta: { title: '工作流管理' }
            },
            {
                path: '/datasets',
                name: 'datasets',
                component: () => import('@/views/datasets/index.vue'),
                meta: { title: '数据集管理' }
            },
            {
                path: '/management',
                name: 'management',
                component: () => import('@/views/management/index.vue'),
                meta: { title: '模型管理' }
            },
            {
                path: 'forward',
                name: 'Forward',
                component: () => import('../views/forward/index.vue'),
                meta: { title: '性能正向预测' }
            },
            {
                path: 'inverse',
                name: 'Inverse',
                component: () => import('../views/inverse/index.vue'),
                meta: { title: '成分逆向设计' }
            },
            {
                path: 'history',
                name: 'History',
                component: () => import('../views/history/index.vue'),
                meta: { title: '实验历史记录' }
            }
        ]
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router