import Taro from '@tarojs/taro'
import { create } from 'zustand'

import { fetchCurrentUser, loginWithCode, persistAvatar, updateProfile } from '@/services/userApi'
import { clearAuthToken, loadAuthToken, saveAuthToken } from '@/services/authStorage'
import type { UserProfile } from '@/types/user'

interface UserState {
  token: string | null
  user: UserProfile | null
  loading: boolean
  loginError: string | null
  setUser: (user: UserProfile | null) => void
  setToken: (token: string | null) => void
  ensureLogin: () => Promise<boolean>
  login: () => Promise<boolean>
  refreshProfile: () => Promise<void>
  updateUserProfile: (payload: { nickname?: string; avatarUrl?: string }) => Promise<void>
  uploadUserAvatar: (filePath: string) => Promise<void>
  logout: () => Promise<void>
}

export const useUserStore = create<UserState>((set, get) => ({
  token: null,
  user: null,
  loading: false,
  loginError: null,

  setUser: (user) => set({ user }),
  setToken: (token) => set({ token }),

  ensureLogin: async () => {
    const savedToken = await loadAuthToken()
    if (savedToken) {
      set({ token: savedToken })
      try {
        await get().refreshProfile()
        return true
      } catch {
        await get().logout()
      }
    }
    return get().login()
  },

  login: async () => {
    set({ loading: true, loginError: null })
    try {
      const loginResult = await Taro.login()
      if (!loginResult.code) {
        throw new Error('微信登录失败')
      }
      const response = await loginWithCode(loginResult.code)
      await saveAuthToken(response.token)
      set({ token: response.token, user: response.user, loading: false })
      return true
    } catch (error) {
      const message = error instanceof Error ? error.message : '登录失败'
      set({ loading: false, loginError: message })
      return false
    }
  },

  refreshProfile: async () => {
    const user = await fetchCurrentUser()
    set({ user })
  },

  updateUserProfile: async (payload) => {
    const user = await updateProfile(payload)
    set({ user })
  },

  uploadUserAvatar: async (filePath) => {
    const user = await persistAvatar(filePath)
    set({ user })
  },

  logout: async () => {
    await clearAuthToken()
    set({ token: null, user: null, loginError: null })
  },
}))
