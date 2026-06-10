import { Canvas, Image, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useCallback, useEffect, useState } from 'react'

import { useSessionStore } from '@/stores/sessionStore'
import { switchMainTab } from '@/utils/mainTab'
import { POSTER_CANVAS_ID, POSTER_HEIGHT, POSTER_WIDTH, renderPosterToTempFile } from '@/utils/posterCanvas'
import { savePosterToAlbum, sharePosterImage } from '@/utils/posterShare'

import './index.scss'

type PosterStatus = 'idle' | 'drawing' | 'ready' | 'error'

export default function SharePage() {
  const report = useSessionStore((state) => state.report)
  const session = useSessionStore((state) => state.session)
  const [status, setStatus] = useState<PosterStatus>('idle')
  const [tempFilePath, setTempFilePath] = useState('')
  const [errorMessage, setErrorMessage] = useState('')

  const drawPoster = useCallback(async () => {
    if (!report || !session) return
    setStatus('drawing')
    setErrorMessage('')
    try {
      const path = await renderPosterToTempFile(report, session)
      setTempFilePath(path)
      setStatus('ready')
    } catch (error) {
      setStatus('error')
      setErrorMessage(error instanceof Error ? error.message : '海报绘制失败')
    }
  }, [report, session])

  Taro.useDidShow(() => {
    if (!report || !session) {
      switchMainTab('home')
    }
  })

  useEffect(() => {
    if (report && session) {
      void drawPoster()
    }
  }, [report, session, drawPoster])

  const handleSave = async () => {
    if (!tempFilePath) return
    try {
      await savePosterToAlbum(tempFilePath)
    } catch (error) {
      Taro.showToast({
        title: error instanceof Error ? error.message : '保存失败',
        icon: 'none',
      })
    }
  }

  const handleShare = () => {
    if (!tempFilePath) {
      Taro.showToast({ title: '海报尚未就绪', icon: 'none' })
      return
    }
    sharePosterImage(tempFilePath)
  }

  if (!report || !session) {
    return <View className='app-page' />
  }

  const actionsDisabled = status !== 'ready' || !tempFilePath

  return (
    <View className='app-page'>
      <View className='app-bar'>
        <View className='app-bar-back' onClick={() => Taro.navigateBack()}>←</View>
        <View className='app-bar-title'>分享战绩</View>
        <View style={{ width: '36px' }} />
      </View>
      <View className='app-content poster-page'>
        <View className='poster-hint'>
          {status === 'drawing' && '正在绘制海报…'}
          {status === 'ready' && '海报已生成，可保存或分享'}
          {status === 'error' && (errorMessage || '海报生成失败')}
        </View>

        {tempFilePath ? (
          <Image className='poster-preview' src={tempFilePath} mode='widthFix' showMenuByLongpress />
        ) : (
          <View className='poster-preview poster-preview--placeholder'>
            {status === 'drawing' ? '绘制中…' : ' '}
          </View>
        )}

        <Canvas
          type='2d'
          id={POSTER_CANVAS_ID}
          canvasId={POSTER_CANVAS_ID}
          className='poster-canvas-hidden'
          style={{ width: `${POSTER_WIDTH}px`, height: `${POSTER_HEIGHT}px` }}
        />

        {status === 'error' && (
          <View className='btn-comic btn-secondary btn-sm poster-retry' onClick={() => void drawPoster()}>
            重试
          </View>
        )}

        <View className='poster-actions'>
          <View
            className={`btn-comic btn-secondary btn-sm${actionsDisabled ? ' btn-disabled' : ''}`}
            onClick={actionsDisabled ? undefined : () => void handleSave()}
          >
            保存相册
          </View>
          <View
            className={`btn-comic btn-amber btn-sm${actionsDisabled ? ' btn-disabled' : ''}`}
            onClick={actionsDisabled ? undefined : handleShare}
          >
            分享海报
          </View>
        </View>
      </View>
    </View>
  )
}
