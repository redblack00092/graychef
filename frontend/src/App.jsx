import { useState } from 'react'
import Header from './components/Header'
import UploadScreen from './components/UploadScreen'
import LoadingScreen from './components/LoadingScreen'
import ResultScreen from './components/ResultScreen'

export default function App() {
  const [screen, setScreen] = useState('upload') // 'upload' | 'loading' | 'result'
  const [imageUrl, setImageUrl] = useState(null)
  const [result, setResult] = useState(null)
  const [mode, setMode] = useState('sweet') // 'sweet' | 'spicy'

  const handleImageSelect = async (file) => {
    const url = URL.createObjectURL(file)
    setImageUrl(url)
    setScreen('loading')

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/analyze', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({}))
        throw new Error(err.detail || '서버 오류가 발생했습니다.')
      }

      const data = await response.json()
      setResult(data)
      setMode('sweet')
      setScreen('result')
    } catch (error) {
      alert(`분석 실패: ${error.message}\n다시 시도해 주세요.`)
      setScreen('upload')
      setImageUrl(null)
    }
  }

  const handleReset = () => {
    setScreen('upload')
    setImageUrl(null)
    setResult(null)
    setMode('sweet')
  }

  const isSpicy = screen === 'result' && mode === 'spicy'

  return (
    <div
      className="min-h-screen transition-colors duration-500"
      style={{ backgroundColor: isSpicy ? 'var(--spicy-bg)' : 'var(--bg)' }}
    >
      <Header />
      {screen === 'upload' && (
        <UploadScreen onImageSelect={handleImageSelect} />
      )}
      {screen === 'loading' && (
        <LoadingScreen imageUrl={imageUrl} />
      )}
      {screen === 'result' && (
        <ResultScreen
          imageUrl={imageUrl}
          result={result}
          mode={mode}
          onModeChange={setMode}
          onReset={handleReset}
        />
      )}
    </div>
  )
}
