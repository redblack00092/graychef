import { useRef } from 'react'
import html2canvas from 'html2canvas'

const SCORES = [
  { key: 'plating_score', label: '플레이팅' },
  { key: 'health_score',  label: '건강' },
  { key: 'taste_score',   label: '예상 맛' },
]

function ScoreBar({ value, isSpicy }) {
  return (
    <div className="w-full h-px overflow-hidden" style={{ backgroundColor: 'rgba(255,255,255,0.15)' }}>
      <div
        className="h-full transition-all duration-700"
        style={{
          width: `${value}%`,
          backgroundColor: isSpicy ? '#8A2A2A' : 'var(--gold)',
        }}
      />
    </div>
  )
}

function ScoreBadge({ score, isSpicy }) {
  return (
    <div
      className="absolute top-3 right-3 w-13 h-13 flex flex-col items-center justify-center"
      style={{
        width: 52,
        height: 52,
        border: `1px solid ${isSpicy ? '#8A2A2A' : 'var(--gold)'}`,
        backgroundColor: isSpicy ? 'rgba(30,5,5,0.9)' : 'rgba(14,14,12,0.85)',
        backdropFilter: 'blur(6px)',
      }}
    >
      <span className="font-black text-base leading-none" style={{ color: 'var(--text)' }}>
        {score}
      </span>
      <span className="text-[9px] leading-none mt-0.5" style={{ color: 'var(--gold)' }}>
        점
      </span>
    </div>
  )
}

function ImageCard({ imageUrl, result, mode, cardRef }) {
  const isSpicy = mode === 'spicy'
  const comment = isSpicy ? result.spicy_comment : result.sweet_comment

  return (
    <div ref={cardRef} className="relative overflow-hidden">
      <img
        src={imageUrl}
        alt="음식 분석"
        className="w-full object-cover"
        crossOrigin="anonymous"
      />

      <ScoreBadge score={result.total_score} isSpicy={isSpicy} />

      {/* Bottom overlay */}
      <div
        className="absolute bottom-0 left-0 right-0 px-4 pt-12 pb-4"
        style={{
          background: isSpicy
            ? 'linear-gradient(to top, rgba(30,5,5,0.95) 0%, transparent 100%)'
            : 'linear-gradient(to top, rgba(14,14,12,0.92) 0%, transparent 100%)',
        }}
      >
        <p className="font-serif-italic text-sm leading-relaxed mb-3" style={{ color: 'var(--text)' }}>
          {comment}
        </p>

        <div className="flex gap-3">
          {SCORES.map(({ key, label }) => {
            const value = result[key]
            return (
              <div key={key} className="flex-1">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-[10px] tracking-wide" style={{ color: 'rgba(232,224,200,0.55)' }}>
                    {label}
                  </span>
                  <span
                    className="text-xs font-bold"
                    style={{ color: isSpicy ? '#C04040' : 'var(--gold)' }}
                  >
                    {value}
                  </span>
                </div>
                <ScoreBar value={value} isSpicy={isSpicy} />
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

function ModeButtons({ mode, onModeChange }) {
  const isSpicy = mode === 'spicy'
  return (
    <div className="flex gap-2">
      <button
        onClick={() => onModeChange('spicy')}
        className="flex-1 py-3.5 text-xs tracking-[0.2em] uppercase font-semibold transition-all duration-200"
        style={{
          backgroundColor: isSpicy ? '#1E0A0A' : '#0E0E0C',
          color: isSpicy ? 'var(--text)' : 'var(--sub)',
          border: `1px solid ${isSpicy ? '#8A2A2A' : 'var(--border)'}`,
        }}
      >
        🌶 빨간맛
      </button>
      <button
        onClick={() => onModeChange('sweet')}
        className="flex-1 py-3.5 text-xs tracking-[0.2em] uppercase font-semibold transition-all duration-200"
        style={{
          backgroundColor: 'transparent',
          color: !isSpicy ? 'var(--bg)' : 'var(--sub)',
          border: `1px solid ${!isSpicy ? 'var(--text)' : 'var(--border)'}`,
          ...((!isSpicy) && { backgroundColor: 'var(--text)' }),
        }}
      >
        🍯 달달한
      </button>
    </div>
  )
}

function TipCards({ result, mode }) {
  const isSpicy = mode === 'spicy'
  const tips = [
    { title: '플레이팅',      text: result.tip_plating },
    { title: '예상 맛 올리기', text: result.tip_taste },
    { title: '건강 챙기기',   text: result.tip_health },
  ]

  return (
    <div className="space-y-2">
      <p
        className="text-[10px] tracking-[0.25em] uppercase px-1 pb-1"
        style={{ color: 'var(--sub)' }}
      >
        개선 제안
      </p>
      {tips.map(({ title, text }) => (
        <div
          key={title}
          className="px-4 py-3 transition-colors duration-300"
          style={{
            backgroundColor: 'var(--card)',
            border: '1px solid var(--border)',
            borderLeft: `2px solid ${isSpicy ? '#8A2A2A' : 'var(--gold)'}`,
          }}
        >
          <p
            className="text-xs font-semibold tracking-wide mb-1"
            style={{ color: isSpicy ? '#C04040' : 'var(--gold)' }}
          >
            {title}
          </p>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--sub)' }}>
            {text}
          </p>
        </div>
      ))}
    </div>
  )
}

export default function ResultScreen({ imageUrl, result, mode, onModeChange, onReset }) {
  const shareRef = useRef(null)  // 캡처 대상: 이미지 + 팁 카드 전체
  const cardRef = useRef(null)   // 이미지 오버레이용

  const handleShare = async () => {
    if (!shareRef.current) return
    try {
      const isSpicy = mode === 'spicy'
      const bgColor = isSpicy ? '#1a0505' : '#0E0E0C'

      const canvas = await html2canvas(shareRef.current, {
        useCORS: true,
        allowTaint: true,
        backgroundColor: bgColor,
        scale: 2,
        logging: false,
        imageTimeout: 15000,
      })

      const blob = await new Promise((resolve) =>
        canvas.toBlob(resolve, 'image/png')
      )
      const filename = 'graychef_결과.png'
      const file = new File([blob], filename, { type: 'image/png' })

      // 모바일 Web Share API (파일 공유 지원 여부 확인)
      if (
        navigator.share &&
        typeof navigator.canShare === 'function' &&
        navigator.canShare({ files: [file] })
      ) {
        await navigator.share({
          title: '그레이셰프 분석 결과',
          text: `그레이셰프가 내 요리를 평가했어요! 총점 ${result.total_score}점 🍳`,
          files: [file],
        })
      } else {
        // fallback: 이미지 다운로드
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
    } catch (err) {
      if (err.name !== 'AbortError') alert('공유에 실패했습니다.')
    }
  }

  return (
    <main className="flex flex-col items-center px-4 pb-16 animate-fade-in">
      <div className="w-full max-w-sm space-y-3">
        {/* shareRef: 이미지 + 팁 카드 — 캡처 대상 영역 */}
        <div
          ref={shareRef}
          className="space-y-3"
          style={{ backgroundColor: mode === 'spicy' ? '#1a0505' : '#0E0E0C', padding: '0 0 8px' }}
        >
          <ImageCard imageUrl={imageUrl} result={result} mode={mode} cardRef={cardRef} />
          <TipCards result={result} mode={mode} />
        </div>

        <ModeButtons mode={mode} onModeChange={onModeChange} />

        <div className="flex gap-2 pt-1">
          <button
            onClick={handleShare}
            className="flex-1 py-3.5 text-xs tracking-[0.2em] uppercase font-semibold transition-all duration-200"
            style={{
              backgroundColor: 'var(--text)',
              color: 'var(--bg)',
              border: '1px solid var(--text)',
            }}
          >
            📤 결과 공유
          </button>
          <button
            onClick={onReset}
            className="px-5 py-3.5 text-xs tracking-[0.15em] uppercase font-semibold"
            style={{
              backgroundColor: 'transparent',
              color: 'var(--sub)',
              border: '1px solid var(--border)',
            }}
          >
            다시 찍기
          </button>
        </div>
      </div>
    </main>
  )
}
