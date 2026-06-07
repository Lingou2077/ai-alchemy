import { Text, Textarea, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useEffect, useMemo, useState } from 'react'

import MainTabBar from '@/components/MainTabBar'
import { EXAMPLE_CHIPS, MAX_CONTENT_LENGTH, PLACEHOLDER_MESSAGE } from '@/constants'
import { loadHistoryItems } from '@/services/storage'
import { useSessionStore } from '@/stores/sessionStore'
import type { HistoryItem } from '@/types/session'

import './index.scss'

export default function IndexPage() {
  const [content, setContent] = useState('')
  const [showError, setShowError] = useState(false)
  const [history, setHistory] = useState<HistoryItem[]>([])
  const setSession = useSessionStore((state) => state.setSession)

  useEffect(() => {
    loadHistoryItems().then(setHistory)
  }, [])

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

  const handleStart = () => {
    if (!content.trim()) {
      setShowError(true)
      return
    }
    setSession(null)
    Taro.navigateTo({
      url: `/pages/generating/index?content=${encodeURIComponent(content.trim())}`,
    })
  }

  const showPlaceholder = () => {
    Taro.showToast({ title: PLACEHOLDER_MESSAGE, icon: 'none' })
  }

  return (
    <View className='app-page phone-screen phone-screen--with-tab'>
      <View className='app-content app-content--with-tab'>
        <View className='home-header'>
          <View className='home-brand'>AI炼金</View>
          <View className='home-tagline'>{tagline}</View>
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
              placeholder='粘贴你想学习的知识…'
              onInput={(event) => {
                setContent(event.detail.value)
                if (event.detail.value.trim()) setShowError(false)
              }}
            />
            <View className='input-card-bar'>
              <View className='input-add-btn disabled'>+</View>
              <Text className='input-card-hint'>文档·链接 即将上线</Text>
              <Text className={`input-counter ${showError ? 'warn' : ''}`}>{count}/{MAX_CONTENT_LENGTH}</Text>
              <Text className='input-paste-link' onClick={handlePaste}>
                {count > 0 ? '重贴' : '粘贴'}
              </Text>
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
          <View className='section-head'>
            <Text className='section-head-title'>最近炼成</Text>
            <Text className='section-head-more' onClick={showPlaceholder}>全部</Text>
          </View>
          <View className='history-list'>
            {history.length === 0 ? (
              <View className='history-item history-item--empty' onClick={showPlaceholder}>
                <View className='history-info'>
                  <View className='history-title'>暂无记录</View>
                  <View className='history-meta'>完成一次闯关后会出现在这里</View>
                </View>
              </View>
            ) : (
              history.slice(0, 2).map((item) => (
                <View key={item.sessionId} className='history-item' onClick={showPlaceholder}>
                  <View className={`history-score-ring ${item.accuracy >= 80 ? 'good' : item.accuracy >= 60 ? 'mid' : 'low'}`}>
                    {Math.round(item.accuracy)}
                  </View>
                  <View className='history-info'>
                    <View className='history-title'>{item.topic}</View>
                    <View className='history-meta'>{item.questionCount} 题 · {Math.round(item.accuracy)}%</View>
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
