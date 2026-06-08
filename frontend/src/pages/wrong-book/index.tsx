import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useCallback, useState } from 'react'

import { fetchWrongQuestions } from '@/services/userApi'
import type { WrongQuestionItem } from '@/types/session'
import { formatRelativeTime } from '@/utils/formatTime'

import '../history/index.scss'
import './index.scss'

export default function WrongBookPage() {
  const [items, setItems] = useState<WrongQuestionItem[]>([])
  const [loading, setLoading] = useState(true)

  Taro.useDidShow(() => {
    loadItems()
  })

  const loadItems = useCallback(async () => {
    setLoading(true)
    try {
      const result = await fetchWrongQuestions(1, 50)
      setItems(result.items)
    } catch (error) {
      Taro.showToast({
        title: error instanceof Error ? error.message : '加载失败',
        icon: 'none',
      })
    } finally {
      setLoading(false)
    }
  }, [])

  const openDetail = (id: number) => {
    Taro.navigateTo({ url: `/pages/wrong-book-detail/index?id=${id}` })
  }

  return (
    <View className='app-page'>
      <View className='app-bar'>
        <View className='app-bar-back' onClick={() => Taro.navigateBack()}>
          <Text>{'<'}</Text>
        </View>
        <View className='app-bar-title'>错题本</View>
        <View style={{ width: '36px' }} />
      </View>
      <View className='app-content sub-page'>
        {loading ? (
          <View className='report-card sub-page-empty'>加载中…</View>
        ) : items.length === 0 ? (
          <View className='report-card sub-page-empty'>
            <View className='sub-page-empty-title'>暂无错题</View>
            <View className='sub-page-empty-desc'>答错的题目会自动收录到这里</View>
          </View>
        ) : (
          <View className='history-list'>
            {items.map((item) => (
              <View key={item.id} className='history-item' onClick={() => openDetail(item.id)}>
                <View className='history-score-ring low wrong-book-ring'>错</View>
                <View className='history-info'>
                  <View className='history-title wrong-book-stem'>{item.stem}</View>
                  <View className='history-meta'>
                    {item.topic} · {formatRelativeTime(item.lastWrongAt)} · 错 {item.wrongCount} 次
                  </View>
                </View>
              </View>
            ))}
          </View>
        )}
      </View>
    </View>
  )
}
