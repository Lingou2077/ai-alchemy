import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useEffect } from 'react'

import LingyunBadge from '@/components/LingyunBadge'
import { saveCurrentSession } from '@/services/storage'
import { useSessionStore } from '@/stores/sessionStore'
import { switchMainTab } from '@/utils/mainTab'
import {
  accuracyRingClass,
  accuracyRingProgressStyle,
  formatRelativeTime,
  resolveQuizDurationSec,
} from '@/utils/formatTime'

import './index.scss'

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
      switchMainTab('home')
    }
  })

  useEffect(() => {
    if (report?.expGain?.leveledUp) {
      Taro.showModal({
        title: '恭喜晋升！',
        content: `你已升至 Lv.${report.expGain.newLevel} · ${report.expGain.newTitle}`,
        showCancel: false,
      })
    }
  }, [report?.expGain?.leveledUp, report?.expGain?.newLevel, report?.expGain?.newTitle])

  if (!session || !report) {
    return <View className='app-page' />
  }

  const failed = session.status === 'failed' || session.hearts <= 0
  const weakNames = report.weakPoints.length
    ? report.weakPoints.map((item) => item.name)
    : session.levels.flatMap((level) => level.questions.flatMap((q) => q.conceptTags)).slice(0, 3)

  const compareValue = report.stats?.compareLastAccuracy
  const weeklyIndex = report.stats?.weeklyQuizIndex
  const relatedHistory = report.stats?.relatedHistory ?? []

  const displayDuration = resolveQuizDurationSec(session.answers, report.duration)

  const restart = async () => {
    resetFlow()
    await saveCurrentSession(null)
    switchMainTab('home')
  }

  const openHistoryDetail = (sessionId: string) => {
    Taro.navigateTo({ url: `/pages/history-detail/index?sessionId=${encodeURIComponent(sessionId)}` })
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
              {failed ? '灵韵散尽…' : '炼金成功！'}
            </View>
            <View className={`report-score ${failed ? 'report-score--fail' : ''}`}>
              {Math.round(report.accuracy)}<Text className='report-score-unit'>%</Text>
            </View>
          </View>
          <View className='report-summary-side'>
            <View className='report-stats'>
              <Text>用时 <Text className='strong'>{displayDuration}</Text> 秒</Text>
              <Text>对 <Text className='strong'>{report.correctCount}</Text> · 错 <Text className='strong'>{report.wrongCount}</Text></Text>
            </View>
            {(compareValue !== null && compareValue !== undefined) || weeklyIndex ? (
              <View className='report-compare'>
                {compareValue !== null && compareValue !== undefined && (
                  <Text className={`compare-pill ${compareValue >= 0 ? 'up' : 'down'}`}>
                    比上次
                    <Text className='compare-pill-sign'>{compareValue >= 0 ? '+' : '-'}</Text>
                    {Math.abs(compareValue)}%
                  </Text>
                )}
                {weeklyIndex ? (
                  <Text className='compare-pill'>本周第 {weeklyIndex} 次</Text>
                ) : null}
              </View>
            ) : null}
          </View>
        </View>

        {(report.expGain?.amount > 0 || failed) && (
          <View className='report-exp-row'>
            {report.expGain && report.expGain.amount > 0 && (
              <View className='report-exp-banner report-card'>
                <Text className='report-exp-amount'>+{report.expGain.amount} EXP</Text>
                {report.expGain.leveledUp && (
                  <Text className='report-exp-level'>晋升 Lv.{report.expGain.newLevel}</Text>
                )}
              </View>
            )}
            {failed && (
              <View className='report-lingyun-card report-card'>
                <LingyunBadge hearts={0} large depleted showHint={false} />
              </View>
            )}
          </View>
        )}

        {report.syncFailed && (
          <View className='report-sync-warn'>云端同步失败，报告已正常展示</View>
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

        {!failed && relatedHistory.length > 0 && (
          <View className='report-related-section'>
            <View className='section-head'>
              <Text className='section-head-title'>相关历史</Text>
            </View>
            <View className='history-list'>
              {relatedHistory.map((item) => (
                <View
                  key={item.sessionId}
                  className='history-item'
                  onClick={() => openHistoryDetail(item.sessionId)}
                >
                  <View
                    className={`history-score-ring history-score-ring--progress ${accuracyRingClass(item.accuracy)}`}
                    style={accuracyRingProgressStyle(item.accuracy)}
                  >
                    {Math.round(item.accuracy)}
                  </View>
                  <View className='history-info'>
                    <View className='history-title'>{item.topic}</View>
                    <View className='history-meta'>
                      {formatRelativeTime(item.finishedAt)} · {Math.round(item.accuracy)}%
                    </View>
                  </View>
                </View>
              ))}
            </View>
          </View>
        )}

        {failed && (
          <View className='report-wrong-section'>
            <View className='section-head'>
              <Text className='section-head-title'>错题将自动收录</Text>
            </View>
            <View className='history-list'>
              {session.answers.filter((item) => !item.isCorrect).map((item) => {
                const question = session.levels.flatMap((level) => level.questions).find((q) => q.id === item.questionId)
                return (
                  <View key={item.questionId} className='history-item history-item--static'>
                    <View className='history-score-ring low history-score-ring--icon'>错</View>
                    <View className='history-info'>
                      <View className='history-title'>{question?.stem || item.questionId}</View>
                      <View className='history-meta'>已收录至错题本</View>
                    </View>
                  </View>
                )
              })}
            </View>
          </View>
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
