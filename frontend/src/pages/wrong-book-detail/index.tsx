import { Text, View } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'
import { useEffect, useState } from 'react'

import { fetchWrongQuestionDetail } from '@/services/userApi'
import type { WrongQuestionDetail } from '@/types/session'

import '../history/index.scss'
import './index.scss'

export default function WrongBookDetailPage() {
  const router = useRouter()
  const recordId = Number(router.params.id || 0)
  const [detail, setDetail] = useState<WrongQuestionDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!recordId) {
      Taro.redirectTo({ url: '/pages/wrong-book/index' })
      return
    }
    fetchWrongQuestionDetail(recordId)
      .then(setDetail)
      .catch((error) => {
        Taro.showToast({
          title: error instanceof Error ? error.message : '加载失败',
          icon: 'none',
        })
        setTimeout(() => Taro.navigateBack(), 500)
      })
      .finally(() => setLoading(false))
  }, [recordId])

  if (loading || !detail) {
    return (
      <View className='app-page'>
        <View className='app-bar'>
          <View className='app-bar-back' onClick={() => Taro.navigateBack()}>
            <Text>{'<'}</Text>
          </View>
          <View className='app-bar-title'>错题详情</View>
          <View style={{ width: '36px' }} />
        </View>
        <View className='app-content sub-page'>
          <View className='report-card sub-page-empty'>加载中…</View>
        </View>
      </View>
    )
  }

  return (
    <View className='app-page'>
      <View className='app-bar'>
        <View className='app-bar-back' onClick={() => Taro.navigateBack()}>
          <Text>{'<'}</Text>
        </View>
        <View className='app-bar-title'>错题详情</View>
        <View style={{ width: '36px' }} />
      </View>
      <View className='app-content sub-page wrong-detail-page'>
        <View className='report-card wrong-detail-meta'>
          <Text className='wrong-detail-topic'>{detail.topic}</Text>
          <Text className='wrong-detail-count'>累计答错 {detail.wrongCount} 次</Text>
        </View>

        <View className='report-section'>
          <View className='report-section-title'>题目</View>
          <View className='report-card'>{detail.stem}</View>
        </View>

        <View className='report-section'>
          <View className='report-section-title'>选项</View>
          <View className='wrong-detail-options'>
            {detail.options.map((option) => {
              const isCorrect = detail.correctAnswer.includes(option.key)
              return (
                <View
                  key={option.key}
                  className={`wrong-detail-option ${isCorrect ? 'correct' : ''}`}
                >
                  <Text className='wrong-detail-option-key'>{option.key}</Text>
                  <Text>{option.text}</Text>
                </View>
              )
            })}
          </View>
        </View>

        <View className='report-section'>
          <View className='report-section-title'>讲解</View>
          <View className='report-card'>{detail.explanation}</View>
        </View>
      </View>
    </View>
  )
}
