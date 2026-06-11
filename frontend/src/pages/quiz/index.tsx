import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useEffect, useMemo, useRef, useState } from 'react'

import LingyunBadge from '@/components/LingyunBadge'
import { INITIAL_HEARTS } from '@/constants'
import { checkAnswer, generateReport, mapReportResponse } from '@/services/api'
import { appendHistoryItem, buildHistoryItem, saveCurrentSession } from '@/services/storage'
import { useSessionStore } from '@/stores/sessionStore'
import { useUserStore } from '@/stores/userStore'
import type { AnswerRecord, Question } from '@/types/session'
import { computeAnswerDurationSec } from '@/utils/formatTime'
import { switchMainTab } from '@/utils/mainTab'

import './index.scss'

type FeedbackState = 'idle' | 'checking' | 'revealed'

const difficultyLabel: Record<Question['difficulty'], string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
}

const typeLabel: Record<Question['type'], string> = {
  single: '单选',
  multiple: '多选',
  boolean: '判断',
}

export default function QuizPage() {
  const session = useSessionStore((state) => state.session)
  const setSession = useSessionStore((state) => state.setSession)
  const setReport = useSessionStore((state) => state.setReport)

  const questions = useMemo(
    () => session?.levels.flatMap((level) => level.questions) ?? [],
    [session],
  )

  const [currentIndex, setCurrentIndex] = useState(session?.currentQuestionIndex ?? 0)
  const [hearts, setHearts] = useState(session?.hearts ?? INITIAL_HEARTS)
  const [answers, setAnswers] = useState<AnswerRecord[]>(session?.answers ?? [])
  const [selectedKeys, setSelectedKeys] = useState<string[]>([])
  const [feedback, setFeedback] = useState<FeedbackState>('idle')
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null)
  const [explanation, setExplanation] = useState('')
  const [correctAnswerKeys, setCorrectAnswerKeys] = useState<string[]>([])
  const [questionStartedAt, setQuestionStartedAt] = useState(Date.now())
  const [reportGenerating, setReportGenerating] = useState(false)
  const quizStartedRef = useRef(false)

  const currentQuestion = questions[currentIndex]

  const persistSession = async (next: NonNullable<typeof session>) => {
    setSession(next)
    await saveCurrentSession(next)
  }

  useEffect(() => {
    if (!session || quizStartedRef.current) return
    quizStartedRef.current = true
    const quizStartedAt = Date.now()
    setQuestionStartedAt(quizStartedAt)
    persistSession({ ...session, startedAt: quizStartedAt, status: 'playing' })
  }, [session])

  Taro.useDidShow(() => {
    if (!session) {
      switchMainTab('home')
    }
  })

  const finishQuiz = async (status: 'completed' | 'failed', nextHearts: number, nextAnswers: AnswerRecord[]) => {
    if (!session || reportGenerating) return
    setReportGenerating(true)
    const finishedSession = {
      ...session,
      hearts: nextHearts,
      answers: nextAnswers,
      currentQuestionIndex: currentIndex,
      status,
      finishedAt: Date.now(),
    }
    await persistSession(finishedSession)

    try {
      const durationSec = computeAnswerDurationSec(nextAnswers)
      const reportPayload = await generateReport(session.sessionId, nextAnswers, {
        quizStatus: status,
        durationSec,
      })
      const report = mapReportResponse(reportPayload as unknown as Record<string, unknown>)
      setReport(report)
      await appendHistoryItem(buildHistoryItem(finishedSession, report))
      const { token, refreshProfile } = useUserStore.getState()
      if (token) {
        refreshProfile().catch(() => undefined)
      }
    } catch {
      const correctCount = nextAnswers.filter((item) => item.isCorrect).length
      const fallback = {
        sessionId: session.sessionId,
        topic: session.topic,
        accuracy: nextAnswers.length ? (correctCount / nextAnswers.length) * 100 : 0,
        totalQuestions: nextAnswers.length,
        correctCount,
        wrongCount: nextAnswers.length - correctCount,
        duration: computeAnswerDurationSec(nextAnswers),
        weakPoints: [],
        summary: '报告生成失败，请查看本地正确率。',
        suggestion: '可稍后重试生成报告。',
        conceptMastery: [],
      }
      setReport(fallback)
    }

    Taro.redirectTo({ url: '/pages/report/index' })
  }

  const resetQuestionState = () => {
    setSelectedKeys([])
    setFeedback('idle')
    setIsCorrect(null)
    setExplanation('')
    setCorrectAnswerKeys([])
    setQuestionStartedAt(Date.now())
  }

  const handleSelect = async (key: string) => {
    if (!session || !currentQuestion || feedback !== 'idle') return

    const nextSelected = currentQuestion.type === 'multiple'
      ? selectedKeys.includes(key)
        ? selectedKeys.filter((item) => item !== key)
        : [...selectedKeys, key]
      : [key]

    if (currentQuestion.type === 'multiple') {
      setSelectedKeys(nextSelected)
      return
    }

    setSelectedKeys(nextSelected)
    setFeedback('checking')
    const timeSpent = Date.now() - questionStartedAt
    const answeredAt = Date.now()

    try {
      const result = await checkAnswer(session.sessionId, currentQuestion.id, nextSelected)
      setTimeout(async () => {
        const correct = result.is_correct
        const record: AnswerRecord = {
          questionId: currentQuestion.id,
          userAnswer: nextSelected,
          isCorrect: correct,
          timeSpent,
          answeredAt,
        }
        const nextAnswers = [...answers, record]
        const nextHearts = correct ? hearts : Math.max(0, hearts - 1)

        setIsCorrect(correct)
        setExplanation(result.explanation)
        setCorrectAnswerKeys(result.correct_answer)
        setFeedback('revealed')
        setAnswers(nextAnswers)
        setHearts(nextHearts)

        await persistSession({
          ...session,
          hearts: nextHearts,
          answers: nextAnswers,
          currentQuestionIndex: currentIndex,
          status: 'playing',
        })
      }, 500)
    } catch (error) {
      setFeedback('idle')
      Taro.showToast({
        title: error instanceof Error ? error.message : '判题失败',
        icon: 'none',
      })
    }
  }

  const submitMultiple = async () => {
    if (!session || !currentQuestion || selectedKeys.length === 0 || feedback !== 'idle') return
    setFeedback('checking')
    const timeSpent = Date.now() - questionStartedAt
    const answeredAt = Date.now()
    try {
      const result = await checkAnswer(session.sessionId, currentQuestion.id, selectedKeys)
      setTimeout(async () => {
        const correct = result.is_correct
        const record: AnswerRecord = {
          questionId: currentQuestion.id,
          userAnswer: selectedKeys,
          isCorrect: correct,
          timeSpent,
          answeredAt,
        }
        const nextAnswers = [...answers, record]
        const nextHearts = correct ? hearts : Math.max(0, hearts - 1)
        setIsCorrect(correct)
        setExplanation(result.explanation)
        setCorrectAnswerKeys(result.correct_answer)
        setFeedback('revealed')
        setAnswers(nextAnswers)
        setHearts(nextHearts)
        await persistSession({
          ...session,
          hearts: nextHearts,
          answers: nextAnswers,
          currentQuestionIndex: currentIndex,
          status: 'playing',
        })
      }, 500)
    } catch (error) {
      setFeedback('idle')
      Taro.showToast({
        title: error instanceof Error ? error.message : '判题失败',
        icon: 'none',
      })
    }
  }

  const goNext = async () => {
    if (reportGenerating) return
    if (currentIndex >= questions.length - 1) {
      const status = hearts > 0 ? 'completed' : 'failed'
      await finishQuiz(status, hearts, answers)
      return
    }
    setCurrentIndex((value) => value + 1)
    resetQuestionState()
  }

  const goPrev = () => {
    if (currentIndex === 0 || feedback === 'checking') return
    setCurrentIndex((value) => value - 1)
    resetQuestionState()
  }

  if (!session || !currentQuestion) {
    return <View className='app-page' />
  }

  const progress = ((currentIndex + 1) / questions.length) * 100
  const isLastQuestion = currentIndex >= questions.length - 1
  const canGoNext = feedback === 'revealed' && !reportGenerating

  return (
    <View className='app-page quiz-page'>
      <View className='quiz-header'>
        <View className='quiz-top-row'>
          <View className='app-bar-back' onClick={() => Taro.showModal({
            title: '确认离开',
            content: '离开后将保留当前进度，确定返回吗？',
            success: (res) => res.confirm && switchMainTab('home'),
          })}
          >
            ←
          </View>
          <View className='quiz-topic'>{session.topic}</View>
          <View className='quiz-top-spacer' />
        </View>
        <View className='quiz-lingyun-row'>
          <LingyunBadge hearts={hearts} depleted={hearts === 0} showHint={false} compact />
        </View>
        <View className='quiz-progress'>
          <View className='quiz-progress-bar'>
            <View className='quiz-progress-fill' style={{ width: `${progress}%` }} />
          </View>
          <Text className='quiz-progress-text'>第 {currentIndex + 1}/{questions.length} 题</Text>
        </View>
      </View>

      <View className='app-content app-content--quiz'>
        <View className='question-panel'>
          <View className='question-tags-row'>
            <Text className={`difficulty-tag ${currentQuestion.difficulty}`}>
              {difficultyLabel[currentQuestion.difficulty]}
            </Text>
            <Text className='question-type-tag'>{typeLabel[currentQuestion.type]}</Text>
          </View>
          <View className='question-stem'>{currentQuestion.stem}</View>
        </View>

        <View className='options-list'>
          {currentQuestion.options.map((option) => {
            const selected = selectedKeys.includes(option.key)
            const revealed = feedback === 'revealed'
            const isCorrectOption = correctAnswerKeys.includes(option.key)
            let className = 'option-item'
            if (selected && !revealed) className += ' selected'
            if (revealed && isCorrectOption) className += ' correct'
            if (revealed && selected && !isCorrectOption) className += ' wrong'

            return (
              <View key={option.key} className={className} onClick={() => handleSelect(option.key)}>
                <Text className='option-key'>{option.key}</Text>
                <Text className='option-text'>{option.text}</Text>
              </View>
            )
          })}
        </View>

        {currentQuestion.type === 'multiple' && feedback === 'idle' && (
          <View className='btn-comic btn-primary btn-sm multiple-submit' onClick={submitMultiple}>
            确认作答
          </View>
        )}

        {feedback === 'revealed' && (
          <View className={`explain-bubble ${isCorrect ? 'correct' : 'wrong'}`}>
            <View className={`explain-header ${isCorrect ? 'correct' : 'wrong'}`}>
              {isCorrect ? '回答正确！' : '答错了，灵韵散逸 -1'}
            </View>
            <View className='explain-body'>{explanation}</View>
          </View>
        )}

        <View className='quiz-footer'>
          <View className='concept-tags-row'>
            {currentQuestion.conceptTags.map((tag) => (
              <Text key={tag} className='concept-tag'>{tag}</Text>
            ))}
          </View>
          <View className='quiz-nav-row'>
            <View className={`btn-comic btn-secondary btn-sm quiz-nav-btn ${currentIndex === 0 ? 'btn-disabled' : ''}`} onClick={goPrev}>
              上一题
            </View>
            <View
              className={`btn-comic btn-sm quiz-nav-btn ${
                reportGenerating
                  ? 'btn-primary btn-loading'
                  : canGoNext
                    ? 'btn-primary'
                    : 'btn-disabled'
              }`}
              onClick={reportGenerating || !canGoNext ? undefined : goNext}
            >
              {reportGenerating && isLastQuestion ? (
                <>
                  <View className='btn-spinner' />
                  生成报告中…
                </>
              ) : (
                isLastQuestion ? '查看报告' : '下一题'
              )}
            </View>
          </View>
        </View>
      </View>
    </View>
  )
}
