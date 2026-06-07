import { View } from '@tarojs/components'

import './index.scss'

interface Props {
  active?: boolean
}

export default function TabBarPlaceholder({ active = true }: Props) {
  return (
    <View className='placeholder-page app-content--with-tab'>
      <View className='placeholder-badge'>Phase 1 即将上线</View>
      <View className='placeholder-text'>
        {active ? '题库功能正在炼制中，敬请期待。' : '个人中心正在炼制中，敬请期待。'}
      </View>
    </View>
  )
}
