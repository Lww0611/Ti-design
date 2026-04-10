/**
 * 后端 API 根地址（无尾斜杠）。
 * - 本地：默认 http://127.0.0.1:8000
 * - 生产（Vercel）：在项目 Environment Variables 中设置 VITE_API_ORIGIN=https://your-api.onrender.com
 */
export const API_ORIGIN = (import.meta.env.VITE_API_ORIGIN || 'http://127.0.0.1:8000').replace(
  /\/$/,
  ''
)

/** 与 FastAPI 挂载的 /api/v1 一致 */
export const API_V1_URL = `${API_ORIGIN}/api/v1`

/** 部分页面使用 /api 再拼接 /v1/... */
export const API_ROOT = `${API_ORIGIN}/api`
