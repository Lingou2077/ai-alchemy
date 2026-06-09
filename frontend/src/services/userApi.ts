import Taro from '@tarojs/taro'

import { loadAuthToken } from '@/services/authStorage'
import { request } from '@/services/http'
import type {
  QuizHistoryDetail,
  QuizHistoryItem,
  WrongQuestionDetail,
  WrongQuestionItem,
} from '@/types/session'
import type { LoginResponse, UpdateProfilePayload, UserProfile, UserStats } from '@/types/user'

const API_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000'

function mapUserProfile(payload: Record<string, unknown>): UserProfile {
  const expProgress = (payload.expProgress ?? payload.exp_progress ?? {}) as Record<string, unknown>
  const stats = (payload.stats ?? {}) as Record<string, unknown>
  return {
    id: Number(payload.id ?? 0),
    nickname: String(payload.nickname ?? '炼金学徒'),
    avatarUrl: String(payload.avatarUrl ?? payload.avatar_url ?? ''),
    exp: Number(payload.exp ?? 0),
    level: Number(payload.level ?? 1),
    title: String(payload.title ?? '见习炼金师'),
    totalQuizzes: Number(payload.totalQuizzes ?? payload.total_quizzes ?? 0),
    createdAt: payload.createdAt ? String(payload.createdAt) : undefined,
    expProgress: {
      current: Number(expProgress.current ?? 0),
      required: Number(expProgress.required ?? 30),
      totalExp: Number(expProgress.totalExp ?? expProgress.total_exp ?? 0),
    },
    stats: {
      totalQuizzes: Number(stats.totalQuizzes ?? stats.total_quizzes ?? 0),
      averageAccuracy: Number(stats.averageAccuracy ?? stats.average_accuracy ?? 0),
      wrongQuestionCount: Number(stats.wrongQuestionCount ?? stats.wrong_question_count ?? 0),
      weeklyQuizCount: Number(stats.weeklyQuizCount ?? stats.weekly_quiz_count ?? 0),
    },
  }
}

function isLocalAvatarPath(url: string): boolean {
  return /^(wxfile:\/\/|file:\/\/|https?:\/\/tmp\/)/.test(url)
}

export async function loginWithCode(code: string) {
  const payload = await request<Record<string, unknown>>(
    `/api/v1/auth/login`,
    {
      method: 'POST',
      data: { code },
    },
    false,
  )
  return {
    token: String(payload.token ?? ''),
    user: mapUserProfile((payload.user ?? {}) as Record<string, unknown>),
  } satisfies LoginResponse
}

export async function fetchCurrentUser() {
  const payload = await request<Record<string, unknown>>(`/api/v1/users/me`, { method: 'GET' })
  return mapUserProfile(payload)
}

export async function uploadAvatar(filePath: string) {
  const token = await loadAuthToken()
  const response = await Taro.uploadFile({
    url: `${API_BASE_URL}/api/v1/users/me/avatar`,
    filePath,
    name: 'file',
    header: token ? { Authorization: `Bearer ${token}` } : {},
  })

  if (response.statusCode === 401 && token) {
    const { useUserStore } = await import('@/stores/userStore')
    const relogged = await useUserStore.getState().login()
    if (relogged) {
      return uploadAvatar(filePath)
    }
  }

  if (response.statusCode >= 400) {
    let message = '头像上传失败'
    try {
      const body = JSON.parse(response.data) as { detail?: string }
      message = body.detail || message
    } catch {
      // ignore parse error
    }
    throw new Error(message)
  }

  const payload = JSON.parse(response.data) as Record<string, unknown>
  return mapUserProfile(payload)
}

export async function updateProfile(data: UpdateProfilePayload) {
  const payload = await request<Record<string, unknown>>(`/api/v1/users/me`, {
    method: 'PATCH',
    data: {
      nickname: data.nickname,
      avatar_url: data.avatarUrl,
    },
  })
  return mapUserProfile(payload)
}

export async function persistAvatar(avatarUrl: string) {
  if (isLocalAvatarPath(avatarUrl)) {
    return uploadAvatar(avatarUrl)
  }
  return updateProfile({ avatarUrl })
}

function mapHistoryItem(payload: Record<string, unknown>): QuizHistoryItem {
  return {
    sessionId: String(payload.sessionId ?? payload.session_id ?? ''),
    topic: String(payload.topic ?? ''),
    accuracy: Number(payload.accuracy ?? 0),
    questionCount: Number(payload.questionCount ?? payload.question_count ?? 0),
    durationSec: Number(payload.durationSec ?? payload.duration_sec ?? 0),
    status: (payload.status as QuizHistoryItem['status']) ?? 'completed',
    finishedAt: String(payload.finishedAt ?? payload.finished_at ?? ''),
  }
}

export async function fetchUserStats() {
  const payload = await request<Record<string, unknown>>(`/api/v1/users/me/stats`, { method: 'GET' })
  return {
    totalQuizzes: Number(payload.totalQuizzes ?? payload.total_quizzes ?? 0),
    averageAccuracy: Number(payload.averageAccuracy ?? payload.average_accuracy ?? 0),
    wrongQuestionCount: Number(payload.wrongQuestionCount ?? payload.wrong_question_count ?? 0),
    weeklyQuizCount: Number(payload.weeklyQuizCount ?? payload.weekly_quiz_count ?? 0),
  } satisfies UserStats
}

export async function fetchQuizHistory(page = 1, limit = 20) {
  const payload = await request<Record<string, unknown>>(
    `/api/v1/users/me/history?page=${page}&limit=${limit}`,
    { method: 'GET' },
  )
  const items = ((payload.items as Record<string, unknown>[]) ?? []).map(mapHistoryItem)
  return {
    items,
    total: Number(payload.total ?? 0),
    page: Number(payload.page ?? page),
    limit: Number(payload.limit ?? limit),
  }
}

export async function deleteQuizHistory(sessionId: string) {
  await request<Record<string, never>>(
    `/api/v1/users/me/history/${encodeURIComponent(sessionId)}`,
    { method: 'DELETE' },
  )
}

export async function fetchQuizHistoryDetail(sessionId: string) {
  const payload = await request<Record<string, unknown>>(
    `/api/v1/users/me/history/${encodeURIComponent(sessionId)}`,
    { method: 'GET' },
  )
  const base = mapHistoryItem(payload)
  return {
    ...base,
    summary: payload.summary ? String(payload.summary) : null,
    suggestion: payload.suggestion ? String(payload.suggestion) : null,
    weakPoints: (payload.weakPoints as QuizHistoryDetail['weakPoints']) ?? [],
  } satisfies QuizHistoryDetail
}

function mapWrongQuestionItem(payload: Record<string, unknown>): WrongQuestionItem {
  return {
    id: Number(payload.id ?? 0),
    questionId: String(payload.questionId ?? payload.question_id ?? ''),
    topic: String(payload.topic ?? ''),
    stem: String(payload.stem ?? ''),
    difficulty: String(payload.difficulty ?? ''),
    wrongCount: Number(payload.wrongCount ?? payload.wrong_count ?? 1),
    lastWrongAt: String(payload.lastWrongAt ?? payload.last_wrong_at ?? ''),
  }
}

export async function fetchWrongQuestions(page = 1, limit = 20) {
  const payload = await request<Record<string, unknown>>(
    `/api/v1/users/me/wrong-questions?page=${page}&limit=${limit}`,
    { method: 'GET' },
  )
  const items = ((payload.items as Record<string, unknown>[]) ?? []).map(mapWrongQuestionItem)
  return {
    items,
    total: Number(payload.total ?? 0),
    page: Number(payload.page ?? page),
    limit: Number(payload.limit ?? limit),
  }
}

export async function fetchWrongQuestionDetail(id: number) {
  const payload = await request<Record<string, unknown>>(
    `/api/v1/users/me/wrong-questions/${id}`,
    { method: 'GET' },
  )
  const base = mapWrongQuestionItem(payload)
  return {
    ...base,
    options: (payload.options as WrongQuestionDetail['options']) ?? [],
    correctAnswer: (payload.correctAnswer as string[]) ?? (payload.correct_answer as string[]) ?? [],
    explanation: String(payload.explanation ?? ''),
  } satisfies WrongQuestionDetail
}

export function resolveAvatarSrc(avatarUrl: string): string {
  if (!avatarUrl) return ''
  if (avatarUrl.startsWith('/uploads/')) {
    return `${API_BASE_URL}${avatarUrl}`
  }
  return avatarUrl
}
