import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useCallback, useRef, useState } from 'react'

import VirtualList from '@/components/VirtualList'
import { fetchWrongQuestions } from '@/services/userApi'
import type { WrongQuestionItem } from '@/types/session'
import { formatRelativeTime } from '@/utils/formatTime'

import '../history/index.scss'
import './index.scss'

const PAGE_SIZE = 20
const ROW_HEIGHT = 92
const ROW_GAP = 8

export default function WrongBookPage() {
  const [items, setItems] = useState<WrongQuestionItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [hasMore, setHasMore] = useState(false)
  const [total, setTotal] = useState(0)
  const pageRef = useRef(1)

  const applyPageResult = useCallback(
    (nextItems: WrongQuestionItem[], page: number, nextTotal: number, append: boolean) => {
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
      const result = await fetchWrongQuestions(1, PAGE_SIZE)
      applyPageResult(result.items, 1, result.total, false)
    } catch (error) {
      Taro.showToast({
        title: error instanceof Error ? error.message : '加载失败',
        icon: 'none',
      })
    } finally {
      setLoading(false)
    }
  }, [applyPageResult])

  const loadMore = useCallback(async () => {
    if (loadingMore || !hasMore) return
    setLoadingMore(true)
    try {
      const nextPage = pageRef.current + 1
      const result = await fetchWrongQuestions(nextPage, PAGE_SIZE)
      applyPageResult(result.items, nextPage, result.total, true)
    } catch (error) {
      Taro.showToast({
        title: error instanceof Error ? error.message : '加载更多失败',
        icon: 'none',
      })
    } finally {
      setLoadingMore(false)
    }
  }, [applyPageResult, hasMore, loadingMore])

  Taro.useDidShow(() => {
    loadFirstPage()
  })

  const openDetail = (id: number) => {
    Taro.navigateTo({ url: `/pages/wrong-book-detail/index?id=${id}` })
  }

  const listFooter = loadingMore ? (
    <View className='list-footer-tip'>加载更多…</View>
  ) : hasMore ? (
    <View className='list-footer-tip'>上拉加载更多错题</View>
  ) : items.length > 0 ? (
    <View className='list-footer-tip'>已显示全部错题</View>
  ) : null

  return (
    <View className='app-page app-page--stacked'>
      <View className='app-bar'>
        <View className='app-bar-back' onClick={() => Taro.navigateBack()}>
          <Text>{'<'}</Text>
        </View>
        <View className='app-bar-title'>错题本</View>
        <View style={{ width: '36px' }} />
      </View>

      <View className='app-content sub-page wrong-book-page'>
        {total > 0 && (
          <View className='wrong-book-summary'>共 {total} 道错题</View>
        )}

        {loading ? (
          <View className='report-card sub-page-empty'>加载中…</View>
        ) : items.length === 0 ? (
          <View className='report-card sub-page-empty'>
            <View className='sub-page-empty-title'>暂无错题</View>
            <View className='sub-page-empty-desc'>答错的题目会自动收录到这里</View>
          </View>
        ) : (
          <VirtualList
            items={items}
            itemHeight={ROW_HEIGHT}
            itemGap={ROW_GAP}
            keyExtractor={(item) => item.id}
            onScrollToLower={loadMore}
            footer={listFooter}
            renderItem={(item) => (
              <View className='history-item wrong-book-item' onClick={() => openDetail(item.id)}>
                <View className='history-score-ring low history-score-ring--icon wrong-book-ring'>错</View>
                <View className='history-info'>
                  <View className='history-title wrong-book-stem'>{item.stem}</View>
                  <View className='history-meta'>
                    {item.topic} · {formatRelativeTime(item.lastWrongAt)} · 错 {item.wrongCount} 次
                  </View>
                </View>
              </View>
            )}
          />
        )}
      </View>
    </View>
  )
}
