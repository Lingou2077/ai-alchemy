import { View } from '@tarojs/components'

import MainTabBar from '@/components/MainTabBar'
import PlaceholderPage from '@/components/PlaceholderPage'

export default function QuestionBankPage() {
  return (
    <View className='app-page phone-screen phone-screen--with-tab'>
      <PlaceholderPage active />
      <MainTabBar active='bank' />
    </View>
  )
}
