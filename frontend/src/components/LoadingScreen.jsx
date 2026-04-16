export default function LoadingScreen({ imageUrl }) {
  return (
    <main className="flex flex-col items-center px-5 pb-16 animate-fade-in">
      <div className="w-full max-w-sm">
        {imageUrl && (
          <div className="relative overflow-hidden mb-6" style={{ border: '1px solid var(--border)' }}>
            <img
              src={imageUrl}
              alt="업로드한 음식"
              className="w-full object-cover"
              style={{ maxHeight: '65vw' }}
            />
            <div
              className="absolute inset-0 flex flex-col items-center justify-center gap-4"
              style={{ backgroundColor: 'rgba(14,14,12,0.75)' }}
            >
              {/* Animated bars */}
              <div className="flex items-end gap-1.5" style={{ height: 24 }}>
                <span className="load-bar" />
                <span className="load-bar" />
                <span className="load-bar" />
                <span className="load-bar" />
                <span className="load-bar" />
              </div>
              <p className="text-xs tracking-[0.25em] uppercase" style={{ color: 'var(--gold)' }}>
                ANALYSING
              </p>
            </div>
          </div>
        )}

        <div className="space-y-2">
          {['플레이팅 분석 중', '건강 점수 계산 중', '예상 맛 예측 중'].map((text, i) => (
            <div
              key={text}
              className="flex items-center gap-3 px-4 py-3"
              style={{ backgroundColor: 'var(--card)', border: '1px solid var(--border)' }}
            >
              <div
                className="w-1.5 h-1.5 animate-pulse"
                style={{
                  backgroundColor: 'var(--gold)',
                  animationDelay: `${i * 0.3}s`,
                }}
              />
              <span className="text-xs tracking-wide" style={{ color: 'var(--sub)' }}>
                {text}
              </span>
            </div>
          ))}
        </div>
      </div>
    </main>
  )
}
