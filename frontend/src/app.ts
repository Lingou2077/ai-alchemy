import { useLaunch } from '@tarojs/taro'
import { PropsWithChildren } from 'react'

import { loadCurrentSession } from '@/services/storage'
import { useSessionStore } from '@/stores/sessionStore'
import './app.scss'

function App({ children }: PropsWithChildren) {
  const setSession = useSessionStore((state) => state.setSession)

  useLaunch(async () => {
    const saved = await loadCurrentSession()
    if (saved && saved.status === 'playing') {
      setSession(saved)
    }
  })

  return children
}

export default App
