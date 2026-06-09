import { request } from '@/services/http'
import type { AnswerRecord, ReportData, SessionData } from '@/types/session'

export async function generateQuestions(content: string, questionsPerLevel = 5) {
  return request<{
    session_id: string
    topic: string
    levels: Array<{
      level_index: number
      questions: Array<{
        id: string
        type: 'single' | 'multiple' | 'boolean'
        difficulty: 'easy' | 'medium' | 'hard'
        stem: string
        options: Array<{ key: string; text: string }>
        conceptTags?: string[]
      }>
    }>
    truncated?: boolean
  }>(`/api/v1/questions/generate`, {
    method: 'POST',
    data: {
      content,
      questions_per_level: questionsPerLevel,
    },
  })
}

export async function checkAnswer(sessionId: string, questionId: string, userAnswer: string[]) {
  return request<{ is_correct: boolean; explanation: string; correct_answer: string[] }>(`/api/v1/answers/check`, {
    method: 'POST',
    data: {
      session_id: sessionId,
      question_id: questionId,
      user_answer: userAnswer,
    },
  })
}

export async function generateReport(
  sessionId: string,
  answers: AnswerRecord[],
  options?: { quizStatus?: 'completed' | 'failed'; durationSec?: number },
) {
  return request<ReportData>(`/api/v1/report/generate`, {
    method: 'POST',
    data: {
      session_id: sessionId,
      answers: answers.map((item) => ({
        question_id: item.questionId,
        user_answer: item.userAnswer,
        is_correct: item.isCorrect,
        time_spent: item.timeSpent,
      })),
      quiz_status: options?.quizStatus,
      duration_sec: options?.durationSec,
    },
  })
}

export function mapGenerateResponseToSession(
  sourceContent: string,
  payload: Awaited<ReturnType<typeof generateQuestions>>,
): SessionData {
  return {
    sessionId: payload.session_id,
    topic: payload.topic,
    sourceContent,
    createdAt: Date.now(),
    status: 'playing',
    levels: payload.levels.map((level) => ({
      levelIndex: level.level_index,
      questions: level.questions.map((question) => ({
        id: question.id,
        type: question.type,
        difficulty: question.difficulty,
        stem: question.stem,
        options: question.options,
        conceptTags: question.conceptTags || [],
      })),
    })),
    hearts: 3,
    currentQuestionIndex: 0,
    answers: [],
    startedAt: Date.now(),
  }
}

export function mapReportResponse(payload: Record<string, unknown>): ReportData {
  const expGainRaw = (payload.expGain ?? payload.exp_gain) as Record<string, unknown> | undefined
  const statsRaw = (payload.stats ?? {}) as Record<string, unknown>
  const relatedHistory = (statsRaw.relatedHistory ?? statsRaw.related_history ?? []) as Record<string, unknown>[]

  return {
    sessionId: String(payload.sessionId ?? payload.session_id ?? ''),
    topic: String(payload.topic ?? ''),
    accuracy: Number(payload.accuracy ?? 0),
    totalQuestions: Number(payload.totalQuestions ?? payload.total_questions ?? 0),
    correctCount: Number(payload.correctCount ?? payload.correct_count ?? 0),
    wrongCount: Number(payload.wrongCount ?? payload.wrong_count ?? 0),
    duration: Number(payload.duration ?? payload.duration_sec ?? payload.durationSec ?? 0),
    weakPoints: (payload.weakPoints as ReportData['weakPoints']) ||
      (payload.weak_points as ReportData['weakPoints']) ||
      [],
    summary: String(payload.summary ?? ''),
    suggestion: String(payload.suggestion ?? ''),
    conceptMastery: (payload.conceptMastery as ReportData['conceptMastery']) ||
      (payload.concept_mastery as ReportData['conceptMastery']) ||
      [],
    expGain: expGainRaw
      ? {
          amount: Number(expGainRaw.amount ?? 0),
          leveledUp: Boolean(expGainRaw.leveledUp ?? expGainRaw.leveled_up),
          newLevel: Number(expGainRaw.newLevel ?? expGainRaw.new_level ?? 1),
          newTitle: String(expGainRaw.newTitle ?? expGainRaw.new_title ?? ''),
          levelBefore: Number(expGainRaw.levelBefore ?? expGainRaw.level_before ?? 1),
        }
      : null,
    stats: statsRaw
      ? {
          compareLastAccuracy:
            statsRaw.compareLastAccuracy !== undefined
              ? Number(statsRaw.compareLastAccuracy)
              : statsRaw.compare_last_accuracy !== undefined
                ? Number(statsRaw.compare_last_accuracy)
                : null,
          weeklyQuizIndex:
            statsRaw.weeklyQuizIndex !== undefined
              ? Number(statsRaw.weeklyQuizIndex)
              : statsRaw.weekly_quiz_index !== undefined
                ? Number(statsRaw.weekly_quiz_index)
                : null,
          relatedHistory: relatedHistory.map((item) => ({
            sessionId: String(item.sessionId ?? item.session_id ?? ''),
            topic: String(item.topic ?? ''),
            accuracy: Number(item.accuracy ?? 0),
            questionCount: Number(item.questionCount ?? item.question_count ?? 0),
            durationSec: Number(item.durationSec ?? item.duration_sec ?? 0),
            status: (item.status as 'completed' | 'failed') ?? 'completed',
            finishedAt: String(item.finishedAt ?? item.finished_at ?? ''),
          })),
        }
      : null,
    syncFailed: Boolean(payload.syncFailed ?? payload.sync_failed),
  }
}

export async function healthCheck() {
  return request<{ status: string }>(`/api/v1/health`, { method: 'GET' })
}
