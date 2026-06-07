import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'

import LingyunBadge from '@/components/LingyunBadge'
import { PLACEHOLDER_MESSAGE } from '@/constants'
import { saveCurrentSession } from '@/services/storage'
import { useSessionStore } from '@/stores/sessionStore'

import './index.scss'

function formatDuration(seconds: number) {
  const minutes = Math.floor(seconds / 60)
  const remain = seconds % 60
  return minutes > 0 ? `${minutes}分${remain}秒` : `${remain}秒`
}

function masteryClass(name: string, report: NonNullable<ReturnType<typeof useSessionStore.getState>['report']>) {
  const node = report.conceptMastery.find((item) => item.name === name)
  if (!node) return 'partial'
  return node.mastery === 'mastered' ? 'good' : node.mastery === 'weak' ? 'weak' : 'partial'
}

export default function ReportPage() {
  const session = useSessionStore((state) => state.session)
  const report = useSessionStore((state) => state.report)
  const resetFlow = useSessionStore((state) => state.resetFlow)

  Taro.useDidShow(() => {
    if (!session || !report) {
      Taro.redirectTo({ url: '/pages/index/index' })
    }
  })

  if (!session || !report) {
    return <View className='app-page' />
  }

  const failed = session.status === 'failed' || session.hearts <= 0
  const weakNames = report.weakPoints.length
    ? report.weakPoints.map((item) => item.name)
    : session.levels.flatMap((level) => level.questions.flatMap((q) => q.conceptTags)).slice(0, 3)

  const showSharePlaceholder = () => {
    Taro.showToast({ title: PLACEHOLDER_MESSAGE, icon: 'none' })
  }

  const restart = async () => {
    resetFlow()
    await saveCurrentSession(null)
    Taro.redirectTo({ url: '/pages/index/index' })
  }

  return (
    <View className='app-page'>
      <View className='app-bar'>
        <View className='app-bar-title'>AI炼金</View>
      </View>
      <View className='app-content report-page'>
        <View className='report-summary'>
          <View className='report-summary-main'>
            <View className={`report-badge ${failed ? 'fail' : 'success'}`}>
              {failed ? '灵韵散尽…' : '炼成成功！'}
            </View>
            <View className={`report-score ${failed ? 'report-score--fail' : ''}`}>
              {Math.round(report.accuracy)}<Text className='report-score-unit'>%</Text>
            </View>
          </View>
          <View className='report-summary-side'>
            <View className='report-stats'>
              <Text>用时 <Text className='strong'>{formatDuration(report.duration)}</Text></Text>
              <Text>对 <Text className='strong'>{report.correctCount}</Text> · 错 <Text className='strong'>{report.wrongCount}</Text></Text>
            </View>
          </View>
        </View>

        {failed && (
          <View className='lingyun-hero'>
            <LingyunBadge hearts={0} large depleted />
          </View>
        )}

        <View className='report-section'>
          <View className='report-section-title'>薄弱知识点</View>
          <View className='weak-tags'>
            {weakNames.map((name) => (
              <Text key={name} className={`weak-tag ${masteryClass(name, report)}`}>{name}</Text>
            ))}
          </View>
        </View>

        <View className='report-section'>
          <View className='report-section-title'>知识总结</View>
          <View className='report-card'>{report.summary}</View>
        </View>

        <View className='report-section'>
          <View className='report-section-title'>学习建议</View>
          <View className='report-card'>{report.suggestion}</View>
        </View>

        {failed && (
          <>
            <View className='section-head'>
              <Text className='section-head-title'>错题将自动收录</Text>
            </View>
            <View className='history-list'>
              {session.answers.filter((item) => !item.isCorrect).slice(0, 2).map((item) => {
                const question = session.levels.flatMap((level) => level.questions).find((q) => q.id === item.questionId)
                return (
                  <View key={item.questionId} className='history-item'>
                    <View className='history-score-ring low'>错</View>
                    <View className='history-info'>
                      <View className='history-title'>{question?.stem || item.questionId}</View>
                      <View className='history-meta'>Phase 1 错题本功能</View>
                    </View>
                  </View>
                )
              })}
            </View>
          </>
        )}

        <View className='report-actions'>
          <View className='btn-comic btn-amber btn-sm' onClick={() => Taro.navigateTo({ url: '/pages/share/index' })}>
            {failed ? '分享复盘' : '分享战绩'}
          </View>
          <View className='btn-comic btn-primary btn-sm' onClick={restart}>再来一局</View>
        </View>
      </View>
    </View>
  )
}
