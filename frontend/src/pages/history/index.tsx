import { View } from '@tarojs/components'
import { useEffect } from 'react'

import { switchMainTab } from '@/utils/mainTab'

import './index.scss'

export default function HistoryPage() {
  useEffect(() => {
    switchMainTab('bank')
  }, [])

  return <View className='app-page' />
}
