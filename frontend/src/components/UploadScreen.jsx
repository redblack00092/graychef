import { useRef, useState } from 'react'

export default function UploadScreen({ onImageSelect }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  const handleFile = (file) => {
    if (!file || !file.type.startsWith('image/')) {
      alert('이미지 파일을 선택해주세요.')
      return
    }
    onImageSelect(file)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  return (
    <main className="flex flex-col items-center px-5 pt-2 pb-16 animate-fade-in">
      <div className="w-full max-w-sm">

        {/* Upload zone */}
        <button
          onClick={() => inputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={() => setDragging(false)}
          className="w-full py-16 flex flex-col items-center gap-5 transition-all duration-200 cursor-pointer"
          style={{
            backgroundColor: 'var(--card)',
            border: `1px solid ${dragging ? 'var(--gold)' : 'var(--border)'}`,
          }}
        >
          <span className="text-3xl opacity-60">📷</span>
          <div className="text-center">
            <p
              className="text-xs tracking-[0.2em] uppercase font-medium mb-2"
              style={{ color: 'var(--text)' }}
            >
              음식 사진 업로드
            </p>
            <p className="text-xs tracking-wide" style={{ color: 'var(--sub)' }}>
              탭해서 갤러리 또는 카메라 선택
            </p>
          </div>
        </button>

        {/* Tip card */}
        <div
          className="mt-6 pl-4 py-2"
          style={{ borderLeft: '2px solid var(--gold)' }}
        >
          <p className="text-xs leading-relaxed" style={{ color: 'var(--sub)' }}>
            자연광에서 촬영하면 더 정확한 분석 결과를 얻을 수 있습니다.
            음식 전체가 잘 보이도록 구도를 잡아주세요.
          </p>
        </div>

        <p className="text-center text-xs mt-6" style={{ color: 'var(--sub)' }}>
          JPG · PNG · WEBP &nbsp;·&nbsp; 최대 10MB
        </p>

        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          className="hidden"
          onChange={(e) => handleFile(e.target.files[0])}
        />
      </div>
    </main>
  )
}
