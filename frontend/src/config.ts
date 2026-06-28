/** API 基础地址 — 生产环境指向 Render 后端 */
export const API_BASE = import.meta.env.PROD
  ? 'https://travel-backend-xxxx.onrender.com' // TODO: 部署后替换为实际 Render URL
  : ''
