import Taro from '@tarojs/taro'

import { STORAGE_KEYS } from '@/constants'

export async function saveAuthToken(token: string) {
  await Taro.setStorage({ key: STORAGE_KEYS.authToken, data: token })
}

export async function loadAuthToken(): Promise<string | null> {
  try {
    const result = await Taro.getStorage<string>({ key: STORAGE_KEYS.authToken })
    return result.data ?? null
  } catch {
    return null
  }
}

export async function clearAuthToken() {
  try {
    await Taro.removeStorage({ key: STORAGE_KEYS.authToken })
  } catch {
    // ignore
  }
}
