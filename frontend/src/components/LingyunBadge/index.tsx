import { View } from '@tarojs/components'

import { FLASK_SVG } from '@/assets/flaskSvg'

import './index.scss'

interface Props {
  hearts: number
  large?: boolean
  compact?: boolean
  depleted?: boolean
  showHint?: boolean
}

export default function LingyunBadge({
  hearts,
  large = false,
  compact = false,
  depleted = false,
  showHint = true,
}: Props) {
  const clamped = Math.max(0, Math.min(3, hearts)) as 0 | 1 | 2 | 3

  return (
    <View
      className={`lingyun-badge ${depleted ? 'lingyun-badge--depleted' : ''} ${large ? 'lingyun-badge--lg' : ''} ${compact ? 'lingyun-badge--compact' : ''}`}
    >
      <View
        className='lingyun-badge-icon'
        style={{ backgroundImage: `url("${FLASK_SVG[clamped]}")` }}
      />
      <View className='lingyun-badge-text'>
        <View className='lingyun-badge-title'>
          灵韵 <text className='lingyun-badge-count'>{clamped}/3</text>
        </View>
        {showHint && (
          <View className='lingyun-badge-hint'>
            {clamped === 0 ? '瓶空力尽，精神的升华已消散殆尽' : '答错散逸 1 缕灵韵'}
          </View>
        )}
      </View>
    </View>
  )
}
