import { View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useCallback, useRef, useState } from 'react'

import MainTabBar from '@/components/MainTabBar'
import VirtualList from '@/components/VirtualList'
import { loadHistoryItems, removeHistoryItem } from '@/services/storage'
import { deleteQuizHistory, fetchQuizHistory } from '@/services/userApi'
import { useUserStore } from '@/stores/userStore'
import type { HistoryItem, QuizHistoryItem } from '@/types/session'
import { accuracyRingClass, accuracyRingProgressStyle, formatRelativeTime } from '@/utils/formatTime'

import '../history/index.scss'
import './index.scss'

const PAGE_SIZE = 20
const ROW_HEIGHT = 76
const ROW_GAP = 8

type DisplayHistoryItem = HistoryItem & { status?: QuizHistoryItem['status'] }

function mapServerHistory(item: QuizHistoryItem): DisplayHistoryItem {
  return {
    sessionId: item.sessionId,
    topic: item.topic,
    accuracy: item.accuracy,
    questionCount: item.questionCount,
    finishedAt: new Date(item.finishedAt).getTime() || Date.now(),
    status: item.status,
  }
}

export default function QuestionBankPage() {
  const token = useUserStore((state) => state.token)
  const refreshProfile = useUserStore((state) => state.refreshProfile)
  const [items, setItems] = useState<DisplayHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [total, setTotal] = useState(0)
  const pageRef = useRef(1)

  const applyPageResult = useCallback(
    (nextItems: DisplayHistoryItem[], page: number, nextTotal: number, append: boolean) => {
      setItems((prev) => (append ? [...prev, ...nextItems] : nextItems))
      setTotal(nextTotal)
      pageRef.current = page
      setHasMore(page * PAGE_SIZE < nextTotal)
    },
    [],
  )

  const loadFirstPage = useCallback(async () => {
    setLoading(true)
    try {
      if (token) {
        const result = await fetchQuizHistory(1, PAGE_SIZE)
        applyPageResult(result.items.map(mapServerHistory), 1, result.total, false)
        return
      }
      const localItems = await loadHistoryItems()
      applyPageResult(localItems, 1, localItems.length, false)
    } catch (error) {
      if (token) {
        Taro.showToast({
          title: error instanceof Error ? error.message : '加载失败',
          icon: 'none',
        })
      }
      const localItems = await loadHistoryItems()
      applyPageResult(localItems, 1, localItems.length, false)
    } finally {
      setLoading(false)
    }
  }, [applyPageResult, token])

  const loadMore = useCallback(async () => {
    if (!token || loadingMore || !hasMore) return
    setLoadingMore(true)
    try {
      const nextPage = pageRef.current + 1
      const result = await fetchQuizHistory(nextPage, PAGE_SIZE)
      applyPageResult(result.items.map(mapServerHistory), nextPage, result.total, true)
    } catch (error) {
      Taro.showToast({
        title: error instanceof Error ? error.message : '加载更多失败',
        icon: 'none',
      })
    } finally {
      setLoadingMore(false)
    }
  }, [applyPageResult, hasMore, loadingMore, token])

  Taro.useDidShow(() => {
    loadFirstPage()
  })

  const openDetail = (sessionId: string) => {
    if (!token) {
      Taro.showToast({ title: '登录后可查看详情', icon: 'none' })
      return
    }
    Taro.navigateTo({ url: `/pages/history-detail/index?sessionId=${encodeURIComponent(sessionId)}` })
  }

  const handleDelete = (sessionId: string) => {
    Taro.showModal({
      title: '删除记录',
      content: '确定删除这条闯关记录吗？删除后不可恢复。',
      confirmText: '删除',
      confirmColor: '#E53935',
      success: async (result) => {
        if (!result.confirm) return
        try {
          if (token) {
            await deleteQuizHistory(sessionId)
            await refreshProfile().catch(() => undefined)
          } else {
            await removeHistoryItem(sessionId)
          }
          setItems((prev) => prev.filter((item) => item.sessionId !== sessionId))
          setTotal((prev) => {
            const nextTotal = Math.max(0, prev - 1)
            setHasMore(pageRef.current * PAGE_SIZE < nextTotal)
            return nextTotal
          })
          Taro.showToast({ title: '已删除', icon: 'success' })
        } catch (error) {
          Taro.showToast({
            title: error instanceof Error ? error.message : '删除失败',
            icon: 'none',
          })
        }
      },
    })
  }

  const listFooter = loadingMore ? (
    <View className='list-footer-tip'>加载更多…</View>
  ) : hasMore ? (
    <View className='list-footer-tip'>上拉加载更早记录</View>
  ) : items.length > 0 ? (
    <View className='list-footer-tip'>已显示全部记录</View>
  ) : null

  return (
    <View className='app-page phone-screen phone-screen--with-tab'>
      <View className='app-content app-content--with-tab question-bank-page'>
        <View className='question-bank-header'>
          <View className='home-tagline'>
            {token ? `全部闯关记录${total > 0 ? ` · 共 ${total} 条` : ''}` : '登录后同步云端记录'}
          </View>
        </View>

        {loading ? (
          <View className='report-card sub-page-empty'>加载中…</View>
        ) : items.length === 0 ? (
          <View className='report-card sub-page-empty'>
            <View className='sub-page-empty-title'>暂无历史记录</View>
            <View className='sub-page-empty-desc'>完成一次闯关后会出现在这里</View>
          </View>
        ) : (
          <VirtualList
            items={items}
            itemHeight={ROW_HEIGHT}
            itemGap={ROW_GAP}
            keyExtractor={(item) => item.sessionId}
            onScrollToLower={loadMore}
            footer={listFooter}
            renderItem={(item) => (
              <View className='history-item history-item--with-action question-bank-item'>
                <View className='history-item-main' onClick={() => openDetail(item.sessionId)}>
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
                      {item.status === 'failed' ? ' · 灵韵散尽' : ''}
                    </View>
                  </View>
                </View>
                <View
                  className='history-delete-btn'
                  onClick={(event) => {
                    event.stopPropagation()
                    handleDelete(item.sessionId)
                  }}
                >
                  删除
                </View>
              </View>
            )}
          />
        )}
      </View>
      <MainTabBar active='bank' />
    </View>
  )
}
