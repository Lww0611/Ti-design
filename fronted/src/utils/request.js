import axios from 'axios'
import { ElMessage } from 'element-plus'
import { API_V1_URL } from '@/config/api'

const service = axios.create({
    baseURL: API_V1_URL,
    timeout: 5000 // 请求超时时间
})

// 响应拦截器：统一处理错误提示
service.interceptors.response.use(
    response => {
        const res = response.data
        if (res.status !== 'success') {
            ElMessage.error(res.message || '后端业务逻辑错误')
            return Promise.reject(new Error(res.message || 'Error'))
        }
        return res.data // 直接返回 data 部分
    },
    error => {
        ElMessage.error('网络请求失败，请检查后端是否启动')
        return Promise.reject(error)
    }
)

export default service