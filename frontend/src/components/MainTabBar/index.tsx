import { Image, View } from '@tarojs/components'
import Taro from '@tarojs/taro'

import { getTabIconSrc } from '@/components/MainTabBar/tabIcons'
import { MAIN_TAB_PATHS, type MainTabKey } from '@/utils/mainTab'

import './index.scss'

const TABS: Array<{ key: MainTabKey; label: string; path: string }> = [
  { key: 'home', label: '首页', path: MAIN_TAB_PATHS.home },
  { key: 'bank', label: '题库', path: MAIN_TAB_PATHS.bank },
  { key: 'profile', label: '我的', path: MAIN_TAB_PATHS.profile },
]

interface Props {
  active: MainTabKey
}

export default function MainTabBar({ active }: Props) {
  const switchTab = (path: string, key: MainTabKey) => {
    if (key === active) return
    Taro.switchTab({ url: path })
  }

  return (
    <View className='tab-bar' aria-label='主导航'>
      {TABS.map((tab) => (
        <View
          key={tab.key}
          className={`tab-bar-item ${tab.key === active ? 'active' : ''}`}
          onClick={() => switchTab(tab.path, tab.key)}
        >
          <Image
            className='tab-bar-icon'
            src={getTabIconSrc(tab.key, tab.key === active)}
            mode='aspectFit'
          />
          <View>{tab.label}</View>
        </View>
      ))}
    </View>
  )
}
