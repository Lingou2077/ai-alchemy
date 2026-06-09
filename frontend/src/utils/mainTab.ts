import Taro from '@tarojs/taro'

export const MAIN_TAB_PATHS = {
  home: '/pages/index/index',
  bank: '/pages/question-bank/index',
  profile: '/pages/profile/index',
} as const

export type MainTabKey = keyof typeof MAIN_TAB_PATHS

export function switchMainTab(key: MainTabKey) {
  return Taro.switchTab({ url: MAIN_TAB_PATHS[key] })
}
