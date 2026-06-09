import { ScrollView, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'

import './index.scss'

export interface VirtualListProps<T> {
  items: T[]
  itemHeight: number
  itemGap?: number
  renderItem: (item: T, index: number) => ReactNode
  keyExtractor: (item: T, index: number) => string | number
  onScrollToLower?: () => void
  lowerThreshold?: number
  footer?: ReactNode
  className?: string
  overscan?: number
}

export default function VirtualList<T>({
  items,
  itemHeight,
  itemGap = 8,
  renderItem,
  keyExtractor,
  onScrollToLower,
  lowerThreshold = 120,
  footer,
  className = '',
  overscan = 4,
}: VirtualListProps<T>) {
  const rowStride = itemHeight + itemGap
  const [scrollTop, setScrollTop] = useState(0)
  const [viewHeight, setViewHeight] = useState(640)

  useEffect(() => {
    const timer = setTimeout(() => {
      Taro.createSelectorQuery()
        .select('.virtual-list__scroll')
        .boundingClientRect((rect) => {
          if (rect && !Array.isArray(rect) && rect.height > 0) {
            setViewHeight(rect.height)
          }
        })
        .exec()
    }, 0)
    return () => clearTimeout(timer)
  }, [items.length])

  const windowRange = useMemo(() => {
    const total = items.length
    if (total === 0) {
      return { start: 0, end: -1, paddingTop: 0, paddingBottom: 0 }
    }

    const start = Math.max(0, Math.floor(scrollTop / rowStride) - overscan)
    const visibleCount = Math.ceil(viewHeight / rowStride) + overscan * 2
    const end = Math.min(total - 1, start + visibleCount)

    return {
      start,
      end,
      paddingTop: start * rowStride,
      paddingBottom: Math.max(0, (total - end - 1) * rowStride),
    }
  }, [items.length, overscan, rowStride, scrollTop, viewHeight])

  const visibleItems = useMemo(
    () => items.slice(windowRange.start, windowRange.end + 1),
    [items, windowRange.end, windowRange.start],
  )

  const onScroll = useCallback((event: { detail: { scrollTop: number } }) => {
    setScrollTop(event.detail.scrollTop)
  }, [])

  return (
    <ScrollView
      className={`virtual-list__scroll ${className}`.trim()}
      scrollY
      enhanced
      showScrollbar={false}
      lowerThreshold={lowerThreshold}
      onScroll={onScroll}
      onScrollToLower={onScrollToLower}
    >
      <View
        className='virtual-list__inner'
        style={{
          paddingTop: `${windowRange.paddingTop}px`,
          paddingBottom: `${windowRange.paddingBottom}px`,
        }}
      >
        {visibleItems.map((item, offset) => {
          const index = windowRange.start + offset
          return (
            <View
              key={keyExtractor(item, index)}
              className='virtual-list__row'
              style={{ height: `${itemHeight}px`, marginBottom: `${itemGap}px` }}
            >
              {renderItem(item, index)}
            </View>
          )
        })}
      </View>
      {footer}
    </ScrollView>
  )
}
