import { View } from '@tarojs/components'
import Taro from '@tarojs/taro'

import './index.scss'

type TabKey = 'home' | 'bank' | 'profile'

const TABS: Array<{ key: TabKey; label: string; path: string }> = [
  { key: 'home', label: '首页', path: '/pages/index/index' },
  { key: 'bank', label: '题库', path: '/pages/question-bank/index' },
  { key: 'profile', label: '我的', path: '/pages/profile/index' },
]

interface Props {
  active: TabKey
}

export default function MainTabBar({ active }: Props) {
  const switchTab = (path: string, key: TabKey) => {
    if (key === active) return
    Taro.redirectTo({ url: path })
  }

  return (
    <View className='tab-bar' aria-label='主导航'>
      {TABS.map((tab) => (
        <View
          key={tab.key}
          className={`tab-bar-item ${tab.key === active ? 'active' : ''}`}
          onClick={() => switchTab(tab.path, tab.key)}
        >
          <View className={`tab-bar-icon tab-bar-icon--${tab.key}`} />
          <View>{tab.label}</View>
        </View>
      ))}
    </View>
  )
}
