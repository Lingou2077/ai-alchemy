import { ScrollView, View } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'
import { useMemo, useState } from 'react'

import { EXPLORE_ALL_TOPIC_ID, type ResearchResponse } from '@/types/research'

import './index.scss'

function domainFromUrl(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

export default function TopicConfirmPage() {
  const router = useRouter()
  const content = decodeURIComponent(router.params.content || '')
  const researchPayload = decodeURIComponent(router.params.research || '{}')
  const research = useMemo(() => JSON.parse(researchPayload) as ResearchResponse, [researchPayload])
  const [selectedId, setSelectedId] = useState<string>('')

  const isDegraded = research.degradedMode !== 'none'
  const showExploreOption = !isDegraded

  const handleConfirm = () => {
    if (!selectedId) {
      Taro.showToast({ title: '请选择一个学习方向', icon: 'none' })
      return
    }
    const params = [
      `content=${encodeURIComponent(content)}`,
      `researchSessionId=${encodeURIComponent(research.researchSessionId)}`,
      `selectedTopicId=${encodeURIComponent(selectedId)}`,
      'webResearch=1',
    ].join('&')
    Taro.navigateTo({ url: `/pages/generating/index?${params}` })
  }

  return (
    <View className='app-page app-page--stacked topic-confirm-page'>
      <View className='app-bar'>
        <View className='app-bar-back' onClick={() => Taro.navigateBack()}>←</View>
        <View className='app-bar-title'>确认学习主题</View>
        <View style={{ width: '36px' }} />
      </View>

      <ScrollView scrollY className='topic-confirm-scroll' enhanced showScrollbar={false}>
        <View className='topic-confirm-body'>
          {research.mockMode ? (
            <View className='topic-banner topic-banner--mock'>当前为 Mock 联网检索（开发模式）</View>
          ) : null}

          {research.candidates.map((candidate) => (
            <View
              key={candidate.id}
              className={[
                'topic-card',
                selectedId === candidate.id ? 'topic-card--selected' : '',
                isDegraded ? 'topic-card--degraded' : '',
              ].filter(Boolean).join(' ')}
              onClick={() => setSelectedId(candidate.id)}
            >
              <View className='topic-card-title'>{candidate.title}</View>
              {candidate.sourceUrls.length > 0 ? (
                <View className='topic-card-meta'>
                  来源：{candidate.sourceUrls.slice(0, 2).map(domainFromUrl).join(' · ')}
                </View>
              ) : null}
            </View>
          ))}

          {showExploreOption ? (
            <View
              className={[
                'topic-card',
                'topic-card--explore',
                selectedId === EXPLORE_ALL_TOPIC_ID ? 'topic-card--selected' : '',
              ].filter(Boolean).join(' ')}
              onClick={() => setSelectedId(EXPLORE_ALL_TOPIC_ID)}
            >
              <View className='topic-card-title'>我不确定，先广泛了解一下</View>
            </View>
          ) : null}
        </View>
      </ScrollView>

      <View className='topic-confirm-footer'>
        <View className={`btn-comic ${selectedId ? 'btn-primary' : 'btn-disabled'}`} onClick={handleConfirm}>
          确认并开始闯关
        </View>
      </View>
    </View>
  )
}
