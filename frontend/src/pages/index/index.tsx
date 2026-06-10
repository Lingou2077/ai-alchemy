import { Text, Textarea, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useCallback, useEffect, useMemo, useState } from 'react'

import MainTabBar from '@/components/MainTabBar'
import { EXAMPLE_CHIPS, MAX_CONTENT_LENGTH } from '@/constants'
import { loadHistoryItems } from '@/services/storage'
import { fetchQuizHistory } from '@/services/userApi'
import { useSessionStore } from '@/stores/sessionStore'
import { useUserStore } from '@/stores/userStore'
import type { HistoryItem, QuizHistoryItem } from '@/types/session'
import { accuracyRingClass, accuracyRingProgressStyle, formatRelativeTime } from '@/utils/formatTime'
import { switchMainTab } from '@/utils/mainTab'

import './index.scss'

function mapServerHistory(item: QuizHistoryItem): HistoryItem {
  return {
    sessionId: item.sessionId,
    topic: item.topic,
    accuracy: item.accuracy,
    questionCount: item.questionCount,
    finishedAt: new Date(item.finishedAt).getTime() || Date.now(),
  }
}

export default function IndexPage() {
  const [content, setContent] = useState('')
  const [webResearchEnabled, setWebResearchEnabled] = useState(false)
  const [showError, setShowError] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const token = useUserStore((state) => state.token)
  const user = useUserStore((state) => state.user)
  const setSession = useSessionStore((state) => state.setSession)

  const loadRecentHistory = useCallback(async () => {
    if (token) {
      try {
        const result = await fetchQuizHistory(1, 2)
        setHistory(result.items.map(mapServerHistory))
        return
      } catch {
        // 登录态失效时回退本地历史
      }
    }
    const localItems = await loadHistoryItems()
    setHistory(localItems)
  }, [token])

  useEffect(() => {
    loadRecentHistory()
  }, [loadRecentHistory])

  Taro.useDidShow(() => {
    loadRecentHistory()
    const { token: authToken, refreshProfile } = useUserStore.getState()
    if (authToken) {
      refreshProfile().catch(() => undefined)
    }
  })

  const count = content.length
  const tagline = useMemo(() => {
    if (showError) return '先写点啥吧'
    if (count > 0) return '开炼！'
    return '粘贴知识，炼成闯关题'
  }, [count, showError])

  const handlePaste = async () => {
    try {
      const clip = await Taro.getClipboardData()
      if (clip.data) {
        setContent(clip.data.slice(0, MAX_CONTENT_LENGTH))
        setShowError(false)
      }
    } catch {
      Taro.showToast({ title: '无法读取剪贴板', icon: 'none' })
    }
  }

  const handleExample = (text: string) => {
    setContent(text.slice(0, MAX_CONTENT_LENGTH))
    setShowError(false)
  }

  const handleStart = async () => {
    if (!content.trim()) {
      setShowError(true)
      return
    }
    setSession(null)
    const trimmed = content.trim()

    if (!webResearchEnabled) {
      Taro.navigateTo({
        url: `/pages/generating/index?content=${encodeURIComponent(trimmed)}`,
      })
      return
    }

    Taro.navigateTo({
      url: `/pages/generating/index?mode=research&content=${encodeURIComponent(trimmed)}`,
    })
  }

  const openHistoryList = () => {
    switchMainTab('bank')
  }

  const openHistoryDetail = (sessionId: string) => {
    if (token) {
      Taro.navigateTo({ url: `/pages/history-detail/index?sessionId=${encodeURIComponent(sessionId)}` })
    }
  }

  return (
    <View className='app-page phone-screen phone-screen--with-tab'>
      <View className='app-content app-content--with-tab'>
        <View className='home-header'>
          <View className='home-brand'>AI炼金</View>
          <View className='home-header-row'>
            <View className='home-tagline'>{tagline}</View>
            {user?.title ? <View className='home-user-title'>{user.title}</View> : null}
          </View>
        </View>

        <View className='input-simple'>
          {showError && (
            <View className='error-toast'>
              <Text>请输入学习内容</Text>
            </View>
          )}
          <View className={`input-card ${showError ? 'error' : ''}`}>
            <Textarea
              className='input-card-textarea'
              value={content}
              maxlength={MAX_CONTENT_LENGTH}
              placeholder='粘贴关键词、网页链接或学习材料…'
              onInput={(event) => {
                setContent(event.detail.value)
                if (event.detail.value.trim()) setShowError(false)
              }}
            />
            <View className='input-card-bar'>
              <View className='input-card-bar-left'>
                <View
                  className='web-research-inline'
                  onClick={() => setWebResearchEnabled((prev) => !prev)}
                >
                  <View className={`web-research-switch ${webResearchEnabled ? 'on' : ''}`}>
                    <View className='web-research-track'>
                      <View className='web-research-knob' />
                    </View>
                  </View>
                  <Text className='web-research-title'>联网搜索</Text>
                </View>
              </View>
              <View className='input-card-bar-center'>
                <View className='input-add-btn disabled'>+</View>
              </View>
              <View className='input-card-bar-actions'>
                <Text className={`input-counter ${showError ? 'warn' : ''}`}>{count}/{MAX_CONTENT_LENGTH}</Text>
                <Text className='input-paste-link' onClick={handlePaste}>
                  {count > 0 ? '重贴' : '粘贴'}
                </Text>
              </View>
            </View>
          </View>

          <View className='input-cta-row'>
            <View
              className={`btn-comic ${content.trim() ? 'btn-primary' : 'btn-disabled'}`}
              onClick={handleStart}
            >
              开始闯关
            </View>
          </View>
        </View>

        <View className='input-below'>
          <View className='input-examples-row'>
            <Text className='input-examples-label'>{showError ? '试试' : '示例'}</Text>
            {EXAMPLE_CHIPS.map((chip) => (
              <Text
                key={chip.label}
                className={`example-chip ${chip.hot ? 'hot' : ''}`}
                onClick={() => handleExample(chip.content)}
              >
                {chip.label}
              </Text>
            ))}
          </View>
          <View className='home-header-row home-recent-head'>
            <Text className='section-head-title'>最近炼成</Text>
            <Text className='section-head-more' onClick={openHistoryList}>全部</Text>
          </View>
          <View className='history-list'>
            {history.length === 0 ? (
              <View className='history-item history-item--empty'>
                <View className='history-info'>
                  <View className='history-title'>暂无记录</View>
                  <View className='history-meta'>完成一次闯关后会出现在这里</View>
                </View>
              </View>
            ) : (
              history.slice(0, 2).map((item) => (
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
                      {formatRelativeTime(new Date(item.finishedAt).toISOString())} · {item.questionCount} 题
                    </View>
                  </View>
                </View>
              ))
            )}
          </View>
        </View>
      </View>
      <MainTabBar active='home' />
    </View>
  )
}
