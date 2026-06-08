export interface ExpProgress {
  current: number
  required: number
  totalExp: number
}

export interface UserStats {
  totalQuizzes: number
  averageAccuracy: number
  wrongQuestionCount: number
  weeklyQuizCount: number
}

export interface UserProfile {
  id: number
  nickname: string
  avatarUrl: string
  exp: number
  level: number
  title: string
  totalQuizzes: number
  createdAt?: string
  expProgress: ExpProgress
  stats: UserStats
}

export interface LoginResponse {
  token: string
  user: UserProfile
}

export interface UpdateProfilePayload {
  nickname?: string
  avatarUrl?: string
}
