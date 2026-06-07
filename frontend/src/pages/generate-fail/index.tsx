import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'

import { useSessionStore } from '@/stores/sessionStore'

import './index.scss'

export default function GenerateFailPage() {
  const failMessage = useSessionStore((state) => state.failMessage)

  return (
    <View className='app-page'>
      <View className='app-bar'>
        <View className='app-bar-title'>AI炼金</View>
      </View>
      <View className='app-content'>
        <View className='fail-illust'>
          <View className='deco-exclaim'>!</View>
        </View>
        <View className='fail-msg'>{failMessage}</View>

        <View className='section-head'>
          <Text className='section-head-title'>可能的原因</Text>
        </View>
        <View className='report-card fail-card'>
          · 内容过长或格式杂乱{'\n'}
          · AI 响应超时（&gt;30s）{'\n'}
          · 网络连接不稳定
        </View>

        <View className='section-head'>
          <Text className='section-head-title'>建议操作</Text>
        </View>
        <View className='history-list'>
          <View className='history-item'>
            <View className='history-score-ring tip-badge'>1</View>
            <View className='history-info'>
              <View className='history-title'>精简至 2,000 字以内</View>
              <View className='history-meta'>去掉无关段落效果更好</View>
            </View>
          </View>
          <View className='history-item'>
            <View className='history-score-ring tip-badge'>2</View>
            <View className='history-info'>
              <View className='history-title'>检查网络后重试</View>
              <View className='history-meta'>单次完整闯关约 0.2–0.45 元</View>
            </View>
          </View>
        </View>

        <View className='input-sticky-cta'>
          <View className='btn-comic btn-secondary' onClick={() => Taro.navigateBack()}>返回修改</View>
          <View className='btn-comic btn-primary' onClick={() => Taro.navigateBack()}>重新尝试</View>
        </View>
      </View>
    </View>
  )
}
