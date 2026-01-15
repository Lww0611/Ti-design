import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
    plugins: [vue()],
    resolve: {
        alias: {
            // 设置 @ 指向 src 目录
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        port: 5173,
        open: true // 自动打开浏览器
    }
})