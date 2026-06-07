import { View } from '@tarojs/components'

import './index.scss'

interface Props {
  hearts: number
  large?: boolean
  depleted?: boolean
}

const FLASKS = ['flask-0', 'flask-1', 'flask-2', 'flask-3'] as const

export default function LingyunBadge({ hearts, large = false, depleted = false }: Props) {
  const clamped = Math.max(0, Math.min(3, hearts))
  const flaskClass = FLASKS[clamped]

  return (
    <View className={`lingyun-badge ${depleted ? 'lingyun-badge--depleted' : ''} ${large ? 'lingyun-badge--lg' : ''}`}>
      <View className={`lingyun-badge-icon lingyun-badge-icon--${flaskClass}`} />
      <View className='lingyun-badge-text'>
        <View className='lingyun-badge-title'>
          灵韵 <text className='lingyun-badge-count'>{clamped}/3</text>
        </View>
        <View className='lingyun-badge-hint'>
          {clamped === 0 ? '瓶空力尽，精神的升华已消散殆尽' : '答错散逸 1 缕灵韵'}
        </View>
      </View>
    </View>
  )
}
