import { Button, Image, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useCallback, useState } from 'react'

import MainTabBar from '@/components/MainTabBar'
import { useUserStore } from '@/stores/userStore'

import './index.scss'

export default function ProfilePage() {
  const user = useUserStore((state) => state.user)
  const loading = useUserStore((state) => state.loading)
  const loginError = useUserStore((state) => state.loginError)
  const login = useUserStore((state) => state.login)
  const updateUserProfile = useUserStore((state) => state.updateUserProfile)
  const [syncing, setSyncing] = useState(false)

  Taro.useDidShow(() => {
    const { token, refreshProfile } = useUserStore.getState()
    if (token) {
      refreshProfile().catch(() => undefined)
    }
  })

  const handleLogin = async () => {
    const ok = await login()
    if (!ok) {
      Taro.showToast({ title: loginError || '登录失败', icon: 'none' })
    }
  }

  const handleChooseAvatar = useCallback(
    async (event: { detail: { avatarUrl: string } }) => {
      const avatarUrl = event.detail.avatarUrl
      if (!avatarUrl) return
      try {
        setSyncing(true)
        await updateUserProfile({ avatarUrl })
        Taro.showToast({ title: '头像已更新', icon: 'success' })
      } catch (error) {
        Taro.showToast({
          title: error instanceof Error ? error.message : '更新失败',
          icon: 'none',
        })
      } finally {
        setSyncing(false)
      }
    },
    [updateUserProfile],
  )

  const handleSyncWechatProfile = async () => {
    try {
      setSyncing(true)
      const profile = await Taro.getUserProfile({ desc: '用于完善个人资料' })
      await updateUserProfile({
        nickname: profile.userInfo.nickName,
        avatarUrl: profile.userInfo.avatarUrl,
      })
      Taro.showToast({ title: '资料已同步', icon: 'success' })
    } catch {
      Taro.showToast({ title: '未授权微信资料', icon: 'none' })
    } finally {
      setSyncing(false)
    }
  }

  const openHistory = () => {
    Taro.navigateTo({ url: '/pages/history/index' })
  }

  const openWrongBook = () => {
    Taro.navigateTo({ url: '/pages/wrong-book/index' })
  }

  const expPercent = user
    ? Math.min(100, Math.round((user.expProgress.current / Math.max(user.expProgress.required, 1)) * 100))
    : 0

  if (!user) {
    return (
      <View className='app-page phone-screen phone-screen--with-tab'>
        <View className='app-content app-content--with-tab profile-page'>
          <View className='profile-header'>
            <View className='home-brand'>我的炼金室</View>
            <View className='home-tagline'>登录后同步学习记录</View>
          </View>
          <View className='profile-login-card report-card'>
            <View className='profile-login-title'>尚未登录</View>
            <View className='profile-login-desc'>
              登录后可查看等级、学习历史与错题本。不影响首页闯关体验。
            </View>
            <View
              className={`btn-comic btn-primary ${loading ? 'btn-disabled' : ''}`}
              onClick={loading ? undefined : handleLogin}
            >
              {loading ? '登录中…' : '微信登录'}
            </View>
          </View>
        </View>
        <MainTabBar active='profile' />
      </View>
    )
  }

  return (
    <View className='app-page phone-screen phone-screen--with-tab'>
      <View className='app-content app-content--with-tab profile-page'>
        <View className='profile-header'>
          <View className='home-brand'>我的炼金室</View>
          <View className='home-tagline'>{user.title}</View>
        </View>

        <View className='profile-user-card report-card'>
          <View className='profile-user-main'>
            <Button
              className='profile-avatar-btn'
              openType='chooseAvatar'
              onChooseAvatar={handleChooseAvatar}
              disabled={syncing}
            >
              {user.avatarUrl ? (
                <Image className='profile-avatar' src={user.avatarUrl} mode='aspectFill' />
              ) : (
                <View className='profile-avatar profile-avatar--placeholder'>
                  <Text>{user.nickname.slice(0, 1)}</Text>
                </View>
              )}
            </Button>
            <View className='profile-user-info'>
              <View className='profile-nickname'>{user.nickname}</View>
              <View className='profile-meta'>Lv.{user.level} · {user.title}</View>
            </View>
          </View>
          <View className='profile-sync-row'>
            <View
              className={`btn-comic btn-secondary btn-sm ${syncing ? 'btn-disabled' : ''}`}
              onClick={syncing ? undefined : handleSyncWechatProfile}
            >
              同步微信资料
            </View>
          </View>
        </View>

        <View className='profile-section report-card'>
          <View className='report-section-title'>成长进度</View>
          <View className='profile-exp-row'>
            <Text className='profile-exp-label'>EXP</Text>
            <Text className='profile-exp-value'>
              {user.expProgress.current}/{user.expProgress.required}
            </Text>
          </View>
          <View className='profile-exp-bar'>
            <View className='profile-exp-fill' style={{ width: `${expPercent}%` }} />
          </View>
          <View className='profile-exp-total'>累计 {user.expProgress.totalExp} EXP</View>
        </View>

        <View className='profile-stats-grid'>
          <View className='profile-stat-card report-card'>
            <View className='profile-stat-value'>{user.stats.totalQuizzes}</View>
            <View className='profile-stat-label'>累计炼成</View>
          </View>
          <View className='profile-stat-card report-card'>
            <View className='profile-stat-value'>
              {user.stats.averageAccuracy > 0 ? `${Math.round(user.stats.averageAccuracy)}%` : '—'}
            </View>
            <View className='profile-stat-label'>平均正确率</View>
          </View>
        </View>

        <View className='section-head'>
          <Text className='section-head-title'>数据中心</Text>
        </View>
        <View className='history-list'>
          <View className='history-item' onClick={openHistory}>
            <View className='history-score-ring mid'>历</View>
            <View className='history-info'>
              <View className='history-title'>学习历史</View>
              <View className='history-meta'>查看全部闯关记录</View>
            </View>
          </View>
          <View className='history-item' onClick={openWrongBook}>
            <View className='history-score-ring low'>错</View>
            <View className='history-info'>
              <View className='history-title'>错题本</View>
              <View className='history-meta'>
                {user.stats.wrongQuestionCount > 0
                  ? `已收录 ${user.stats.wrongQuestionCount} 道错题`
                  : '答错的题目会自动收录'}
              </View>
            </View>
          </View>
        </View>
      </View>
      <MainTabBar active='profile' />
    </View>
  )
}
