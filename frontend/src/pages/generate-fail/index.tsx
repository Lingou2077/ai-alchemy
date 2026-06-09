import { ScrollView, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'

import { MAX_CONTENT_LENGTH } from '@/constants'

import './index.scss'

export default function GenerateFailPage() {
  return (
    <View className='app-page generate-fail-page'>
      <View className='app-bar'>
        <View className='app-bar-title'>AI炼金</View>
      </View>

      <ScrollView scrollY className='generate-fail-scroll' enhanced showScrollbar={false}>
        <View className='generate-fail-body'>
          <View className='fail-illust'>
            <View className='deco-exclaim'>!</View>
          </View>
          <View className='fail-msg'>知识解析失败</View>

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
          <View className='history-list fail-suggest-list'>
            <View className='history-item'>
              <View className='history-score-ring tip-badge history-score-ring--icon'>1</View>
              <View className='history-info'>
                <View className='history-title'>精简至 {MAX_CONTENT_LENGTH} 字以内</View>
              </View>
            </View>
            <View className='history-item'>
              <View className='history-score-ring tip-badge history-score-ring--icon'>2</View>
              <View className='history-info'>
                <View className='history-title'>检查网络后重试</View>
              </View>
            </View>
          </View>
        </View>
      </ScrollView>

      <View className='generate-fail-footer'>
        <View className='btn-comic btn-secondary' onClick={() => Taro.navigateBack()}>返回修改</View>
        <View className='btn-comic btn-primary' onClick={() => Taro.navigateBack()}>重新尝试</View>
      </View>
    </View>
  )
}
