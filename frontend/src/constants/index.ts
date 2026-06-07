export const EXAMPLE_CHIPS = [
  {
    label: 'Go 并发',
    hot: true,
    content:
      'Go 语言中，goroutine 是轻量级线程，由 Go 运行时调度。channel 用于 goroutine 之间通信，遵循「不要通过共享内存来通信，而要通过通信来共享内存」的哲学。sync.Mutex 用于保护共享资源。',
  },
  {
    label: '量子力学',
    content:
      '量子力学是描述微观粒子行为的物理理论。波函数描述粒子状态，测量会导致波函数坍缩。海森堡不确定性原理指出，某些物理量无法同时精确测定。',
  },
  {
    label: '考研政治',
    content:
      '马克思主义基本原理包括唯物论、辩证法和认识论。实践是认识的基础，认识对实践具有反作用。矛盾是事物发展的根本动力。',
  },
] as const

export const MAX_CONTENT_LENGTH = 5000
export const INITIAL_HEARTS = 3
export const STORAGE_KEYS = {
  currentSession: 'current_session',
  quizHistory: 'quiz_history',
} as const

export const PLACEHOLDER_MESSAGE = '即将上线，敬请期待'
