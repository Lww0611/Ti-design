/**
 * 后端 API 根地址（无尾斜杠）。
 *
 * 本地：`npm run dev` 未配置时可默认 http://127.0.0.1:8000
 * 生产（Vercel）：必须在构建前配置 Environment Variable：
 *   VITE_API_ORIGIN=https://你的-render-服务.onrender.com
 * （无协议则无效；改完后需重新 Build / Redeploy，Vite 在打包时写入变量）
 */
const fromEnv = (import.meta.env.VITE_API_ORIGIN || '').trim()

let origin =
  fromEnv ||
  (import.meta.env.DEV ? 'http://127.0.0.1:8000' : '')

if (!fromEnv && !import.meta.env.DEV) {
  // eslint-disable-next-line no-console
  console.error(
    '[Ti-design] 生产构建未设置 VITE_API_ORIGIN。请在 Vercel → Settings → Environment Variables 添加后重新部署。'
  )
}

export const API_ORIGIN = origin.replace(/\/$/, '')

/** 与 FastAPI 挂载的 /api/v1 一致 */
export const API_V1_URL = `${API_ORIGIN}/api/v1`

/** 部分页面使用 /api 再拼接 /v1/... */
export const API_ROOT = `${API_ORIGIN}/api`
