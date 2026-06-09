import { Button, Image, Input, Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useCallback, useEffect, useState } from 'react'

import MainTabBar from '@/components/MainTabBar'
import { resolveAvatarSrc } from '@/services/userApi'
import { useUserStore } from '@/stores/userStore'
import { switchMainTab } from '@/utils/mainTab'
import { accuracyStatClass } from '@/utils/formatTime'

import './index.scss'

export default function ProfilePage() {
  const user = useUserStore((state) => state.user)
  const loading = useUserStore((state) => state.loading)
  const loginError = useUserStore((state) => state.loginError)
  const login = useUserStore((state) => state.login)
  const updateUserProfile = useUserStore((state) => state.updateUserProfile)
  const uploadUserAvatar = useUserStore((state) => state.uploadUserAvatar)
  const [syncing, setSyncing] = useState(false)
  const [nicknameDraft, setNicknameDraft] = useState('')
  const [nicknameFocus, setNicknameFocus] = useState(false)

  useEffect(() => {
    if (user?.nickname) {
      setNicknameDraft(user.nickname)
    }
  }, [user?.nickname])

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
        await uploadUserAvatar(avatarUrl)
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
    [uploadUserAvatar],
  )

  const saveNickname = useCallback(
    async (nickname: string) => {
      const trimmed = nickname.trim()
      if (!trimmed || trimmed === user?.nickname) return
      try {
        setSyncing(true)
        await updateUserProfile({ nickname: trimmed })
        Taro.showToast({ title: '昵称已更新', icon: 'success' })
      } catch (error) {
        Taro.showToast({
          title: error instanceof Error ? error.message : '更新失败',
          icon: 'none',
        })
      } finally {
        setSyncing(false)
      }
    },
    [updateUserProfile, user?.nickname],
  )

  const handleSyncWechatProfile = () => {
    if (syncing) return
    setNicknameFocus(true)
    Taro.showToast({ title: '请选择微信昵称', icon: 'none' })
  }

  const handleNicknameBlur = (event: { detail: { value: string } }) => {
    setNicknameFocus(false)
    void saveNickname(event.detail.value)
  }

  const avatarSrc = resolveAvatarSrc(user?.avatarUrl ?? '')

  const openHistory = () => {
    switchMainTab('bank')
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
        </View>

        <View className='profile-user-card report-card'>
          <View className='profile-user-main'>
            <Button
              className='profile-avatar-btn'
              openType='chooseAvatar'
              onChooseAvatar={handleChooseAvatar}
              disabled={syncing}
            >
              {avatarSrc ? (
                <Image className='profile-avatar' src={avatarSrc} mode='aspectFill' />
              ) : (
                <View className='profile-avatar profile-avatar--placeholder'>
                  <Text>{user.nickname.slice(0, 1)}</Text>
                </View>
              )}
            </Button>
            <View className='profile-user-info'>
              <Input
                className='profile-nickname-input'
                type='nickname'
                value={nicknameDraft}
                focus={nicknameFocus}
                placeholder='点击同步微信昵称'
                disabled={syncing}
                onInput={(event) => setNicknameDraft(event.detail.value)}
                onBlur={handleNicknameBlur}
                onConfirm={(event) => {
                  setNicknameFocus(false)
                  void saveNickname(event.detail.value)
                }}
              />
              <View className='profile-meta'>Lv.{user.level} · {user.title}</View>
            </View>
            <View
              className={`btn-comic btn-secondary btn-sm profile-sync-btn ${syncing ? 'btn-disabled' : ''}`}
              onClick={syncing ? undefined : handleSyncWechatProfile}
            >
              同步微信
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
          <View className={`profile-stat-card report-card profile-stat-card--${accuracyStatClass(user.stats.averageAccuracy)}`}>
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
            <View className='data-center-icon data-center-icon--history'>历</View>
            <View className='history-info'>
              <View className='history-title'>答题历史</View>
              <View className='history-meta'>查看全部闯关记录</View>
            </View>
          </View>
          <View className='history-item' onClick={openWrongBook}>
            <View className='data-center-icon data-center-icon--wrong'>错</View>
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
