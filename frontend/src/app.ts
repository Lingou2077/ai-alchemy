import { useLaunch } from '@tarojs/taro'
import { PropsWithChildren } from 'react'

import { loadCurrentSession } from '@/services/storage'
import { useSessionStore } from '@/stores/sessionStore'
import { useUserStore } from '@/stores/userStore'
import './app.scss'

function App({ children }: PropsWithChildren) {
  const setSession = useSessionStore((state) => state.setSession)
  const ensureLogin = useUserStore((state) => state.ensureLogin)

  useLaunch(async () => {
    const saved = await loadCurrentSession()
    if (saved && saved.status === 'playing') {
      setSession(saved)
    }
    setTimeout(() => {
      ensureLogin().catch(() => {
        // 静默登录失败不阻断首页
      })
    }, 300)
  })

  return children
}

export default App
