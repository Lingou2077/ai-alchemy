import { Text, View } from '@tarojs/components'
import Taro, { useRouter } from '@tarojs/taro'
import { useEffect, useMemo } from 'react'

import { flaskFullDataUrl } from '@/assets/flaskSvg'
import { generateQuestions, mapGenerateResponseToSession } from '@/services/api'
import { saveCurrentSession } from '@/services/storage'
import { useSessionStore } from '@/stores/sessionStore'

import './index.scss'

export default function GeneratingPage() {
  const router = useRouter()
  const setSession = useSessionStore((state) => state.setSession)
  const setFailMessage = useSessionStore((state) => state.setFailMessage)
  const content = decodeURIComponent(router.params.content || '')
  const flaskIcon = useMemo(() => flaskFullDataUrl(), [])

  useEffect(() => {
    let cancelled = false

    const run = async () => {
      try {
        const response = await generateQuestions(content, 5)
        if (cancelled) return
        const session = mapGenerateResponseToSession(content, response)
        setSession(session)
        await saveCurrentSession(session)
        if (response.truncated) {
          Taro.showToast({ title: '内容已截断至前 4000 字', icon: 'none' })
        }
        Taro.redirectTo({ url: '/pages/quiz/index' })
      } catch (error) {
        if (cancelled) return
        const message = error instanceof Error ? error.message : '知识解析失败，请精简内容后重试'
        setFailMessage(message)
        Taro.redirectTo({ url: '/pages/generate-fail/index' })
      }
    }

    run()
    return () => {
      cancelled = true
    }
  }, [content, setFailMessage, setSession])

  return (
    <View className='app-page generating-page'>
      <View className='app-bar'>
        <View className='app-bar-title'>AI炼金</View>
      </View>
      <View className='app-content loading-page'>
        <View className='loading-center'>
          <View
            className='loading-flask loading-flask--animated'
            style={{ backgroundImage: `url("${flaskIcon}")` }}
          />
          <View className='loading-text'>AI 正在准备关卡…</View>
          <View className='loading-progress'>
            <View className='loading-progress-bar' />
          </View>
          <View className='loading-sub'>结构化知识 → 生成题目</View>
        </View>

        <View className='section-head'>
          <Text className='section-head-title'>本次素材</Text>
        </View>
        <View className='report-card material-preview'>{content.slice(0, 80)}{content.length > 80 ? '…' : ''}（{content.length} 字）</View>

        <View className='loading-tips'>
          <View className='loading-tips-title'>温馨提示</View>
          <View className='loading-tips-item'>每关 3–5 题，约 3–5 分钟完成</View>
          <View className='loading-tips-item'>答错散逸 1 缕灵韵，炼金炉药液代表三次机会</View>
          <View className='loading-tips-item'>通关后 AI 生成个性化复盘报告</View>
        </View>
      </View>
    </View>
  )
}
