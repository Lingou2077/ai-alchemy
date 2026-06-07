import Taro from '@tarojs/taro'

import type { HistoryItem, ReportData, SessionData } from '@/types/session'
import { STORAGE_KEYS } from '@/constants'

export async function saveCurrentSession(session: SessionData | null) {
  if (!session) {
    await Taro.removeStorage({ key: STORAGE_KEYS.currentSession })
    return
  }
  await Taro.setStorage({ key: STORAGE_KEYS.currentSession, data: session })
}

export async function loadCurrentSession(): Promise<SessionData | null> {
  try {
    const result = await Taro.getStorage<SessionData>({ key: STORAGE_KEYS.currentSession })
    return result.data ?? null
  } catch {
    return null
  }
}

export async function appendHistoryItem(item: HistoryItem) {
  const existing = await loadHistoryItems()
  const next = [item, ...existing.filter((entry) => entry.sessionId !== item.sessionId)].slice(0, 20)
  await Taro.setStorage({ key: STORAGE_KEYS.quizHistory, data: next })
}

export async function loadHistoryItems(): Promise<HistoryItem[]> {
  try {
    const result = await Taro.getStorage<HistoryItem[]>({ key: STORAGE_KEYS.quizHistory })
    return result.data ?? []
  } catch {
    return []
  }
}

export function buildHistoryItem(session: SessionData, report: ReportData): HistoryItem {
  const questionCount = session.levels.reduce((sum, level) => sum + level.questions.length, 0)
  return {
    sessionId: session.sessionId,
    topic: report.topic,
    accuracy: report.accuracy,
    questionCount,
    finishedAt: session.finishedAt ?? Date.now(),
  }
}
