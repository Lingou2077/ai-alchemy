import { Text, View } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'
import { useEffect, useState } from 'react'

import { fetchQuizHistoryDetail } from '@/services/userApi'
import type { QuizHistoryDetail } from '@/types/session'
import { switchMainTab } from '@/utils/mainTab'
import { formatDuration, formatRelativeTime } from '@/utils/formatTime'

import '../history/index.scss'
import './index.scss'

export default function HistoryDetailPage() {
  const router = useRouter()
  const sessionId = router.params.sessionId || ''
  const [detail, setDetail] = useState<QuizHistoryDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!sessionId) {
      switchMainTab('bank')
      return
    }
    fetchQuizHistoryDetail(sessionId)
      .then(setDetail)
      .catch((error) => {
        Taro.showToast({
          title: error instanceof Error ? error.message : '加载失败',
          icon: 'none',
        })
        setTimeout(() => Taro.navigateBack(), 500)
      })
      .finally(() => setLoading(false))
  }, [sessionId])

  if (loading || !detail) {
    return (
      <View className='app-page'>
        <View className='app-bar'>
          <View className='app-bar-back' onClick={() => Taro.navigateBack()}>
            <Text>{'<'}</Text>
          </View>
          <View className='app-bar-title'>历史详情</View>
          <View style={{ width: '36px' }} />
        </View>
        <View className='app-content sub-page'>
          <View className='report-card sub-page-empty'>加载中…</View>
        </View>
      </View>
    )
  }

  const failed = detail.status === 'failed'

  return (
    <View className='app-page'>
      <View className='app-bar'>
        <View className='app-bar-back' onClick={() => Taro.navigateBack()}>
          <Text>{'<'}</Text>
        </View>
        <View className='app-bar-title'>历史详情</View>
        <View style={{ width: '36px' }} />
      </View>
      <View className='app-content sub-page history-detail-page'>
        <View className='report-summary history-detail-summary'>
          <View className='report-summary-main'>
            <View className={`report-badge ${failed ? 'fail' : 'success'}`}>
              {failed ? '灵韵散尽' : '炼成成功'}
            </View>
            <View className={`report-score ${failed ? 'report-score--fail' : ''}`}>
              {Math.round(detail.accuracy)}<Text className='report-score-unit'>%</Text>
            </View>
          </View>
          <View className='report-summary-side'>
            <View className='report-stats'>
              <Text>用时 <Text className='strong'>{formatDuration(detail.durationSec)}</Text></Text>
              <Text>{detail.questionCount} 题 · {formatRelativeTime(detail.finishedAt)}</Text>
            </View>
          </View>
        </View>

        {detail.weakPoints && detail.weakPoints.length > 0 && (
          <View className='report-section'>
            <View className='report-section-title'>薄弱知识点</View>
            <View className='weak-tags'>
              {detail.weakPoints.map((point) => (
                <Text key={point.name} className='weak-tag partial'>{point.name}</Text>
              ))}
            </View>
          </View>
        )}

        {detail.summary && (
          <View className='report-section'>
            <View className='report-section-title'>知识总结</View>
            <View className='report-card'>{detail.summary}</View>
          </View>
        )}

        {detail.suggestion && (
          <View className='report-section'>
            <View className='report-section-title'>学习建议</View>
            <View className='report-card'>{detail.suggestion}</View>
          </View>
        )}
      </View>
    </View>
  )
}
