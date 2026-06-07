import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'

import { PLACEHOLDER_MESSAGE } from '@/constants'
import { useSessionStore } from '@/stores/sessionStore'

import './index.scss'

export default function SharePage() {
  const report = useSessionStore((state) => state.report)
  const session = useSessionStore((state) => state.session)

  Taro.useDidShow(() => {
    if (!report || !session) {
      Taro.redirectTo({ url: '/pages/index/index' })
    }
  })

  const showPlaceholder = () => {
    Taro.showToast({ title: PLACEHOLDER_MESSAGE, icon: 'none' })
  }

  if (!report || !session) {
    return <View className='app-page' />
  }

  const failed = session.status === 'failed' || session.hearts <= 0

  return (
    <View className='app-page'>
      <View className='app-bar'>
        <View className='app-bar-back' onClick={() => Taro.navigateBack()}>←</View>
        <View className='app-bar-title'>分享战绩</View>
        <View style={{ width: '36px' }} />
      </View>
      <View className='app-content poster-page'>
        <View className='poster-hint'>海报已生成，可保存或分享（Phase 1 占位）</View>
        <View className={`share-poster ${failed ? '' : 'share-poster--success'}`}>
          <View className='share-poster-brand'>AI炼金</View>
          <View className={`share-poster-badge ${failed ? 'fail' : 'success'}`}>
            {failed ? '灵韵散尽…' : '炼成成功！'}
          </View>
          <View className='share-poster-score'>{Math.round(report.accuracy)}<Text>%</Text></View>
          <View className='share-poster-topic'>{report.topic}</View>
          <View className='share-poster-stats'>
            用时 {report.duration} 秒 · 对 {report.correctCount} 错 {report.wrongCount}
          </View>
          <View className='share-poster-footer'>
            <View className='share-poster-qr'><View className='qr-grid' /></View>
            <View className='share-poster-qr-text'>
              <Text className='strong'>扫码一起炼金</Text>
              <Text>长按识别小程序码</Text>
            </View>
          </View>
        </View>
        <View className='poster-actions'>
          <View className='btn-comic btn-secondary btn-sm' onClick={showPlaceholder}>保存相册</View>
          <View className='btn-comic btn-amber btn-sm' onClick={showPlaceholder}>分享海报</View>
        </View>
      </View>
    </View>
  )
}
