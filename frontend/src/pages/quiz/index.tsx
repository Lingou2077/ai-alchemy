import { Text, View } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useMemo, useState } from 'react'

import LingyunBadge from '@/components/LingyunBadge'
import { INITIAL_HEARTS } from '@/constants'
import { checkAnswer, generateReport, mapReportResponse } from '@/services/api'
import { appendHistoryItem, buildHistoryItem, saveCurrentSession } from '@/services/storage'
import { useSessionStore } from '@/stores/sessionStore'
import { useUserStore } from '@/stores/userStore'
import type { AnswerRecord, Question } from '@/types/session'

import './index.scss'

type FeedbackState = 'idle' | 'checking' | 'revealed'

const difficultyLabel: Record<Question['difficulty'], string> = {
  easy: '简单',
  medium: '中等',
  hard: '困难',
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
  const [startedAt] = useState(session?.startedAt ?? Date.now())
  const [questionStartedAt, setQuestionStartedAt] = useState(Date.now())

  const currentQuestion = questions[currentIndex]

  Taro.useDidShow(() => {
    if (!session) {
      Taro.redirectTo({ url: '/pages/index/index' })
    }
  })

  const persistSession = async (next: NonNullable<typeof session>) => {
    setSession(next)
    await saveCurrentSession(next)
  }

  const finishQuiz = async (status: 'completed' | 'failed', nextHearts: number, nextAnswers: AnswerRecord[]) => {
    if (!session) return
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
      const durationSec = Math.max(1, Math.floor((Date.now() - startedAt) / 1000))
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
        duration: Math.max(1, Math.floor((Date.now() - startedAt) / 1000)),
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

    try {
      const result = await checkAnswer(session.sessionId, currentQuestion.id, nextSelected)
      setTimeout(async () => {
        const correct = result.is_correct
        const record: AnswerRecord = {
          questionId: currentQuestion.id,
          userAnswer: nextSelected,
          isCorrect: correct,
          timeSpent: Date.now() - questionStartedAt,
          answeredAt: Date.now(),
        }
        const nextAnswers = [...answers, record]
        const nextHearts = correct ? hearts : hearts - 1

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
    try {
      const result = await checkAnswer(session.sessionId, currentQuestion.id, selectedKeys)
      setTimeout(async () => {
        const correct = result.is_correct
        const record: AnswerRecord = {
          questionId: currentQuestion.id,
          userAnswer: selectedKeys,
          isCorrect: correct,
          timeSpent: Date.now() - questionStartedAt,
          answeredAt: Date.now(),
        }
        const nextAnswers = [...answers, record]
        const nextHearts = correct ? hearts : hearts - 1
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
    if (hearts <= 0) {
      await finishQuiz('failed', hearts, answers)
      return
    }
    if (currentIndex >= questions.length - 1) {
      await finishQuiz('completed', hearts, answers)
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

  return (
    <View className='app-page quiz-page'>
      <View className='quiz-header'>
        <View className='quiz-top-row'>
          <View className='app-bar-back' onClick={() => Taro.showModal({
            title: '确认离开',
            content: '离开后将保留当前进度，确定返回吗？',
            success: (res) => res.confirm && Taro.redirectTo({ url: '/pages/index/index' }),
          })}
          >
            ←
          </View>
          <View className='quiz-topic'>{session.topic}</View>
          <View className='quiz-top-spacer' />
        </View>
        <View className='quiz-lingyun-row'>
          <LingyunBadge hearts={hearts} depleted={hearts === 0} />
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
          <Text className={`difficulty-tag ${currentQuestion.difficulty}`}>
            {difficultyLabel[currentQuestion.difficulty]}
          </Text>
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
              className={`btn-comic btn-sm quiz-nav-btn ${feedback === 'revealed' ? 'btn-primary' : 'btn-disabled'}`}
              onClick={goNext}
            >
              {currentIndex >= questions.length - 1 ? '查看报告' : '下一题'}
            </View>
          </View>
        </View>
      </View>
    </View>
  )
}
