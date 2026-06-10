import { POLL_REQUEST_TIMEOUT_MS, request, sleep } from '@/services/http'
import type { ResearchResponse } from '@/types/research'
import type { AnswerRecord, ReportData, SessionData } from '@/types/session'

const POLL_INTERVAL_MS = 8000
const POLL_TIMEOUT_MS = 5 * 60 * 1000

export type TaskStatus = 'pending' | 'running' | 'done' | 'failed'
export type TaskStep =
  | 'pending'
  | 'research'
  | 'topic_candidates'
  | 'knowledge'
  | 'questions'
  | 'done'
  | 'failed'

interface TaskCreatedPayload {
  task_id: string
  status: TaskStatus
}

interface TaskStatusPayload<T> {
  task_id: string
  status: TaskStatus
  step: TaskStep
  progress_message?: string | null
  error_message?: string | null
  result?: T
}

function readTaskId(payload: Record<string, unknown>): string {
  const taskId = payload.task_id ?? payload.taskId
  if (!taskId) {
    throw new Error('未获取到任务 ID，请重新尝试')
  }
  return String(taskId)
}

function mapResearchResponse(payload: Record<string, unknown>): ResearchResponse {
  const candidates = (payload.candidates as Record<string, unknown>[] | undefined) || []
  return {
    researchSessionId: String(payload.research_session_id ?? payload.researchSessionId ?? ''),
    candidates: candidates.map((item) => ({
      id: String(item.id ?? ''),
      title: String(item.title ?? ''),
      summary: String(item.summary ?? ''),
      sourceUrls: (item.source_urls as string[] | undefined) || (item.sourceUrls as string[] | undefined) || [],
    })),
    inputKind: (payload.input_kind ?? payload.inputKind ?? 'keyword') as ResearchResponse['inputKind'],
    degradedMode: (payload.degraded_mode ?? payload.degradedMode ?? 'none') as ResearchResponse['degradedMode'],
    mockMode: Boolean(payload.mock_mode ?? payload.mockMode),
    degradedMessage: (payload.degraded_message ?? payload.degradedMessage ?? null) as string | null,
  }
}

function mapGenerateResult(payload: Record<string, unknown>) {
  return {
    session_id: String(payload.session_id ?? ''),
    topic: String(payload.topic ?? ''),
    levels: ((payload.levels as Record<string, unknown>[]) || []).map((level) => ({
      level_index: Number(level.level_index ?? 0),
      questions: ((level.questions as Record<string, unknown>[]) || []).map((question) => ({
        id: String(question.id ?? ''),
        type: question.type as 'single' | 'multiple' | 'boolean',
        difficulty: question.difficulty as 'easy' | 'medium' | 'hard',
        stem: String(question.stem ?? ''),
        options: (question.options as Array<{ key: string; text: string }>) || [],
        conceptTags: (question.conceptTags as string[] | undefined) || (question.concept_tags as string[] | undefined) || [],
      })),
    })),
    truncated: Boolean(payload.truncated),
    grounded: Boolean(payload.grounded),
  }
}

async function pollTaskUntilDone<T>(
  pollFn: () => Promise<TaskStatusPayload<T>>,
  onProgress?: (step: TaskStep, message?: string | null) => void,
): Promise<T> {
  const startedAt = Date.now()
  while (Date.now() - startedAt < POLL_TIMEOUT_MS) {
    const status = await pollFn()
    onProgress?.(status.step, status.progress_message)
    if (status.status === 'done' && status.result) {
      return status.result
    }
    if (status.status === 'failed') {
      throw new Error(status.error_message || '任务失败，请稍后重试')
    }
    await sleep(POLL_INTERVAL_MS)
  }
  throw new Error('处理超时，请稍后重试')
}

export async function startResearchTask(content: string) {
  const payload = await request<Record<string, unknown>>(
    `/api/v1/questions/research`,
    { method: 'POST', data: { content } },
    true,
    POLL_REQUEST_TIMEOUT_MS,
  )
  return readTaskId(payload)
}

export async function pollResearchTask(taskId: string) {
  return request<TaskStatusPayload<Record<string, unknown>>>(
    `/api/v1/questions/research/${encodeURIComponent(taskId)}`,
    { method: 'GET' },
    true,
    POLL_REQUEST_TIMEOUT_MS,
  )
}

export async function researchTopics(content: string, onProgress?: (step: TaskStep, message?: string | null) => void) {
  const taskId = await startResearchTask(content)
  const result = await pollTaskUntilDone(() => pollResearchTask(taskId), onProgress)
  return mapResearchResponse(result)
}

export async function startGenerateTask(
  content: string,
  questionsPerLevel = 5,
  options?: { researchSessionId?: string; selectedTopicId?: string },
) {
  const payload = await request<Record<string, unknown>>(
    `/api/v1/questions/generate`,
    {
      method: 'POST',
      data: {
        content,
        questions_per_level: questionsPerLevel,
        research_session_id: options?.researchSessionId,
        selected_topic_id: options?.selectedTopicId,
      },
    },
    true,
    POLL_REQUEST_TIMEOUT_MS,
  )
  return readTaskId(payload)
}

export async function pollGenerateTask(taskId: string) {
  return request<TaskStatusPayload<Record<string, unknown>>>(
    `/api/v1/questions/generate/${encodeURIComponent(taskId)}`,
    { method: 'GET' },
    true,
    POLL_REQUEST_TIMEOUT_MS,
  )
}

export async function generateQuestions(
  content: string,
  questionsPerLevel = 5,
  options?: {
    researchSessionId?: string
    selectedTopicId?: string
    onProgress?: (step: TaskStep, message?: string | null) => void
  },
) {
  const taskId = await startGenerateTask(content, questionsPerLevel, options)
  const result = await pollTaskUntilDone(() => pollGenerateTask(taskId), options?.onProgress)
  return mapGenerateResult(result)
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
    shareTagline: String(
      payload.shareTagline ?? payload.share_tagline ?? '',
    ),
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
