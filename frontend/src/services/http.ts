import Taro from '@tarojs/taro'

import { loadAuthToken } from '@/services/authStorage'

const API_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000'
export const DEFAULT_REQUEST_TIMEOUT_MS = 60000
export const POLL_REQUEST_TIMEOUT_MS = 15000

interface ApiErrorBody {
  detail?: string
}

async function getAuthHeader(): Promise<Record<string, string>> {
  const token = await loadAuthToken()
  if (!token) return {}
  return { Authorization: `Bearer ${token}` }
}

export async function request<T>(
  path: string,
  options: Taro.request.Option,
  retryOn401 = true,
  timeout = DEFAULT_REQUEST_TIMEOUT_MS,
): Promise<T> {
  const authHeader = await getAuthHeader()
  const response = await Taro.request<T & ApiErrorBody>({
    url: `${API_BASE_URL}${path}`,
    timeout,
    header: {
      'Content-Type': 'application/json',
      ...authHeader,
      ...(options.header || {}),
    },
    ...options,
  })

  if (response.statusCode === 401 && retryOn401 && authHeader.Authorization) {
    const { useUserStore } = await import('@/stores/userStore')
    const relogged = await useUserStore.getState().login()
    if (relogged) {
      return request<T>(path, options, false, timeout)
    }
  }

  if (response.statusCode >= 400) {
    const message = (response.data as ApiErrorBody)?.detail || '请求失败，请稍后重试'
    throw new Error(message)
  }

  return response.data as T
}

export function sleep(ms: number) {
  return new Promise<void>((resolve) => {
    setTimeout(resolve, ms)
  })
}
