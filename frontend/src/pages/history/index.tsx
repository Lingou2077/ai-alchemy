import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useCallback, useState } from 'react'

import { fetchQuizHistory } from '@/services/userApi'
import type { QuizHistoryItem } from '@/types/session'
import { accuracyRingClass, formatRelativeTime } from '@/utils/formatTime'

import './index.scss'

export default function HistoryPage() {
  const [items, setItems] = useState<QuizHistoryItem[]>([])
  const [loading, setLoading] = useState(true)

  Taro.useDidShow(() => {
    loadHistory()
  })

  const loadHistory = useCallback(async () => {
    setLoading(true)
    try {
      const result = await fetchQuizHistory(1, 50)
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

  const openDetail = (sessionId: string) => {
    Taro.navigateTo({ url: `/pages/history-detail/index?sessionId=${encodeURIComponent(sessionId)}` })
  }

  return (
    <View className='app-page'>
      <View className='app-bar'>
        <View className='app-bar-back' onClick={() => Taro.navigateBack()}>
          <Text>{'<'}</Text>
        </View>
        <View className='app-bar-title'>学习历史</View>
        <View style={{ width: '36px' }} />
      </View>
      <View className='app-content sub-page'>
        {loading ? (
          <View className='report-card sub-page-empty'>加载中…</View>
        ) : items.length === 0 ? (
          <View className='report-card sub-page-empty'>
            <View className='sub-page-empty-title'>暂无历史记录</View>
            <View className='sub-page-empty-desc'>完成一次闯关后会出现在这里</View>
          </View>
        ) : (
          <View className='history-list'>
            {items.map((item) => (
              <View key={item.sessionId} className='history-item' onClick={() => openDetail(item.sessionId)}>
                <View className={`history-score-ring ${accuracyRingClass(item.accuracy)}`}>
                  {Math.round(item.accuracy)}
                </View>
                <View className='history-info'>
                  <View className='history-title'>{item.topic}</View>
                  <View className='history-meta'>
                    {formatRelativeTime(item.finishedAt)} · {item.questionCount} 题
                    {item.status === 'failed' ? ' · 灵韵散尽' : ''}
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
