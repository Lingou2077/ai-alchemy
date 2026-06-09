export const EXAMPLE_CHIPS = [
  {
    label: 'Go 并发',
    hot: true,
    content:
      'Go 语言中，goroutine 的默认栈大小是多少？channel 的主要作用是什么？为什么说「不要通过共享内存来通信，而要通过通信来共享内存」？',
  },
  {
    label: '量子力学',
    content:
      '什么是波函数坍缩？海森堡不确定性原理说明了什么？微观粒子的位置和动量能否同时精确测定？',
  },
  {
    label: '考研政治',
    content:
      '实践与认识的关系是什么？唯物论和辩证法分别研究什么？矛盾在事物发展中起什么作用？',
  },
] as const

export const MAX_CONTENT_LENGTH = 500
export const INITIAL_HEARTS = 3
export const STORAGE_KEYS = {
  currentSession: 'current_session',
  quizHistory: 'quiz_history',
  authToken: 'auth_token',
} as const

export const PLACEHOLDER_MESSAGE = '即将上线，敬请期待'
