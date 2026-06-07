import Taro from '@tarojs/taro'

import type { AnswerRecord, ReportData, SessionData } from '@/types/session'

const API_BASE_URL = process.env.API_BASE_URL || 'http://127.0.0.1:8000'

interface ApiErrorBody {
  detail?: string
}

async function request<T>(path: string, options: Taro.request.Option): Promise<T> {
  const response = await Taro.request<T & ApiErrorBody>({
    url: `${API_BASE_URL}${path}`,
    timeout: 60000,
    header: {
      'Content-Type': 'application/json',
      ...(options.header || {}),
    },
    ...options,
  })

  if (response.statusCode >= 400) {
    const message = (response.data as ApiErrorBody)?.detail || '请求失败，请稍后重试'
    throw new Error(message)
  }

  return response.data as T
}

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

export async function generateReport(sessionId: string, answers: AnswerRecord[]) {
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
  return {
    sessionId: String(payload.sessionId ?? payload.session_id ?? ''),
    topic: String(payload.topic ?? ''),
    accuracy: Number(payload.accuracy ?? 0),
    totalQuestions: Number(payload.totalQuestions ?? payload.total_questions ?? 0),
    correctCount: Number(payload.correctCount ?? payload.correct_count ?? 0),
    wrongCount: Number(payload.wrongCount ?? payload.wrong_count ?? 0),
    duration: Number(payload.duration ?? 0),
    weakPoints: (payload.weakPoints as ReportData['weakPoints']) ||
      (payload.weak_points as ReportData['weakPoints']) ||
      [],
    summary: String(payload.summary ?? ''),
    suggestion: String(payload.suggestion ?? ''),
    conceptMastery: (payload.conceptMastery as ReportData['conceptMastery']) ||
      (payload.concept_mastery as ReportData['conceptMastery']) ||
      [],
  }
}

export async function healthCheck() {
  return request<{ status: string }>(`/api/v1/health`, { method: 'GET' })
}
