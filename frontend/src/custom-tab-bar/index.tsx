import { View } from '@tarojs/components'

import './index.scss'

/** 微信 custom tabBar 占位（实际导航由页面内 MainTabBar 渲染） */
export default function CustomTabBar() {
  return <View className='custom-tab-bar-placeholder' />
}
